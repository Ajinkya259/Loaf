import AppKit

// Loaf is an accessory app: no dock icon, no application menu. She lives on the
// desktop and is controlled entirely from the drawn paw item in the menu bar
// (MenuBarIcon.swift). Setting this before `run()` is what stops a second,
// redundant dock icon appearing next to her.

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

// LOAF_PAW_SNAPSHOT=/tmp/p.png [LOAF_PAW_T=0.55] captures the paw-drop gesture at a
// given elapsed second, since it isn't a LoafState and LOAF_SNAPSHOT doesn't cover it.
if let out = ProcessInfo.processInfo.environment["LOAF_PAW_SNAPSHOT"] {
    let t = Double(ProcessInfo.processInfo.environment["LOAF_PAW_T"] ?? "") ?? 0.55
    let ok = MainActor.assumeIsolated { Snapshot.renderPawDrop(elapsed: t, to: out) }
    FileHandle.standardError.write(Data((ok ? "wrote \(out)\n" : "snapshot failed\n").utf8))
    exit(ok ? 0 : 1)
}

// LOAF_SAY_SNAPSHOT=/tmp/s.png [LOAF_SAY_TEXT="..."] captures the speech bubble,
// with a specific line or a random one from the pool if LOAF_SAY_TEXT is unset.
if let out = ProcessInfo.processInfo.environment["LOAF_SAY_SNAPSHOT"] {
    let text = ProcessInfo.processInfo.environment["LOAF_SAY_TEXT"]
    let ok = MainActor.assumeIsolated { Snapshot.renderSpeechBubble(text: text, to: out) }
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
