import subprocess
import time


class iOSSimulator:
    def __init__(self, udid="booted"):
        self.udid = udid

    def _find_udid(self):
        import json
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "--json"],
            capture_output=True, text=True, check=True
        )
        devices = json.loads(result.stdout).get("devices", {})
        for runtime, devlist in devices.items():
            if "iOS" not in runtime:
                continue
            for dev in devlist:
                if dev.get("isAvailable"):
                    return dev["udid"]
        raise RuntimeError("No available iOS simulator found")

    def boot(self):
        if self.udid == "booted":
            self.udid = self._find_udid()
        result = subprocess.run(
            ["xcrun", "simctl", "boot", self.udid],
            capture_output=True, text=True
        )
        # "Unable to boot device in current state: Booted" is fine
        if result.returncode != 0 and "current state: Booted" not in result.stderr:
            raise RuntimeError(f"Boot failed: {result.stderr.strip()}")

    def wait_until_booted(self, timeout=60):
        start = time.time()
        while time.time() - start < timeout:
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", self.udid],
                capture_output=True, text=True
            )
            if "Booted" in result.stdout:
                return
            time.sleep(2)
        raise RuntimeError("Simulator did not boot in time")

    def open_simulator_app(self):
        subprocess.run(["open", "-a", "Simulator"], check=True)
        self.wait_until_booted()

    def open_settings(self):
        subprocess.run(
            ["xcrun", "simctl", "launch", self.udid, "com.apple.Preferences"],
            check=True
        )

    def launch(self):
        self.boot()
        self.open_simulator_app()
        self.open_settings()


if __name__ == "__main__":
    sim = iOSSimulator()
    sim.launch()
