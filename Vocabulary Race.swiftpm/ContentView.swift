import SwiftUI
import WebKit

class WebViewCoordinator: NSObject, WKNavigationDelegate {
    let loader: AppLoader

    init(loader: AppLoader) {
        self.loader = loader
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        Task {
            await injectDictionary(into: webView)
        }
    }

    private func injectDictionary(into webView: WKWebView) async {
        guard let dictText = await loader.getDictionaryText() else { return }
        // Экранируем для безопасной передачи в JS-строку
        let escaped = dictText
            .replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "`", with: "\\`")
        let js = "window.__injectDictionary(`\(escaped)`);"
        await MainActor.run {
            webView.evaluateJavaScript(js, completionHandler: nil)
        }
    }
}

struct ContentView: UIViewRepresentable {
    let loader: AppLoader

    func makeCoordinator() -> WebViewCoordinator {
        WebViewCoordinator(loader: loader)
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.scrollView.isScrollEnabled = true
        webView.scrollView.bounces = false
        webView.navigationDelegate = context.coordinator

        Task {
            await loadApp(into: webView)
        }

        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    private func loadApp(into webView: WKWebView) async {
        guard let indexURL = await loader.getIndexURL() else {
            await MainActor.run {
                _ = webView.loadHTMLString("<h1>❌ index.html не найден</h1>", baseURL: nil)
            }
            return
        }

        guard let appFolder = await loader.getAppFolderURL() else {
            await MainActor.run {
                _ = webView.loadHTMLString("<h1>❌ Папка приложения не найдена</h1>", baseURL: nil)
            }
            return
        }

        await MainActor.run {
            _ = webView.loadFileURL(indexURL, allowingReadAccessTo: appFolder)
        }
    }
}
