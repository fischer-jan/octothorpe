import SwiftUI
import UniformTypeIdentifiers

/// The drop target. Big and inviting when the queue is empty, a slim strip when it is not.
struct DropZoneView: View {
    var hasFiles: Bool
    @Binding var isTargeted: Bool
    var onTap: () -> Void
    var onDropProviders: ([NSItemProvider]) -> Void

    private let types = ["PDF", "DOCX", "PPTX", "XLSX", "HTML", "EPUB", "IMAGES", "AUDIO", "JSON", "ZIP"]

    var body: some View {
        Button(action: onTap) {
            ZStack {
                shape.fill(isTargeted ? Ink.amber.opacity(0.10) : Ink.panel)
                shape.fill(.ultraThinMaterial).opacity(0.25)
                MarchingBorder(active: isTargeted, radius: Ink.radius)
                if hasFiles { compact } else { hero }
            }
            .frame(maxWidth: .infinity)
            .frame(minHeight: hasFiles ? 58 : 220, maxHeight: hasFiles ? 58 : .infinity)
            .contentShape(shape)
            .scaleEffect(isTargeted ? 1.01 : 1)
            .shadow(color: isTargeted ? Ink.amber.opacity(0.25) : .black.opacity(0.3), radius: isTargeted ? 30 : 16, y: 8)
            .animation(.spring(response: 0.3, dampingFraction: 0.8), value: isTargeted)
            .animation(.spring(response: 0.35, dampingFraction: 0.85), value: hasFiles)
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Add files")
        .accessibilityHint("Opens a file picker. Dropped files start convert.")
        .onDrop(of: [.fileURL], isTargeted: $isTargeted) { providers in
            onDropProviders(providers)
            return true
        }
    }

    private var shape: RoundedRectangle { RoundedRectangle(cornerRadius: Ink.radius, style: .continuous) }

    private var hero: some View {
        VStack(spacing: 18) {
            GlyphMorph(active: isTargeted)
            VStack(spacing: 6) {
                Text(isTargeted ? "Release to convert" : "Drop anything. Get Markdown.")
                    .font(.inkSerif(26, weight: .semibold))
                    .foregroundStyle(Ink.text)
                    .contentTransition(.opacity)
                Text("Drop files here, or click to choose. Dropped files convert at once.")
                    .font(.system(size: 13))
                    .foregroundStyle(Ink.muted)
            }
            HStack(spacing: 6) {
                ForEach(types, id: \.self) { t in
                    Text(t)
                        .font(.inkMono(10, weight: .semibold))
                        .foregroundStyle(Ink.badgeColor(for: t == "IMAGES" ? "png" : t == "AUDIO" ? "mp3" : t).opacity(0.9))
                        .padding(.horizontal, 8).padding(.vertical, 4)
                        .background(Color.white.opacity(0.04), in: Capsule())
                        .overlay(Capsule().stroke(Ink.line))
                }
            }
            .padding(.top, 4)
        }
        .padding(24)
    }

    private var compact: some View {
        HStack(spacing: 12) {
            Image(systemName: isTargeted ? "arrow.down.doc.fill" : "plus.circle")
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(Ink.amber)
                .contentTransition(.symbolEffect(.replace))
            Text(isTargeted ? "Release to convert" : "Drop more files, or click to add")
                .font(.system(size: 13, weight: .medium))
                .foregroundStyle(isTargeted ? Ink.text : Ink.muted)
            Spacer()
            Text("drop = convert now")
                .font(.inkMono(11))
                .foregroundStyle(Ink.dim)
        }
        .padding(.horizontal, 18)
    }
}

/// Dashed outline whose dashes march while a drag hovers.
struct MarchingBorder: View {
    var active: Bool
    var radius: CGFloat

    var body: some View {
        TimelineView(.animation(minimumInterval: 1 / 30, paused: !active)) { ctx in
            let t = ctx.date.timeIntervalSinceReferenceDate
            RoundedRectangle(cornerRadius: radius, style: .continuous)
                .strokeBorder(
                    active ? AnyShapeStyle(Ink.accentGradient) : AnyShapeStyle(Color.white.opacity(0.12)),
                    style: StrokeStyle(lineWidth: active ? 2 : 1.2, dash: [9, 7], dashPhase: active ? CGFloat(-t * 40).truncatingRemainder(dividingBy: 16) : 0)
                )
        }
    }
}

/// Three document cards that fan out, with a `#` badge that lights up when a drag hovers.
struct GlyphMorph: View {
    var active: Bool

    var body: some View {
        ZStack {
            ForEach(0..<3, id: \.self) { i in
                let off = CGFloat(i - 1)
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .fill(Ink.card)
                    .overlay(RoundedRectangle(cornerRadius: 8, style: .continuous).stroke(Ink.line, lineWidth: 1))
                    .overlay(alignment: .topLeading) {
                        VStack(alignment: .leading, spacing: 4) {
                            ForEach(0..<4, id: \.self) { l in
                                Capsule().fill(Ink.muted.opacity(0.25))
                                    .frame(width: [26, 38, 20, 32][l], height: 3)
                            }
                        }
                        .padding(10)
                    }
                    .frame(width: 56, height: 72)
                    .rotationEffect(.degrees(active ? off * 14 : off * 5))
                    .offset(x: active ? off * 30 : off * 12, y: active ? -abs(off) * 6 : 0)
                    .shadow(color: .black.opacity(0.3), radius: 8, y: 4)
                    .zIndex(i == 1 ? 1 : 0)
            }
            Text("#")
                .font(.system(size: 22, weight: .heavy, design: .monospaced))
                .foregroundStyle(Color(red: 0.12, green: 0.07, blue: 0.04))
                .frame(width: 40, height: 40)
                .background(Ink.accentGradient, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
                .shadow(color: Ink.amber.opacity(active ? 0.7 : 0.4), radius: active ? 18 : 10, y: 4)
                .offset(y: active ? 34 : 28)
                .scaleEffect(active ? 1.15 : 1)
                .zIndex(2)
        }
        .frame(height: 100)
        .animation(.spring(response: 0.35, dampingFraction: 0.7), value: active)
    }
}
