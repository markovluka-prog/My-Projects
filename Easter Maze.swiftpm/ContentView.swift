import SwiftUI
import WebKit

struct ContentView: UIViewRepresentable {
    let loader: AppLoader

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.scrollView.isScrollEnabled = true
        webView.scrollView.bounces = false

        Task {
            await loadApp(into: webView)
        }

        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    private func loadApp(into webView: WKWebView) async {
        guard let indexURL = await loader.getIndexURL() else {
            await MainActor.run {
                webView.loadHTMLString("<h1>❌ index.html не найден</h1>", baseURL: nil)
            }
            return
        }

        guard let appFolder = await loader.getAppFolderURL() else {
            await MainActor.run {
                webView.loadHTMLString("<h1>❌ Папка приложения не найдена</h1>", baseURL: nil)
            }
            return
        }

        await MainActor.run {
            webView.loadFileURL(indexURL, allowingReadAccessTo: appFolder)
        }
    }
}
