import SwiftUI

/// User preferences, persisted in `UserDefaults`. Deliberately tiny — an app with a
/// large settings surface is one that couldn't decide how it should behave.
@MainActor
final class Settings: ObservableObject {

    /// How big she is on screen, as a multiplier on `AppDelegate.baseSize`.
    @Published var scale: Double = {
        let v = UserDefaults.standard.double(forKey: "loaf.scale")
        return v > 0 ? v : 1.0
    }() {
        didSet { UserDefaults.standard.set(scale, forKey: "loaf.scale") }
    }

    /// Does she wander the dock on her own?
    @Published var wanders: Bool = UserDefaults.standard.object(forKey: "loaf.wanders") as? Bool ?? true {
        didSet { UserDefaults.standard.set(wanders, forKey: "loaf.wanders") }
    }

    /// How heavy she is, which is the app's core signal made visible.
    ///
    /// Driven by task load once there is a task source; until then it is set by hand
    /// from the menu. Writing straight through to `Sprites.weight` keeps one source of
    /// truth - nothing else in the app should ever look at a weight directory.
    @Published var weight: String = UserDefaults.standard.string(forKey: "loaf.weight") ?? "normal" {
        didSet {
            UserDefaults.standard.set(weight, forKey: "loaf.weight")
            Sprites.weight = weight
        }
    }

    /// Heaviest first is deliberate: the menu reads as a load gauge filling up.
    static let weights: [(name: String, id: String)] = [
        ("Chonk — lots to do", "chonk"),
        ("Normal",             "normal"),
        ("Lean — all clear",   "lean"),
    ]

    /// `didSet` doesn't fire during init, so the persisted weight has to be pushed
    /// through by hand or she launches at "normal" whatever was saved.
    init() { Sprites.weight = weight }

    /// Named sizes for the menu. At 1.0 she is 160×128pt, which puts her roughly two
    /// dock icons tall — big enough to read the face, small enough not to be furniture.
    static let sizePresets: [(name: String, value: Double)] = [
        ("Small",  0.7),
        ("Medium", 1.0),
        ("Large",  1.4),
    ]
}
