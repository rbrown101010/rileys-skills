# iOS Capabilities & Entitlements Reference

Per-capability rules that are NOT obvious from the entitlement key alone. Every rule here has been empirically validated against Xcode 26 + current iOS. When the user asks for one of these, apply the matching line.

**Only listed here if there's a rule.** No-op entitlements (App Attest environment, get-task-allow, team-identifier, `keychain-access-groups` wildcard, user notification sub-flags, etc.) are handled automatically by the signing service — don't put them in your `.entitlements` file unless the rule below says to.

---

## 1. Capabilities with a runtime code rule

These sign fine but fail at runtime if the Swift code doesn't follow the rule. The signed entitlement being present is NOT sufficient.

- **Keychain Sharing** — `kSecAttrAccessGroup` must be the **fully-qualified** string `"TEAMID.groupname"`, NOT the bare `"groupname"`. iOS does a strict literal match. Read team id from `Bundle.main.infoDictionary?["AppIdentifierPrefix"]` (ends with a dot) or hardcode.
- **App Groups** — suite names in `UserDefaults(suiteName:)` and container queries in `FileManager.containerURL(forSecurityApplicationGroupIdentifier:)` must **exactly** match an `app-groups` entitlement value, which must **start with `group.`**.
- **iCloud / CloudKit** — `CKContainer(identifier:)` value must exactly match `com.apple.developer.icloud-container-identifiers`. Container id must start with **`iCloud.`** (literal prefix). Also declare `com.apple.developer.icloud-services = ["CloudKit"]` and `com.apple.developer.ubiquity-container-identifiers` with the same value.
- **Apple Pay (in-app)** — `PKPaymentRequest.merchantIdentifier` must match a `com.apple.developer.in-app-payments` array entry, each starting with literal **`merchant.`**.
- **PassKit (Wallet passes)** — pass type id must start with literal **`pass.`**. The .pkpass cert generation is a separate manual step Apple does not automate.
- **App Intents / Shortcuts** (iOS 16+) — no entitlement needed. Implement `AppIntent` protocols. Do NOT add a legacy SiriKit Intents extension unless the user asks for Siri voice specifically. Apple deprecated the Intents extension path for new work.

---

## 2. Capabilities with a required Info.plist usage description

Every one of these crashes on first use if the Info.plist key is missing. Entitlement key (if any) + Info.plist key:

| Capability | Entitlement key (if any) | Required Info.plist keys |
|---|---|---|
| HealthKit | `com.apple.developer.healthkit = true` | `NSHealthShareUsageDescription`, `NSHealthUpdateUsageDescription` |
| HomeKit | `com.apple.developer.homekit = true` | `NSHomeKitUsageDescription` |
| Contacts | — | `NSContactsUsageDescription` |
| Calendar | — | `NSCalendarsUsageDescription` |
| Reminders | — | `NSRemindersUsageDescription` |
| Photo Library (read) | — | `NSPhotoLibraryUsageDescription` |
| Photo Library (write) | — | `NSPhotoLibraryAddUsageDescription` |
| Camera | — | `NSCameraUsageDescription` |
| Microphone | — | `NSMicrophoneUsageDescription` |
| Speech Recognition | — | `NSSpeechRecognitionUsageDescription` |
| Core Bluetooth (always) | — | `NSBluetoothAlwaysUsageDescription` |
| Core Bluetooth (peripheral mode) | — | `NSBluetoothPeripheralUsageDescription` |
| Location (when-in-use) | — | `NSLocationWhenInUseUsageDescription` |
| Location (always) | — | `NSLocationAlwaysAndWhenInUseUsageDescription` |
| Motion / CMMotionManager | — | `NSMotionUsageDescription` |
| Face ID | — | `NSFaceIDUsageDescription` |
| NFC | `com.apple.developer.nfc.readersession.formats = ["TAG"]` | `NFCReaderUsageDescription` |
| Media Library (Apple Music) | — | `NSAppleMusicUsageDescription` |
| Siri (legacy SiriKit) | `com.apple.developer.siri = true` | `NSSiriUsageDescription` |
| Local Network (iOS 14+) | — | `NSLocalNetworkUsageDescription` |
| User Tracking (ATT) | — | `NSUserTrackingUsageDescription` |

Rule: if an agent imports a framework that shows a system permission prompt, the Info.plist needs the matching `NS*UsageDescription`. No exceptions.

---

## 3. Capabilities that need a manual Apple portal step (cannot fully automate)

The signing service enables the ASC capability flag and raises a `CapabilityManualStepRequiredError` with actionable instructions. Tell the user up front these will require one-time portal clicks.

