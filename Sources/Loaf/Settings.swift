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

    /// Named sizes for the menu. At 1.0 she is 160×128pt, which puts her roughly two
    /// dock icons tall — big enough to read the face, small enough not to be furniture.
    static let sizePresets: [(name: String, value: Double)] = [
        ("Small",  0.7),
        ("Medium", 1.0),
        ("Large",  1.4),
    ]
}
