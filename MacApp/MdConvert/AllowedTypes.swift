import Foundation
import UniformTypeIdentifiers

/// Extensions MarkItDown accepts. The CLI still validates each file.
enum AllowedTypes {
    static let extensions: Set<String> = [
        "pdf",
        "docx", "pptx", "xlsx", "xls",
        "html", "htm",
        "txt", "text", "csv", "json", "jsonl", "xml", "rss", "atom",
        "epub", "ipynb",
        "png", "jpg", "jpeg", "tiff", "tif", "webp", "bmp", "gif",
        "wav", "mp3", "m4a", "mp4",
        "zip", "msg",
    ]

    static var contentTypes: [UTType] {
        let mapped = extensions.compactMap { UTType(filenameExtension: $0) }
        var seen = Set<String>()
        return mapped.filter { seen.insert($0.identifier).inserted }
    }

    static func isAllowed(url: URL) -> Bool {
        let ext = url.pathExtension.lowercased()
        if ext.isEmpty { return false }
        if ext == "md" || ext == "markdown" { return false }
        return extensions.contains(ext)
    }

    static func symbolName(for url: URL) -> String {
        switch url.pathExtension.lowercased() {
        case "pdf":
            return "doc.richtext"
        case "png", "jpg", "jpeg", "tiff", "tif", "webp", "bmp", "gif":
            return "photo"
        case "docx", "txt", "text", "rtf":
            return "doc.text"
        case "pptx":
            return "play.rectangle"
        case "xlsx", "xls", "csv":
            return "tablecells"
        case "html", "htm", "xml", "rss", "atom":
            return "globe"
        case "json", "jsonl", "ipynb":
            return "curlybraces"
        case "epub":
            return "book"
        case "wav", "mp3", "m4a":
            return "waveform"
        case "mp4":
            return "film"
        case "zip":
            return "doc.zipper"
        default:
            return "doc"
        }
    }
}
