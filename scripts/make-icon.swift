// Renders the MdConvert app icon (1024 px PNG). Usage: swift scripts/make-icon.swift out.png
import AppKit

let out = CommandLine.arguments[1]
let S = 1024.0
let img = NSImage(size: NSSize(width: S, height: S))
img.lockFocus()
let ctx = NSGraphicsContext.current!.cgContext
let amber = NSColor(red: 1.0, green: 0.706, blue: 0.33, alpha: 1)
let coral = NSColor(red: 1.0, green: 0.42, blue: 0.34, alpha: 1)
let ink = NSColor(red: 0.12, green: 0.07, blue: 0.04, alpha: 1)

// squircle background, warm charcoal
let inset = S * 0.05
let rect = CGRect(x: inset, y: inset, width: S - 2 * inset, height: S - 2 * inset)
ctx.addPath(CGPath(roundedRect: rect, cornerWidth: S * 0.22, cornerHeight: S * 0.22, transform: nil)); ctx.clip()
let bg = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(), colors: [
    NSColor(red: 0.16, green: 0.12, blue: 0.10, alpha: 1).cgColor,
    NSColor(red: 0.055, green: 0.047, blue: 0.043, alpha: 1).cgColor] as CFArray, locations: [0, 1])!
ctx.drawLinearGradient(bg, start: CGPoint(x: 0, y: S), end: CGPoint(x: S, y: 0), options: [])

// faint # watermark grid
let hash = NSAttributedString(string: "#", attributes: [.font: NSFont.monospacedSystemFont(ofSize: 44, weight: .bold), .foregroundColor: amber.withAlphaComponent(0.07)])
var row = 0
var y = inset + 20.0
while y < S { var x = inset + (row % 2 == 0 ? 20.0 : 70.0); while x < S { hash.draw(at: CGPoint(x: x, y: y)); x += 100 }; y += 100; row += 1 }

// a paper sheet, slightly tilted, with text lines
ctx.saveGState()
ctx.translateBy(x: S * 0.5, y: S * 0.52)
ctx.rotate(by: -0.07)
let sheet = CGRect(x: -S * 0.21, y: -S * 0.28, width: S * 0.42, height: S * 0.56)
ctx.setShadow(offset: CGSize(width: 0, height: -18), blur: 50, color: NSColor.black.withAlphaComponent(0.6).cgColor)
ctx.setFillColor(NSColor(red: 0.953, green: 0.933, blue: 0.894, alpha: 1).cgColor)
ctx.addPath(CGPath(roundedRect: sheet, cornerWidth: 40, cornerHeight: 40, transform: nil)); ctx.fillPath()
ctx.setShadow(offset: .zero, blur: 0, color: nil)
ctx.setFillColor(NSColor(red: 0.12, green: 0.07, blue: 0.04, alpha: 0.18).cgColor)
let widths: [CGFloat] = [0.26, 0.34, 0.2, 0.3, 0.16, 0.32]
for (i, w) in widths.enumerated() {
    let ly = sheet.maxY - 90 - CGFloat(i) * 52
    ctx.addPath(CGPath(roundedRect: CGRect(x: sheet.minX + 50, y: ly, width: S * w, height: 20), cornerWidth: 10, cornerHeight: 10, transform: nil))
}
ctx.fillPath()
ctx.restoreGState()

// amber # badge, bottom-right, with glow
let badge = CGRect(x: S * 0.50, y: S * 0.14, width: S * 0.34, height: S * 0.34)
ctx.saveGState()
ctx.setShadow(offset: .zero, blur: 70, color: amber.withAlphaComponent(0.7).cgColor)
ctx.addPath(CGPath(roundedRect: badge, cornerWidth: 80, cornerHeight: 80, transform: nil)); ctx.clip()
let g = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(), colors: [amber.cgColor, coral.cgColor] as CFArray, locations: [0, 1])!
ctx.drawLinearGradient(g, start: CGPoint(x: badge.minX, y: badge.maxY), end: CGPoint(x: badge.maxX, y: badge.minY), options: [])
ctx.restoreGState()
let glyph = NSAttributedString(string: "#", attributes: [.font: NSFont.monospacedSystemFont(ofSize: 250, weight: .black), .foregroundColor: ink])
let gs = glyph.size()
glyph.draw(at: CGPoint(x: badge.midX - gs.width / 2, y: badge.midY - gs.height / 2 + 6))
img.unlockFocus()

let png = NSBitmapImageRep(data: img.tiffRepresentation!)!.representation(using: .png, properties: [:])!
try! png.write(to: URL(fileURLWithPath: out))
