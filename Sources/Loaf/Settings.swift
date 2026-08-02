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

    /// Where she sits in the window stack.
    ///
    /// Two genuinely different ideas of what a desktop pet is, so it is a real choice
    /// rather than a preference:
    ///
    /// - `float` — above every window. She is a companion you always see.
    /// - `desktop` — down among the desktop icons, BEHIND every app window. She is
    ///   part of the desktop, and covering it covers her. Quieter, and the right pick
    ///   if she is ever distracting while you work.
    @Published var layer: String = UserDefaults.standard.string(forKey: "loaf.layer") ?? "float" {
        didSet { UserDefaults.standard.set(layer, forKey: "loaf.layer") }
    }

    /// Follow the user across Spaces, or stay on the one she started in.
    ///
    /// Separate from `layer` on purpose - they answer different questions ("what
    /// covers her" vs "does she follow me"), and folding them into one list of modes
    /// would hide half the combinations.
    @Published var allSpaces: Bool =
        UserDefaults.standard.object(forKey: "loaf.allSpaces") as? Bool ?? true {
        didSet { UserDefaults.standard.set(allSpaces, forKey: "loaf.allSpaces") }
    }

    static let layers: [(name: String, id: String)] = [
        ("Above all windows",   "float"),
        ("On the desktop only", "desktop"),
    ]

    /// Does she react to CPU and memory pressure?
    @Published var reactToSystem: Bool =
        UserDefaults.standard.object(forKey: "loaf.reactToSystem") as? Bool ?? true {
        didSet { UserDefaults.standard.set(reactToSystem, forKey: "loaf.reactToSystem") }
    }

    /// Random speech-bubble one-liners (`SpeechBubbleView.swift`). A real toggle and
    /// not folded into `reactToSystem` - that one is about her body reacting to the
    /// machine, this is her talking, and someone might want one without the other.
    @Published var letHerTalk: Bool =
        UserDefaults.standard.object(forKey: "loaf.letHerTalk") as? Bool ?? true {
        didSet { UserDefaults.standard.set(letHerTalk, forKey: "loaf.letHerTalk") }
    }

    /// Water-break nudges (paw drop + a speech bubble, every 1-2h). Its own toggle,
    /// separate from `letHerTalk` - personality quips and a recurring health nudge are
    /// different enough in kind that someone may want one without the other, and a
    /// nag you can't turn off individually is exactly the kind of thing that gets an
    /// app force-quit.
    @Published var hydrationReminders: Bool =
        UserDefaults.standard.object(forKey: "loaf.hydrationReminders") as? Bool ?? true {
        didSet { UserDefaults.standard.set(hydrationReminders, forKey: "loaf.hydrationReminders") }
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
    ]
}
