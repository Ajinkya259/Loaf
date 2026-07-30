import AppKit

// Loaf is an accessory app: no dock icon, no application menu. She lives on the
// desktop and is controlled entirely from the 🍞 item in the menu bar. Setting this
// before `run()` is what stops a second, redundant dock icon appearing next to her.

// Headless snapshot mode, mirroring lil-cleo's CLEO_RENDER: rasterise the real
// SwiftUI view and exit. The only way to see what the app draws rather than what
// Blender rendered.
if let out = ProcessInfo.processInfo.environment["LOAF_SNAPSHOT"] {
    let raw = ProcessInfo.processInfo.environment["LOAF_STATE"] ?? "sleep"
    let state = LoafState(rawValue: raw) ?? .sleep
    let ok = MainActor.assumeIsolated { Snapshot.render(state: state, to: out) }
    FileHandle.standardError.write(Data((ok ? "wrote \(out)\n" : "snapshot failed\n").utf8))
    exit(ok ? 0 : 1)
}

// LOAF_ICON=/tmp/paw.png dumps the menu-bar icon, magnified, so it can actually be
// looked at - a template image is invisible to a normal screenshot of the menu bar.
if let out = ProcessInfo.processInfo.environment["LOAF_ICON"] {
    let ok = MainActor.assumeIsolated { MenuBarIcon.dump(to: out) }
    FileHandle.standardError.write(Data((ok ? "wrote \(out)\n" : "failed\n").utf8))
    exit(ok ? 0 : 1)
}

let app = NSApplication.shared
let delegate = MainActor.assumeIsolated { AppDelegate() }   // top-level code is main-thread
app.delegate = delegate
app.setActivationPolicy(.accessory)
app.run()
