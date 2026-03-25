# Контекст для Claude — Vocabulary Race

## Статус
Игра рабочая (v2.0). Все экраны, анимации, боты, главное меню — готово.

## Что сделали в последних сессиях
- Откалибровали ROUTE вручную (48 точек, пользователь расставил сам через интерактивный режим)
- Добавили главное меню (screen-menu) с анимированными полосами и машинками
- Добавили экран настройки (screen-setup): слоты игроков, переключатель 👤/🤖, сложность 😊/🔥
- Добавили ботов: botPlayTurn, botDoTask, botFindWords — бот авто-играет, использует спец-карты
- Бот сложность: normal=50% успех, hard=80% успех (явная вероятность)
- Бот авто-использует карту Гонщика и карту Судьи (выбирает жертву с наибольшим счётом)
- Авто-продолжение для людей на экране результата (таймер 4 сек с обратным отсчётом)
- Подсказка после провала: показывает слова которые можно было составить
- Экран победы переработан: трофей, имя победителя с glow, таблица мест, кнопки
- overlay-bot вынесен в fullscreen (position:fixed, z-index:300)
- offset фишек масштабируется относительно размера поля (ir.width * 0.032)
- Поворот машинки в сторону следующей клетки (CSS --ta переменная)
- Плавное движение между клетками без прыжков
- Кнопка "← Назад" в экране setup

## Структура экранов
screen-menu → screen-setup → screen-game → screen-blind → screen-task → screen-result → screen-game
screen-game → screen-judge (карта судьи)
screen-result → screen-win (победа)

## Важные детали
- Папка: VocabularyRace/
- Главный файл: VocabularyRace/index.html
- ROUTE: 48 точек [left%, top%] — откалиброваны вручную
- WIN_SCORE = 50, TASK_TIME = 60 сек
- MOVE_DELAY = время между шагами фишки
- Спец-карты: racer (🏎️ Гонщик) и judge (⚖️ Судья)
- setupSlots: массив с {included, isBot, botDifficulty} для каждого из 4 игроков
- botFindWords(card, needed, sampleSize) — возвращает массив найденных слов
- resultHandled — флаг против двойного вызова afterMove

## Что нельзя ломать
- MyApp.swift, ContentView.swift, Package.swift — не трогать
- showScreen(id) — система экранов через CSS .active (НЕ добавлять display:flex в #screen-*)
- rollDice() — Promise-based, await в startTurn()
- positionToken(player, instant) — instant=true при первичной расстановке

## Открытые вопросы
- Расширить словарь если 891 слово мало для длинных партий
- Звуки (assets/*.mp3) не подключены
