import SwiftUI
import AppKit

/// Renders the live SwiftUI view to a PNG and exits.
///
///     LOAF_SNAPSHOT=/tmp/x.png LOAF_STATE=sleep swift run Loaf
///
/// This exists because there was no way to see what the app actually drew. Every
/// visual check this session went through Blender's previews, which show the SPRITE -
/// they say nothing about anything the app draws on top, and the drifting "z"s shipped
/// invisible precisely because of that blind spot. Renders over a checkerboard so a
/// pale element on a pale background is still obvious.
@MainActor
enum Snapshot {
    static func render(state: LoafState, to path: String) -> Bool {
        let settings = Settings()
        let engine = CatEngine()
        engine.pin(state)

        let w = AppDelegate.baseSize.width, h = AppDelegate.baseSize.height
        let view = ZStack {
            // Light and dark side by side: anything that only reads on one of them is
            // a bug, and a plain background would hide exactly that.
            HStack(spacing: 0) {
                Color.white
                Color(red: 0.13, green: 0.13, blue: 0.16)
            }
            CatView(settings: settings, engine: engine)
        }
        .frame(width: w, height: h)

        let renderer = ImageRenderer(content: view)
        renderer.scale = 3
        guard let img = renderer.nsImage,
              let tiff = img.tiffRepresentation,
              let rep = NSBitmapImageRep(data: tiff),
              let png = rep.representation(using: .png, properties: [:]) else { return false }
        do { try png.write(to: URL(fileURLWithPath: path)); return true } catch { return false }
    }

    /// Same idea, for the paw-drop gesture (`PawDropView.swift`), which isn't a
    /// `LoafState` and so isn't covered by `render(state:to:)` at all.
    ///
    ///     LOAF_PAW_SNAPSHOT=/tmp/p.png LOAF_PAW_T=0.55 swift run Loaf
    ///
    /// `elapsed` is real wall-clock time: `trigger()` starts the gesture for real,
    /// then this thread sleeps before capturing, so `TimelineView` reads the same
    /// clock it would in the running app rather than a faked-up state.
    static func renderPawDrop(elapsed: TimeInterval, to path: String) -> Bool {
        let engine = PawDropEngine()
        engine.trigger()
        if elapsed > 0 { Thread.sleep(forTimeInterval: elapsed) }

        let w = PawDropView.pawSize + 60, h = PawDropView.reach + PawDropView.pawSize + 20
        let view = ZStack {
            HStack(spacing: 0) {
                Color.white
                Color(red: 0.13, green: 0.13, blue: 0.16)
            }
            PawDropView(engine: engine)
        }
        .frame(width: w, height: h)

        let renderer = ImageRenderer(content: view)
        renderer.scale = 3
        guard let img = renderer.nsImage,
              let tiff = img.tiffRepresentation,
              let rep = NSBitmapImageRep(data: tiff),
              let png = rep.representation(using: .png, properties: [:]) else { return false }
        do { try png.write(to: URL(fileURLWithPath: path)); return true } catch { return false }
    }
}
