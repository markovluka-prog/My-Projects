import SwiftUI

import SwiftUI

/// Вспомогательная вьюха для тестирования обновлений (опционально)
/// Добавьте это в ваш интерфейс если хотите видеть статус обновлений
struct UpdateDebugView: View {
    let updater: GitHubUpdater
    @State private var status: String = "Проверка..."
    @State private var currentSource: String = "Неизвестно"
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("🔄 Статус обновлений")
                .font(.headline)
            
            Text("Источник: \(currentSource)")
                .font(.caption)
                .foregroundColor(.secondary)
            
            Text(status)
                .font(.caption)
                .foregroundColor(.secondary)
            
            Button("Проверить обновления вручную") {
                Task {
                    await updater.checkForUpdatesInBackground()
                    status = "Обновление запущено..."
                }
            }
            .font(.caption)
            .buttonStyle(.bordered)
        }
        .padding()
        .background(Color.black.opacity(0.7))
        .cornerRadius(12)
        .task {
            await checkCurrentSource()
        }
    }
    
    private func checkCurrentSource() async {
        if let url = await updater.getIndexURL() {
            if url.path.contains("Documents") {
                currentSource = "📂 Documents (обновлено)"
            } else {
                currentSource = "📦 Bundle (по умолчанию)"
            }
            status = "Готово"
        } else {
            currentSource = "❌ Не найдено"
            status = "Ошибка"
        }
    }
}

// MARK: - Пример использования в ContentView

/*
 Чтобы добавить debug overlay, измените ContentView так:
 
 struct ContentView: UIViewRepresentable {
     let updater: GitHubUpdater
     
     func makeUIView(context: Context) -> WKWebView {
         // ... ваш код
     }
     
     func updateUIView(_ uiView: WKWebView, context: Context) {}
 }
 
 // И оберните в ZStack в MyApp.swift:
 
 WindowGroup {
     ZStack {
         ContentView(updater: updater)
             .ignoresSafeArea()
         
         // Debug overlay (удалите в продакшене)
         VStack {
             Spacer()
             HStack {
                 UpdateDebugView(updater: updater)
                 Spacer()
             }
         }
         .padding()
     }
     .task {
         updater.checkForUpdatesInBackground()
     }
 }
 */
