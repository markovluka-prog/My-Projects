import SwiftUI

import SwiftUI

/// Обертка для ContentView с экраном загрузки
struct LoadingGameView: View {
    let updater: GitHubUpdater
    @State private var isLoading = true
    
    var body: some View {
        ZStack {
            // Основной контент - WebView с игрой
            ContentView(updater: updater)
                .opacity(isLoading ? 0 : 1)
                .animation(.easeIn(duration: 0.3), value: isLoading)
            
            // Экран загрузки
            if isLoading {
                Color.black.ignoresSafeArea()
                
                VStack(spacing: 20) {
                    Image(systemName: "gamecontroller.fill")
                        .font(.system(size: 60))
                        .foregroundColor(.white)
                    
                    Text("Рыцари и Замки")
                        .font(.title)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                    
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(1.5)
                    
                    Text("Загрузка игры...")
                        .font(.subheadline)
                        .foregroundColor(.white.opacity(0.7))
                }
            }
        }
        .task {
            // Небольшая задержка для плавности
            try? await Task.sleep(nanoseconds: 500_000_000) // 0.5 секунды
            isLoading = false
        }
    }
}
