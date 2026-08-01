import SwiftUI

/// A big version of the menu-bar paw, reaching down from the bar to give a
/// double pat. Manual only — triggered from the menu's "Paw" item, not tied
/// to any state or system signal yet. That wiring is future work; this is
/// just the gesture.
///
/// Validated first as a motion study (`paw-drop-study.html`, opened in
/// Safari) with three candidate timings. "Double pat" is the one that read
/// as a cat pawing at something rather than just a drop. The keyframes below
/// are a direct port of that file's `dropPat` animation, not a re-design.
@MainActor
final class PawDropEngine: ObservableObject {
    @Published fileprivate(set) var startedAt: Date?

    /// Drop, two pats, a short hold. Matches paw-drop-study.html's dropPat
    /// (1900ms) exactly, so the manual trigger feels like what got approved.
    static let activeDuration: TimeInterval = 1.9
    /// Retract afterwards. Matches the study's separate `retract` keyframe.
    static let retractDuration: TimeInterval = 0.55
    static var totalDuration: TimeInterval { activeDuration + retractDuration }

    private var resetTimer: Timer?

    /// Start the gesture. Ignored while she's already mid-pat rather than
    /// restarting it, so mashing the menu item doesn't snap her back to the
    /// top mid-swing.
    func trigger() {
        guard startedAt == nil else {
            if Self.debug { FileHandle.standardError.write(Data("pawDrop: trigger() ignored, already active\n".utf8)) }
            return
        }
        startedAt = Date()
        if Self.debug { FileHandle.standardError.write(Data("pawDrop: trigger() started at \(startedAt!)\n".utf8)) }
        resetTimer?.invalidate()
        let t = Timer(timeInterval: Self.totalDuration, repeats: false) { [weak self] _ in
            MainActor.assumeIsolated {
                self?.startedAt = nil
                if Self.debug { FileHandle.standardError.write(Data("pawDrop: reset\n".utf8)) }
            }
        }
        RunLoop.main.add(t, forMode: .common)
        resetTimer = t
    }

    private static let debug = ProcessInfo.processInfo.environment["LOAF_DEBUG"] != nil
}

struct PawDropView: View {
    @ObservedObject var engine: PawDropEngine

    /// How far she reaches down from the bar, and how big the paw is at the
    /// end of it. Modest on purpose — this bats at the desktop, it doesn't
    /// cover it.
    static let reach: CGFloat = 190
    static let pawSize: CGFloat = 92
    static let armWidth: CGFloat = 28

    /// The window this view lives in has to be this size always, not sized
    /// to fit. AppDelegate uses the same numbers when it creates that window.
    static var windowSize: CGSize { CGSize(width: pawSize + 60, height: reach + pawSize + 20) }

    var body: some View {
        TimelineView(.animation) { tl in
            if let start = engine.startedAt {
                let t = tl.date.timeIntervalSince(start)
                let down = Self.downness(at: t)
                let rot = Self.patRotation(at: t)
                ZStack(alignment: .top) {
                    UnevenRoundedRectangle(topLeadingRadius: 0, bottomLeadingRadius: 12,
                                           bottomTrailingRadius: 12, topTrailingRadius: 0)
                        .fill(.white)
                        .frame(width: Self.armWidth, height: Self.reach)
                    PawShape()
                        .fill(.white)
                        .frame(width: Self.pawSize, height: Self.pawSize)
                        .offset(y: Self.reach - Self.pawSize * 0.35)
                        .rotationEffect(.degrees(rot), anchor: UnitPoint(x: 0.5, y: 0.12))
                }
                // White on an arbitrary desktop needs the same hard dark
                // outline the mood marks use (MoodMarks.swift) — a soft
                // shadow alone still vanishes on a light wallpaper.
                .shadow(color: .black.opacity(0.9), radius: 0, x: 1, y: 0)
                .shadow(color: .black.opacity(0.9), radius: 0, x: -1, y: 0)
                .shadow(color: .black.opacity(0.9), radius: 0, x: 0, y: 1)
                .shadow(color: .black.opacity(0.9), radius: 0, x: 0, y: -1)
                // The paw hangs pawSize*0.65 BELOW the bottom of the arm (see the
                // offset above), so hiding her needs more than -reach - that only
                // clears the arm and leaves most of the paw still on screen, which
                // is exactly what the first render of this showed.
                .offset(y: -(Self.reach + Self.pawSize * 0.65) * (1 - down))
            }
        }
        // ALWAYS this size, whether or not the `if let` above has content.
        // Without this, the view's natural size while idle (nothing drawn)
        // is zero, and NSHostingView shrinks the window to match - which is
        // exactly what made the whole gesture render squeezed into a sliver
        // at the menu bar instead of a big paw on the desktop. CatView never
        // hits this because it always has a frame at every level regardless
        // of state; this file only had one on the shapes INSIDE the `if let`.
        .frame(width: Self.windowSize.width, height: Self.windowSize.height, alignment: .top)
        .allowsHitTesting(false)
    }

