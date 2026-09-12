import AppKit
import SwiftUI

@main
struct MdConvertApp: App {
    @State private var session = ConvertSession()
    @State private var settings = SettingsStore()

    var body: some Scene {
        Window("Octothorpe", id: "main") {
            ContentView()
                .environment(session)
                .environment(settings)
                .onAppear { Snapshot.runIfRequested(session: session) }
        }
        .defaultSize(width: 760, height: 620)
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentMinSize)
        .commands {
            CommandGroup(replacing: .newItem) {
                Button("Add Files…") {
                    session.chooseFiles(settings: settings)
                }
                .keyboardShortcut("o", modifiers: .command)
            }
            CommandGroup(after: .newItem) {
                Button("Convert") {
                    Task { await session.convertQueued(using: settings) }
                }
                .keyboardShortcut(.defaultAction)
                .disabled(!session.canConvert)
                Button("Clear") {
                    session.clear()
                }
                .disabled(!session.canClear)
            }
        }

        Settings {
            SettingsView()
                .environment(settings)
        }
    }
}

/// Debug aid: MDCONVERT_SNAPSHOT=/path/out.png renders the window to a PNG and quits.
/// MDCONVERT_DEMO=1 first fills the queue with sample rows in every state;
/// MDCONVERT_CONVERT_TO=/dir really converts the test fixtures into that folder.
/// Needs no screen-recording permission; used to check the UI from a terminal.
enum Snapshot {
    @MainActor
    static func runIfRequested(session: ConvertSession) {
        let env = ProcessInfo.processInfo.environment
        guard let out = env["MDCONVERT_SNAPSHOT"] else { return }
        Task { @MainActor in
            if env["MDCONVERT_DEMO"] != nil {
                let root = ProjectRoot.resolve().appendingPathComponent("tests/fixtures")
                var items = ["hello.pdf", "hello.txt", "tiny.png", "blank.pdf"].map { QueueItem(url: root.appendingPathComponent($0)) }
                if items.count == 4 {
                    items[0].status = .done(outputPath: "/tmp/hello.md")
                    items[1].status = .converting
                    items[3].status = .failed("no text layer and OCR found nothing")
                }
                session.items = items
                session.footer = .converting(current: 2, total: 4)
            }
            if let outDir = env["MDCONVERT_CONVERT_TO"] {
                // Real run: convert the fixtures into outDir, then snapshot the result.
                let settings = SettingsStore()
                settings.outputDir = outDir
                let root = ProjectRoot.resolve().appendingPathComponent("tests/fixtures")
                session.add(urls: ["hello.pdf", "hello.txt", "tiny.png", "blank.pdf"].map { root.appendingPathComponent($0) }, startConvert: false, settings: settings)
                await session.convertQueued(using: settings)
                for item in session.items { print(item.filename, item.status) }
            }
            try? await Task.sleep(for: .seconds(1.5))
            if let win = NSApp.windows.first(where: { $0.isVisible }), let view = win.contentView,
               let rep = view.bitmapImageRepForCachingDisplay(in: view.bounds) {
                view.cacheDisplay(in: view.bounds, to: rep)
                if let png = rep.representation(using: .png, properties: [:]) {
                    try? png.write(to: URL(fileURLWithPath: out))
                }
            }
            NSApp.terminate(nil)
        }
    }
}
