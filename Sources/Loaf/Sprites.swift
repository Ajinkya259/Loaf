import AppKit

/// Loads and caches the PNGs Blender renders.
///
/// Everything here assumes the sprite contract (SPRITE_CONTRACT.md): every file is
/// 640×512 RGBA with the ground line 24px above the bottom edge, so the app can
/// anchor them all bottom-centre and trust that she neither jumps nor resizes when
/// she changes state.
enum Sprites {

    // MARK: Geometry, straight out of the contract

    /// Canvas aspect. The character window must preserve this or she distorts.
    static let aspect: CGFloat = 640.0 / 512.0

    /// Her feet sit 24px above the bottom of a 512px canvas — measured from the PNGs,
    /// not assumed. Multiply by the window height to get the inset in points.
    static let groundFraction: CGFloat = 24.0 / 512.0

    // MARK: Bundle

    /// The resource bundle, which is in two different places depending on how she was
    /// launched. SwiftPM's generated `Bundle.module` only looks in the .app root and
    /// the absolute dev build path, so it cannot see a bundle placed in
    /// `Contents/Resources/` by a packaging script — check there first, then fall back
    /// to `.module` for `swift run`. lil-cleo hit this exact problem.
    private static let bundle: Bundle = {
        if let url = Bundle.main.resourceURL?.appendingPathComponent("Loaf_Loaf.bundle"),
           let b = Bundle(url: url) { return b }
        return .module
    }()

    // MARK: Weight

    /// Which body weight to draw. Set from `Settings`; every lookup goes through it.
    ///
    /// Weight is a DIRECTORY, not a filename suffix - `sprites/<weight>/<state>.png`.
    /// Fatness applies to every pose, so as a suffix it would be a cross product that
    /// multiplies again with each new state. As a directory the naming contract inside
    /// each folder is identical, so a new state gets every weight for free and a new
    /// weight gets every state for free.
    static var weight = "normal" {
        didSet {
            guard weight != oldValue else { return }
            // Caches are keyed by weight, so nothing has to be thrown away - but the
            // frame counts must not be, or a state that has a cycle at one weight and
            // not another would silently keep the wrong count.
            frameCounts.removeAll()
        }
    }

    // MARK: Loading

    private static var cache: [String: NSImage] = [:]

    /// One sprite by filename stem, cached. Returns nil when the file isn't bundled.
    static func image(_ name: String) -> NSImage? {
        let key = "\(weight)/\(name)"
        if let hit = cache[key] { return hit }
        guard let url = bundle.url(forResource: name, withExtension: "png",
                                   subdirectory: "sprites/\(weight)")
                ?? bundle.url(forResource: "sprites/\(weight)/\(name)", withExtension: "png"),
              let img = NSImage(contentsOf: url) else { return nil }
        cache[key] = img
        return img
    }

    private static var frameCounts: [String: Int] = [:]

    /// How many frames `<name>1.png … <name>N.png` are bundled. 0 means this state is
    /// a single still, not a cycle. Capped at 16 so a bad name can't spin forever.
    static func frameCount(_ name: String) -> Int {
        let key = "\(weight)/\(name)"
        if let hit = frameCounts[key] { return hit }
        var n = 0
        while n < 16, image("\(name)\(n + 1)") != nil { n += 1 }
        frameCounts[key] = n
        return n
    }

    /// Is there any art for this state?
    ///
    /// A still **or** a cycle counts. Checking only one is a real trap: `sit` ships as
    /// a lone `sit.png` and `walk` ships only as `walk1…8.png` with no `walk.png`, so
    /// either test alone marks one of them missing.
    static func exists(_ name: String) -> Bool {
        image(name) != nil || frameCount(name) > 0
    }

    /// The frame to draw for a state at time `t`. Stills ignore `t`.
    static func frameName(_ name: String, t: TimeInterval, fps: Double) -> String {
        let n = frameCount(name)
        guard n > 0 else { return name }
        return "\(name)\(Int(t * fps) % n + 1)"
    }
}
