# Контекст для Claude — Рыцари и Замки

## Статус
Версия 2 в разработке. Основной движок работает, 3 главы кампании готовы, структура ИИ настроена.

## Что делали в последний раз
- Создали документацию по шаблону (info.md, description.md, roadmap.md, bugs.md, changelog.md, context.md)

## Что нужно сделать сейчас
- Заполнить roadmap — решить что делать в v3

## Важные детали
- Весь игровой код — в `KnightsGame/index.html` (один большой файл)
- Сюжет и пресеты ИИ — в `KnightsGame/story.txt`
- Swift-обёртка: `MyApp.swift` (GitHubUpdater + LoadingGameView + App), `ContentView.swift` (WKWebView)
- GitHubUpdater: сначала ищет index.html в Documents/KnightsGame/, если нет — берёт из Bundle. Позволяет обновлять игру без пересборки через Finder/Files
- Canvas зафиксирован на 480×960 пикселей, масштабируется через CSS

## Что нельзя ломать
- Структура Package.swift (Swift Playgrounds её перезаписывает — не редактировать вручную)
- Механизм GitHubUpdater — путь Documents/KnightsGame/ должен совпадать с `gameFolder`
- `story.txt` — формат файла важен, парсится JS-кодом в index.html

## Открытые вопросы
- Что делать в следующей версии?
- Нужна ли Глава 4 или сначала полировать существующее?
