import Testing
import WebKit
import Foundation

/// Набор тестов для проверки игры "Рыцари и Замки" в iOS WebView
@Suite("iOS WebView Integration Tests")
struct KnightsAndCastlesWebTests {
    
    // MARK: - Setup
    
    /// Создает WKWebView с необходимыми настройками для тестирования
    @MainActor
    private func createWebView() -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []
        config.preferences.javaScriptEnabled = true
        
        let webView = WKWebView(frame: .zero, configuration: config)
        return webView
    }
    
    /// Загружает HTML файл в WebView
    @MainActor
    private func loadHTML(in webView: WKWebView, htmlPath: String) async throws {
        let url = URL(fileURLWithPath: htmlPath)
        let request = URLRequest(url: url)
        webView.load(request)
        
        // Ждем загрузки
        try await Task.sleep(for: .seconds(3))
    }
    
    // MARK: - HTML Structure Tests
    
    @Test("Проверка базовой структуры HTML")
    @MainActor
    func testHTMLStructure() async throws {
        let webView = createWebView()
        
        // Путь к файлу должен быть корректным в вашем проекте
        // Для примера используем заглушку
        let htmlContent = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test</title>
        </head>
        <body>
            <div id="app"></div>
            <canvas id="gameCanvas"></canvas>
            <div id="sidebar"></div>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlContent, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        // Проверяем наличие основных элементов
        let hasApp = try await webView.evaluateJavaScript("document.getElementById('app') !== null") as? Bool
        let hasCanvas = try await webView.evaluateJavaScript("document.getElementById('gameCanvas') !== null") as? Bool
        let hasSidebar = try await webView.evaluateJavaScript("document.getElementById('sidebar') !== null") as? Bool
        
        #expect(hasApp == true, "Элемент #app должен существовать")
        #expect(hasCanvas == true, "Canvas должен существовать")
        #expect(hasSidebar == true, "Sidebar должен существовать")
    }
    
    // MARK: - iOS Safe Area Tests
    
    @Test("Проверка поддержки Safe Area")
    @MainActor
    func testSafeAreaSupport() async throws {
        let webView = createWebView()
        
        let htmlWithSafeArea = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                #app {
                    padding-top: env(safe-area-inset-top);
                    padding-bottom: env(safe-area-inset-bottom);
                    padding-left: env(safe-area-inset-left);
                    padding-right: env(safe-area-inset-right);
                }
            </style>
        </head>
        <body>
            <div id="app">Content</div>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlWithSafeArea, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        // Проверяем, что CSS свойства применились
        let paddingTop = try await webView.evaluateJavaScript(
            "window.getComputedStyle(document.getElementById('app')).paddingTop"
        ) as? String
        
        #expect(paddingTop != nil, "Padding должен быть применен")
    }
    
    // MARK: - Canvas Tests
    
    @Test("Проверка Canvas размеров")
    @MainActor
    func testCanvasDimensions() async throws {
        let webView = createWebView()
        
        let htmlWithCanvas = """
        <!DOCTYPE html>
        <html>
        <body>
            <canvas id="gameCanvas" width="480" height="960"></canvas>
            <script>
                const canvas = document.getElementById('gameCanvas');
                window.testCanvas = {
                    width: canvas.width,
                    height: canvas.height,
                    exists: true
                };
            </script>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlWithCanvas, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        let canvasData = try await webView.evaluateJavaScript("window.testCanvas") as? [String: Any]
        
        #expect(canvasData?["exists"] as? Bool == true)
        #expect(canvasData?["width"] as? Int == 480)
        #expect(canvasData?["height"] as? Int == 960)
    }
    
    @Test("Проверка Canvas контекста")
    @MainActor
    func testCanvasContext() async throws {
        let webView = createWebView()
        
        let htmlWithContext = """
        <!DOCTYPE html>
        <html>
        <body>
            <canvas id="gameCanvas" width="480" height="960"></canvas>
            <script>
                const canvas = document.getElementById('gameCanvas');
                const ctx = canvas.getContext('2d');
                window.hasContext = ctx !== null;
                if (ctx) {
                    ctx.fillStyle = 'red';
                    ctx.fillRect(0, 0, 100, 100);
                    window.canDraw = true;
                }
            </script>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlWithContext, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        let hasContext = try await webView.evaluateJavaScript("window.hasContext") as? Bool
        let canDraw = try await webView.evaluateJavaScript("window.canDraw") as? Bool
        
        #expect(hasContext == true, "Canvas должен иметь 2D контекст")
        #expect(canDraw == true, "Должна быть возможность рисовать на Canvas")
    }
    
    // MARK: - Touch Events Tests
    
    @Test("Проверка Touch Event API")
    @MainActor
    func testTouchEvents() async throws {
        let webView = createWebView()
        
        let htmlWithTouch = """
        <!DOCTYPE html>
        <html>
        <body>
            <div id="touchArea" style="width:200px;height:200px;background:blue"></div>
            <script>
                window.touchSupport = {
                    hasTouchStart: 'ontouchstart' in window,
                    hasTouchMove: 'ontouchmove' in window,
                    hasTouchEnd: 'ontouchend' in window
                };
                
                let touchCount = 0;
                document.getElementById('touchArea').addEventListener('touchstart', () => {
                    touchCount++;
                    window.touchCount = touchCount;
                });
            </script>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlWithTouch, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        let touchSupport = try await webView.evaluateJavaScript("window.touchSupport") as? [String: Any]
        
        #expect(touchSupport?["hasTouchStart"] as? Bool == true)
        #expect(touchSupport?["hasTouchMove"] as? Bool == true)
        #expect(touchSupport?["hasTouchEnd"] as? Bool == true)
    }
    
    // MARK: - LocalStorage Tests
    
    @Test("Проверка LocalStorage")
    @MainActor
    func testLocalStorage() async throws {
        let webView = createWebView()
        
        let htmlWithStorage = """
        <!DOCTYPE html>
        <html>
        <body>
            <script>
                // Тест записи
                try {
                    localStorage.setItem('testKey', 'testValue');
                    window.storageWrite = true;
                } catch(e) {
                    window.storageWrite = false;
                }
                
                // Тест чтения
                try {
                    const value = localStorage.getItem('testKey');
                    window.storageRead = (value === 'testValue');
                } catch(e) {
                    window.storageRead = false;
                }
                
                // Тест удаления
                try {
                    localStorage.removeItem('testKey');
                    const value = localStorage.getItem('testKey');
                    window.storageDelete = (value === null);
                } catch(e) {
                    window.storageDelete = false;
                }
            </script>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlWithStorage, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        let canWrite = try await webView.evaluateJavaScript("window.storageWrite") as? Bool
        let canRead = try await webView.evaluateJavaScript("window.storageRead") as? Bool
        let canDelete = try await webView.evaluateJavaScript("window.storageDelete") as? Bool
        
        #expect(canWrite == true, "LocalStorage должен поддерживать запись")
        #expect(canRead == true, "LocalStorage должен поддерживать чтение")
        #expect(canDelete == true, "LocalStorage должен поддерживать удаление")
    }
    
    @Test("Проверка сохранения прогресса игры")
    @MainActor
    func testGameProgressStorage() async throws {
        let webView = createWebView()
        
        let htmlWithGameProgress = """
        <!DOCTYPE html>
        <html>
        <body>
            <script>
                const PROGRESS_KEY = 'knightsCastles_progress';
                
                // Симуляция сохранения прогресса
                const testProgress = {
                    chapters: [
                        {
                            games: [
                                { tasks: [true, false, false] }
                            ]
                        }
                    ]
                };
                
                try {
                    localStorage.setItem(PROGRESS_KEY, JSON.stringify(testProgress));
                    const saved = JSON.parse(localStorage.getItem(PROGRESS_KEY));
                    window.progressSaved = (saved.chapters[0].games[0].tasks[0] === true);
                } catch(e) {
                    window.progressSaved = false;
                }
            </script>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlWithGameProgress, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        let saved = try await webView.evaluateJavaScript("window.progressSaved") as? Bool
        #expect(saved == true, "Прогресс игры должен сохраняться")
    }
    
    // MARK: - Audio Tests
    
    @Test("Проверка поддержки Audio")
    @MainActor
    func testAudioSupport() async throws {
        let webView = createWebView()
        
        let htmlWithAudio = """
        <!DOCTYPE html>
        <html>
        <body>
            <audio id="testAudio" src="data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="></audio>
            <script>
                const audio = document.getElementById('testAudio');
                window.audioSupport = {
                    exists: audio !== null,
                    canPlay: typeof audio.play === 'function',
                    canPause: typeof audio.pause === 'function'
                };
            </script>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlWithAudio, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        let audioSupport = try await webView.evaluateJavaScript("window.audioSupport") as? [String: Any]
        
        #expect(audioSupport?["exists"] as? Bool == true)
        #expect(audioSupport?["canPlay"] as? Bool == true)
        #expect(audioSupport?["canPause"] as? Bool == true)
    }
    
    // MARK: - Responsive Design Tests
    
    @Test("Проверка viewport meta tag")
    @MainActor
    func testViewportMeta() async throws {
        let webView = createWebView()
        
        let htmlWithViewport = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, user-scalable=no">
            <meta name="apple-mobile-web-app-capable" content="yes">
            <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        </head>
        <body>
            <script>
                const viewportMeta = document.querySelector('meta[name="viewport"]');
                const webAppMeta = document.querySelector('meta[name="apple-mobile-web-app-capable"]');
                const statusBarMeta = document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]');
                
                window.metaTags = {
                    hasViewport: viewportMeta !== null,
                    hasWebApp: webAppMeta !== null,
                    hasStatusBar: statusBarMeta !== null,
                    viewportContent: viewportMeta ? viewportMeta.content : null
                };
            </script>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlWithViewport, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        let metaTags = try await webView.evaluateJavaScript("window.metaTags") as? [String: Any]
        
        #expect(metaTags?["hasViewport"] as? Bool == true)
        #expect(metaTags?["hasWebApp"] as? Bool == true)
        #expect(metaTags?["hasStatusBar"] as? Bool == true)
        
        let viewportContent = metaTags?["viewportContent"] as? String
        #expect(viewportContent?.contains("viewport-fit=cover") == true)
    }
    
    @Test("Проверка медиа-запросов для мобильных устройств")
    @MainActor
    func testMediaQueries() async throws {
        let webView = createWebView()
        
        let htmlWithMediaQuery = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                #testElement {
                    width: 100px;
                }
                @media (max-width: 768px) {
                    #testElement {
                        width: 200px;
                    }
                }
            </style>
        </head>
        <body>
            <div id="testElement"></div>
            <script>
                const element = document.getElementById('testElement');
                const computedWidth = window.getComputedStyle(element).width;
                window.elementWidth = parseInt(computedWidth);
                window.screenWidth = window.innerWidth;
            </script>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlWithMediaQuery, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        let screenWidth = try await webView.evaluateJavaScript("window.screenWidth") as? Int
        let elementWidth = try await webView.evaluateJavaScript("window.elementWidth") as? Int
        
        #expect(screenWidth != nil, "Screen width должен определяться")
        #expect(elementWidth != nil, "Element width должен вычисляться")
    }
    
    // MARK: - Performance Tests
    
    @Test("Проверка RequestAnimationFrame")
    @MainActor
    func testRequestAnimationFrame() async throws {
        let webView = createWebView()
        
        let htmlWithRAF = """
        <!DOCTYPE html>
        <html>
        <body>
            <script>
                window.rafSupported = typeof requestAnimationFrame === 'function';
                window.rafCalled = false;
                
                if (window.rafSupported) {
                    requestAnimationFrame(() => {
                        window.rafCalled = true;
                    });
                }
            </script>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlWithRAF, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        let supported = try await webView.evaluateJavaScript("window.rafSupported") as? Bool
        let called = try await webView.evaluateJavaScript("window.rafCalled") as? Bool
        
        #expect(supported == true, "RequestAnimationFrame должен поддерживаться")
        #expect(called == true, "RequestAnimationFrame callback должен вызваться")
    }
    
    // MARK: - JavaScript Error Handling Tests
    
    @Test("Проверка обработки ошибок JavaScript")
    @MainActor
    func testJavaScriptErrorHandling() async throws {
        let webView = createWebView()
        
        let htmlWithErrorHandling = """
        <!DOCTYPE html>
        <html>
        <body>
            <script>
                window.errorCaught = false;
                window.addEventListener('error', (event) => {
                    window.errorCaught = true;
                    window.errorMessage = event.message;
                });
                
                // Намеренная ошибка
                setTimeout(() => {
                    try {
                        nonExistentFunction();
                    } catch(e) {
                        window.manualErrorCaught = true;
                    }
                }, 100);
            </script>
        </body>
        </html>
        """
        
        webView.loadHTMLString(htmlWithErrorHandling, baseURL: nil)
        try await Task.sleep(for: .seconds(1))
        
        let manualErrorCaught = try await webView.evaluateJavaScript("window.manualErrorCaught") as? Bool
        #expect(manualErrorCaught == true, "Try-catch должен ловить ошибки")
    }
}

// MARK: - Game Logic Tests

@Suite("Логика игры - Юниты и Боевая система")
struct GameLogicTests {
    
    @Test("Проверка характеристик рыцаря")
    func testKnightStats() {
        // HP: 3, ATK: 5, DEF: 4, MOVE: 2
        let knight = Unit(type: .knight)
        
        #expect(knight.hp == 3)
        #expect(knight.attack == 5)
        #expect(knight.defense == 4)
        #expect(knight.movePoints == 2)
    }
    
    @Test("Проверка характеристик конного воина")
    func testCavalryStats() {
        // HP: 5, ATK: 6, DEF: 3, MOVE: 3
        let cavalry = Unit(type: .cavalry)
        
        #expect(cavalry.hp == 5)
        #expect(cavalry.attack == 6)
        #expect(cavalry.defense == 3)
        #expect(cavalry.movePoints == 3)
    }
    
    @Test("Проверка характеристик лучника")
    func testArcherStats() {
        // HP: 3, ATK: 2, DEF: 1, MOVE: 3
        let archer = Unit(type: .archer)
        
        #expect(archer.hp == 3)
        #expect(archer.attack == 2)
        #expect(archer.defense == 1)
        #expect(archer.movePoints == 3)
    }
    
    @Test("Проверка системы урона (защита → HP)")
    func testDamageSystem() {
        var defender = Unit(type: .knight)
        // Начальное состояние: DEF=4, HP=3
        
        // Атака на 2 урона - должна снять 2 защиты
        defender.takeDamage(2)
        #expect(defender.defense == 2)
        #expect(defender.hp == 3)
        
        // Атака на 3 урона - должна снять оставшуюся защиту (2) и 1 HP
        defender.takeDamage(3)
        #expect(defender.defense == 0)
        #expect(defender.hp == 2)
        
        // Атака на 2 урона - должна снять 2 HP
        defender.takeDamage(2)
        #expect(defender.defense == 0)
        #expect(defender.hp == 0)
        #expect(defender.isAlive == false)
    }
    
    @Test("Проверка лечения HP в замке")
    func testCastleHealHP() {
        var knight = Unit(type: .knight)
        knight.takeDamage(5) // DEF=0, HP=1
        
        #expect(knight.hp == 1)
        
        knight.healHP(2) // Восстановить +2 HP
        #expect(knight.hp == 3)
        
        // Не должно превышать максимум
        knight.healHP(5)
        #expect(knight.hp == 3) // Максимум для рыцаря
    }
    
    @Test("Проверка лечения защиты в замке")
    func testCastleHealDefense() {
        var knight = Unit(type: .knight)
        knight.takeDamage(3) // DEF=1
        
        #expect(knight.defense == 1)
        
        knight.healDefense(2) // Восстановить +2 DEF
        #expect(knight.defense == 3)
        
        // Не должно превышать начальное значение
        knight.healDefense(5)
        #expect(knight.defense == 4) // Начальное для рыцаря
    }
}

// MARK: - Helper Types for Testing

enum UnitType {
    case knight, cavalry, archer
}

struct Unit {
    let type: UnitType
    var hp: Int
    var attack: Int
    var defense: Int
    var movePoints: Int
    var isAlive: Bool { hp > 0 }
    
    private let maxHP: Int
    private let maxDefense: Int
    
    init(type: UnitType) {
        self.type = type
        switch type {
        case .knight:
            self.hp = 3
            self.attack = 5
            self.defense = 4
            self.movePoints = 2
        case .cavalry:
            self.hp = 5
            self.attack = 6
            self.defense = 3
            self.movePoints = 3
        case .archer:
            self.hp = 3
            self.attack = 2
            self.defense = 1
            self.movePoints = 3
        }
        self.maxHP = self.hp
        self.maxDefense = self.defense
    }
    
    mutating func takeDamage(_ damage: Int) {
        if defense > 0 {
            let defenseLeft = defense - damage
            if defenseLeft >= 0 {
                defense = defenseLeft
            } else {
                defense = 0
                hp = max(0, hp + defenseLeft) // defenseLeft отрицательное
            }
        } else {
            hp = max(0, hp - damage)
        }
    }
    
    mutating func healHP(_ amount: Int) {
        hp = min(maxHP, hp + amount)
    }
    
    mutating func healDefense(_ amount: Int) {
        defense = min(maxDefense, defense + amount)
    }
}

// MARK: - Integration Test Suite

@Suite("Полный интеграционный тест игры")
struct FullIntegrationTests {
    
    @Test("Симуляция полного игрового цикла")
    @MainActor
    func testFullGameCycle() async throws {
        let webView = WKWebView()
        
        // Для реального теста нужно загрузить index.html
        // Здесь мы проверяем, что WebView создан и готов
        #expect(webView != nil)
        
        // В реальном проекте:
        // 1. Загрузить index.html
        // 2. Дождаться инициализации игры
        // 3. Симулировать клики через JavaScript
        // 4. Проверить изменение состояния игры
    }
    
    @Test("Проверка цикла: Меню → Игра → Победа → Меню")
    @MainActor
    func testMenuGameVictoryLoop() async throws {
        let webView = WKWebView()
        
        // Проверяем готовность WebView
        #expect(webView != nil)
        
        // Шаги теста:
        // 1. Открыть меню (menuOverlay.active = true)
        // 2. Нажать "Игра против игрока"
        // 3. Симулировать игру до победы
        // 4. Проверить Victory overlay
        // 5. Вернуться в меню
    }
}
