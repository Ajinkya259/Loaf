import AppKit
import SwiftUI

/// Borderless window that is still allowed to become key, so SwiftUI gestures inside
/// it reach Loaf even though the app is an accessory with no dock icon.
final class CharacterWindow: NSWindow {
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }
}

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, NSMenuDelegate {

    let settings = Settings()
    let engine = CatEngine()

    var characterWindow: CharacterWindow!
    var statusItem: NSStatusItem!

    // MARK: Geometry

    /// Her window at scale 1.0.
    ///
    /// 160×128 is 5:4, which is the sprite canvas aspect (640×512) — the window must
    /// preserve it or she stretches. The absolute size is chosen so she stands about
    /// two dock icons tall: readable face, not furniture.
    static let baseSize = NSSize(width: 160, height: 128)

    var charSize: NSSize {
        NSSize(width: Self.baseSize.width * CGFloat(settings.scale),
               height: Self.baseSize.height * CGFloat(settings.scale))
    }

    /// How far her feet sit above the window's bottom edge.
    ///
    /// Straight from the contract: the ground line is 24px up a 512px canvas. Getting
    /// this wrong doesn't look like a bug, it looks like she's hovering — which is
    /// harder to notice and harder to diagnose.
    var footInset: CGFloat { charSize.height * Sprites.groundFraction }

    // MARK: Wander state (see AppDelegate+Wander.swift)

    var wanderTimer: Timer?
    /// Authoritative sub-pixel x. `NSWindow` origins are pixel-rounded, so a slow step
    /// accumulated there would round away to nothing and she'd never move.
    var loafX: CGFloat = 0
    var activity: Activity = .strolling
    var strollEndsAt = Date()
    var strollTargetX: CGFloat?
    var strollSpeed: CGFloat = 0
    var dwellUntil = Date.distantPast
    var cruiseFactor: CGFloat = 1
    var restCorner: CGFloat = 1
    var cornerTargetX: CGFloat = 0
    var restStartedAt = Date()

    enum Activity { case strolling, toCorner, resting, jumping }

    // MARK: The jump

    /// How far she travels, how high she gets, and how long it takes - at scale 1.
    ///
    /// These are the numbers that decide whether a jump feels natural, which is why
    /// they live here and not in the art: the sprites carry the pose, the app carries
    /// the parabola. 140pt is about 1.2 of her body lengths, which is a confident hop
    /// rather than a pounce - a real cat clears several body lengths, but on a dock
    /// that overshoots the screen and reads as a glitch. Height is 0.4 of the length,
    /// the ratio that keeps an arc looking like a jump instead of a skip or a lob.
    static let jumpLength: CGFloat = 140
    static let jumpHeight: CGFloat = 55
    static let jumpDuration: TimeInterval = 0.55

    var jumpStartedAt = Date.distantPast
    var jumpFromX: CGFloat = 0
    var jumpDX: CGFloat = 0

    /// Points per frame at 50Hz — about 55pt/s at scale 1. lil-cleo's number. Whether
    /// it matches her stride (and so whether she moonwalks) is a thing to judge on
    /// screen, not to derive from an assumed stride length.
    var walkSpeed: CGFloat { 1.1 * CGFloat(settings.scale) }

    // MARK: Lifecycle

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupStatusItem()
        setupCharacterWindow()

        // Test hook, mirroring lil-cleo's CLEO_ACTION: `LOAF_STATE=sit swift run Loaf`
        // holds one state centred with no wandering. This is how each state gets
        // verified with a screenshot instead of nine menu clicks.
        if let raw = ProcessInfo.processInfo.environment["LOAF_STATE"],
           let s = LoafState(rawValue: raw) {
            // A one-shot can't be pinned, so the hook has to PLAY it - on a loop, so
            // there is something to watch for longer than half a second.
            if s.isOneShot {
                startWandering()
                startJump()
                Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { [weak self] _ in
                    MainActor.assumeIsolated { self?.startJump() }
                }
            } else {
                engine.pin(s)
            }
        } else if settings.wanders {
            beginStroll(seconds: Double.random(in: 20...40))
            startWandering()
        }
    }

    // MARK: The menu-bar control

    private func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.button?.title = "🍞"
        let menu = NSMenu()
        menu.delegate = self          // rebuilt on open so checkmarks are never stale
        statusItem.menu = menu
    }

    /// Rebuild the menu every time it opens.
    ///
    /// Cheaper than keeping a dozen `NSMenuItem` references in sync, and it means the
    /// "no art yet" section updates itself the moment Blender renders a new state —
    /// no code change needed to light one up.
    func menuNeedsUpdate(_ menu: NSMenu) {
        menu.removeAllItems()

        let header = NSMenuItem(title: "Loaf — \(engine.state.title)", action: nil, keyEquivalent: "")
        header.isEnabled = false
        menu.addItem(header)
        menu.addItem(.separator())

        let auto = NSMenuItem(title: "Autopilot", action: #selector(pickAutopilot), keyEquivalent: "")
        auto.target = self
        auto.state = engine.autopilot ? .on : .off
        menu.addItem(auto)
        menu.addItem(.separator())

        for s in LoafState.rendered {
            let item = NSMenuItem(title: s.title, action: #selector(pickState(_:)), keyEquivalent: "")
            item.target = self
            item.representedObject = s.rawValue
            item.state = (engine.pinned == s) ? .on : .off
            menu.addItem(item)
        }

        // Show what's coming rather than hiding it. Seeing "Sleep — no art yet" is more
        // useful than wondering why sleep isn't in the list.
        let missing = LoafState.planned
        if !missing.isEmpty {
            menu.addItem(.separator())
            for s in missing {
                let item = NSMenuItem(title: "\(s.title) — no art yet", action: nil, keyEquivalent: "")
                item.isEnabled = false
                menu.addItem(item)
            }
        }

        menu.addItem(.separator())
        let weightMenu = NSMenu()
        for (name, id) in Settings.weights {
            let item = NSMenuItem(title: name, action: #selector(pickWeight(_:)), keyEquivalent: "")
            item.target = self
            item.representedObject = id
            item.state = (settings.weight == id) ? .on : .off
            weightMenu.addItem(item)
        }
        let weightRoot = NSMenuItem(title: "Weight", action: nil, keyEquivalent: "")
        weightRoot.submenu = weightMenu
        menu.addItem(weightRoot)

        let sizeMenu = NSMenu()
        for (name, value) in Settings.sizePresets {
            let item = NSMenuItem(title: name, action: #selector(pickSize(_:)), keyEquivalent: "")
            item.target = self
            item.representedObject = value
            item.state = abs(settings.scale - value) < 0.001 ? .on : .off
            sizeMenu.addItem(item)
        }
        let sizeRoot = NSMenuItem(title: "Size", action: nil, keyEquivalent: "")
        sizeRoot.submenu = sizeMenu
        menu.addItem(sizeRoot)

        menu.addItem(.separator())
        menu.addItem(withTitle: "Quit Loaf", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
    }

    @objc private func pickAutopilot() {
        engine.pin(nil)
        beginStroll(seconds: Double.random(in: 20...40))
        if wanderTimer == nil { startWandering() }
    }

    @objc private func pickState(_ sender: NSMenuItem) {
        guard let raw = sender.representedObject as? String,
              let s = LoafState(rawValue: raw) else { return }
        // A one-shot PLAYS; it is not held. Pinning a jump would freeze her mid-air.
        if s.isOneShot {
            engine.pin(nil)
            if wanderTimer == nil { startWandering() }
            startJump()
            return
        }
        // Face right while pinned. A mirrored sprite is a fine thing to *test*, but a
        // confusing default when you're trying to look at her.
        engine.facing = 1
        engine.pin(s)
    }

    @objc private func pickWeight(_ sender: NSMenuItem) {
        guard let id = sender.representedObject as? String else { return }
        settings.weight = id
    }

    @objc private func pickSize(_ sender: NSMenuItem) {
        guard let v = sender.representedObject as? Double else { return }
        settings.scale = v
        applyScale()
    }

    // MARK: Her window

    private func setupCharacterWindow() {
        let window = CharacterWindow(contentRect: NSRect(origin: .zero, size: charSize),
                                     styleMask: [.borderless],
                                     backing: .buffered,
                                     defer: false)
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = false
        window.level = .floating
        // Follow the user across spaces and stay put in Mission Control, so she reads
        // as part of the desktop rather than a document window that got lost.
        window.collectionBehavior = [.canJoinAllSpaces, .stationary, .fullScreenAuxiliary]
        window.isMovableByWindowBackground = true      // drag her somewhere else

        window.contentView = NSHostingView(
            rootView: CatView(settings: settings, engine: engine)
        )
        characterWindow = window

        positionAtDock()
        window.orderFrontRegardless()
    }

    /// Plant her on the dock line, centred.
    private func positionAtDock() {
        guard let screen = NSScreen.main else { return }
        let x = screen.visibleFrame.midX - charSize.width / 2
        loafX = x
        characterWindow.setFrameOrigin(NSPoint(x: x, y: dockTopY(screen) - footInset))
    }

    /// Resize and re-plant her feet. Both halves matter: `footInset` scales with the
    /// window, so changing size without repositioning leaves her floating or sunk.
    private func applyScale() {
        guard let screen = NSScreen.main else { return }
        characterWindow.setContentSize(charSize)
        let (minX, maxX) = walkBounds(screen: screen, width: charSize.width)
        loafX = min(max(loafX, minX), maxX)
        characterWindow.setFrameOrigin(NSPoint(x: loafX.rounded(), y: dockTopY(screen) - footInset))
    }
}