- **iCloud containers** — create and link the container at developer.apple.com (or password-auth automated).
- **Apple Pay merchant IDs** — create + link + generate payment processing certificate (cert is always manual).
- **App Groups** — create + link the group (or password-auth automated).
- **Pass Type IDs** — create + link + generate pass type certificate (cert is always manual).
- **WeatherKit** — `com.apple.developer.weatherkit = true`. Requires **paid** Apple Developer Program membership AND a manual toggle in Account → Services → WeatherKit. Not in ASC's capabilityType list at all. Runtime will fail with JWT auth error until enabled on the paid portal side.
- **Family Controls / Screen Time** — `com.apple.developer.family-controls = true`. Requires a human-reviewed Apple approval request. Entitlement can be declared but runtime will fail until Apple approves.
- **CarPlay** — any `com.apple.developer.carplay-*` entitlement requires a filled-out CarPlay entitlement request form at Apple. Not approvable for random test apps.
- **MusicKit** — no entitlement key needed. Requires `NSAppleMusicUsageDescription` in Info.plist + MusicKit capability enabled on the bundle id at developer.apple.com → Identifiers → select bundle → MusicKit. Without this, `MusicAuthorization.request()` succeeds but all catalog/library calls return empty.
- **Network Extension (VPN)** — `com.apple.developer.networking.networkextension` must contain the exact provider type as an array value: `["packet-tunnel-provider"]` for VPN, `["app-proxy-provider"]` for proxy, `["content-filter-provider"]` for content filter, `["dns-proxy"]` for DNS proxy. If the entitlement value is wrong or generic, iOS refuses install even though the capability flag is enabled.

If the user has password auth configured on the signing service, App Groups / iCloud containers / merchant ids are auto-created and linked via the Dev Portal API. API-key-only users get the manual-step error.

---

## 4. Extension matrix

All app extensions share the same rules. Apply all five for every extension target:

1. **Bundle id**: must be a strict child prefix of the main app's bundle id (`com.example.app.widget`, NOT `com.example.widget`).
2. **Info.plist (Option B)**: write a manual `Info.plist` in the extension folder with the correct `NSExtension` dictionary. In `project.pbxproj`, set `GENERATE_INFOPLIST_FILE = NO` and `INFOPLIST_FILE = "<Extension>/Info.plist"` for that target. Xcode 26's auto-generated plist + manual plist merge-conflicts — Option B is the only working pattern.
3. **`CFBundleDisplayName`**: EVERY `.appex` extension Info.plist MUST have `CFBundleDisplayName` set to a non-empty string. iOS refuses to install without it. Add it right next to `CFBundleName`.
4. **Shared entitlements**: if the extension reads/writes data shared with the main app, declare the same App Group in both targets' `.entitlements` files.
5. **Deployment target**: extension's `IPHONEOS_DEPLOYMENT_TARGET` must be ≥ main app's. Mismatches break `embeddedProvisioningProfileValidation`.
6. **Icon**: if the user asked for a visible extension (widget, Live Activity, watchOS), the extension's own asset catalog needs an icon entry or it renders blank.

Per-extension `NSExtensionPointIdentifier` values:

| Extension type | NSExtensionPointIdentifier | Notes |
|---|---|---|
| WidgetKit widget | `com.apple.widgetkit-extension` | Also used for Live Activities (iOS 16+) |
| Notification Service | `com.apple.usernotifications.service` | Modify push payloads |
| Notification Content | `com.apple.usernotifications.content-extension` | Custom push UI |
| Share Extension | `com.apple.share-services` | Upload/share from other apps |
| Action Extension | `com.apple.ui-services` | Transform content in place |
| iMessage App | `com.apple.message-payload-provider` | Or `com.apple.messages.MSMessagesAppExtension` for full Messages app |
| File Provider | `com.apple.fileprovider-nonui` | Cloud storage backends |
| File Provider UI | `com.apple.fileprovider-actionsui` | UI for File Provider actions |
| Document Browser | — (no extension, main app `LSSupportsOpeningDocumentsInPlace = YES`) | Set `UISupportsDocumentBrowser = YES` |
| Broadcast Upload | `com.apple.broadcast-services-upload` | Screen recording to cloud |
| Broadcast UI | `com.apple.broadcast-services-setupui` | UI wrapper for Broadcast Upload |
| AutoFill Credential Provider | `com.apple.authentication-services-credential-provider-ui` | Entitlement goes on the extension, NOT the main app |
| Call Directory | `com.apple.callkit.call-directory` | Spam blocker / caller ID |
| Intents (legacy SiriKit) | `com.apple.intents-service` | Prefer App Intents for new work |
| Intents UI (legacy SiriKit) | `com.apple.intents-ui-service` | Custom Siri UI |
| watchOS app | — (own target, not an extension of the phone app after watchOS 7) | Needs `WKApplication = YES` in watch Info.plist |

### Live Activities / Dynamic Island

- Main app Info.plist: `NSSupportsLiveActivities = YES`
- Widget target Info.plist: `NSExtensionPointIdentifier = com.apple.widgetkit-extension`
- Swift: implement `ActivityAttributes` in a file shared between both targets, use `Activity<Attrs>.request(attributes:content:)` to start.
- No extra entitlement.

### Share Extension specifically

- Define `NSExtensionAttributes` → `NSExtensionActivationRule` to declare what types you accept (URL, image, text, etc.). Without this, the extension never appears in the share sheet.

---

## How to use this file

When writing any iOS app that uses a capability or ships an extension:

1. Grep this file for the capability or framework name.
2. If a rule is listed, **apply it verbatim**. Do not invent your own.
3. If nothing is listed, the capability is a no-op and you don't need to declare it.
4. If a rule says "manual portal step", tell the user that step up front — don't surprise them after sign fails.
