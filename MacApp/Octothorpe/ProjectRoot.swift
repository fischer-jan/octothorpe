import Foundation

enum ProjectRoot {
    /// Used only when scripts/install-mac.sh has not written project_root.txt yet.
    static let defaultPath = FileManager.default.homeDirectoryForCurrentUser
        .appendingPathComponent("octothorpe").path

    static func resolve() -> URL {
        let support = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
        if let support {
            let marker = support
                .appendingPathComponent("Octothorpe", isDirectory: true)
                .appendingPathComponent("project_root.txt")
            if let text = try? String(contentsOf: marker, encoding: .utf8) {
                let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
                if !trimmed.isEmpty {
                    return URL(fileURLWithPath: trimmed, isDirectory: true)
                }
            }
        }
        return URL(fileURLWithPath: defaultPath, isDirectory: true)
    }

    static func cliURL() -> URL {
        resolve().appendingPathComponent(".venv/bin/octothorpe")
    }
}
