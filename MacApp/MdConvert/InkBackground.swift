import SwiftUI

/// Warm paper-dark background with a faint `#` pattern and an amber glow that breathes while busy.
struct InkBackground: View {
    var busy: Bool

    var body: some View {
        ZStack {
            Ink.bg
            RadialGradient(colors: [Ink.bgWarm, Ink.bg], center: UnitPoint(x: 0.15, y: -0.2), startRadius: 0, endRadius: 900)
            HashPattern()
                .mask(LinearGradient(stops: [.init(color: .clear, location: 0), .init(color: .black, location: 0.12), .init(color: .black.opacity(0.3), location: 0.6), .init(color: .clear, location: 1)], startPoint: .top, endPoint: .bottom))
            TimelineView(.animation(minimumInterval: 1 / 30, paused: !busy)) { ctx in
                let t = ctx.date.timeIntervalSinceReferenceDate
                let k = busy ? 0.8 + 0.2 * sin(t * 2.2) : 1
                RadialGradient(colors: [Ink.amber.opacity(0.13 * k), Ink.coral.opacity(0.05 * k), .clear],
                               center: UnitPoint(x: 0.5, y: 0), startRadius: 0, endRadius: 520)
                    .scaleEffect(busy ? 1 + 0.05 * sin(t * 2.2) : 1, anchor: .top)
                    .blur(radius: 24)
            }
        }
        .ignoresSafeArea()
    }
}

/// A sparse grid of small `#` glyphs, like a watermark.
struct HashPattern: View {
    var body: some View {
        Canvas { g, size in
            let step: CGFloat = 64
            var y: CGFloat = 20
            var row = 0
            while y < size.height {
                var x: CGFloat = row.isMultiple(of: 2) ? 20 : 52
                while x < size.width {
                    let text = Text("#").font(.system(size: 13, weight: .semibold, design: .monospaced)).foregroundColor(Ink.amber.opacity(0.045))
                    g.draw(text, at: CGPoint(x: x, y: y))
                    x += step
                }
                y += step
                row += 1
            }
        }
        .allowsHitTesting(false)
    }
}
