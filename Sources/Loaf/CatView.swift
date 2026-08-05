import SwiftUI

/// Draws Loaf.
///
/// Deliberately thin: pick a frame, mirror it if she's walking left, add a small
/// procedural bob. Everything about *which* state to draw lives in `CatEngine`, and
/// everything about how she looks lives in Blender. If this file starts growing
/// opinions about her behaviour, they're in the wrong place.
struct CatView: View {
    @ObservedObject var settings: Settings
    @ObservedObject var engine: CatEngine

    /// Drag handling is the app's, not AppKit's.
    ///
    /// `isMovableByWindowBackground` was doing this before and could not work: AppKit
    /// moved the window while the wander loop wrote the same origin 50 times a second,
    /// pinning the y you were trying to change. Owning the gesture means the loop can
    /// be suspended for exactly as long as the drag lasts.
    var onDrag: ((CGSize) -> Void)?
    var onDrop: (() -> Void)?

    /// Hover or a plain click/tap - not a drag. See AppDelegate.greet().
    var onGreet: (() -> Void)?

    /// 8 frames at 6.5fps is a 1.23s walk cycle, tuned against a real mocap walk
    /// rather than guessed at.
    /// Per-state rates live on `LoafState.fps`; this one drives the procedural bob.
    private static let walkFPS = 6.5

    var body: some View {
        let s = CGFloat(settings.scale)
        TimelineView(.animation) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            let state = engine.state

            ZStack(alignment: .bottom) {
                sprite(for: state, t: t)
                    .frame(width: AppDelegate.baseSize.width * s,
                           height: AppDelegate.baseSize.height * s,
                           alignment: .bottom)
                    // anchor .bottom is (0.5, 1.0): mirrored about the HORIZONTAL
                    // centre, pivoting on her feet. This is exactly why the profile
                    // sprites had to be recentred in Blender — see SPRITE_CONTRACT.md.
                    // Mirroring an off-centre silhouette teleports her.
                    .scaleEffect(x: engine.facing, anchor: .bottom)

                // OUTSIDE the mirrored layer on purpose: flipping this too would draw
                // a backwards "z". It takes `facing` as a plain number instead.
                if state == .sleep {
                    ZzzView(scale: s, facing: engine.facing, t: t)
                } else if state == .stressed {
                    AlarmView(scale: s, facing: engine.facing, t: t)
                }
            }
            .frame(width: AppDelegate.baseSize.width * s,
                   height: AppDelegate.baseSize.height * s,
                   alignment: .bottom)
            .offset(y: bob(state, t: t) * s)
            .animation(.easeInOut(duration: 0.22), value: state)
        }
        .frame(width: AppDelegate.baseSize.width * s,
               height: AppDelegate.baseSize.height * s,
               alignment: .bottom)
        .contentShape(Rectangle())
        .gesture(
            DragGesture(minimumDistance: 2, coordinateSpace: .global)
                .onChanged { onDrag?($0.translation) }
                .onEnded { _ in onDrop?() }
        )
        // `simultaneousGesture`, not `.onTapGesture` bare: a plain tap gesture placed
        // alongside `.gesture()` can get swallowed by the drag recognizer's
        // exclusivity. This runs alongside it instead of competing with it - a real
        // click never satisfies the drag's 2pt minimum distance anyway, so there's no
        // double-firing to worry about.
        .simultaneousGesture(TapGesture().onEnded { onGreet?() })
        .onHover { hovering in if hovering { onGreet?() } }
    }

    /// Which frame to draw. Kept out of the `@ViewBuilder` below, which can't hold
    /// ordinary control flow.
    ///
    /// A jump is scrubbed by PROGRESS, not by the clock. Everything else loops on
    /// time, but a jump has to land on its last frame exactly when the arc lands, and
    /// two independent timers would drift apart within a few hops.
    private func frameName(_ state: LoafState, t: TimeInterval) -> String {
        if state == .jump, let p = engine.jumpProgress {
            let n = max(Sprites.frameCount("jump"), 1)
            return "jump\(min(n - 1, max(0, Int(p * Double(n)))) + 1)"
        }
        return Sprites.frameName(state.sprite, t: t, fps: state.fps)
    }

    /// The sprite for this state, with the contract's fallback chain.
    ///
    /// `<state>` → `side_idle`. Deliberately only two hops: a third would be a dead
    /// branch. This is also why `side_idle.png` must always exist — it is what every
    /// unrendered state resolves to.
    @ViewBuilder private func sprite(for state: LoafState, t: TimeInterval) -> some View {
        let name = frameName(state, t: t)
        if let img = Sprites.image(name) ?? Sprites.image("side_idle") {
            Image(nsImage: img)
                .resizable()
                // .high, not .none: these are 640×512 renders shown at ~160×128, so
                // this is a 4x downscale. Nearest-neighbour would alias the voxel
                // edges into shimmering noise as she walks.
                .interpolation(.high)
                .scaledToFit()
        } else {
            Color.clear
        }
    }

    /// A vertical bob layered on top of the sprite.
    ///
    /// The rendered walk is a symmetric pendulum with no weight shift in it (see
    /// CLAUDE.md §7). Rather than re-cut the Blender curves on a hunch, this adds the
    /// missing body bob in code, where it's free to tune. Four bobs per 1.23s cycle,
    /// which matches a quadruped's four footfalls. Whether that rescues the walk is a
    /// question to answer by watching her, not by reasoning about it.
    private func bob(_ state: LoafState, t: TimeInterval) -> CGFloat {
        guard state.isLocomotion else { return 0 }
        return -abs(sin(t * .pi * Self.walkFPS / 2)) * 2.5
    }
}
