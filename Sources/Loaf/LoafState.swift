import Foundation

/// Every state Loaf can be in.
///
/// This enum is the **renderer-agnostic contract** between her behaviour and her art,
/// the same role `Emotion.swift` plays in lil-cleo. It names *states*, never pictures:
/// behaviour code says `.sit`, and only `sprite` knows that lives in `sit.png`.
///
/// Cases exist here before their art does. `available` asks the bundle at runtime
/// whether a state can actually be drawn, so a state that has no sprite yet shows up
/// disabled in the menu instead of silently rendering as something else — and enables
/// itself the moment Blender renders it, with no code change.
enum LoafState: String, CaseIterable, Identifiable {
    // Rendered.
    case idle           // standing, profile — the resting state and the fallback
    case walk           // 8-frame cycle, profile
    case look           // standing, turned to face you
    case sit            // sitting, front
    case sitSide        // sitting, profile — the same angle she walks in
    case sleep          // curled up asleep, profile
    case jump           // 6-frame arc, profile — plays once, never held

    // Planned. See CLAUDE.md §6. No art yet; the menu disables these.
    case chill          // lounging with a prop vignette (coffee, popcorn)
    case chonk          // the task-load body, heavier and visibly fed up
    case stressed       // hunched, ears flat — blocked on ear bones
    case wake           // the morning stretch

    var id: String { rawValue }

    /// Sprite basename under `Resources/sprites/`. A cycle is `<sprite>1…N.png`;
    /// a still is `<sprite>.png`.
    ///
    /// The three renamings are deliberate. Blender names files by *camera angle*
    /// (`side_idle`, `front_idle`) because that is what a render is; the app names
    /// them by *intent* (`idle`, `look`) because that is what behaviour code cares
    /// about. Keeping both vocabularies and mapping between them here means neither
    /// side has to adopt the other's naming.
    var sprite: String {
        switch self {
        case .idle:    "side_idle"
        case .look:    "front_idle"
        case .sitSide: "sit_side"
        default:    rawValue
        }
    }

    var title: String {
        switch self {
        case .idle:     "Idle"
        case .walk:     "Walk"
        case .look:     "Look at me"
        case .sit:      "Sit (front)"
        case .sitSide:  "Sit (side)"
        case .sleep:    "Sleep"
        case .jump:     "Jump"
        case .chill:    "Chill"
        case .chonk:    "Chonk"
        case .stressed: "Stressed"
        case .wake:     "Wake"
        }
    }

    /// True if this state is drawn in profile.
    ///
    /// **Profile is for locomotion, front is for personality** — lil-cleo's rule, and
    /// mostly ours. `sitSide` is the deliberate exception: she arrives at a corner
    /// walking in profile, and turning 90° to face the camera just to sit down is
    /// something nothing alive does.
    ///
    /// That exception only exists because it got its own geometry. The rule was
    /// originally written from a failed attempt to render the *front* sit sideways,
    /// which read as a marmot — the bell taper that makes that pose work lives in the
    /// width axis, exactly what a side camera cannot see. The real lesson was
    /// "front-designed geometry doesn't survive profile", not "a sit can't be shown in
    /// profile". See SPRITE_CONTRACT.md §2.
    var isProfile: Bool { self == .idle || self == .walk || self == .sitSide || self == .sleep || self == .jump }

    /// Locomotion states travel, so the wander loop moves the window under them.
    /// Everything else plays in place.
    var isLocomotion: Bool { self == .walk }

    /// Plays once and ends, rather than looping or being held.
    ///
    /// The menu treats these differently: picking one *performs* it and hands control
    /// straight back, because pinning a jump would freeze her mid-air.
    var isOneShot: Bool { self == .jump }

    /// Can this state actually be drawn right now?
    var available: Bool { Sprites.exists(sprite) }

    /// The states with art, in menu order.
    static var rendered: [LoafState] { allCases.filter(\.available) }

    /// The states still waiting on Blender.
    static var planned: [LoafState] { allCases.filter { !$0.available } }
}
