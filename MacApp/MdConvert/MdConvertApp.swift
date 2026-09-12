import SwiftUI

@main
struct MdConvertApp: App {
    @State private var session = ConvertSession()
    @State private var settings = SettingsStore()

    var body: some Scene {
        Window("MdConvert", id: "main") {
            ContentView()
                .environment(session)
                .environment(settings)
        }
        .defaultSize(width: 640, height: 560)
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
