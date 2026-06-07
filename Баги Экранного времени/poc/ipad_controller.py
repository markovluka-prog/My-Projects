import time
import subprocess
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.screenshot import ScreenshotService
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.services.dvt.instruments.device_info import DeviceInfo
from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
from pymobiledevice3.services.springboard import SpringBoardServicesService


class iPadController:
    # Координаты для iPhone/iPad (нормализованные 0.0–1.0 от размера экрана)
    # Будут конвертированы в пиксели после подключения

    SETTINGS_BUNDLE = "com.apple.Preferences"

    def __init__(self):
        self.lockdown = None
        self.screen_width = None
        self.screen_height = None

    def connect(self):
        """Подключиться к iPad по USB."""
        self.lockdown = create_using_usbmux()
        print(f"Подключён: {self.lockdown.product_type} — iOS {self.lockdown.product_version}")

    def screenshot(self, path="/tmp/ipad_screen.png"):
        """Сделать скриншот и сохранить."""
        data = ScreenshotService(self.lockdown).take_screenshot()
        with open(path, "wb") as f:
            f.write(data)
        print(f"Скриншот сохранён: {path}")
        return path

    def launch_app(self, bundle_id):
        """Запустить приложение по bundle ID."""
        subprocess.run(
            ["xcrun", "devicectl", "device", "process", "launch",
             "--device", self.lockdown.udid, bundle_id],
            capture_output=True
        )
        time.sleep(1.5)

    def tap(self, x_ratio, y_ratio):
        """
        Тап по относительным координатам (0.0–1.0).
        Использует HID-сервис pymobiledevice3.
        """
        from pymobiledevice3.services.hid import HIDService
        hid = HIDService(self.lockdown)

        # Получить реальный размер экрана из скриншота
        if not self.screen_width:
            self._detect_screen_size()

        x = int(x_ratio * self.screen_width)
        y = int(y_ratio * self.screen_height)

        hid.click(x, y)
        time.sleep(0.5)

    def type_text(self, text):
        """Ввести текст (для полей ввода)."""
        from pymobiledevice3.services.hid import HIDService
        hid = HIDService(self.lockdown)
        for char in text:
            hid.press(char)
            time.sleep(0.05)

    def _detect_screen_size(self):
        """Определить размер экрана через скриншот."""
        from PIL import Image
        path = self.screenshot("/tmp/_size_check.png")
        img = Image.open(path)
        self.screen_width, self.screen_height = img.size
        print(f"Экран: {self.screen_width}x{self.screen_height}")

    # ── Навигация по настройкам ──────────────────────────────────────

    def open_settings(self):
        """Открыть Настройки."""
        self.launch_app(self.SETTINGS_BUNDLE)
        time.sleep(1)
        print("Настройки открыты")

    def go_to_erase(self):
        """
        Путь: Настройки → Основные → Перенос или сброс → Стереть контент.
        Возвращает скриншот финального экрана.
        """
        self.open_settings()
        time.sleep(1)

        # Нажать "Основные" (примерно y=30% от верха списка)
        self.tap(0.5, 0.30)
        time.sleep(0.8)
        self._screenshot_step("01_general")

        # Скролл вниз до "Перенос или сброс iPhone"
        self._scroll_down()
        time.sleep(0.5)

        # Нажать "Перенос или сброс"
        self.tap(0.5, 0.85)
        time.sleep(0.8)
        self._screenshot_step("02_transfer_reset")

        # Нажать "Стереть контент и настройки"
        self.tap(0.5, 0.65)
        time.sleep(0.8)
        self._screenshot_step("03_erase")

    def enter_passcode(self, passcode: str):
        """Ввести пароль устройства на экране пин-кода."""
        for digit in passcode:
            self._tap_digit(digit)
            time.sleep(0.3)
        time.sleep(1)
        self._screenshot_step("04_after_passcode")

    def enter_screen_time_passcode(self, passcode: str):
        """Ввести пароль Screen Time."""
        for digit in passcode:
            self._tap_digit(digit)
            time.sleep(0.3)
        time.sleep(1)
        return self._screenshot_step("05_after_screen_time")

    def check_apple_id_dialog(self) -> bool:
        """Проверить — появился ли диалог Apple ID на экране."""
        path = self.screenshot("/tmp/ipad_check.png")
        # Простая проверка через ocr или анализ скриншота
        # Здесь — визуальная проверка через имя файла
        print(f"Проверь скриншот: {path}")
        return path

    def _tap_digit(self, digit: str):
        """Тап по цифре на PIN-клавиатуре iOS."""
        # Клавиатура занимает нижние ~50% экрана, 3 колонки x 4 строки
        digit_positions = {
            "1": (0.17, 0.58), "2": (0.50, 0.58), "3": (0.83, 0.58),
            "4": (0.17, 0.68), "5": (0.50, 0.68), "6": (0.83, 0.68),
            "7": (0.17, 0.78), "8": (0.50, 0.78), "9": (0.83, 0.78),
            "0": (0.50, 0.88),
        }
        if digit in digit_positions:
            x, y = digit_positions[digit]
            self.tap(x, y)

    def _scroll_down(self):
        """Свайп вверх (скролл вниз) посередине экрана."""
        from pymobiledevice3.services.hid import HIDService
        hid = HIDService(self.lockdown)
        if not self.screen_width:
            self._detect_screen_size()
        cx = self.screen_width // 2
        hid.swipe(cx, int(self.screen_height * 0.7), cx, int(self.screen_height * 0.3))
        time.sleep(0.5)

    def _screenshot_step(self, name: str):
        path = f"/tmp/ipad_{name}.png"
        self.screenshot(path)
        return path


def check(passcode: str, screen_time_passcode: str) -> bool:
    """
    Полный путь: Настройки → Основные → Стереть контент →
    ввод пароля устройства → ввод пароля Screen Time →
    проверка появления диалога Apple ID.

    Возвращает True если диалог Apple ID появился, False если нет.
    """
    ipad = iPadController()
    ipad.connect()

    ipad.go_to_erase()

    # Нажать Continue
    ipad.tap(0.5, 0.75)
    time.sleep(1)

    ipad.enter_passcode(passcode)
    ipad.enter_screen_time_passcode(screen_time_passcode)

    # Скриншот финального экрана
    path = ipad.screenshot("/tmp/ipad_result.png")

    # Проверить наличие диалога Apple ID по скриншоту
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(path).convert("RGB")
        # Диалог Apple ID обычно появляется в центре экрана
        # Делаем простую проверку — если экран не чёрный и не PIN-экран
        w, h = img.size
        center_pixel = img.getpixel((w // 2, h // 2))
        # Белый/светлый центр = диалог открыт
        apple_id_visible = all(c > 200 for c in center_pixel)
    except ImportError:
        # Без Pillow — просто сообщаем путь
        apple_id_visible = None
        print(f"Установи Pillow для авто-проверки: pip install pillow")

    print(f"Скриншот результата: {path}")
    print(f"Диалог Apple ID появился: {apple_id_visible}")
    return apple_id_visible


if __name__ == "__main__":
    result = check(
        passcode="1234",
        screen_time_passcode="0000"
    )
    print(f"Результат: {result}")
