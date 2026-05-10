# Common Gotchas

## Build Issues

### `type X does not conform to protocol 'ObservableObject'` at compile time

**Cause:** Xcode 26's strict `MemberImportVisibility` requires `import Combine` in any file that declares `class X: ObservableObject` or uses `@Published`. Importing SwiftUI is NOT sufficient — `ObservableObject`, `@Published`, and `ObservableObjectPublisher` live in Combine.

**Fix:** Add `import Combine` at the top of every file that declares an `ObservableObject` conformance or uses `@Published`. Example:

```swift
import Foundation
import Combine          // ← required, even if this file also imports SwiftUI

final class MyViewModel: ObservableObject {
    @Published var value: String = ""
}
```

When writing any new class that conforms to `ObservableObject`, always include `import Combine`.

### App crashes on launch after install

**Cause:** The `.app` was built for the iOS Simulator, not a real device.

Check the binary platform:

```bash
otool -l MyApp.app/MyApp | grep -A2 'platform'
```

- `platform 2` = iOS (real device) — correct
- `platform 7` = iOS Simulator — will crash on device

**Fix:** Send the project through the hosted build pipeline and confirm the produced artifact targets real devices, not the simulator.

### Hosted build can't find a scheme

**Cause:** The `.xcodeproj` doesn't have shared schemes.

**Fix:** Ensure the project has at least one shared scheme, or send the intended scheme name as part of the hosted build request when the service supports it.

## Signing Issues

### "You already have a current iOS Development certificate"

**Cause:** Apple limits the number of active development certificates. The signing service tries to create a new one but one already exists.

The signing service handles this by falling back to the `DEVELOPMENT` certificate type if `IOS_DEVELOPMENT` fails with a 409 conflict.

### "This certificate can only be revoked by Apple Developer Program Support"

**Cause:** Some certificates are locked by Apple and can't be revoked via the API.

**Fix:** The signing service falls back to trying alternative certificate types automatically. If all fail, you may need to revoke certificates manually at [https://developer.apple.com/account/resources/certificates](https://developer.apple.com/account/resources/certificates).

### "No registered iOS devices were found in App Store Connect"

**Cause:** No devices are registered with the Apple Developer account. Ad-hoc provisioning profiles require at least one device.

**Fix:** Register devices first using the device registration flow (`/register/{userId}`), then call `POST /api/devices/{userId}/register-apple`.

### "App Store Connect request failed (401): NOT_AUTHORIZED"

**Cause:** Invalid API key credentials.

Common mistakes:

- **Wrong keyID** — the `.p8` filename is `AuthKey_{keyID}.p8`, use the ID from the filename
- **Wrong issuerID** — find it at App Store Connect > Users and Access > Integrations > Keys
- **Expired or revoked key** — check at App Store Connect

## OTA Install Issues

### "Unable to install" on iPhone

**Causes:**

1. Device UDID not in provisioning profile — register the device and re-sign
2. Bundle ID mismatch between app and profile
3. iOS version too old for the app's minimum deployment target

### Install button does nothing

**Cause:** OTA install requires HTTPS. The `itms-services://` protocol only works with HTTPS manifest URLs.

The hosted signing service at `https://ios-service.vibecodeapp.com` uses HTTPS. Or you can host a custom install page on Chorus.host.

## Pipeline Issues

### Azure pipeline stuck on "notStarted"

**Cause:** No available hosted macOS workers, or the build queue is backed up.

**Fix:** Retry after a short wait and check the hosted build job status again before assuming the project itself is broken.

