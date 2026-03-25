import Foundation

/// Фоновое обновление файлов игры из GitHub
actor GitHubUpdater {
    // MARK: - Конфигурация
    
    /// Владелец/название репозитория (например "username/repo")
    private let repository = "markovluka-prog/KnightsAndCastles" // ← ЗАМЕНИТЕ НА ВАШ РЕПОЗИТОРИЙ
    
    /// Название папки в репозитории
    private let folderName = "KnightsGame" // ← НАЗВАНИЕ ПАПКИ НА GITHUB
    
    /// Ветка для скачивания
    private let branch = "main"
    
    // MARK: - Пути
    
    /// Папка в Documents для кэшированных файлов
    private var documentsGameFolder: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("KnightsGame")
    }
    
    /// Временная папка для скачивания
    private var tempDownloadFolder: URL {
        FileManager.default.temporaryDirectory
            .appendingPathComponent("KnightsGame_Download")
    }
    
    // MARK: - Публичный API
    
    /// Проверить и скачать обновления в фоне (не блокирует UI)
    func checkForUpdatesInBackground() async {
        await performBackgroundUpdate()
    }
    
    /// Очистить кэш (вернуться к Bundle версии)
    /// Полезно для отладки или если обновление повредило файлы
    func clearCache() {
        let fm = FileManager.default
        if fm.fileExists(atPath: documentsGameFolder.path) {
            try? fm.removeItem(at: documentsGameFolder)
            print("🗑️ Кэш очищен, приложение будет использовать Bundle версию")
        }
    }
    
    /// Получить URL для загрузки игры (Documents если есть, иначе Bundle)
    func getGameFolderURL() -> URL? {
        let fm = FileManager.default
        
        // Сначала проверяем Documents
        if fm.fileExists(atPath: documentsGameFolder.path) {
            print("📂 Загружаем из Documents (обновлённая версия)")
            return documentsGameFolder
        }
        
        // Если нет в Documents, используем Bundle
        if let bundleURL = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "KnightsGame") {
            print("📦 Загружаем из Bundle (версия по умолчанию)")
            return bundleURL.deletingLastPathComponent()
        }
        
        print("❌ Не найдена папка KnightsGame ни в Documents, ни в Bundle")
        return nil
    }
    
    /// Получить URL для index.html
    func getIndexURL() -> URL? {
        let fm = FileManager.default
        
        // Проверяем Documents
        let documentsIndex = documentsGameFolder.appendingPathComponent("index.html")
        if fm.fileExists(atPath: documentsIndex.path) {
            print("📂 index.html из Documents")
            return documentsIndex
        }
        
        // Проверяем Bundle
        if let bundleURL = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "KnightsGame") {
            print("📦 index.html из Bundle")
            return bundleURL
        }
        
        return nil
    }
    
    // MARK: - Приватные методы
    
    /// Выполнить фоновое обновление
    private func performBackgroundUpdate() async {
        let startTime = Date()
        print("🔄 Начинаем фоновое обновление...")
        
        // Проверяем интернет (простая проверка)
        guard await hasInternetConnection() else {
            let elapsed = Date().timeIntervalSince(startTime)
            print("📡 Нет подключения к интернету, обновление пропущено (\(String(format: "%.2f", elapsed))с)")
            return
        }
        print("✅ Интернет доступен")
        
        do {
            // Получаем список файлов из GitHub
            print("📋 Запрашиваем список файлов...")
            let files = try await fetchFileListFromGitHub()
            print("📋 Получен список файлов: \(files.count) файлов")
            
            // Скачиваем файлы во временную папку
            print("⬇️ Начинаем скачивание...")
            try await downloadFilesToTemp(files: files)
            print("⬇️ Файлы скачаны во временную папку")
            
            // Перемещаем временную папку в Documents
            print("📦 Устанавливаем обновление...")
            try replaceGameFolder()
            
            let elapsed = Date().timeIntervalSince(startTime)
            print("✅ Обновление завершено успешно за \(String(format: "%.2f", elapsed)) секунд")
            
        } catch {
            let elapsed = Date().timeIntervalSince(startTime)
            print("❌ Ошибка обновления (\(String(format: "%.2f", elapsed))с): \(error.localizedDescription)")
            // Очищаем временную папку при ошибке
            cleanupTempFolder()
        }
    }
    
    /// Проверка интернет-соединения
    private func hasInternetConnection() async -> Bool {
        let url = URL(string: "https://api.github.com")!
        
        do {
            let (_, response) = try await URLSession.shared.data(from: url)
            return (response as? HTTPURLResponse)?.statusCode == 200
        } catch {
            return false
        }
    }
    
    /// Получить список файлов из GitHub через API
    private func fetchFileListFromGitHub() async throws -> [GitHubFile] {
        let apiURL = "https://api.github.com/repos/\(repository)/git/trees/\(branch)?recursive=1"
        
        guard let url = URL(string: apiURL) else {
            throw UpdateError.invalidURL
        }
        
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw UpdateError.networkError
        }
        
        let tree = try JSONDecoder().decode(GitHubTree.self, from: data)
        
        // Фильтруем только файлы из нужной папки
        return tree.tree.filter { item in
            item.type == "blob" &&
            item.path.hasPrefix("\(folderName)/")
        }
    }
    
    /// Скачать файлы во временную папку
    private func downloadFilesToTemp(files: [GitHubFile]) async throws {
        let fm = FileManager.default
        
        // Очищаем временную папку если существует
        if fm.fileExists(atPath: tempDownloadFolder.path) {
            try fm.removeItem(at: tempDownloadFolder)
        }
        
        // Создаём временную папку
        try fm.createDirectory(at: tempDownloadFolder, withIntermediateDirectories: true)
        
        // Скачиваем каждый файл
        for file in files {
            // Убираем префикс папки из пути
            let relativePath = file.path.replacingOccurrences(of: "\(folderName)/", with: "")
            let destinationURL = tempDownloadFolder.appendingPathComponent(relativePath)
            
            // Создаём подпапки если нужно
            let folderURL = destinationURL.deletingLastPathComponent()
            if !fm.fileExists(atPath: folderURL.path) {
                try fm.createDirectory(at: folderURL, withIntermediateDirectories: true)
            }
            
            // Скачиваем файл
            let downloadURL = "https://raw.githubusercontent.com/\(repository)/\(branch)/\(file.path)"
            guard let url = URL(string: downloadURL) else { continue }
            
            let (data, _) = try await URLSession.shared.data(from: url)
            try data.write(to: destinationURL)
            
            print("✅ Скачан: \(relativePath)")
        }
    }
    
    /// Заменить папку игры в Documents на новую версию
    private func replaceGameFolder() throws {
        let fm = FileManager.default
        
        // Удаляем старую версию если существует
        if fm.fileExists(atPath: documentsGameFolder.path) {
            try fm.removeItem(at: documentsGameFolder)
        }
        
        // Перемещаем временную папку в Documents
        try fm.moveItem(at: tempDownloadFolder, to: documentsGameFolder)
    }
    
    /// Очистить временную папку
    private func cleanupTempFolder() {
        let fm = FileManager.default
        if fm.fileExists(atPath: tempDownloadFolder.path) {
            try? fm.removeItem(at: tempDownloadFolder)
        }
    }
}

// MARK: - Модели данных

private struct GitHubTree: Decodable {
    let tree: [GitHubFile]
}

private struct GitHubFile: Decodable {
    let path: String
    let type: String
    let url: String
}

// MARK: - Ошибки

private enum UpdateError: Error {
    case invalidURL
    case networkError
    case fileSystemError
}
