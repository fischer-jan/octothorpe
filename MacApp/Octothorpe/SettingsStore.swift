import Foundation
import Observation

@MainActor
@Observable
final class SettingsStore {
    var outputDir: String
    var ocrMode: String
    var ocrEngine: String
    var tidy: Bool

    init() {
        let loaded = AppConfigFile.load()
        outputDir = loaded.output_dir
        ocrMode = loaded.ocr
        ocrEngine = loaded.ocr_engine
        tidy = loaded.tidy
    }

    var snapshot: AppConfigFile {
        AppConfigFile(output_dir: outputDir, ocr: ocrMode, ocr_engine: ocrEngine, tidy: tidy)
    }

    func persist() {
        do {
            try snapshot.save()
        } catch {
            // Settings stay in memory; the next convert still gets CLI flags.
        }
    }

    func reload() {
        let loaded = AppConfigFile.load()
        outputDir = loaded.output_dir
        ocrMode = loaded.ocr
        ocrEngine = loaded.ocr_engine
        tidy = loaded.tidy
    }
}
