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
    lazy var systemMonitor = SystemMonitor()
    lazy var userIdleMonitor = UserIdleMonitor()
    let pawDropEngine = PawDropEngine()
    let speechEngine = SpeechEngine()

    var characterWindow: CharacterWindow!
    var statusItem: NSStatusItem!
    var pawDropWindow: NSWindow!
    var speechWindow: NSWindow!
    var speechTimer: Timer?

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

    enum Activity { case strolling, toCorner, resting, jumping, falling }

    // MARK: Being picked up

    var dragOrigin: NSPoint?
    var dragMouseStart: NSPoint?
    var fallSpeed: CGFloat = 0

    /// One frame of a drag.
    ///
    /// PICKING HER UP WAKES HER. A cat that stays asleep while you carry it across the
    /// screen is wrong, and the same goes for staying alarmed - being handled is a new
    /// thing happening to her, so she turns front-on and looks at you.
    func dragTo(_ translation: CGSize) {
        guard let window = characterWindow else { return }

        // THE GESTURE'S TRANSLATION IS UNUSABLE HERE, and this is the actual cause of
        // the flicker rather than the wander loop.
        //
        // SwiftUI's `.global` coordinate space on macOS is the WINDOW, not the screen.
        // So moving the window in response to a translation changes what the next
        // translation reports - the pointer has not moved relative to the window, so
        // the translation collapses, so she snaps back, so it grows again. A feedback
        // loop at gesture rate, which looks exactly like flicker.
        //
        // `NSEvent.mouseLocation` is in SCREEN coordinates and cannot feed back. The
        // translation is now used only as a signal that a drag is in progress.
        let mouse = NSEvent.mouseLocation
        if dragOrigin == nil {
            dragOrigin = window.frame.origin
            dragMouseStart = mouse
            engine.held = true
            engine.jumpProgress = nil
            if engine.autopilot { engine.setAuto(.look) }
        }
        guard let o = dragOrigin, let m0 = dragMouseStart else { return }
        let p = NSPoint(x: o.x + (mouse.x - m0.x), y: o.y + (mouse.y - m0.y))
        window.setFrameOrigin(p)
        loafX = p.x
    }

    /// Let go. She falls back to the dock line rather than teleporting to it.
    func dropped() {
        dragOrigin = nil
        dragMouseStart = nil
        engine.held = false
        fallSpeed = 0
        activity = .falling
        if wanderTimer == nil { startWandering() }
    }

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
        setupPawDropWindow()
        setupSpeechWindow()
        scheduleNextPing()

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

        // Machine load drives her posture. Task load drives her body (the weight
        // directories) - deliberately separate axes, so she can be fat AND frightened,
        // which is exactly the "too much to do and the laptop is dying" case.
        systemMonitor.onChange = { [weak self] hot in
            guard let self else { return }
            engine.overloaded = hot
            if !hot { beginStroll(seconds: Double.random(in: 10...20)) }
        }
        if settings.reactToSystem { systemMonitor.start() }

        // Unconditional, unlike systemMonitor - there's no version of this app where
        // staying awake forever while you're away is the right call, so it isn't
        // behind the "React to system load" toggle. That toggle is specifically about
        // CPU/memory, not about whether she notices you've left.
        userIdleMonitor.onChange = { [weak self] idle in
            guard let self else { return }
            engine.userIdle = idle
            if !idle { beginStroll(seconds: Double.random(in: 15...30)) }
        }
        userIdleMonitor.start()

        // The "morning greeting" from CLAUDE.md's state model, minus the text she
        // doesn't have anything to say yet - the gesture alone reads as a greeting
        // without needing the brain layer. Reuses the same gesture "Paw" plays.
        NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didWakeNotification, object: nil, queue: .main
        ) { [weak self] _ in
            MainActor.assumeIsolated {
                guard let self else { return }
                self.repositionPawDropWindow()
                self.pawDropEngine.trigger()
            }
        }
    }

    // MARK: The menu-bar control

    private func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        // A drawn template paw rather than an emoji. An emoji ignores the menu bar's
        // light/dark and highlight states, and always renders at whatever size and
        // colour the font decides.
        statusItem.button?.image = MenuBarIcon.paw()
        statusItem.button?.image?.accessibilityDescription = "Loaf"
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

        // Not a LoafState: this doesn't touch her body or pose at all, it's a
        // separate overlay (PawDropView.swift) layered above whatever she's
        // already doing. One-shot, like Jump, but its own thing rather than
        // folded into the state list.
        let paw = NSMenuItem(title: "Paw", action: #selector(pickPawDrop), keyEquivalent: "")
        paw.target = self
        menu.addItem(paw)

        let say = NSMenuItem(title: "Say something", action: #selector(pickSaySomething), keyEquivalent: "")
        say.target = self
        menu.addItem(say)

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

        let showMenu = NSMenu()
        for (name, id) in Settings.layers {
            let item = NSMenuItem(title: name, action: #selector(pickLayer(_:)), keyEquivalent: "")
            item.target = self
            item.representedObject = id
            item.state = (settings.layer == id) ? .on : .off
            showMenu.addItem(item)
        }
        showMenu.addItem(.separator())
        let spaces = NSMenuItem(title: "On all Spaces",
                                action: #selector(toggleAllSpaces(_:)), keyEquivalent: "")
        spaces.target = self
        spaces.state = settings.allSpaces ? .on : .off
        showMenu.addItem(spaces)
        let showRoot = NSMenuItem(title: "Show", action: nil, keyEquivalent: "")
        showRoot.submenu = showMenu
        menu.addItem(showRoot)

        let react = NSMenuItem(title: "React to system load",
                               action: #selector(toggleReact(_:)), keyEquivalent: "")
        react.target = self
        react.state = settings.reactToSystem ? .on : .off
        menu.addItem(react)

        let talk = NSMenuItem(title: "Let her talk",
                              action: #selector(toggleTalk(_:)), keyEquivalent: "")
        talk.target = self
        talk.state = settings.letHerTalk ? .on : .off
        menu.addItem(talk)

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

    @objc private func pickPawDrop() {
        if ProcessInfo.processInfo.environment["LOAF_DEBUG"] != nil {
            FileHandle.standardError.write(Data("menu: paw clicked, startedAt was \(String(describing: pawDropEngine.startedAt))\n".utf8))
        }
        repositionPawDropWindow()
        pawDropEngine.trigger()
    }

    /// Manual trigger, mirroring `pickPawDrop` - bypasses `maybeSpeak`'s
    /// idle/overloaded/locomotion guard entirely, since picking this from the menu
    /// already means you're looking right at her.
    @objc private func pickSaySomething() {
        repositionSpeechWindow()
        speechEngine.say()
    }

    @objc private func pickLayer(_ sender: NSMenuItem) {
        guard let id = sender.representedObject as? String else { return }
        settings.layer = id
        applyPlacement(to: characterWindow)
    }

    @objc private func toggleAllSpaces(_ sender: NSMenuItem) {
        settings.allSpaces.toggle()
        sender.state = settings.allSpaces ? .on : .off
        applyPlacement(to: characterWindow)
    }

    @objc private func toggleReact(_ sender: NSMenuItem) {
        settings.reactToSystem.toggle()
        sender.state = settings.reactToSystem ? .on : .off
        if settings.reactToSystem { systemMonitor.start() } else { systemMonitor.stop() }
    }

    @objc private func toggleTalk(_ sender: NSMenuItem) {
        settings.letHerTalk.toggle()
        sender.state = settings.letHerTalk ? .on : .off
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
        applyPlacement(to: window)
        // NOT isMovableByWindowBackground. See CatView.onDrag: AppKit's own dragging
        // fights the wander loop over the same window origin.
        window.isMovableByWindowBackground = false

        window.contentView = NSHostingView(
            rootView: CatView(settings: settings, engine: engine,
                              onDrag: { [weak self] in self?.dragTo($0) },
                              onDrop: { [weak self] in self?.dropped() })
        )
        characterWindow = window

        positionAtDock()
        window.orderFrontRegardless()
    }

    /// A second, small window for the paw-drop gesture (`PawDropView.swift`).
    ///
    /// Always ordered front, like `characterWindow` — the SwiftUI content
    /// simply draws nothing while `pawDropEngine.startedAt` is nil, so there
    /// is no show/hide to keep in sync with the animation's own timer.
    /// Ignores mouse events: nothing is wired up to click yet.
    private func setupPawDropWindow() {
        guard let screen = NSScreen.main else { return }
        let size = PawDropView.windowSize
        let window = NSWindow(
            contentRect: NSRect(x: 0, y: screen.frame.maxY - size.height, width: size.width, height: size.height),
            styleMask: [.borderless], backing: .buffered, defer: false)
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = false
        window.level = .statusBar
        window.ignoresMouseEvents = true
        window.collectionBehavior = [.canJoinAllSpaces, .stationary, .fullScreenAuxiliary]
        // contentMinSize/contentMaxSize pin the window to `size`, so nothing -
        // not even the hosting view collapsing to fit an empty SwiftUI
        // conditional - can resize it out from under us again.
        window.contentMinSize = size
        window.contentMaxSize = size
        window.contentView = NSHostingView(rootView: PawDropView(engine: pawDropEngine))
        pawDropWindow = window
        repositionPawDropWindow()
        window.orderFrontRegardless()
    }

    /// Slides `pawDropWindow` under wherever the real status item currently
    /// is, and re-measures the menu bar height too. Called again right
    /// before every trigger rather than trusted from setup time.
    ///
    /// `statusItem.button?.window?.frame` right after `setupStatusItem()` is
    /// NOT nil, but it isn't the real position either — the status bar server
    /// hasn't laid the item out yet, so it comes back as a degenerate
    /// `(0, 0, 34, 0)`: real width already, but HEIGHT still zero. A `??`
    /// fallback only catches nil, so that placeholder silently won and put
    /// the whole gesture off-screen at the top-left instead of under the icon
    /// at the top-right — found by logging the actual frame under LOAF_DEBUG
    /// rather than guessing from the symptom. Checking width alone would
    /// have made the exact same mistake again, since 34 already reads as
    /// "real" — height is the dimension that's actually zero until layout
    /// has happened, so that's what has to be checked.
    /// By the time someone has clicked "Paw" from the real menu, the status
    /// item has definitely been laid out for real, so re-deriving the
    /// position at trigger time sidesteps the whole timing problem.
    private func repositionPawDropWindow() {
        guard let window = pawDropWindow, let screen = NSScreen.main else { return }
        let w = window.frame.width, h = window.frame.height
        let menuBarHeight = NSStatusBar.system.thickness
        let iconX = (statusItem.button?.window?.frame.height ?? 0) > 1
            ? statusItem.button!.window!.frame.midX
            : screen.frame.maxX - 60
        window.setFrameOrigin(NSPoint(x: iconX - w / 2, y: screen.frame.maxY - menuBarHeight - h))

        if ProcessInfo.processInfo.environment["LOAF_DEBUG"] != nil {
            FileHandle.standardError.write(Data(
                "pawDropWindow repositioned frame=\(window.frame) statusItemWindow=\(String(describing: statusItem.button?.window?.frame))\n".utf8))
        }
    }

    // MARK: The speech bubble (SpeechBubbleView.swift)

    /// A third small window, for random one-liners above her head. Same shape as
    /// `pawDropWindow` - always ordered front, content draws nothing while
    /// `speechEngine.message` is nil, size pinned so an empty message can't shrink
    /// the window the way the first version of PawDropView did.
    private func setupSpeechWindow() {
        let size = SpeechBubbleView.windowSize
        let window = NSWindow(
            contentRect: NSRect(origin: .zero, size: size),
            styleMask: [.borderless], backing: .buffered, defer: false)
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = false
        window.level = .floating
        window.ignoresMouseEvents = true
        window.collectionBehavior = [.canJoinAllSpaces, .stationary, .fullScreenAuxiliary]
        window.contentMinSize = size
        window.contentMaxSize = size
        window.contentView = NSHostingView(rootView: SpeechBubbleView(engine: speechEngine))
        speechWindow = window
        window.orderFrontRegardless()
    }

    /// Centres the bubble over wherever `characterWindow` actually is right now.
    /// Not `private`: `stepWander` (AppDelegate+Wander.swift) calls this every tick
    /// while a message is showing, so the bubble follows her if she starts moving
    /// again mid-message rather than staying wherever she was when it began.
    func repositionSpeechWindow() {
        guard let window = speechWindow, let char = characterWindow else { return }
        let cf = char.frame
        let size = window.frame.size
        window.setFrameOrigin(NSPoint(x: cf.midX - size.width / 2, y: cf.maxY + 4))
    }

    /// Roll the dice on a random line, roughly every 1.5-4 minutes. Skips silently
    /// (and just reschedules) if the conditions aren't right rather than forcing a
    /// line in - see the guard for exactly what "right" means.
    private func scheduleNextPing() {
        speechTimer?.invalidate()
        let delay = Double.random(in: 90...240)
        let t = Timer(timeInterval: delay, repeats: false) { [weak self] _ in
            MainActor.assumeIsolated { self?.maybeSpeak() }
        }
        RunLoop.main.add(t, forMode: .common)
        speechTimer = t
    }

    private func maybeSpeak() {
        defer { scheduleNextPing() }
        guard settings.letHerTalk, engine.autopilot, !engine.held,
              !engine.overloaded, !engine.userIdle,
              !engine.state.isLocomotion, !engine.state.isOneShot else { return }
        repositionSpeechWindow()
        speechEngine.say()
    }

    /// Window level and Space behaviour, from `Settings`.
    ///
    /// `desktopIconWindow` is the level Finder puts your desktop icons at, so she ends
    /// up genuinely ON the desktop - behind every app window rather than floating over
    /// them. That is a different thing from being on all Spaces, which is why they are
    /// two controls.
    func applyPlacement(to window: NSWindow) {
        window.level = settings.layer == "desktop"
            ? NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.desktopIconWindow)) + 1)
            : .floating
        var behaviour: NSWindow.CollectionBehavior = [.stationary, .fullScreenAuxiliary]
        if settings.allSpaces { behaviour.insert(.canJoinAllSpaces) }
        window.collectionBehavior = behaviour
        // Re-assert the level: dropping to the desktop can leave her ordered above the
        // windows she is now supposed to sit behind until something reorders her.
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
