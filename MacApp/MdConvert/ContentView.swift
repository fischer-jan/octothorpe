import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @Environment(ConvertSession.self) private var session
    @Environment(SettingsStore.self) private var settings

    var body: some View {
        @Bindable var session = session
        NavigationStack {
            VStack(spacing: 12) {
                DropZoneView(
                    hasFiles: !session.items.isEmpty,
                    isTargeted: $session.isDropTargeted,
                    onTap: { session.chooseFiles(settings: settings) },
                    onDropProviders: { session.ingestDropProviders($0, settings: settings) }
                )
                if !session.items.isEmpty {
                    List(session.items) { item in
                        FileRowView(item: item)
                    }
                    .listStyle(.inset)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
                FooterBar(footer: session.footer)
            }
            .padding(16)
            .frame(minWidth: 520, minHeight: 420)
            .toolbar {
                ToolbarItem(placement: .navigation) {
                    Button {
                        session.chooseFiles(settings: settings)
                    } label: {
                        Image(systemName: "plus")
                    }
                    .help("Add files")
                    .accessibilityLabel("Add files")
                    .keyboardShortcut("o", modifiers: .command)
                }
                ToolbarItem(placement: .navigation) {
                    Button {
                        session.clear()
                    } label: {
                        Image(systemName: "trash")
                    }
                    .help("Clear list")
                    .accessibilityLabel("Clear list")
                    .disabled(!session.canClear)
                }
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        Task { await session.convertQueued(using: settings) }
                    } label: {
                        Label("Convert", systemImage: "play.fill")
                    }
                    .buttonStyle(.borderedProminent)
                    .keyboardShortcut(.defaultAction)
                    .help("Convert queued files")
                    .accessibilityLabel("Convert queued files")
                    .disabled(!session.canConvert)
                }
                ToolbarItem(placement: .automatic) {
                    SettingsLink {
                        Image(systemName: "gearshape")
                    }
                    .help("Settings")
                    .accessibilityLabel("Settings")
                }
            }
            .navigationTitle("MdConvert")
        }
        .onDrop(of: [.fileURL], isTargeted: $session.isDropTargeted) { providers in
            session.ingestDropProviders(providers, settings: settings)
            return true
        }
    }
}

#Preview {
    ContentView()
        .environment(ConvertSession())
        .environment(SettingsStore())
        .frame(width: 640, height: 560)
}
