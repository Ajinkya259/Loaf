import SwiftUI

/// What Loaf is doing right now, and who decided it.
///
/// Two sources want to set her state and they must not fight: the wander loop (which
/// wants her to stroll and nap) and you (who wants to hold her in one pose and look at
/// her). `pinned` settles it — when you pick a state from the menu it wins outright
/// and the wander loop's updates are dropped on the floor until you hand control back.
///
/// This is lil-cleo's `autopilot` idea, narrowed to the one thing Phase 1 needs.
@MainActor
final class CatEngine: ObservableObject {

    /// The state currently being drawn.
    @Published private(set) var state: LoafState = .idle

    /// Travel direction: +1 faces screen-right (how every sprite is rendered), -1 is
    /// mirrored. Only ever set by the wander loop.
    @Published var facing: CGFloat = 1

    /// A state you chose by hand, or nil when she's running herself.
    @Published private(set) var pinned: LoafState?

    /// How far through a jump she is, 0…1, or nil when she isn't jumping.
    ///
    /// The frame AND the trajectory both read this one value, which is the point: a
    /// jump driven by a wall clock and an arc driven by a separate timer drift apart,
    /// and then she lands two frames after her feet touch down.
    @Published var jumpProgress: Double?

    /// The machine is struggling. Set by `SystemMonitor`, read by the wander loop.
    ///
    /// Held separately from `state` because it OUTRANKS the wander loop rather than
    /// being one of its options: while this is true she stays put and stressed, and
    /// the loop's strolling and napping are simply not consulted.
    @Published var overloaded = false

    /// True when the wander loop is allowed to drive.
    var autopilot: Bool { pinned == nil }

    /// Hold her in one state for inspection. Passing nil returns her to autopilot.
    func pin(_ s: LoafState?) {
        pinned = s
        if let s { state = s }
    }

    /// The wander loop's way in. Ignored while pinned, which is the whole point —
    /// callers don't have to know whether they're allowed to move her.
    func setAuto(_ s: LoafState) {
        guard autopilot, s != state else { return }
        state = s
    }
}
