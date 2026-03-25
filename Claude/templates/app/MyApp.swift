import SwiftUI
import Foundation

// MARK: - AppLoader
// Загружает HTML-приложение из папки {{GAME_FOLDER}}

@MainActor
class AppLoader {

    private let gameFolder = "{{GAME_FOLDER}}"
    private let documentsURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!

    func getIndexURL() async -> URL? {
        let documentsGameFolder = documentsURL.appendingPathComponent(gameFolder)
        let documentsIndex = documentsGameFolder.appendingPathComponent("index.html")

        if FileManager.default.fileExists(atPath: documentsIndex.path) {
            return documentsIndex
        }

        if let bundleIndex = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: gameFolder) {
            return bundleIndex
        }

        if let bundleFolder = Bundle.main.url(forResource: gameFolder, withExtension: nil) {
            do {
                try FileManager.default.copyItem(at: bundleFolder, to: documentsGameFolder)
                return documentsIndex
            } catch {
                print("❌ Ошибка копирования: \(error)")
            }
        }

        return nil
    }

    func getAppFolderURL() async -> URL? {
        let documentsGameFolder = documentsURL.appendingPathComponent(gameFolder)
        if FileManager.default.fileExists(atPath: documentsGameFolder.path) {
            return documentsGameFolder
        }
        return Bundle.main.url(forResource: gameFolder, withExtension: nil)
    }
}

// MARK: - LoadingView

struct LoadingView: View {
    let loader: AppLoader

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            ContentView(loader: loader)
                .ignoresSafeArea()
        }
    }
}

// MARK: - App

@main
struct {{APP_NAME}}App: App {
    private let loader = AppLoader()

    var body: some Scene {
        WindowGroup {
            LoadingView(loader: loader)
                .ignoresSafeArea()
        }
    }
}
