import SwiftUI
import Foundation

// MARK: - AppLoader
// Загружает HTML-приложение из папки VocabularyRace

@MainActor
class AppLoader {

    private let gameFolder = "GameWeb"
    // Caches: пишется и в песочнице, и без неё, не защищён TCC (в отличие от ~/Documents).
    // Именно сюда копируем веб-контент, чтобы WebContent-процесс мог его читать.
    private let documentsURL = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first!

    func getIndexURL() async -> URL? {
        let documentsGameFolder = documentsURL.appendingPathComponent(gameFolder)
        let documentsIndex = documentsGameFolder.appendingPathComponent("index.html")

        // ВАЖНО (Mac Catalyst): WebContent-процесс не может читать из бандла
        // приложения (он вне контейнера данных). Поэтому всегда копируем
        // GameWeb в Documents (контейнер данных) и грузим оттуда.
        // Копируем заново при каждом запуске, чтобы подхватывать обновления.
        if let bundleFolder = Bundle.main.url(forResource: gameFolder, withExtension: nil) {
            try? FileManager.default.removeItem(at: documentsGameFolder)
            do {
                try FileManager.default.copyItem(at: bundleFolder, to: documentsGameFolder)
            } catch {
                print("❌ Ошибка копирования GameWeb: \(error)")
            }
        }

        if FileManager.default.fileExists(atPath: documentsIndex.path) {
            return documentsIndex
        }

        // Fallback — прямо из бандла (на iOS читается без проблем)
        return Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: gameFolder)
    }

    func getAppFolderURL() async -> URL? {
        let documentsGameFolder = documentsURL.appendingPathComponent(gameFolder)
        if FileManager.default.fileExists(atPath: documentsGameFolder.path) {
            return documentsGameFolder
        }
        return Bundle.main.url(forResource: gameFolder, withExtension: nil)
    }

    // name без расширения: "dictionary" (рус) или "dictionary_en" (англ)
    func getDictionaryText(_ name: String = "dictionary") async -> String? {
        // Сначала ищем в Caches (если уже скопировали)
        let cachesDict = documentsURL.appendingPathComponent(gameFolder).appendingPathComponent("\(name).txt")
        if let text = try? String(contentsOf: cachesDict, encoding: .utf8) {
            return text
        }
        // Затем в бандле
        if let bundleURL = Bundle.main.url(forResource: name, withExtension: "txt", subdirectory: gameFolder),
           let text = try? String(contentsOf: bundleURL, encoding: .utf8) {
            return text
        }
        return nil
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
struct VocabularyRaceApp: App {
    private let loader = AppLoader()

    var body: some Scene {
        WindowGroup {
            LoadingView(loader: loader)
                .ignoresSafeArea()
        }
    }
}
