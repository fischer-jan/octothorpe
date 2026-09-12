import AppKit
import SwiftUI

struct FileRowView: View {
    var item: QueueItem
    var index: Int
    @State private var hover = false

    var body: some View {
        HStack(spacing: 12) {
            Badge(ext: item.url.pathExtension)
            VStack(alignment: .leading, spacing: 3) {
                Text(item.filename)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(Ink.text)
                    .lineLimit(1)
                    .truncationMode(.middle)
                if case .failed(let message) = item.status {
                    Text(message)
                        .font(.system(size: 12))
                        .foregroundStyle(Ink.bad)
                        .lineLimit(2)
                } else if case .done(let out) = item.status, let out {
                    HStack(spacing: 4) {
                        Text("→").foregroundStyle(Ink.amber)
                        Text((out as NSString).lastPathComponent)
                    }
                    .font(.inkMono(11.5))
                    .foregroundStyle(Ink.muted)
                    .lineLimit(1)
                    .truncationMode(.middle)
                } else {
                    Text(item.folder)
                        .font(.inkMono(11.5))
                        .foregroundStyle(Ink.muted)
                        .lineLimit(1)
                        .truncationMode(.head)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            statusView
        }
        .padding(.horizontal, 14).padding(.vertical, 10)
        .background(rowBackground, in: RoundedRectangle(cornerRadius: 11, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 11, style: .continuous).stroke(borderColor, lineWidth: 1))
        .overlay(alignment: .bottom) {
            if case .converting = item.status { Shimmer().clipShape(RoundedRectangle(cornerRadius: 11, style: .continuous)) }
        }
        .onHover { hover = $0 }
        .animation(.easeOut(duration: 0.15), value: hover)
        .animation(.easeOut(duration: 0.25), value: item.status)
        .accessibilityElement(children: .combine)
    }

    private var rowBackground: Color {
        switch item.status {
        case .converting: Ink.amber.opacity(0.07)
        case .failed: Ink.bad.opacity(0.06)
        default: hover ? Color.white.opacity(0.05) : Ink.card
        }
    }

    private var borderColor: Color {
        switch item.status {
        case .converting: Ink.amber.opacity(0.4)
        case .failed: Ink.bad.opacity(0.35)
        case .done: hover ? Ink.ok.opacity(0.35) : Ink.line
        default: Ink.line
        }
    }

    @ViewBuilder
    private var statusView: some View {
        switch item.status {
        case .queued:
            Text("queued")
                .font(.inkMono(11))
                .foregroundStyle(Ink.dim)
        case .converting:
            HStack(spacing: 7) {
                ProgressView().controlSize(.small).tint(Ink.amber)
                Text("converting")
                    .font(.inkMono(11, weight: .medium))
                    .foregroundStyle(Ink.amber)
            }
        case .done(let out):
            HStack(spacing: 8) {
                if hover, let out {
                    Button {
                        NSWorkspace.shared.selectFile(out, inFileViewerRootedAtPath: (out as NSString).deletingLastPathComponent)
                    } label: {
                        Label("Reveal", systemImage: "folder")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundStyle(Ink.text)
                            .padding(.horizontal, 9).padding(.vertical, 4)
                            .background(Color.white.opacity(0.08), in: Capsule())
                    }
                    .buttonStyle(.plain)
                    .help("Reveal the Markdown file in Finder")
                    // Fade in with a short slide from the left, so the button
                    // never passes under the checkmark to its right.
                    .transition(.opacity.combined(with: .offset(x: -8)))
                }
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 15))
                    .foregroundStyle(Ink.ok)
                    .symbolEffect(.bounce, value: item.status)
            }
        case .failed:
            Image(systemName: "xmark.circle.fill")
                .font(.system(size: 15))
                .foregroundStyle(Ink.bad)
        }
    }
}

struct Badge: View {
    let ext: String
    var body: some View {
        let color = Ink.badgeColor(for: ext)
        Text(Ink.badgeText(for: ext))
            .font(.inkMono(10, weight: .bold))
            .kerning(0.4)
            .foregroundStyle(color)
            .frame(width: 44, height: 34)
            .background(color.opacity(0.13), in: RoundedRectangle(cornerRadius: 8, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 8, style: .continuous).stroke(color.opacity(0.25), lineWidth: 1))
    }
}

/// A thin amber light that sweeps along the bottom edge of a converting row.
struct Shimmer: View {
    var body: some View {
        TimelineView(.animation(minimumInterval: 1 / 30)) { ctx in
            let t = ctx.date.timeIntervalSinceReferenceDate
            GeometryReader { geo in
                let w = geo.size.width
                let x = CGFloat((t * 0.6).truncatingRemainder(dividingBy: 1)) * (w + 160) - 80
                LinearGradient(colors: [.clear, Ink.amber.opacity(0.9), .clear], startPoint: .leading, endPoint: .trailing)
                    .frame(width: 160, height: 2)
                    .offset(x: x, y: geo.size.height - 2)
            }
        }
        .allowsHitTesting(false)
    }
}
