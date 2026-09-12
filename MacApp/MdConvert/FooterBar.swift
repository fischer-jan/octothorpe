import SwiftUI

struct FooterBar: View {
    var footer: FooterKind
    var progress: Double?     // 0…1 while converting
    var counts: (done: Int, failed: Int, queued: Int)

    var body: some View {
        VStack(spacing: 8) {
            ZStack(alignment: .leading) {
                Capsule().fill(Color.white.opacity(0.06)).frame(height: 3)
                if let progress {
                    GeometryReader { geo in
                        Capsule()
                            .fill(Ink.accentGradient)
                            .frame(width: max(6, geo.size.width * progress), height: 3)
                            .shadow(color: Ink.amber.opacity(0.6), radius: 6)
                            .animation(.easeOut(duration: 0.4), value: progress)
                    }
                    .frame(height: 3)
                }
            }
            .opacity(progress == nil ? 0.5 : 1)
            HStack(spacing: 10) {
                Circle().fill(color).frame(width: 6, height: 6)
                    .shadow(color: color.opacity(0.8), radius: 4)
                Text(footer.text)
                    .font(.system(size: 12.5))
                    .foregroundStyle(color)
                    .lineLimit(2)
                Spacer(minLength: 0)
                HStack(spacing: 10) {
                    if counts.queued > 0 { Text("\(counts.queued) queued").foregroundStyle(Ink.dim) }
                    if counts.done > 0 { Text("\(counts.done) done").foregroundStyle(Ink.ok.opacity(0.85)) }
                    if counts.failed > 0 { Text("\(counts.failed) failed").foregroundStyle(Ink.bad) }
                }
                .font(.inkMono(11))
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(footer.text)
    }

    private var color: Color {
        switch footer {
        case .ready, .queued: Ink.muted
        case .converting: Ink.amber
        case .finished(_, let failed): failed > 0 ? Ink.bad : Ink.ok
        case .error: Ink.bad
        }
    }
}
