import AppKit

/// The dock stroll: Loaf ambles along the dock for a while, then finds a corner and
/// sits down. Adapted from lil-cleo's `AppDelegate+Wander.swift`, cut down to what
/// Phase 1 needs — no system reactions, no panic run, no speech.
///
/// The one idea worth preserving from the original: **destination-based movement**.
/// She picks a spot, eases toward it, lingers, then picks another. Constant-speed
/// wall-bouncing was tried there and reads as a screensaver; walking somewhere reads
/// as intent.
extension AppDelegate {

    func startWandering() {
        let timer = Timer(timeInterval: 1.0 / 50.0, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.stepWander() }
        }
        // .common, so she keeps moving while a menu is open — otherwise she freezes
        // mid-stride every time you go to look at her.
        RunLoop.main.add(timer, forMode: .common)
        wanderTimer = timer
    }

    func stopWandering() {
        wanderTimer?.invalidate()
        wanderTimer = nil
    }

    func stepWander() {
        // Pinned from the menu: she's being inspected, so hold still.
        guard engine.autopilot, let screen = NSScreen.main, characterWindow.isVisible else { return }

        // She's draggable. If she moved while we weren't placing her, adopt the new x
        // so she carries on from where she was dropped instead of snapping back.
        let actualX = characterWindow.frame.origin.x
        if abs(actualX - loafX.rounded()) > 1 { loafX = actualX }

        let (minX, maxX) = walkBounds(screen: screen, width: charSize.width)
        let y = dockTopY(screen) - footInset

        switch activity {
        case .strolling:
            strollStep(minX: minX, maxX: maxX, y: y)
            if Date() >= strollEndsAt {
                cornerTargetX = (restCorner > 0) ? minX : maxX     // alternate corners
                activity = .toCorner
            }

        case .toCorner:
            if walkToward(cornerTargetX, y: y, minX: minX, maxX: maxX, cruise: walkSpeed) {
                activity = .resting
                restStartedAt = Date()
                restCorner = (cornerTargetX <= minX + 1) ? -1 : 1
                engine.facing = 1
                engine.setAuto(.sit)
            }

        case .resting:
            // Sit a while, then get up and stroll again. When `sleep` has art this is
            // where she'll drift off instead.
            if Date().timeIntervalSince(restStartedAt) > Double.random(in: 12...20) {
                beginStroll(seconds: Double.random(in: 20...40))
            }
        }
    }

    /// Start a stroll lasting `seconds`, after which she heads for a corner.
    func beginStroll(seconds: Double) {
        activity = .strolling
        strollEndsAt = Date().addingTimeInterval(seconds)
        strollTargetX = nil
        strollSpeed = 0
        dwellUntil = .distantPast
    }

    /// One frame of ambling: walk to a chosen spot, pause there, pick a new one.
    func strollStep(minX: CGFloat, maxX: CGFloat, y: CGFloat) {
        if Date() < dwellUntil { engine.setAuto(.idle); return }
        let target = min(max(strollTargetX ?? pickStrollTarget(minX: minX, maxX: maxX), minX), maxX)
        strollTargetX = target
        if walkToward(target, y: y, minX: minX, maxX: maxX, cruise: walkSpeed * cruiseFactor) {
            strollTargetX = nil
            engine.setAuto(.idle)
            // Usually a short pause; occasionally a longer "noticed something" stand.
            dwellUntil = Date().addingTimeInterval(
                Int.random(in: 0..<6) == 0 ? Double.random(in: 3.5...6.0)
                                           : Double.random(in: 0.7...2.6))
        }
    }

    /// One eased step toward `target`. Accelerates from rest, cruises, brakes into the
    /// stop, and never about-faces at speed — heading the wrong way she brakes to a
    /// halt first, then turns while standing. Returns true on arrival.
    ///
    /// The no-about-face rule is what stops the mirror flip from looking like a glitch:
    /// flipping `facing` mid-stride swaps the sprite instantly, and at walking speed
    /// that reads as a teleport rather than a turn.
    @discardableResult
    func walkToward(_ target: CGFloat, y: CGFloat, minX: CGFloat, maxX: CGFloat, cruise: CGFloat) -> Bool {
        let dist = abs(target - loafX)
        if dist <= max(strollSpeed, 1) {
            strollSpeed = 0
            place(target, y)
            return true
        }
        let dir: CGFloat = (target > loafX) ? 1 : -1
        let accel = cruise / 30                       // ~0.6s from rest to cruise at 50Hz

        if dir != engine.facing, strollSpeed > accel {
            strollSpeed = max(0, strollSpeed - accel * 2)
            engine.setAuto(.walk)
            place(min(max(loafX + engine.facing * strollSpeed, minX), maxX), y)
            return false
        }

        let brakeDist = cruise * 18
        let desired = dist < brakeDist ? max(cruise * dist / brakeDist, cruise * 0.25) : cruise
        strollSpeed = min(desired, strollSpeed + accel)
        engine.facing = dir
        engine.setAuto(.walk)
        place(min(max(loafX + dir * strollSpeed, minX), maxX), y)
        return false
    }

    /// Somewhere new to amble to: usually a modest hop, occasionally a long crossing,
    /// weighted toward open space so she doesn't hug an edge. Each leg gets its own
    /// pace so the walk isn't metronomic.
    func pickStrollTarget(minX: CGFloat, maxX: CGFloat) -> CGFloat {
        cruiseFactor = CGFloat.random(in: 0.85...1.15)
        let span = maxX - minX
        guard span > 8 else { return minX }
        let long = Int.random(in: 0..<5) == 0
        let hop = span * (long ? CGFloat.random(in: 0.45...0.85) : CGFloat.random(in: 0.12...0.40))
        let roomR = maxX - loafX, roomL = loafX - minX
        let dir: CGFloat = CGFloat.random(in: 0..<max(roomL + roomR, 1)) < roomR ? 1 : -1
        return min(max(loafX + dir * hop, minX), maxX)
    }

    /// Move her, tracking the authoritative sub-pixel x in `loafX`.
    func place(_ nx: CGFloat, _ y: CGFloat) {
        loafX = nx
        characterWindow.setFrameOrigin(NSPoint(x: nx.rounded(), y: y))
    }

    // MARK: Dock geometry

    /// The band she paces.
    ///
    /// lil-cleo probes the Dock's real icon strip through the Accessibility API, which
    /// needs the user to grant Accessibility permission. Loaf asks for **no permissions
    /// at all**, so this uses their permission-free fallback: a centred band roughly
    /// over a typical dock. Worth revisiting only if she visibly misses the dock.
    func walkBounds(screen: NSScreen, width: CGFloat) -> (CGFloat, CGFloat) {
        let vf = screen.visibleFrame
        let band = vf.width * 0.28                  // ~56% of the screen, centred
        let lo = vf.midX - band
        let hi = vf.midX + band
        return (lo, max(lo, hi - width))
    }

    /// Screen y of the dock's top edge, where her feet rest. `visibleFrame` already
    /// excludes the dock, so its bottom edge *is* the dock's top edge.
    func dockTopY(_ screen: NSScreen) -> CGFloat { screen.visibleFrame.minY }
}
