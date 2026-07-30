import AppKit

/// Her menu-bar icon: a paw print, drawn rather than shipped as an asset.
///
/// Drawn in code because a menu-bar icon has to be a **template image** — macOS recolours
/// it for the light and dark menu bar, for the highlighted state and for reduced
/// transparency. Ship a coloured PNG and it looks wrong in half of those. Vector-ish
/// drawing also means it stays crisp at whatever point size the bar happens to be.
///
/// Four toes on an arc over one big pad. The outer toes sit LOWER than the inner pair,
/// which is what makes a paw print read as a paw rather than as four dots on a blob —
/// the arc is the recognisable part.
enum MenuBarIcon {

    static func paw() -> NSImage {
        let side: CGFloat = 18
        let img = NSImage(size: NSSize(width: side, height: side), flipped: false) { _ in
            NSColor.black.setFill()

            // The big pad. Wider than tall and slightly domed, so it doesn't read as a
            // plain rounded square sitting under the toes.
            NSBezierPath(roundedRect: NSRect(x: 3.1, y: 1.5, width: 11.8, height: 7.6),
                         xRadius: 3.4, yRadius: 3.0).fill()

            // Toes: (x, y, w, h). The two inner ones are taller and higher; the outer
            // pair drop and shrink, which is the arc.
            let toes: [(CGFloat, CGFloat, CGFloat, CGFloat)] = [
                (0.9,  8.2, 3.5, 4.4),
                (5.1, 10.1, 3.6, 4.9),
                (9.3, 10.1, 3.6, 4.9),
                (13.6, 8.2, 3.5, 4.4),
            ]
            for (x, y, w, h) in toes {
                NSBezierPath(ovalIn: NSRect(x: x, y: y, width: w, height: h)).fill()
            }
            return true
        }
        // The whole point: without this it is a fixed black paw that vanishes on a dark
        // menu bar.
        img.isTemplate = true
        return img
    }

    /// Render the paw at 8x onto both a light and a dark strip, for eyeballing.
    ///
    /// A template image draws as a shape mask, so screenshotting the real menu bar
    /// tells you nothing about the artwork - and at 18pt no detail is legible anyway.
    @MainActor
    static func dump(to path: String) -> Bool {
        let s: CGFloat = 8, side = 18 * s
        let out = NSImage(size: NSSize(width: side * 2, height: side), flipped: false) { _ in
            NSColor.white.setFill(); NSRect(x: 0, y: 0, width: side, height: side).fill()
            NSColor(white: 0.13, alpha: 1).setFill()
            NSRect(x: side, y: 0, width: side, height: side).fill()
            let paw = NSBezierPath()
            paw.append(NSBezierPath(roundedRect: NSRect(x: 3.1, y: 1.5, width: 11.8, height: 7.6),
                                    xRadius: 3.4, yRadius: 3.0))
            for (x, y, w, h) in [(0.9, 8.2, 3.5, 4.4), (5.1, 10.1, 3.6, 4.9),
                                 (9.3, 10.1, 3.6, 4.9), (13.6, 8.2, 3.5, 4.4)]
                as [(CGFloat, CGFloat, CGFloat, CGFloat)] {
                paw.append(NSBezierPath(ovalIn: NSRect(x: x, y: y, width: w, height: h)))
            }
            for (dx, colour) in [(CGFloat(0), NSColor.black), (side, NSColor.white)] {
                let t = NSAffineTransform()
                t.translateX(by: dx, yBy: 0); t.scaleX(by: s, yBy: s)
                let scaled = paw.copy() as! NSBezierPath
                scaled.transform(using: t as AffineTransform)
                colour.setFill(); scaled.fill()
            }
            return true
        }
        guard let tiff = out.tiffRepresentation,
              let rep = NSBitmapImageRep(data: tiff),
              let png = rep.representation(using: .png, properties: [:]) else { return false }
        return (try? png.write(to: URL(fileURLWithPath: path))) != nil
    }
}
