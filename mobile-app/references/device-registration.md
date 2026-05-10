# Device Registration

For ad-hoc distribution, each tester's device UDID must be registered with the Apple Developer account. The signing service handles this via Apple's `.mobileconfig` enrollment profile.

## Flow

```
1. Share link: https://ios-service.vibecodeapp.com/register/{userId}
2. Tester opens on iPhone → taps "Register Device"
3. iOS downloads .mobileconfig profile
4. Tester installs in Settings > General > VPN & Device Management
5. iOS POSTs device UDID to the signing service callback
6. Tester sees success page
7. Call POST /api/devices/{userId}/register-apple to register with Apple
8. Next signing request will include the new device in the provisioning profile
```

## Endpoints

### GET /register/{userId}

Mobile-friendly landing page. Share this URL with testers.

### GET /api/devices/{userId}

List registered devices:

```json
{
  "devices": [
    {
      "udid": "00008110-000A1CD6268A801E",
      "product": "iPhone14,2",
      "deviceName": "John's iPhone",
      "registeredAt": "2026-03-25T06:18:41.000Z",
      "appleRegistered": true
    }
  ]
}
```

### POST /api/devices/{userId}/register-apple

Registers all unregistered devices with Apple Developer portal. Call this after new devices have enrolled.

```json
{
  "ok": true,
  "total": 3,
  "registered": [{"udid": "...", "product": "iPhone14,2", "deviceName": "..."}],
  "failed": []
}
```

## Developer Mode

Devices must have Developer Mode enabled to install ad-hoc signed apps:

1. **Settings > Privacy & Security > Developer Mode**
2. Toggle ON
3. iPhone will prompt to restart — tap Restart
4. After reboot, confirm when prompted

Developer Mode persists across app installs — only needs to be enabled once.

## Important

- Devices must be registered BEFORE signing. The provisioning profile is created at sign time and includes all registered device UDIDs.
- If a new device is added after a build was signed, you need to re-sign the app (not rebuild — just re-sign with the same appUrl). The old provisioning profile won't include the new device.
- The signing service caches signing assets (cert, key, profile) per user. To force a fresh provisioning profile with new devices, the cached assets may need to be cleared.
