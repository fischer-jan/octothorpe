import SwiftUI

struct HeaderBar: View {
    @Environment(ConvertSession.self) private var session
    @Environment(SettingsStore.self) private var settings

    var body: some View {
        HStack(alignment: .center, spacing: 14) {
            Wordmark(busy: session.isBusy)
            Spacer()
            statusPill
            HStack(spacing: 8) {
                Button { session.chooseFiles(settings: settings) } label: { Image(systemName: "plus") }
                    .buttonStyle(IconButtonStyle())
                    .help("Add files (⌘O)")
                    .accessibilityLabel("Add files")
                    .keyboardShortcut("o", modifiers: .command)
                Button { session.clear() } label: { Image(systemName: "trash") }
                    .buttonStyle(IconButtonStyle(danger: true))
                    .help("Clear list")
                    .accessibilityLabel("Clear list")
                    .disabled(!session.canClear)
                    .opacity(session.canClear ? 1 : 0.4)
                SettingsLink { Image(systemName: "gearshape") }
                    .buttonStyle(IconButtonStyle())
                    .help("Settings (⌘,)")
                    .accessibilityLabel("Settings")
            }
            Button {
                Task { await session.convertQueued(using: settings) }
            } label: {
                HStack(spacing: 7) {
                    Image(systemName: "play.fill").font(.system(size: 11, weight: .bold))
                    Text(convertTitle)
                }
            }
            .buttonStyle(ConvertButtonStyle())
            .keyboardShortcut(.defaultAction)
            .help("Convert queued files (↩)")
            .accessibilityLabel("Convert queued files")
            .disabled(!session.canConvert)
        }
    }

    private var convertTitle: String {
        let n = session.queuedCount
        return n > 1 ? "Convert \(n)" : "Convert"
    }

    @ViewBuilder
    private var statusPill: some View {
        switch session.footer {
        case .converting: Pill(text: "CONVERTING", color: Ink.amber, glow: true)
        case .finished(_, let failed): Pill(text: failed > 0 ? "DONE · ERRORS" : "DONE", color: failed > 0 ? Ink.bad : Ink.ok)
        case .error: Pill(text: "ERROR", color: Ink.bad)
        case .queued: Pill(text: "READY")
        case .ready: EmptyView()
        }
    }
}

/// The app name in serif, with a small animated `#` glyph that spins into `↓` while busy.
struct Wordmark: View {
    var busy: Bool

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 11)
                    .fill(Ink.accentGradient)
                    .frame(width: 40, height: 40)
                    .shadow(color: Ink.amber.opacity(busy ? 0.6 : 0.3), radius: busy ? 14 : 8, y: 3)
                TimelineView(.animation(minimumInterval: 1 / 60, paused: !busy)) { ctx in
                    let t = ctx.date.timeIntervalSinceReferenceDate
                    Text("#")
                        .font(.system(size: 24, weight: .heavy, design: .monospaced))
                        .foregroundStyle(Color(red: 0.12, green: 0.07, blue: 0.04))
                        .rotationEffect(.degrees(busy ? (t * 90).truncatingRemainder(dividingBy: 360) : 0))
                }
            }
            VStack(alignment: .leading, spacing: 1) {
                Text("Octothorpe")
                    .font(.inkSerif(24))
                    .foregroundStyle(Ink.text)
                HStack(spacing: 0) {
                    Text("anything ").foregroundStyle(Ink.muted)
                    Text("→").foregroundStyle(Ink.amber)
                    Text(" .md").foregroundStyle(Ink.amber).font(.inkMono(12, weight: .semibold))
                }
                .font(.system(size: 12))
            }
        }
        .animation(.easeInOut(duration: 0.3), value: busy)
    }
}
