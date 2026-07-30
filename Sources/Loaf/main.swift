import AppKit

// Loaf is an accessory app: no dock icon, no application menu. She lives on the
// desktop and is controlled entirely from the 🍞 item in the menu bar. Setting this
// before `run()` is what stops a second, redundant dock icon appearing next to her.

let app = NSApplication.shared
let delegate = MainActor.assumeIsolated { AppDelegate() }   // top-level code is main-thread
app.delegate = delegate
app.setActivationPolicy(.accessory)
app.run()
