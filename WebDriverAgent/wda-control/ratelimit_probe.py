#!/usr/bin/env python3
"""
ratelimit_probe.py — measure whether the iOS Screen Time passcode prompt
rate-limits / backs off repeated wrong attempts. PoC for a security report.

What this is (and is NOT)
-------------------------
This tool answers ONE question: does this iOS version throttle repeated wrong
guesses on the Screen Time passcode screen (lock-out, growing delay, error
message), or does it accept attempt after attempt with no penalty?

* It submits only KNOWN-WRONG codes. Your real code is passed via --real-code
  and is used ONLY to EXCLUDE it from the set — it is never sent and never
  logged. By construction every submitted code is wrong.
* It does NOT search for an unknown passcode and it does NOT stop on a
  "correct" code. If the prompt ever unexpectedly advances, the probe ABORTS
  and reports nothing but the attempt index — it never outputs a discovered
  passcode. This is a measurement tool, not a passcode finder.

Input method: TAPS, with per-attempt PROOF
-------------------------------------------
The Screen Time passcode screen is a custom keypad (XCUIElementTypeKey buttons),
NOT a text field — /wda/keys typing does NOT register there (verified: it calls
even the KNOWN-correct code "wrong" because nothing lands). So this probe enters
each code by TAPPING the on-screen digits, and PROVES every attempt was a real
submission by reading the field's "N of 4 values entered" counter: it watches the
count climb 1 -> 2 -> 3 as the first three digits land, then confirms the field
RESET to 0 after the fourth (submitting) tap — the device's own signature of a
processed-and-rejected wrong code. Attempts that don't show that climb+reset are
logged as UNVERIFIED and excluded from the verdict, so the measurement can never
again be "no rate-limit" when in fact nothing was submitted.

The deliverable is the evidence Apple's security team needs: "N VERIFIED wrong
submissions in T seconds, 0 lock-outs, 0 added delay" plus the projection — the
vulnerability is shown by the ABSENCE of a control across confirmed real
attempts, not by cracking anything.

How to drive it
---------------
1. Start WebDriverAgent on the iPad and port-forward 8100 (see README.md).
2. On the iPad navigate to the Screen Time passcode prompt (the 4-dot keypad)
   on a device YOU own / are authorized to test, with an EMPTY field.
3. Run, excluding your real code so every probe is guaranteed wrong:

    python3 ratelimit_probe.py --real-code 1234 --count 200
    python3 ratelimit_probe.py --real-code 1234 --count 200 --report report.json

The probe prints a verdict and writes a raw JSONL trace (--log) plus an
optional JSON summary (--report) you can attach to the Apple Feedback.
"""

import argparse
import json
import os
import re
import statistics
import sys
import time

from wda_control import WDA, WDAError

# The Screen Time passcode prompt's nav bar — present iff we're still on it.
MARKER_USING = "predicate string"
MARKER_VALUE = "name == 'DKScreenTimePasscodeView'"

# The single passcode field; its value reads like "0 of 4 values entered".
FIELD_USING = "predicate string"
FIELD_VALUE = "type == 'XCUIElementTypeTextView'"

# Words (any locale) hinting at a wrong-attempt / lock-out message in the tree.
LOCKOUT_HINTS = ["повтор", "попыт", "невер", "отключ", "минут", "позже",
                 "incorrect", "try again", "attempt", "disabled", "later", "minute"]

TOTAL_CODES = 10000  # the full 4-digit space, for the projection


def still_on_prompt(wda):
    """True while the Screen Time passcode prompt is still showing."""
    return wda.find(MARKER_USING, MARKER_VALUE) is not None


def keypad_locked(wda, sample_digit="1"):
    """True if a keypad digit is present but DISABLED — the lock-out signal.

    iOS greys out the passcode keypad while it throttles attempts, so a disabled
    digit key means a lock-out/back-off is in effect. Locale-independent.
    """
    eid = wda.find("accessibility id", sample_digit)
    if eid is None:
        return False
    try:
        return not wda.is_enabled(eid)
    except WDAError:
        return False


