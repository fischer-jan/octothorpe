import Foundation

enum CLIRunner {
    struct ConvertResult: Sendable {
        var ok: Bool
        var message: String
    }

    static func convert(file: URL, config: AppConfigFile) async -> ConvertResult {
        await Task.detached(priority: .userInitiated) {
            run(file: file, config: config)
        }.value
    }

    private static func run(file: URL, config: AppConfigFile) -> ConvertResult {
        let cli = ProjectRoot.cliURL()
        let fm = FileManager.default
        guard fm.isExecutableFile(atPath: cli.path) else {
            return ConvertResult(
                ok: false,
                message: "octothorpe CLI not found at \(cli.path)"
            )
        }

        let process = Process()
        process.executableURL = cli
        var args = [file.path]
        let output = config.output_dir.trimmingCharacters(in: .whitespacesAndNewlines)
        if !output.isEmpty {
            args.append(contentsOf: ["-o", output])
        }
        args.append(contentsOf: [
            "--ocr", config.ocr,
            "--ocr-engine", config.ocr_engine,
            "--force",
        ])
        process.arguments = args
        process.currentDirectoryURL = ProjectRoot.resolve()

        let stdout = Pipe()
        let stderr = Pipe()
        process.standardOutput = stdout
        process.standardError = stderr
        process.standardInput = FileHandle.nullDevice

        do {
            try process.run()
        } catch {
            return ConvertResult(ok: false, message: shortError(error.localizedDescription))
        }
        process.waitUntilExit()

        let errData = stderr.fileHandleForReading.readDataToEndOfFile()
        let outData = stdout.fileHandleForReading.readDataToEndOfFile()
        let errText = String(data: errData, encoding: .utf8) ?? ""
        let outText = String(data: outData, encoding: .utf8) ?? ""

        if process.terminationStatus == 0 {
            return ConvertResult(ok: true, message: outText.trimmingCharacters(in: .whitespacesAndNewlines))
        }

        let parsed = parseCLIError(errText, fallback: outText)
        return ConvertResult(ok: false, message: shortError(parsed))
    }

    private static func parseCLIError(_ stderr: String, fallback: String) -> String {
        let lines = stderr.split(whereSeparator: \.isNewline).map { String($0) }
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            if trimmed.hasPrefix("error:") {
                var rest = String(trimmed.dropFirst("error:".count)).trimmingCharacters(in: .whitespaces)
                if let colon = rest.firstIndex(of: ":") {
                    rest = String(rest[rest.index(after: colon)...]).trimmingCharacters(in: .whitespaces)
                }
                if !rest.isEmpty {
                    return rest
                }
            }
        }
        let combined = (stderr + "\n" + fallback).trimmingCharacters(in: .whitespacesAndNewlines)
        if combined.isEmpty {
            return "Conversion failed"
        }
        return combined
    }

    static func shortError(_ text: String) -> String {
        let collapsed = text.split(whereSeparator: \.isWhitespace).joined(separator: " ")
        if collapsed.isEmpty {
            return "Conversion failed"
        }
        if collapsed.count > 72 {
            let idx = collapsed.index(collapsed.startIndex, offsetBy: 69)
            return String(collapsed[..<idx]) + "…"
        }
        return collapsed
    }
}
