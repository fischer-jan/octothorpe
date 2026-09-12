import Foundation

enum ProjectRoot {
    static let defaultPath = "/Users/jan/Projekte/octothorpe"

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