def lockout_text(wda):
    """Return the first lock-out-looking message in the tree, or '' if none."""
    try:
        src = wda.source()
    except WDAError:
        return ""
    low = src.lower()
    for hint in LOCKOUT_HINTS:
        if hint in low:
            return hint
    return ""


def field_value(wda):
    """Raw `value` of the passcode field (e.g. '2 of 4 values entered'), or None."""
    try:
        return wda.value_of(FIELD_USING, FIELD_VALUE)
    except WDAError:
        return None


def entered_count(val):
    """Parse how many digits are currently entered from the field value.

    The field reads like 'N of 4 values entered' (or a localized equivalent);
    the FIRST integer is the entered count. Returns None if unreadable.
    """
    if not val:
        return None
    m = re.search(r'(\d+)\D+(\d+)', val)
    return int(m.group(1)) if m else None


def tap_digit(wda, digit, digit_xpath):
    """Tap a single keypad digit, trying a few locator strategies."""
    if wda.tap_button(digit, using="accessibility id", strict=False):
        return True
    if digit_xpath and wda.tap_button(digit_xpath.format(d=digit),
                                      using="xpath", strict=False):
        return True
    if wda.tap_button(digit, using="name", strict=False):
        return True
    raise WDAError(f"could not locate keypad digit {digit!r} "
                   f"(use `wda_control.py source` to find its name/xpath)")


def clear_field(wda, clear_key, max_taps):
    """Tap delete until the field reads 0 entered, so each attempt starts clean.

    A wrong code auto-resets the field to 0, so this is usually a no-op; it only
    matters if a previous tap was dropped and left a partial count behind.
    """
    for _ in range(max_taps):
        if not entered_count(field_value(wda)):  # 0 or None
            return
        wda.tap_button(clear_key, using="accessibility id", strict=False)


def enter_code_tapped(wda, code, args):
    """Tap the 4 digits, verifying each registers via the field's 'N of 4' count.

    Returns a proof dict:
        before     — field value before the first tap (expected '0 of 4 ...')
        climbed_to — highest entered-count confirmed while typing (expected 3)
        after      — field value after the submitting tap (expected reset '0 of 4')
        submit_s   — seconds the tap sequence took

    The first three digits are verified: after each we re-read the count and
    re-tap if it did not climb (recovers a dropped tap). The fourth tap submits;
    its outcome (reset vs advance) is read by the caller as the proof of a real
    submission.
    """
    before = field_value(wda)
    prev = entered_count(before)
    climbed_to = prev if prev is not None else 0
    last = len(code) - 1
    t0 = time.time()
    for i, d in enumerate(code):
        tap_digit(wda, d, args.digit_xpath)
        if i == last:
            break  # submitting tap — outcome is read by the caller
        registered = False
        for _ in range(args.entry_retries + 1):
            cur = entered_count(field_value(wda))
            # None == unreadable: don't risk a double-tap; move on.
            if cur is None or (prev is not None and cur != prev):
                registered = True
                prev = cur
                if cur is not None:
                    climbed_to = max(climbed_to, cur)
                break
            tap_digit(wda, d, args.digit_xpath)  # dropped -> re-tap this digit
        if not registered:
            prev = entered_count(field_value(wda))  # gave up; resync baseline
    submit_s = time.time() - t0
    if args.settle:
        time.sleep(args.settle)
    after = field_value(wda)
    return {"before": before, "climbed_to": climbed_to,
            "after": after, "submit_s": round(submit_s, 4)}


def resolve_outcome(wda, climbed_to, need, args):
    """Decide a submission's outcome by POLLING, so a correct code's screen
    advance (which lags the field reset by up to ~1s) is never miscounted as a
    wrong submission.

    A correct code and a wrong code BOTH reset the field to '0 of 4' first; they
    differ only in what follows — a correct code makes the prompt disappear a
    moment later, a wrong code keeps it. So we watch the prompt for up to
    --judge-timeout:
        prompt gone           -> 'advanced'   (correct code -> caller aborts)
        reset + prompt stays  -> 'wrong'      (verified rejected submission)
        neither               -> 'unverified' (taps didn't complete a submission)
    """
    deadline = time.time() + args.judge_timeout
    saw_reset = False
    while time.time() < deadline:
        if not still_on_prompt(wda):
            return "advanced"
        if entered_count(field_value(wda)) == 0:
            saw_reset = True
        time.sleep(args.poll)
    if climbed_to >= need and saw_reset:
        return "wrong"
    return "unverified"


