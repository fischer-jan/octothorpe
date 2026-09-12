import SwiftUI

/// "Ink & amber": warm charcoal paper, amber-to-coral accent, serif wordmark, mono details.
enum Ink {
    static let bg = Color(red: 0.055, green: 0.047, blue: 0.043)        // #0e0c0b
    static let bgWarm = Color(red: 0.125, green: 0.098, blue: 0.082)    // #201915
    static let panel = Color(red: 0.11, green: 0.094, blue: 0.086).opacity(0.78)
    static let card = Color(red: 0.13, green: 0.112, blue: 0.1).opacity(0.7)
    static let line = Color.white.opacity(0.07)
    static let text = Color(red: 0.953, green: 0.933, blue: 0.894)      // #f3eee4
    static let muted = Color(red: 0.64, green: 0.588, blue: 0.54)       // #a3968a
    static let dim = Color(red: 0.42, green: 0.38, blue: 0.35)
    static let amber = Color(red: 1.0, green: 0.706, blue: 0.33)        // #ffb454
    static let coral = Color(red: 1.0, green: 0.42, blue: 0.34)         // #ff6b57
    static let ok = Color(red: 0.6, green: 0.87, blue: 0.55)
    static let bad = Color(red: 1.0, green: 0.45, blue: 0.5)

    static let accentGradient = LinearGradient(colors: [amber, coral], startPoint: .topLeading, endPoint: .bottomTrailing)
    static let radius: CGFloat = 14

    /// Colour family for a file extension badge.
    static func badgeColor(for ext: String) -> Color {
        switch ext.lowercased() {
        case "pdf": Color(red: 1.0, green: 0.48, blue: 0.42)
        case "docx", "doc", "rtf", "txt", "text": Color(red: 0.47, green: 0.68, blue: 1.0)
        case "pptx", "ppt": Color(red: 1.0, green: 0.6, blue: 0.35)
        case "xlsx", "xls", "csv": Color(red: 0.45, green: 0.85, blue: 0.6)
        case "html", "htm", "xml", "rss", "atom": Color(red: 0.55, green: 0.8, blue: 1.0)
        case "json", "jsonl", "ipynb": Color(red: 0.85, green: 0.75, blue: 1.0)
        case "png", "jpg", "jpeg", "tiff", "tif", "webp", "bmp", "gif": amber
        case "wav", "mp3", "m4a", "mp4": Color(red: 0.8, green: 0.6, blue: 1.0)
        case "epub": Color(red: 0.9, green: 0.8, blue: 0.55)
        case "zip", "msg": Color(red: 0.7, green: 0.7, blue: 0.7)
        default: muted
        }
    }

    static func badgeText(for ext: String) -> String {
        let e = ext.uppercased()
        return e.count > 4 ? String(e.prefix(4)) : (e.isEmpty ? "FILE" : e)
    }
}

extension Font {
    static func inkMono(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .monospaced)
    }
    static func inkSerif(_ size: CGFloat, weight: Font.Weight = .semibold) -> Font {
        .system(size: size, weight: weight, design: .serif)
    }
}

/// Small pill used for keyboard hints and counters.
struct Pill: View {
    let text: String
    var color: Color = Ink.muted
    var glow = false
    var body: some View {
        Text(text)
            .font(.inkMono(11, weight: .medium))
            .kerning(0.8)
            .foregroundStyle(color)
            .padding(.horizontal, 10).padding(.vertical, 5)
            .background(Ink.panel, in: Capsule())
            .overlay(Capsule().stroke(glow ? color.opacity(0.5) : Ink.line, lineWidth: 1))
            .shadow(color: glow ? color.opacity(0.35) : .clear, radius: 8)
    }
}

struct IconButtonStyle: ButtonStyle {
    var danger = false
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 14, weight: .medium))
            .foregroundStyle(danger ? Ink.bad : Ink.muted)
            .frame(width: 34, height: 34)
            .background(Color.white.opacity(configuration.isPressed ? 0.1 : 0.04), in: RoundedRectangle(cornerRadius: 9))
            .overlay(RoundedRectangle(cornerRadius: 9).stroke(Ink.line, lineWidth: 1))
            .contentShape(RoundedRectangle(cornerRadius: 9))
    }
}

struct ConvertButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var enabled
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .bold))
            .foregroundStyle(enabled ? Color(red: 0.12, green: 0.07, blue: 0.04) : Ink.dim)
            .padding(.horizontal, 18).padding(.vertical, 9)
            .background {
                if enabled {
                    RoundedRectangle(cornerRadius: 10).fill(Ink.accentGradient)
                } else {
                    RoundedRectangle(cornerRadius: 10).fill(Color.white.opacity(0.05))
                        .overlay(RoundedRectangle(cornerRadius: 10).stroke(Ink.line))
                }
            }
            .shadow(color: enabled ? Ink.amber.opacity(0.4) : .clear, radius: 12, y: 4)
            .brightness(configuration.isPressed ? -0.08 : 0)
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}
