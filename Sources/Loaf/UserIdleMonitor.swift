import Foundation
import CoreGraphics

/// Watches for the keyboard and mouse going quiet. The other half of the "she reacts
/// to the machine" idea `SystemMonitor` covers - that one watches what the machine is
/// doing, this one watches whether YOU are still there.
///
/// Same shape as `SystemMonitor` on purpose: edge-triggered, reporting a crossing
/// rather than polling a level into the view, so she settles down once when you leave
/// and wakes once when you're back rather than flickering at every sample.
///
/// `CGEventSource.secondsSinceLastEventType` needs no permission at all - it's a
/// system-wide idle counter, not a tap on the events themselves, which is the
/// Accessibility-gated thing. Consistent with the rest of the app asking for nothing.
@MainActor
final class UserIdleMonitor {

    /// Called only when the verdict actually changes.
    var onChange: ((Bool) -> Void)?
    private(set) var idle = false

    private var timer: Timer?

    /// How long the keyboard and mouse have to be untouched before she's "away from
    /// the keyboard" rather than just reading something on screen for a bit. Long
    /// enough that scrolling a page or watching a video doesn't put her to sleep
    /// under you.
    /// LOAF_IDLE_THRESHOLD overrides this in seconds, for testing without
    /// actually waiting three minutes with your hands off the keyboard.
    static var idleThreshold: TimeInterval =
        Double(ProcessInfo.processInfo.environment["LOAF_IDLE_THRESHOLD"] ?? "") ?? 180

    private static let debug = ProcessInfo.processInfo.environment["LOAF_DEBUG"] != nil

    func start() {
        stop()
        let t = Timer(timeInterval: 5.0, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.poll() }
        }
        RunLoop.main.add(t, forMode: .common)
        timer = t
    }

    func stop() {
        timer?.invalidate(); timer = nil
        if idle { idle = false; onChange?(false) }
    }

    private func poll() {
        // kCGAnyInputEventType, i.e. "since the last input of any kind" - not one
        // specific device, so a mouse jiggle counts the same as a keystroke.
        let seconds = CGEventSource.secondsSinceLastEventType(.combinedSessionState,
                                                               eventType: CGEventType(rawValue: ~0)!)
        let now = seconds >= Self.idleThreshold
        if Self.debug {
            FileHandle.standardError.write(Data(
                "idle: \(Int(seconds))s since input, threshold \(Int(Self.idleThreshold))s, idle \(now)\n".utf8))
        }
        guard now != idle else { return }
        idle = now
        onChange?(now)
    }
}
