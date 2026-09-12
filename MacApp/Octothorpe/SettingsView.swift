import AppKit
import SwiftUI

struct SettingsView: View {
    @Environment(SettingsStore.self) private var settings

    var body: some View {
        @Bindable var settings = settings
        Form {
            Section("Output folder") {
                HStack(spacing: 8) {
                    TextField("Leave empty to write in the project folder", text: $settings.outputDir)
                        .textFieldStyle(.roundedBorder)
                    Button("Choose…") {
                        chooseFolder()
                    }
                }
                Text("Markdown files are written here. The CLI uses the same config.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }
            Section("OCR mode") {
                Picker("OCR mode", selection: $settings.ocrMode) {
                    Text("Auto").tag("auto")
                    Text("Always").tag("always")
                    Text("Never").tag("never")
                }
                .pickerStyle(.radioGroup)
                .labelsHidden()
            }
            Section("OCR engine") {
                Picker("OCR engine", selection: $settings.ocrEngine) {
                    Text("RapidOCR").tag("rapidocr")
                    Text("Tesseract").tag("tesseract")
                }
                .pickerStyle(.radioGroup)
                .labelsHidden()
            }
        }
        .formStyle(.grouped)
        .frame(minWidth: 420, minHeight: 280)
        .onChange(of: settings.outputDir) { _, _ in settings.persist() }
        .onChange(of: settings.ocrMode) { _, _ in settings.persist() }
        .onChange(of: settings.ocrEngine) { _, _ in settings.persist() }
        .onAppear { settings.reload() }
    }

    private func chooseFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.canCreateDirectories = true
        panel.prompt = "Choose"
        panel.message = "Markdown output directory"
        if !settings.outputDir.isEmpty {
            panel.directoryURL = URL(fileURLWithPath: settings.outputDir, isDirectory: true)
        }
        guard panel.runModal() == .OK, let url = panel.url else { return }
        settings.outputDir = url.path
        settings.persist()
    }
}