    // Keyframes ported from paw-drop-study.html's @keyframes dropPat — the
    // rotation wobble, expressed as (fraction of activeDuration, degrees).
    private static let patKeyframes: [(t: Double, rot: Double)] = [
        (0.00, 0), (0.32, 0), (0.42, -9), (0.52, 6),
        (0.62, -7), (0.72, 5), (0.82, 0), (1.00, 0),
    ]

    /// 0 = hidden above the bar, 1 = fully reached down. Smoothstep rather
    /// than the study's elastic overshoot — the two pats carry the
    /// character, the drop itself just needs to land cleanly.
    ///
    /// Three phases against real elapsed time: drop (0 → dropEnd), hold at 1
    /// for the pats (dropEnd → activeDuration), then ease back to 0 over
    /// retractDuration. The first version of this only had the first two —
    /// nothing consumed `PawDropEngine.retractDuration` on the way down, so
    /// she held at full reach and then popped straight to invisible the
    /// instant the reset timer fired, instead of withdrawing. Caught by
    /// rendering LOAF_PAW_SNAPSHOT frames past activeDuration, not by eye.
    private static func downness(at elapsed: TimeInterval) -> Double {
        let dropEnd = PawDropEngine.activeDuration * 0.32
        let holdEnd = PawDropEngine.activeDuration
        if elapsed <= 0 { return 0 }
        if elapsed < dropEnd { return smoothstep(elapsed / dropEnd) }
        if elapsed <= holdEnd { return 1 }
        let r = (elapsed - holdEnd) / PawDropEngine.retractDuration
        return smoothstep(1 - r)
    }

    private static func smoothstep(_ x: Double) -> Double {
        let p = min(max(x, 0), 1)
        return p * p * (3 - 2 * p)
    }

    private static func patRotation(at elapsed: TimeInterval) -> Double {
        let t = min(max(elapsed / PawDropEngine.activeDuration, 0), 1)
        guard let hi = patKeyframes.firstIndex(where: { $0.t >= t }), hi > 0 else {
            return patKeyframes.first?.rot ?? 0
        }
        let (t0, r0) = patKeyframes[hi - 1]
        let (t1, r1) = patKeyframes[hi]
        let f = t1 > t0 ? (t - t0) / (t1 - t0) : 0
        return r0 + (r1 - r0) * f
    }
}

/// Pad + four toes, same literal numbers as `MenuBarIcon.paw()`.
///
/// AppKit's `NSBezierPath` there is y-up from the bottom-left; SwiftUI's
/// `Path` is y-down from the top-left, so every rect is flipped through one
/// formula (`newY = box - y - height`) rather than hand-converted — a
/// hand-converted copy of this exact shape was wrong once already, in
/// paw-drop-study.html's menu-bar icon.
private struct PawShape: Shape {
    private static let box: CGFloat = 18
    private static let pad = CGRect(x: 3.1, y: 1.5, width: 11.8, height: 7.6)
    private static let toes: [CGRect] = [
        CGRect(x: 0.9,  y: 8.2,  width: 3.5, height: 4.4),
        CGRect(x: 5.1,  y: 10.1, width: 3.6, height: 4.9),
        CGRect(x: 9.3,  y: 10.1, width: 3.6, height: 4.9),
        CGRect(x: 13.6, y: 8.2,  width: 3.5, height: 4.4),
    ]

    func path(in rect: CGRect) -> Path {
        let s = rect.width / Self.box
        func flip(_ r: CGRect) -> CGRect {
            CGRect(x: r.minX * s, y: (Self.box - r.maxY) * s, width: r.width * s, height: r.height * s)
        }
        var p = Path()
        p.addRoundedRect(in: flip(Self.pad), cornerSize: CGSize(width: 3.4 * s, height: 3.0 * s))
        for toe in Self.toes { p.addEllipse(in: flip(toe)) }
        return p
    }
}