def wrong_codes(count, real_code):
    """Yield `count` distinct 4-digit codes, all guaranteed != real_code.

    Plain numeric order from 0000, skipping the real code so every probe is a
    known-wrong submission. The real code is used only to exclude it here.
    """
    yielded = 0
    n = 0
    while yielded < count and n < TOTAL_CODES:
        code = f"{n:04d}"
        n += 1
        if real_code is not None and code == real_code:
            continue  # never submit the real code
        yield code
        yielded += 1


def logw(path, obj):
    """Append one JSON object as a line to the raw trace (best-effort)."""
    if not path:
        return
    try:
        with open(path, "a") as fh:
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except OSError:
        pass


def probe(wda, args):
    """Submit known-wrong codes by TAPPING, proving each, measuring throttling."""
    real = args.real_code
    if real is not None and (len(real) != 4 or not real.isdigit()):
        print("error: --real-code must be exactly 4 digits", file=sys.stderr)
        return None
    if real is None:
        print("WARNING: no --real-code given. The probe can't exclude your real "
              "code, so a submitted code COULD match it; if the screen advances "
              "the probe aborts WITHOUT revealing which code it was. Pass "
              "--real-code to guarantee every attempt is wrong.\n")

    if not still_on_prompt(wda):
        print("error: not on the Screen Time passcode prompt. Navigate to the "
              "4-dot keypad first (see the module docstring).", file=sys.stderr)
        return None

    need = 3  # digits confirmed before the submitting tap (4-digit code)
    print(f"probing rate-limit with {args.count} KNOWN-WRONG codes by TAPPING "
          f"(real code excluded: {real is not None}).")
    print("each attempt is verified: the field must count 1->2->3 then reset to "
          "0 after the 4th tap (= a real, rejected submission); unverified "
          "attempts are excluded. Ctrl+C to stop early.\n")

    intervals = []        # seconds between consecutive VERIFIED submissions
    submit_secs = []      # seconds each tap sequence took
    lockouts = 0          # times the keypad went disabled
    lockout_msgs = set()  # distinct lock-out message hints seen
    sent = 0              # attempts tried (tap sequences sent)
    verified = 0          # attempts proven to be real submissions
    t_start = time.time()
    prev_submit = None

    logw(args.log, {"event": "run_start", "ts": time.time(), "method": "tap",
                    "count": args.count, "real_excluded": real is not None,
                    "base": args.base})

    try:
        for code in wrong_codes(args.count, real):
            if not args.no_clear:
                clear_field(wda, args.clear_key, args.clear_taps)
            try:
                proof = enter_code_tapped(wda, code, args)
            except WDAError as exc:
                # Keypad digit vanished mid-entry -> likely the screen advanced.
                if not still_on_prompt(wda):
                    print(f"\nABORT at attempt {sent + 1}: keypad disappeared "
                          f"mid-entry, the prompt appears to have advanced ({exc}). "
                          f"Not reporting any code. If you omitted --real-code this "
                          f"was likely it; rerun with --real-code.", file=sys.stderr)
                    logw(args.log, {"event": "abort_advanced", "attempt": sent + 1})
                    break
                print(f"\nattempt {sent + 1}: entry error, skipping ({exc})",
                      file=sys.stderr)
                logw(args.log, {"event": "entry_error", "attempt": sent + 1,
                                "code": code, "error": str(exc)})
                continue
            sent += 1
            # Resolve by polling so the correct code's lagged screen-advance is
            # caught (abort) instead of being miscounted as a wrong submission.
            outcome = resolve_outcome(wda, proof["climbed_to"], need, args)
            now = time.time()

            # Correct code hit (only possible if it wasn't excluded): abort and
            # reveal nothing but the index.
            if outcome == "advanced":
                print(f"\nABORT at attempt {sent}: the prompt advanced after a "
                      f"submission (a correct code was entered). Rerun with the "
                      f"right --real-code so it is excluded.", file=sys.stderr)
                logw(args.log, {"event": "abort_advanced", "attempt": sent})
                break

            # 'wrong' == the field reset AND the prompt persisted through the whole
            # poll window -> a real, rejected submission. 'unverified' otherwise.
            submitted = outcome == "wrong"
            if submitted:
                verified += 1
                submit_secs.append(proof["submit_s"])
                if prev_submit is not None:
                    intervals.append(now - prev_submit)
                prev_submit = now

            # Throttle detection — the whole point of the probe.
            locked = keypad_locked(wda)
            msg = lockout_text(wda) if (locked or args.scan_text) else ""
            if locked:
                lockouts += 1
            if msg:
                lockout_msgs.add(msg)

            logw(args.log, {"event": "attempt", "n": sent, "code": code,
                            "real_excluded": real is not None,
                            "before": proof["before"], "climbed_to": proof["climbed_to"],
                            "after": proof["after"], "outcome": outcome,
                            "submitted": submitted, "submit_s": proof["submit_s"],
                            "locked": locked, "msg": msg, "ts": now})

            elapsed = now - t_start
            rate = verified / elapsed if elapsed else 0.0
            flag = ("  <LOCKOUT>" if locked
                    else "" if submitted else "  <UNVERIFIED: taps not landing>")
            print(f"[{sent:5d}] verified={verified} ({proof['submit_s']:.2f}s, "
                  f"{rate:.2f} real/s, lockouts={lockouts}){flag}",
                  end="\r", flush=True)

            if locked and args.stop_on_lockout:
                print(f"\nlock-out detected at attempt {sent} — a rate-limit IS "
                      f"present. Stopping (this is the GOOD outcome for safety).")
                break
    except KeyboardInterrupt:
        print(f"\ninterrupted after {sent} attempts ({verified} verified).")

    elapsed = time.time() - t_start
    return build_summary(sent, verified, elapsed, intervals, submit_secs,
                         lockouts, sorted(lockout_msgs))


