import SwiftUI
import SwiftUI
import WebKit

struct ContentView: UIViewRepresentable {
    let updater: GitHubUpdater
    
    func makeUIView(context: Context) -> WKWebView {
        // Настраиваем конфигурацию для быстрой загрузки
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []
        
        // Создаем WebView с оптимизацией
        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.scrollView.isScrollEnabled = true
        webView.scrollView.bounces = false
        
        // Загружаем игру асинхронно
        Task {
            await loadGame(into: webView)
        }
        
        return webView
    }
    
    func updateUIView(_ uiView: WKWebView, context: Context) {}
    
    // MARK: - Загрузка игры
    
    private func loadGame(into webView: WKWebView) async {
        print("⏱️ Начинаем загрузку игры...")
        let startTime = Date()
        
        // Получаем URL для index.html (Documents или Bundle)
        guard let indexURL = await updater.getIndexURL() else {
            await MainActor.run {
                webView.loadHTMLString(
                    "<h1>❌ Файлы игры не найдены</h1>",
                    baseURL: nil
                )
            }
            print("❌ index.html не найден ни в Documents, ни в Bundle")
            return
        }
        
        // Получаем папку игры для доступа к ресурсам
        guard let gameFolder = await updater.getGameFolderURL() else {
            await MainActor.run {
                webView.loadHTMLString(
                    "<h1>❌ Папка игры не найдена</h1>",
                    baseURL: nil
                )
            }
            return
        }
        
        // Загружаем игру в WebView
        await MainActor.run {
            print("📂 Загрузка из:", indexURL.path)
            webView.loadFileURL(indexURL, allowingReadAccessTo: gameFolder)
            let elapsed = Date().timeIntervalSince(startTime)
            print("✅ index.html загружен за \(String(format: "%.2f", elapsed)) секунд")
        }
    }
}
