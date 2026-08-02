import Foundation
import Security

/// A thin wrapper over the one Keychain item this app has: the OpenRouter API key.
///
/// Not an environment variable, on purpose - `LOAF_*` vars are how every OTHER debug
/// knob in this app works, but they don't survive "Launch at login" (PawDropView.swift's
/// SMAppService registration), which starts her with no shell environment behind her at
/// all. The key has to persist somewhere that isn't a shell profile, and it can't be a
/// plaintext file in the repo or `UserDefaults` either - Keychain is the only one of
/// those that's actually meant for secrets. Still a system framework, not a dependency.
enum Keychain {
    private static let service = "com.ajinkya.loaf"
    private static let account = "openrouter-api-key"

    static func save(_ value: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        // Delete-then-add rather than SecItemUpdate: simpler, and this is a
        // "set it occasionally from a menu dialog" item, not a hot path where
        // the extra round-trip would matter.
        SecItemDelete(query as CFDictionary)
        var attributes = query
        attributes[kSecValueData as String] = Data(value.utf8)
        SecItemAdd(attributes as CFDictionary, nil)
    }

    static func load() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var result: AnyObject?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    static func delete() {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        SecItemDelete(query as CFDictionary)
    }
}
