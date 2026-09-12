import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @Environment(ConvertSession.self) private var session
    @Environment(SettingsStore.self) private var settings

    var body: some View {
        @Bindable var session = session
        ZStack {
            InkBackground(busy: session.isBusy)
            VStack(spacing: 14) {
                HeaderBar()
                    .padding(.top, 26)
                DropZoneView(
                    hasFiles: !session.items.isEmpty,
                    isTargeted: $session.isDropTargeted,
                    onTap: { session.chooseFiles(settings: settings) },
                    onDropProviders: { session.ingestDropProviders($0, settings: settings) }
                )
                if !session.items.isEmpty {
                    ScrollView {
                        LazyVStack(spacing: 6) {
                            ForEach(Array(session.items.enumerated()), id: \.element.id) { index, item in
                                FileRowView(item: item, index: index)
                                    .transition(.opacity.combined(with: .move(edge: .top)))
                            }
                        }
                        .padding(2)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .animation(.spring(response: 0.3, dampingFraction: 0.85), value: session.items.map(\.id))
                }
                FooterBar(footer: session.footer, progress: session.progress, counts: session.counts)
            }
            .padding(.horizontal, 22)
            .padding(.bottom, 16)
        }
        .preferredColorScheme(.dark)
        .foregroundStyle(Ink.text)
        .frame(minWidth: 640, minHeight: 480)
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
        .frame(width: 720, height: 600)
}
