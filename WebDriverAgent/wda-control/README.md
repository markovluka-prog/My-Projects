# wda-control

Минимальный клиент к запущенному **WebDriverAgent** для двух примитивов:

- **ввод с клавиатуры** (`/wda/keys`)
- **тап по любой кнопке/элементу** (поиск элемента + `click`)

Только стандартная библиотека Python 3.7+, без зависимостей. Предназначено
для автоматизации устройства, которым ты владеешь / уполномочен тестировать.

## 1. Запустить WebDriverAgent на устройстве

Из корня репозитория, через Xcode:

1. Открой `WebDriverAgent.xcodeproj`.
2. Выбери таргет **WebDriverAgentRunner**, своё устройство, поставь Team в
   Signing & Capabilities.
3. Запусти тест (`Cmd+U`) — WDA поднимет HTTP-сервер на устройстве.

## 2. Пробросить порт на Mac

WDA слушает порт `8100` на устройстве. Пробрось его на localhost, например
через `iproxy` (из пакета libimobiledevice):

```bash
iproxy 8100 8100
```

Проверь, что сервер виден:

```bash
python3 wda_control.py status
```

## 3. Использование

CLI:

```bash
# напечатать строку в активное поле
python3 wda_control.py keys 1234

# тап по кнопке по name / accessibility id
python3 wda_control.py tap "Continue"

# тап по предикату iOS (частичное совпадение и т.п.)
python3 wda_control.py tap-pred "label CONTAINS 'Next'"

# тап по xpath
python3 wda_control.py tap-xpath "//XCUIElementTypeButton[@name='1']"

# выгрузить дерево элементов — чтобы найти точные name кнопок
python3 wda_control.py source
```

Как библиотека:

```python
from wda_control import WDA

wda = WDA()                  # подключение + создание сессии
wda.keys("1234")             # ввод
wda.tap_button("Continue")   # найти по name/accessibility id и тапнуть
wda.tap_button("1", using="xpath")  # или другой стратегией поиска
```

## Подсказки

- Имена кнопок цифровой клавиатуры обычно равны самой цифре (`"1"`…`"0"`).
  Если `accessibility id` не находит — посмотри `source` и используй
  `tap-xpath` / `tap-pred`.
- `keys` печатает в **сфокусированное** поле. Если фокуса нет — сначала
  тапни по полю.
- Все стратегии поиска: `accessibility id`, `name`, `class name`,
  `-ios predicate string`, `xpath`.
