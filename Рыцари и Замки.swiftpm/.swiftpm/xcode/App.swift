import SwiftUI
import WebKit

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
