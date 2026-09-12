import Foundation

struct AppConfigFile: Codable, Equatable, Sendable {
    var output_dir: String
    var ocr: String
    var ocr_engine: String

    static let ocrModes = ["auto", "always", "never"]
    static let ocrEngines = ["rapidocr", "tesseract"]

    static let `default` = AppConfigFile(output_dir: "", ocr: "auto", ocr_engine: "rapidocr")

    static func configURL() -> URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".config", isDirectory: true)
            .appendingPathComponent("octothorpe", isDirectory: true)
            .appendingPathComponent("config.json")
    }

    static func load() -> AppConfigFile {
        let url = configURL()
        guard let data = try? Data(contentsOf: url),
              let raw = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        else {
            return .default
        }
        return normalize(raw)
    }

    static func normalize(_ data: [String: Any]) -> AppConfigFile {
        var ocr = String(describing: data["ocr"] ?? "auto").lowercased()
        if ocr.isEmpty || !ocrModes.contains(ocr) {
            ocr = "auto"
        }
        var engine = String(describing: data["ocr_engine"] ?? "rapidocr").lowercased()
        if engine.isEmpty || !ocrEngines.contains(engine) {
            engine = "rapidocr"
        }
        let output: String
        if let value = data["output_dir"] as? String {
            output = value
        } else {
            output = ""
        }
        return AppConfigFile(output_dir: output, ocr: ocr, ocr_engine: engine)
    }

    func save() throws {
        var file = self
        if !Self.ocrModes.contains(file.ocr) {
            file.ocr = "auto"
        }
        if !Self.ocrEngines.contains(file.ocr_engine) {
            file.ocr_engine = "rapidocr"
        }
        let url = Self.configURL()
        try FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        var data = try encoder.encode(file)
        if var text = String(data: data, encoding: .utf8) {
            text = text.replacingOccurrences(of: "\\/", with: "/")
            if !text.hasSuffix("\n") {
                text.append("\n")
            }
            data = Data(text.utf8)
        }
        try data.write(to: url, options: .atomic)
    }
}
