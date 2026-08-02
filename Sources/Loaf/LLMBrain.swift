import Foundation

/// The "brain layer" from `Idea.md`, finally wired in - `SpeechEngine.say(_:)` was
/// always the exact seam for this, so nothing about the display or timing code
/// needed to change, only what picks the line.
///
/// Only used for the ambient personality pings (`AppDelegate.maybeSpeak`) and the
/// manual "Say something" menu item. Greeting and hydration lines stay on their
/// fixed pools on purpose - hovering her is a direct interaction and the model
/// takes several seconds to answer, which would make a hover feel broken rather
/// than responsive. Ambient pings already have no urgency: nothing is waiting on
/// them, so the same latency is invisible there.
///
/// Degrades exactly like `TaskLoadMonitor`: no key in Keychain, or any failure
/// along the way (network, timeout, malformed response), and this simply returns
/// nil - callers fall back to `SpeechEngine.lines`, the fixed pool, same as if
/// this file didn't exist.
@MainActor
enum LLMBrain {
    /// Picked after comparing several free OpenRouter models against this exact
    /// prompt shape: no hidden reasoning tokens (several of the free tier's
    /// models are reasoning models that burn their whole token budget on
    /// invisible chain-of-thought before ever answering), small completions,
    /// genuinely funny, in-character output on the first try. ~7s typical
    /// latency on the free tier, which is fine here - see the type doc above
    /// for why that only works for the ambient path.
    private static let model = "google/gemma-4-26b-a4b-it:free"
    private static let endpoint = URL(string: "https://openrouter.ai/api/v1/chat/completions")!
    private static let debug = ProcessInfo.processInfo.environment["LOAF_DEBUG"] != nil

    private static let system = """
    You are Loaf, a sarcastic voxel cat desktop pet who lives in a macOS menu \
    bar. You never need food, just power and attention - lower maintenance \
    than a real cat, and you know it. Reply with exactly ONE short sentence, \
    under 14 words, in character. No quotes, no emoji, no hashtags, no \
    explanation - just the line itself.
    """

    /// `weight` and `overloaded` are the same two live signals everything else in
    /// the app already reacts to (Settings.weight, CatEngine.overloaded) - she
    /// gets to riff on her actual situation instead of talking in a vacuum, but
    /// isn't forced to mention it in every line.
    static func line(weight: String, overloaded: Bool) async -> String? {
        // LOAF_OPENROUTER_KEY for now - matches every other LOAF_* knob in this
        // app, and is enough while this is being driven from a terminal. It won't
        // survive "Launch at login" (SMAppService starts her with no shell
        // environment at all), so Keychain.swift already exists as the real,
        // permanent home for this - checked second, so wiring up a menu item to
        // call Keychain.save(_:) later needs no changes here.
        guard let key = ProcessInfo.processInfo.environment["LOAF_OPENROUTER_KEY"] ?? Keychain.load(),
              !key.isEmpty else { return nil }

        let load: String
        switch weight {
        case "chonk": load = "chonky right now - lots of tasks queued"
        case "lean": load = "lean right now - nothing much queued"
        default: load = "a normal weight right now - a moderate task load"
        }
        let machine = overloaded ? " The machine is also struggling right now." : ""
        let user = "Your current status: you're \(load).\(machine) Say something in " +
                   "character - you can reference your status or just make an " +
                   "observation, whichever's funnier."

        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("Bearer \(key)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 15

        let body: [String: Any] = [
            "model": model,
            "messages": [
                ["role": "system", "content": system],
                ["role": "user", "content": user],
            ],
            "max_tokens": 60,
        ]
        guard let httpBody = try? JSONSerialization.data(withJSONObject: body) else { return nil }
        request.httpBody = httpBody

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
                if debug {
                    let code = (response as? HTTPURLResponse)?.statusCode ?? -1
                    FileHandle.standardError.write(Data("llm: bad response, status=\(code)\n".utf8))
                }
                return nil
            }
            guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let choices = json["choices"] as? [[String: Any]],
                  let message = choices.first?["message"] as? [String: Any],
                  let content = message["content"] as? String else {
                if debug { FileHandle.standardError.write(Data("llm: unparseable response\n".utf8)) }
                return nil
            }
            let trimmed = content.trimmingCharacters(in: .whitespacesAndNewlines)
            // A well-behaved 14-word reply is well under this; a much longer one
            // means the model ignored the instruction, and the bubble's own
            // lineLimit(3) would just truncate it awkwardly rather than this
            // falling back to a pool line that's guaranteed to fit.
            guard !trimmed.isEmpty, trimmed.count <= 140 else {
                if debug { FileHandle.standardError.write(Data("llm: empty or too long: \(trimmed)\n".utf8)) }
                return nil
            }
            if debug { FileHandle.standardError.write(Data("llm: \(trimmed)\n".utf8)) }
            return trimmed
        } catch {
            if debug { FileHandle.standardError.write(Data("llm: request failed: \(error)\n".utf8)) }
            return nil
        }
    }
}
