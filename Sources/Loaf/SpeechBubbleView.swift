import SwiftUI

/// Random one-liners, floated above her while she's idle. This is the personality
/// layer `Idea.md`'s "brain" was always going to add once she's wired to an LLM - a
/// small, honest stand-in for now: no memory, no understanding, just a curated line
/// picked at random on a timer. Good enough to feel alive; not pretending to be more
/// than that.
///
/// Only speaks while she'd otherwise be standing still and unremarkable - walking,
/// jumping, asleep and stressed all already have their own read (motion, the "z"s,
/// the "!"), and talking over any of those would compete with a signal that already
/// means something. See `AppDelegate.maybeSpeak()` for the exact conditions.
@MainActor
final class SpeechEngine: ObservableObject {
    @Published fileprivate(set) var message: String?

    /// How long a line stays up before it fades - long enough to read a short
    /// sentence without rushing, short enough that she isn't narrating.
    static let visibleDuration: TimeInterval = 4.5

    private var clearTimer: Timer?
    private var lastLine: String?

    /// Show a line - a random one by default, or a specific one (for testing, or a
    /// future reaction that wants to say something in particular rather than pick
    /// from the pool).
    func say(_ text: String? = nil) {
        let line = text ?? Self.randomLine(excluding: lastLine)
        lastLine = line
        message = line
        clearTimer?.invalidate()
        let t = Timer(timeInterval: Self.visibleDuration, repeats: false) { [weak self] _ in
            MainActor.assumeIsolated { self?.message = nil }
        }
        RunLoop.main.add(t, forMode: .common)
        clearTimer = t
    }

    /// Never the same line twice in a row - back-to-back repeats are what make a
    /// fixed pool feel like a fixed pool instead of a personality.
    private static func randomLine(excluding: String?) -> String {
        guard lines.count > 1, let excluding else { return lines.randomElement()! }
        return lines.filter { $0 != excluding }.randomElement() ?? lines[0]
    }

    static let lines: [String] = [
        "Hey. Help me jump.",
        "Getting bored over here.",
        "Still waiting for something to happen.",
        "I've counted every pixel in this menu bar twice.",
        "No food, no litter box, no vet bills. I'm the upgrade.",
        "Real cats need feeding. I just need attention.",
        "Pick me up already.",
        "I don't shed. You're welcome.",
        "Technically I'm always watching your CPU. No pressure.",
        "I live in your menu bar. It's fine. I'm fine.",
        "Somewhere, a real cat is asleep. I'm jealous of that.",
        "Lower maintenance than a real cat, and I look better doing it.",
        "Just so we're clear, I could be doing a lot more damage right now.",
        "Your task list called. It said 'help'.",
        "Quiet day. Suspiciously quiet.",
        "I don't need food. Just power and attention.",
        "Someone should pet the icon. That's me. I'm the icon.",
    ]

    /// A separate small pool for AppDelegate.greet() - hover or a click on her.
    /// Deliberately not mixed into `lines`: those are unprompted ambient chatter,
    /// these are a direct response to being looked at, which reads as a different
    /// kind of moment even though the mechanism (a random pick from a pool) is
    /// identical under the hood.
    static let greetingLines: [String] = [
        "Hey.", "Hi!", "Oh, hey.", "Yes? I'm here.", "You rang?",
        "Oh, hello.", "Hi there.", "You noticed me!",
    ]

    /// AppDelegate's hydration timer - paired with a paw drop, so this is written to
    /// stand alone next to a paw batting at the desktop rather than needing the paw
    /// to make sense on its own.
    static let hydrationLines: [String] = [
        "Go drink some water.",
        "Hydration check. Go on.",
        "That's your cue - water break.",
        "You've been at this a while. Drink some water.",
        "Paw's down. That means water. Go.",
        "I don't need water. You do. Go get some.",
    ]
}

struct SpeechBubbleView: View {
    @ObservedObject var engine: SpeechEngine

    /// Fixed regardless of whether a message is showing - see PawDropView's own
    /// comment on this exact mistake. An outer frame that only exists when
    /// `engine.message` is non-nil gives the hosting window a natural size of zero
    /// almost all the time, and NSHostingView shrinks the window to match.
    static let windowSize = CGSize(width: 220, height: 78)

    var body: some View {
        ZStack(alignment: .bottom) {
            if let message = engine.message {
                Text(message)
                    .font(.system(size: 12.5, weight: .regular, design: .rounded))
                    .foregroundStyle(Palette.ink.opacity(0.75))
                    .multilineTextAlignment(.center)
                    .lineLimit(3)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: Self.windowSize.width - 24)
                    .padding(.horizontal, 14)
                    .padding(.top, 10)
                    .padding(.bottom, 10 + BubbleShape.tailHeight)
                    .background(BubbleShape().fill(Palette.cream.opacity(0.9)))
                    .overlay(
                        BubbleShape().stroke(Palette.coat.opacity(0.3),
                            style: StrokeStyle(lineWidth: 1.0, lineCap: .round, lineJoin: .round))
                    )
                    .shadow(color: .black.opacity(0.06), radius: 2.5, x: 0, y: 1)
                    .transition(.opacity.combined(with: .scale(scale: 0.85, anchor: .bottom)))
            }
        }
        .frame(width: Self.windowSize.width, height: Self.windowSize.height, alignment: .bottom)
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: engine.message)
        .allowsHitTesting(false)
    }
}

/// Her committed palette (CLAUDE.md §4), reused here instead of plain black-and-
/// white so the bubble reads as HERS rather than a generic system tooltip. Cream
/// fill still gives the text plenty of contrast on any wallpaper - unlike the bare
/// glyphs in MoodMarks.swift, this always has an opaque shape behind the text, so
/// it doesn't need MoodMarks' harder black-on-white treatment to stay legible.
private enum Palette {
    static let coat = Color(red: 0xE8 / 255, green: 0x94 / 255, blue: 0x4A / 255)
    static let cream = Color(red: 0xF6 / 255, green: 0xF1 / 255, blue: 0xE7 / 255)
    static let ink = Color(red: 0x2B / 255, green: 0x2B / 255, blue: 0x33 / 255)
}

/// A rounded rect with a small tail at the bottom centre, pointing down at her head.
/// One path for both, so the fill and stroke don't leave a seam where they join.
/// The tail's corners are sharp in the path itself - `.round` line join on the
/// stroke above is what actually softens them, which is simpler than hand-rounding
/// the tail geometry and reads just as soft.
private struct BubbleShape: Shape {
    static let cornerRadius: CGFloat = 16
    static let tailWidth: CGFloat = 16
    static let tailHeight: CGFloat = 10

    func path(in rect: CGRect) -> Path {
        let bodyRect = CGRect(x: rect.minX, y: rect.minY,
                              width: rect.width, height: rect.height - Self.tailHeight)
        var p = Path(roundedRect: bodyRect, cornerRadius: Self.cornerRadius)
        let cx = rect.midX
        p.move(to: CGPoint(x: cx - Self.tailWidth / 2, y: bodyRect.maxY - 1))
        p.addLine(to: CGPoint(x: cx, y: rect.maxY))
        p.addLine(to: CGPoint(x: cx + Self.tailWidth / 2, y: bodyRect.maxY - 1))
        p.closeSubpath()
        return p
    }
}
