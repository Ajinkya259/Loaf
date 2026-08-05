import Foundation

/// Watches the machine and tells the app when it's struggling.
///
/// Cut to the two signals that actually mean
/// "this computer is having a hard time": sustained CPU, and kernel memory pressure.
/// Everything here is a system framework — no third-party dependency, no permission.
///
/// **Edge-triggered, not polled into the UI.** It reports a *crossing*, not a level, so
/// she reacts once when things go bad and once when they recover. Feeding a level
/// straight to the view would have her flicker in and out of alarm on every sample.
@MainActor
final class SystemMonitor {

    /// Called only when the verdict actually changes.
    var onChange: ((Bool) -> Void)?
    private(set) var overloaded = false

    private var timer: Timer?
    private var memSource: DispatchSourceMemoryPressure?

    // MARK: CPU

    private var prevCPU: host_cpu_load_info?
    private var hotStreak = 0
    private var cpuHot = false

    /// Three consecutive samples over the line, i.e. ~12s of sustained load.
    ///
    /// A streak, not a single reading, because a momentary spike is what a Spotlight
    /// index or a browser tab opening looks like, and reacting to those would make her
    /// alarm meaningless. What the signal is for is the machine being *stuck*.
    private static let cpuBusy = 78.0
    private static let streakToTrip = 3

    // MARK: Memory

    /// Memory pressure DECAYS rather than latching, and this is not a style choice.
    /// The kernel reports warning/critical events but there is no reliable way to poll
    /// for recovery — `vm_pressure_level` stays at "warning" for minutes while the
    /// compressor drains — so a level poll would pin her in alarm long after the load
    /// had gone. Instead each event refreshes a hold, and pressure lapses on its own.
    private static let memHold: TimeInterval = 30
    private var memUntil = Date.distantPast
    private var memPressured: Bool { Date() < memUntil }

    // MARK: Lifecycle

    func start() {
        stop()
        let src = DispatchSource.makeMemoryPressureSource(
            eventMask: [.warning, .critical], queue: .main)
        src.setEventHandler { [weak self] in
            Task { @MainActor in
                self?.memUntil = Date().addingTimeInterval(Self.memHold)
                self?.evaluate()
            }
        }
        src.resume()
        memSource = src

        let t = Timer(timeInterval: 4.0, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.poll() }
        }
        RunLoop.main.add(t, forMode: .common)
        timer = t
    }

    func stop() {
        timer?.invalidate(); timer = nil
        memSource?.cancel(); memSource = nil
        hotStreak = 0; cpuHot = false; prevCPU = nil
        memUntil = .distantPast
        if overloaded { overloaded = false; onChange?(false) }
    }

    /// `LOAF_DEBUG=1` logs every sample. The monitor is the one part of the app with
    /// no visible output until it fires, so without this a threshold that never trips
    /// is indistinguishable from a machine that is simply never busy.
    private static let debug = ProcessInfo.processInfo.environment["LOAF_DEBUG"] != nil

    private func poll() {
        if let pct = cpuUsage() {
            if Self.debug {
                FileHandle.standardError.write(Data(
                    "cpu \(Int(pct))%  streak \(hotStreak)  hot \(cpuHot)  mem \(memPressured)  overloaded \(overloaded)\n".utf8))
            }
            hotStreak = pct >= Self.cpuBusy ? hotStreak + 1 : 0
            if hotStreak >= Self.streakToTrip { cpuHot = true }
            if hotStreak == 0 { cpuHot = false }
        }
        evaluate()
    }

    private func evaluate() {
        let now = cpuHot || memPressured
        guard now != overloaded else { return }
        overloaded = now
        onChange?(now)
    }

    /// CPU busy percentage since the previous sample.
    ///
    /// Mach reports cumulative ticks, so a single reading is the average since boot and
    /// says nothing about now — the value only exists as a difference between two
    /// samples, which is why the first call always returns nil.
    private func cpuUsage() -> Double? {
        var info = host_cpu_load_info()
        var count = mach_msg_type_number_t(
            MemoryLayout<host_cpu_load_info>.size / MemoryLayout<integer_t>.size)
        let kr = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                host_statistics(mach_host_self(), HOST_CPU_LOAD_INFO, $0, &count)
            }
        }
        guard kr == KERN_SUCCESS else { return nil }
        defer { prevCPU = info }
        guard let prev = prevCPU else { return nil }

        let user = Double(info.cpu_ticks.0 &- prev.cpu_ticks.0)
        let sys  = Double(info.cpu_ticks.1 &- prev.cpu_ticks.1)
        let idle = Double(info.cpu_ticks.2 &- prev.cpu_ticks.2)
        let nice = Double(info.cpu_ticks.3 &- prev.cpu_ticks.3)
        let total = user + sys + idle + nice
        guard total > 0 else { return nil }
        return (user + sys + nice) / total * 100
    }
}
