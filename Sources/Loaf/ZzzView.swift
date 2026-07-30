import SwiftUI

/// The little "z"s drifting up off a sleeping cat.
///
/// This lives in the app rather than in the sprites, and that is the whole design.
/// Baked into Blender it would be stuck on the four breath frames at 1.5fps - four
/// discrete positions, ticking upward. Here it is continuous, can outlive the sprite
/// cycle it sits on, and costs no art at all.
///
/// It also does real work. A cat lying on the floor is a solid mass with no negative
/// space inside its outline, which is why the sleeping pose took seven passes to read
/// at 160x128 (see SPRITE_CONTRACT.md). Zzz is the one sleep signal that does not
/// depend on silhouette in any way, so it carries the state on its own.
struct ZzzView: View {
    let scale: CGFloat
    let facing: CGFloat
    let t: TimeInterval

    /// Seconds for one "z" to travel from her head to the top of its climb.
    private static let riseSeconds = 3.2
    private static let count = 3

    var body: some View {
        ZStack {
            ForEach(0..<Self.count, id: \.self) { i in
                // Staggered by an even fraction of the cycle, so one leaves as the
                // one before it is fading out rather than all three pulsing together.
                let p = ((t / Self.riseSeconds) + Double(i) / Double(Self.count))
                    .truncatingRemainder(dividingBy: 1)
                glyph(p)
            }
        }
        // Fills the character window so the offsets below are measured from its
        // CENTRE. Without this the ZStack shrinks to fit the glyphs and the parent's
        // .bottom alignment pins it to her feet, putting the "z"s under her chin.
        .frame(width: 160 * scale, height: 128 * scale)
        .allowsHitTesting(false)
    }

    @ViewBuilder private func glyph(_ p: Double) -> some View {
        // Grows as it rises, which reads as drifting toward you rather than simply
        // sliding up the screen.
        let size = 11 * scale * (0.62 + 0.75 * p)
        // In fast, out slow. A symmetric fade makes them pop in at full strength at
        // her head, which looks like they are being emitted rather than exhaled.
        let alpha = min(1, p / 0.18) * (1 - p) * (1 - p)
        Text("z")
            .font(.system(size: size, weight: .heavy, design: .rounded))
            .foregroundStyle(.white)
            // A dark halo, because a desktop can be any colour and plain white "z"s
            // disappear on a light wallpaper.
            .shadow(color: .black.opacity(0.55), radius: 1.2 * scale, x: 0, y: 0)
            .opacity(alpha)
            .offset(
                // Anchored just off her head, mirrored with her so they stay by her
                // face when she is sleeping the other way round. The glyph itself is
                // never mirrored - that would render a backwards "z".
                x: facing * (0.27 + 0.06 * p) * 160 * scale,
                y: (-0.10 - 0.34 * p) * 128 * scale
            )
    }
}
