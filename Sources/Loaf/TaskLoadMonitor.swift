import Foundation
import EventKit

/// Turns incomplete Reminders into her weight - the real task-load source this
/// project has been pointing at since `Idea.md`. Everything downstream already
/// existed before this file did: `Settings.weight` already drives all 72 sprites,
/// so this is purely about producing a number.
///
/// **Degrades gracefully, never nags.** If access is denied, this simply never
/// calls back, and `Settings.weight` stays exactly whatever the menu last set it
/// to. There is no re-prompt loop and no fallback UI badgering you to reconsider -
/// once macOS has recorded a decision, this respects it and the Weight menu remains
/// a perfectly good manual substitute.
@MainActor
final class TaskLoadMonitor {
    /// Called with a weight id ("lean" | "normal" | "chonk") whenever the count of
    /// incomplete reminders changes enough to cross a threshold.
    var onChange: ((String) -> Void)?

    private let store = EKEventStore()
    private var observer: NSObjectProtocol?

    private static let debug = ProcessInfo.processInfo.environment["LOAF_DEBUG"] != nil

    /// Request access once, then listen for Reminders changing rather than polling -
    /// `EKEventStoreChanged` fires whenever anything in Reminders.app (or Siri, or
    /// another app) adds, completes, or deletes one.
    func start() {
        Task {
            do {
                let granted = try await store.requestFullAccessToReminders()
                if Self.debug {
                    FileHandle.standardError.write(Data("taskLoad: access granted=\(granted)\n".utf8))
                }
                guard granted else { return }

                observer = NotificationCenter.default.addObserver(
                    forName: .EKEventStoreChanged, object: store, queue: .main
                ) { [weak self] _ in
                    // `queue: .main` guarantees this runs on the main queue at
                    // runtime, but the closure's own type isn't @MainActor, so the
                    // compiler can't verify that statically - hopping explicitly is
                    // what actually satisfies it rather than just silencing it.
                    Task { @MainActor in self?.refresh() }
                }
                refresh()
            } catch {
                if Self.debug {
                    FileHandle.standardError.write(Data("taskLoad: request failed: \(error)\n".utf8))
                }
            }
        }
    }

    /// 0-2 lean, 3-6 normal, 7+ chonk - the thresholds CONTEXT.md already
    /// recommended before this file existed to implement them.
    private func refresh() {
        let predicate = store.predicateForIncompleteReminders(
            withDueDateStarting: nil, ending: nil, calendars: nil)
        // fetchReminders' completion runs on an arbitrary queue, not necessarily
        // main - unlike this app's Timer-driven callbacks, which are always main
        // because they're added to RunLoop.main. Hopping to @MainActor explicitly
        // here rather than assuming isolation is what keeps that safe.
        store.fetchReminders(matching: predicate) { [weak self] reminders in
            let count = reminders?.count ?? 0
            let weight = count >= 7 ? "chonk" : count >= 3 ? "normal" : "lean"
            Task { @MainActor in
                if Self.debug {
                    FileHandle.standardError.write(Data(
                        "taskLoad: \(count) incomplete reminders -> \(weight)\n".utf8))
                }
                self?.onChange?(weight)
            }
        }
    }
}
