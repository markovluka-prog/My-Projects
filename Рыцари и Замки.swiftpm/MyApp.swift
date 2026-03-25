import SwiftUI
import Foundation

// MARK: - GitHubUpdater

/// Класс для управления обновлениями игры из GitHub
@MainActor
class GitHubUpdater {
    
    // MARK: - Properties
    
    private let gameFolder = "KnightsGame"
    private let documentsURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
    
    // MARK: - Public Methods
    
    /// Получить URL для index.html
    func getIndexURL() async -> URL? {
        // Сначала проверяем Documents
        let documentsGameFolder = documentsURL.appendingPathComponent(gameFolder)
        let documentsIndex = documentsGameFolder.appendingPathComponent("index.html")
        
        if FileManager.default.fileExists(atPath: documentsIndex.path) {
            return documentsIndex
        }
        
        // Затем проверяем Bundle
        if let bundleIndex = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: gameFolder) {
            return bundleIndex
        }
        
        // Если не нашли в Documents, копируем из Bundle
        if let bundleFolder = Bundle.main.url(forResource: gameFolder, withExtension: nil) {
            do {
                try FileManager.default.copyItem(at: bundleFolder, to: documentsGameFolder)
                return documentsIndex
            } catch {
                print("❌ Ошибка копирования игры: \(error)")
            }
        }
        
        return nil
    }
    
    /// Получить URL папки с игрой
    func getGameFolderURL() async -> URL? {
        let documentsGameFolder = documentsURL.appendingPathComponent(gameFolder)
        
        if FileManager.default.fileExists(atPath: documentsGameFolder.path) {
            return documentsGameFolder
        }
        
        // Возвращаем Bundle как fallback
        return Bundle.main.url(forResource: gameFolder, withExtension: nil)
    }
    
    /// Проверить обновления в фоне
    func checkForUpdatesInBackground() async {
        // Здесь можно добавить логику проверки обновлений с GitHub
        print("🔄 Проверка обновлений...")
    }
}

// MARK: - LoadingGameView

struct LoadingGameView: View {
    let updater: GitHubUpdater
    
    var body: some View {
        ZStack {
            // Фон
            Color.black.ignoresSafeArea()
            
            // WebView с игрой
            ContentView(updater: updater)
                .ignoresSafeArea()
        }
    }
}

// MARK: - App

@main
struct KnightsAndCastlesApp: App {
    private let updater = GitHubUpdater()
    
    var body: some Scene {
        WindowGroup {
            LoadingGameView(updater: updater)
                .ignoresSafeArea()
                .onAppear {
                    // Запускаем обновление ПОСЛЕ того, как UI появился
                    // Это не блокирует загрузку игры!
                    Task.detached(priority: .utility) {
                        // Небольшая задержка, чтобы игра успела загрузиться
                        try? await Task.sleep(nanoseconds: 2_000_000_000) // 2 секунды
                        await updater.checkForUpdatesInBackground()
                    }
                }
        }
    }
}
