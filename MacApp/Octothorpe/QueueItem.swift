import Foundation

enum ConvertStatus: Equatable {
    case queued
    case converting
    case done(outputPath: String?)
    case failed(String)

    var isDone: Bool { if case .done = self { return true }; return false }
    var isFailed: Bool { if case .failed = self { return true }; return false }
}

struct QueueItem: Identifiable, Equatable {
    let id: String
    var url: URL
    var status: ConvertStatus = .queued

    init(url: URL) {
        let standardized = url.standardizedFileURL
        self.url = standardized
        self.id = standardized.path
    }

    var filename: String {
        url.lastPathComponent
    }

    var folder: String {
        let parent = url.deletingLastPathComponent().path
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        if parent == home {
            return "~"
        }
        if parent.hasPrefix(home + "/") {
            return "~" + parent.dropFirst(home.count)
        }
        return parent
    }
}

enum FooterKind: Equatable {
    case ready
    case queued(Int)
    case converting(current: Int, total: Int)
    case finished(ok: Int, failed: Int)
    case error(String)

    var text: String {
        switch self {
        case .ready:
            return "Ready"
        case .queued(let n):
            return n == 1 ? "1 file queued" : "\(n) files queued"
        case .converting(let current, let total):
            return "Converting \(current) of \(total)…"
        case .finished(let ok, let failed):
            return Self.formatDone(ok: ok, failed: failed)
        case .error(let message):
            return message
        }
    }

    static func formatDone(ok: Int, failed: Int) -> String {
        if failed > 0 && ok > 0 {
            let okBit = ok == 1 ? "1 file" : "\(ok) files"
            let failBit = failed == 1 ? "1 failed" : "\(failed) failed"
            return "Converted \(okBit), \(failBit)"
        }
        if failed > 0 {
            return failed == 1 ? "1 file failed" : "\(failed) files failed"
        }
        if ok == 1 {
            return "Converted 1 file"
        }
        return "Converted \(ok) files"
    }
}