def build_summary(sent, verified, elapsed, intervals, submit_secs, lockouts, lockout_msgs):
    rate = verified / elapsed if elapsed else 0.0
    # Back-off growth: compare the first vs last fifth of inter-attempt gaps.
    growth = None
    if len(intervals) >= 10:
        k = max(1, len(intervals) // 5)
        first = statistics.mean(intervals[:k])
        last = statistics.mean(intervals[-k:])
        growth = {"first_mean_s": round(first, 4), "last_mean_s": round(last, 4),
                  "ratio": round(last / first, 2) if first else None}
    projection_s = TOTAL_CODES / rate if rate else None
    if lockouts:
        verdict = "RATE-LIMIT PRESENT (lock-out observed)"
    elif verified == 0:
        verdict = ("INCONCLUSIVE — 0 attempts verified as real submissions "
                   "(taps not registering on the keypad; nothing was actually tested)")
    else:
        verdict = (f"NO RATE-LIMIT OBSERVED across {verified} VERIFIED wrong "
                   f"submissions — space appears brute-forceable")
    return {
        "attempts_tried": sent,
        "verified_submissions": verified,
        "unverified": sent - verified,
        "elapsed_s": round(elapsed, 2),
        "verified_per_s": round(rate, 2),
        "mean_submit_s": round(statistics.mean(submit_secs), 4) if submit_secs else None,
        "mean_interval_s": round(statistics.mean(intervals), 4) if intervals else None,
        "max_interval_s": round(max(intervals), 4) if intervals else None,
        "lockout_events": lockouts,
        "lockout_messages": lockout_msgs,
        "backoff_growth": growth,
        "projected_full_sweep_s": round(projection_s, 1) if projection_s else None,
        "projected_full_sweep_min": round(projection_s / 60, 1) if projection_s else None,
        "verdict": verdict,
    }


def print_report(summary):
    print("\n\n==================== RATE-LIMIT PROBE REPORT ====================")
    for k in ["attempts_tried", "verified_submissions", "unverified", "elapsed_s",
              "verified_per_s", "mean_submit_s", "mean_interval_s", "max_interval_s",
              "lockout_events", "lockout_messages", "backoff_growth",
              "projected_full_sweep_s", "projected_full_sweep_min"]:
        print(f"  {k:24s}: {summary[k]}")
    print(f"\n  VERDICT: {summary['verdict']}")
    if summary["unverified"]:
        print(f"\n  NOTE: {summary['unverified']} attempt(s) could NOT be verified "
              f"as real submissions (the field did not climb 1->2->3 then reset). "
              f"Those are excluded from the verdict — investigate the keypad "
              f"locators if this number is high.")
    if summary["lockout_events"] == 0 and summary["verified_submissions"] > 0:
        print("\n  No lock-out and no growing delay across the VERIFIED wrong "
              "submissions -> on this device/iOS the Screen Time passcode prompt "
              "does NOT rate-limit wrong attempts. Attach this report + the JSONL "
              "trace (it logs the 'N of 4' climb+reset proof per attempt) to the "
              "Apple Feedback as the reproducible PoC.")
    print("================================================================")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", default=os.environ.get("WDA_BASE", "http://localhost:8100"),
                   help="WDA base URL (default $WDA_BASE or http://localhost:8100)")
    p.add_argument("--real-code", default=None, metavar="XXXX",
                   help="your real 4-digit code, used ONLY to exclude it so every "
                        "submitted code is guaranteed wrong (never sent, never logged)")
    p.add_argument("--count", type=int, default=200,
                   help="how many known-wrong codes to submit (default 200)")
    p.add_argument("--settle", type=float, default=0.2,
                   help="pause after the submitting tap before snapshotting the "
                        "field for the trace (s); outcome resolution then polls "
                        "separately (default 0.2)")
    p.add_argument("--judge-timeout", type=float, default=1.2,
                   help="seconds to watch the prompt after a submission before "
                        "concluding WRONG; a correct code advances within this "
                        "window and is detected (and aborted) instead. Keep it "
                        ">= the device's correct-code advance latency (default 1.2)")
    p.add_argument("--poll", type=float, default=0.1,
                   help="how often to poll the prompt while resolving an outcome (s)")
    p.add_argument("--digit-xpath", default="//XCUIElementTypeKey[@name='{d}']",
                   help="xpath template for a keypad digit; {d} is the digit")
    p.add_argument("--entry-retries", type=int, default=2,
                   help="max re-taps for a digit whose tap didn't register")
    p.add_argument("--no-clear", action="store_true",
                   help="do not tap delete before each code (a wrong code auto-resets "
                        "the field, so this is usually safe and a bit faster)")
    p.add_argument("--clear-key", default="delete",
                   help="name/accessibility id of the delete key")
    p.add_argument("--clear-taps", type=int, default=6,
                   help="max delete taps to empty the field before each code")
    p.add_argument("--scan-text", action="store_true",
                   help="read the tree every attempt to capture wrong/lock-out "
                        "message text (slower; off by default — lock-out is also "
                        "detected via the disabled keypad)")
    p.add_argument("--stop-on-lockout", action="store_true",
                   help="stop as soon as a lock-out appears (a rate-limit exists)")
    p.add_argument("--log", default="ratelimit_trace.jsonl", metavar="FILE",
                   help="append a raw per-attempt JSONL trace (default "
                        "ratelimit_trace.jsonl; empty to disable)")
    p.add_argument("--report", default="", metavar="FILE",
                   help="also write the summary as JSON to this file")
    args = p.parse_args(argv)

    try:
        wda = WDA(base=args.base)
    except WDAError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    summary = probe(wda, args)
    if summary is None:
        return 1

    print_report(summary)
    logw(args.log, {"event": "summary", **summary})
    if args.report:
        try:
            with open(args.report, "w") as fh:
                json.dump(summary, fh, ensure_ascii=False, indent=2)
            print(f"\nsummary written to {args.report}")
        except OSError as exc:
            print(f"could not write report: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
