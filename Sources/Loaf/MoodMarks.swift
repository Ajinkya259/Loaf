import SwiftUI

/// Small symbols drawn ABOVE her to say what a silhouette can't.
///
/// The lesson these come from is worth stating once: the sleeping pose took seven
/// passes to read and none of them worked, because a cat lying on the floor is a solid
/// mass with no negative space inside its outline - and at 160x128 the outline is the
/// entire read. A drifting "z" fixed it instantly, because it does not depend on
/// silhouette at all. Stress has the same problem for the same reason, so it gets the
/// same answer.
///
/// Both marks share a treatment on purpose - white fill, hard black outline - so they
/// read as one visual language rather than two unrelated effects, and so both survive
/// a desktop of any colour. A single soft halo is not enough: white vanishes on a light
/// wallpaper and a dark glyph vanishes on a dark one.

/// A bold "!" flashing over a frightened cat.
struct AlarmView: View {
    let scale: CGFloat
    let facing: CGFloat
    let t: TimeInterval

    /// Fast. The sleeping "z"s take 3.2s each because slow reads as calm; alarm has to
    /// be the opposite, and a mark that pulses quickly reads as urgent before you have
    /// consciously registered what the symbol is.
    private static let beat = 0.62

    var body: some View {
        let p = (t / Self.beat).truncatingRemainder(dividingBy: 1)
        // Snaps in, holds, drops away - not a smooth sine, which would read as
        // breathing. The hard attack is the point.
        let pop = p < 0.16 ? p / 0.16 : 1.0
        let alpha = p < 0.72 ? 1.0 : max(0, (1 - p) / 0.28)
        Text("!")
            .font(.system(size: 22 * scale * (0.55 + 0.45 * pop), weight: .black,
                          design: .rounded))
            .foregroundStyle(.white)
            .shadow(color: .black.opacity(0.9), radius: 0, x:  1.2 * scale, y: 0)
            .shadow(color: .black.opacity(0.9), radius: 0, x: -1.2 * scale, y: 0)
            .shadow(color: .black.opacity(0.9), radius: 0, x: 0, y:  1.2 * scale)
            .shadow(color: .black.opacity(0.9), radius: 0, x: 0, y: -1.2 * scale)
            .opacity(alpha)
            // Over her HEAD, which in this pose is low and forward - not over the
            // arch, which is the tallest part of her but not the part you look at.
            .offset(x: facing * 0.24 * 160 * scale, y: -0.30 * 128 * scale)
            .frame(width: 160 * scale, height: 128 * scale)
            .allowsHitTesting(false)
    }
}

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
        let size = 13 * scale * (0.70 + 0.70 * p)
        // Fade in fast, hold, fade out at the top. The first version squared the
        // falloff, which left them under 0.3 opacity for most of the climb - visible
        // in a snapshot, invisible on a desktop.
        let alpha = min(1, p / 0.12) * min(1, (1 - p) / 0.30)
        Text("z")
            .font(.system(size: size, weight: .black, design: .rounded))
            .foregroundStyle(.white)
            // WHITE FILL, HARD BLACK OUTLINE. A desktop can be any colour, and a
            // single soft halo is not enough: white "z"s vanish on a light wallpaper
            // and a dark glyph vanishes on a dark one. Four zero-radius shadows make a
            // real outline, so the pair reads on anything.
            .shadow(color: .black.opacity(0.9), radius: 0, x:  1.1 * scale, y: 0)
            .shadow(color: .black.opacity(0.9), radius: 0, x: -1.1 * scale, y: 0)
            .shadow(color: .black.opacity(0.9), radius: 0, x: 0, y:  1.1 * scale)
            .shadow(color: .black.opacity(0.9), radius: 0, x: 0, y: -1.1 * scale)
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
