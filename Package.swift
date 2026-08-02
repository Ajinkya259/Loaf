// swift-tools-version: 6.0
import PackageDescription

// Loaf has ZERO third-party dependencies and that is a deliberate constraint, not an
// accident of being early. She is an always-running background app: every dependency
// is memory she holds all day, launch time on every login, and a supply chain for
// something that only needs AppKit, SwiftUI and a folder of PNGs.
let package = Package(
    name: "Loaf",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "Loaf",
            path: "Sources/Loaf",
            resources: [
                // .copy, not .process. `process` flattens and may recompress PNGs;
                // the sprite contract depends on these files being byte-exact at
                // 640x512 with their alpha and their 24px ground line intact.
                .copy("Resources/sprites")
            ],
            swiftSettings: [
                // Swift 6 strict concurrency vs AppKit Timer/RunLoop callbacks is a
                // fight with no prize here. v5 mode with an explicitly @MainActor
                // AppDelegate gives the same safety for a single-threaded UI app.
                .swiftLanguageMode(.v5)
            ],
            linkerSettings: [
                // `swift run`/`swift build` produce a bare Mach-O binary with no
                // .app bundle, so there is no Info.plist for TCC to read the
                // Reminders usage-description string from - and without one,
                // requesting access doesn't prompt or fail gracefully, it crashes
                // outright. Embedding Info.plist directly into the binary's own
                // __TEXT,__info_plist section is what NSBundle.main reads even
                // with no bundle around it, so the dev binary and the packaged
                // .app (which gets its own separate Info.plist from
                // tools/package.sh) both work. Same trick lil-cleo doesn't need,
                // since it asks for no permissions at all.
                .unsafeFlags([
                    "-Xlinker", "-sectcreate",
                    "-Xlinker", "__TEXT",
                    "-Xlinker", "__info_plist",
                    "-Xlinker", "Info.plist",
                ])
            ]
        )
    ]
)
