#!/usr/bin/env python3
"""
wda_control.py — minimal WebDriverAgent client: keyboard input + button taps.

Talks to an already-running WebDriverAgent HTTP server (default
http://localhost:8100) and exposes just two primitives plus the glue needed
to use them:

    * keyboard input  -> POST /session/:id/wda/keys
    * tap any button  -> POST /session/:id/element        (find)
                         POST /session/:id/element/:id/click  (tap)

No third-party dependencies (uses only the Python standard library), so it
runs as-is with any Python 3.7+.

Intended for automating a device you own / are authorized to test.

Usage as a CLI
--------------
    # check the server is up
    python3 wda_control.py status

    # type a string into the currently focused field
    python3 wda_control.py keys 1234

    # tap a button by its name / accessibility id
    python3 wda_control.py tap "Continue"

    # tap by iOS predicate string (e.g. partial label match)
    python3 wda_control.py tap-pred "label CONTAINS 'Next'"

    # tap by xpath
    python3 wda_control.py tap-xpath "//XCUIElementTypeButton[@name='1']"

    # dump the current accessibility tree (to find element names)
    python3 wda_control.py source

Usage as a library
------------------
    from wda_control import WDA
    wda = WDA()                 # connects + creates a session
    wda.keys("1234")            # type
    wda.tap_button("Continue")  # find by name/accessibility id and tap
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "http://localhost:8100"
# W3C element-reference key returned by find-element calls.
W3C_KEY = "element-6066-11e4-a52e-4f735466cecf"


class WDAError(RuntimeError):
    """Raised when WebDriverAgent returns an error or is unreachable."""


class WDA:
    """Thin WebDriverAgent client: just enough for typing and tapping."""

    def __init__(self, base=DEFAULT_BASE, session_id=None, timeout=30, auto_session=True):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.session_id = session_id
        if auto_session and self.session_id is None:
            self.create_session()

    # ---- low-level HTTP -------------------------------------------------

    def _request(self, method, path, body=None):
        url = self.base + path
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
        except urllib.error.URLError as exc:
            raise WDAError(f"cannot reach WDA at {url}: {exc.reason}") from exc
        except OSError as exc:
            # e.g. ConnectionResetError / ConnectionRefusedError from the bridge
            raise WDAError(f"connection error to {url}: {exc}") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            raise WDAError(f"non-JSON response from {url}: {raw[:200]!r}")

        # WDA wraps errors as {"value": {"error": ..., "message": ...}}
        value = payload.get("value")
        if isinstance(value, dict) and value.get("error"):
            raise WDAError(f"{value.get('error')}: {value.get('message', '')}".strip())
        return payload

    def _session_path(self, suffix=""):
        if not self.session_id:
            raise WDAError("no active session; call create_session() first")
        return f"/session/{self.session_id}{suffix}"

    # ---- session --------------------------------------------------------

    def status(self):
        return self._request("GET", "/status").get("value", {})

    def create_session(self, capabilities=None):
        # shouldWaitForQuiescence=false: don't block each command waiting for the
        # app (keyboard animations etc.) to go idle — a big per-command speedup.
        caps = {"shouldWaitForQuiescence": False}
        if capabilities:
            caps.update(capabilities)
        body = {
            "capabilities": {"alwaysMatch": caps, "firstMatch": [{}]},
            "desiredCapabilities": caps,  # legacy field some builds still read
        }
        payload = self._request("POST", "/session", body)
        value = payload.get("value") or {}
        self.session_id = value.get("sessionId") or payload.get("sessionId")
        if not self.session_id:
            raise WDAError(f"could not obtain sessionId from: {payload}")
        # Also disable the idle/animation cool-off waits at the settings level.
        try:
            self.set_settings({"waitForIdleTimeout": 0, "animationCoolOffTimeout": 0})
        except WDAError:
            pass  # older WDA builds may not support these keys
        return self.session_id

    def set_settings(self, settings):
        """Update WDA session settings (e.g. {'waitForIdleTimeout': 0})."""
        self._request("POST", self._session_path("/appium/settings"),
                      {"settings": settings})
        return True

    # ---- inspection -----------------------------------------------------

    def source(self):
        """Return the current accessibility tree as a string."""
        return self._request("GET", self._session_path("/source")).get("value", "")

    # ---- keyboard input -------------------------------------------------

    def keys(self, text):
        """Type `text` into the currently focused field (one char at a time)."""
        body = {"value": list(str(text))}
        self._request("POST", self._session_path("/wda/keys"), body)
        return True

    # ---- buttons / taps -------------------------------------------------

    def find(self, using, value):
        """Return an element id for the first match, or None if not found."""
        body = {"using": using, "value": value}
        try:
            payload = self._request("POST", self._session_path("/element"), body)
        except WDAError as exc:
            if "no such element" in str(exc).lower():
                return None
            raise
        el = payload.get("value") or {}
        return el.get(W3C_KEY) or el.get("ELEMENT")

    def attribute(self, element_id, name):
        """Read an element attribute, e.g. 'value', 'label', 'enabled'."""
        path = self._session_path(f"/element/{element_id}/attribute/{name}")
        return self._request("GET", path).get("value")

    def value_of(self, using, value):
        """Find an element and return its 'value' attribute, or None if absent."""
        element_id = self.find(using, value)
        if element_id is None:
            return None
        return self.attribute(element_id, "value")

    def is_enabled(self, element_id):
        """Return whether an element is enabled (tappable)."""
        path = self._session_path(f"/element/{element_id}/enabled")
        return bool(self._request("GET", path).get("value"))

    def tap_element(self, element_id):
        """Tap an element by its WDA element id."""
        self._request("POST", self._session_path(f"/element/{element_id}/click"), {})
        return True

    def tap_button(self, name, using="accessibility id", strict=True):
        """Find a button/element by `name` and tap it.

        `using` strategies: "accessibility id", "name", "class name",
        "-ios predicate string", "xpath".
        """
        element_id = self.find(using, name)
        if element_id is None:
            if strict:
                raise WDAError(f"no element matched ({using} = {name!r})")
            return False
        return self.tap_element(element_id)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(description="Minimal WDA keyboard + button control.")
    p.add_argument("--base", default=os.environ.get("WDA_BASE", DEFAULT_BASE),
                   help=f"WDA base URL (default $WDA_BASE or {DEFAULT_BASE})")
    p.add_argument("--session", help="reuse an existing session id instead of creating one")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="print server status")
    sub.add_parser("source", help="dump the current accessibility tree")

    sp = sub.add_parser("keys", help="type text into the focused field")
    sp.add_argument("text", help="text to type, e.g. 1234")

    sp = sub.add_parser("tap", help="tap a button by name / accessibility id")
    sp.add_argument("name")

    sp = sub.add_parser("tap-pred", help="tap by iOS predicate string")
    sp.add_argument("predicate")

    sp = sub.add_parser("tap-xpath", help="tap by xpath")
    sp.add_argument("xpath")

    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    need_session = args.cmd != "status"
    try:
        wda = WDA(base=args.base, session_id=args.session, auto_session=need_session)

        if args.cmd == "status":
            print(json.dumps(wda.status(), indent=2))
        elif args.cmd == "source":
            print(wda.source())
        elif args.cmd == "keys":
            wda.keys(args.text)
            print(f"typed: {args.text}")
        elif args.cmd == "tap":
            wda.tap_button(args.name, using="accessibility id")
            print(f"tapped: {args.name}")
        elif args.cmd == "tap-pred":
            wda.tap_button(args.predicate, using="-ios predicate string")
            print(f"tapped (predicate): {args.predicate}")
        elif args.cmd == "tap-xpath":
            wda.tap_button(args.xpath, using="xpath")
            print(f"tapped (xpath): {args.xpath}")
    except WDAError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
