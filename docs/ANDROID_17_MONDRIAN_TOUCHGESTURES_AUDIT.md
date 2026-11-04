# P1 — TouchGestures Android 17 / mondrian integration and security audit

Date: 2026-11-04. Status: **AUDIT ONLY; NOT PORTED, NOT SELECTED IN AOSP17 MANIFEST.**

## Provenance and coupling

- Historical PixelExperience-Reborn `packages_apps_TouchGestures` branch `seventeen`, HEAD `ae1a28843f4e96d2acb684a3ab0d02418240b920`. History contains CyanogenMod/LineageOS gesture implementations and translation updates.
- Legacy `Android.bp` defines privileged, platform-signed `TouchGestures`, `system_ext_specific: true`, `platform_apis: true`, and the removed/obsolete-for-this-graph `SettingsLibDefaults` dependency.
- Legacy `AndroidManifest.xml` uses `android.uid.system`, `targetSdkVersion="29"`, a persistent application, protected broadcast and exported screen-off launch activity guarded by `com.android.touch.gestures.TRIGGER_SCREEN_OFF_GESTURE` with historical `signatureOrSystem` protection.
- The old PE Settings repo contains a `TouchGestures -> ../TouchGestures` symlink and declares `TouchGestures/res` in `Settings-core`; this is a cross-repository resource/build coupling. Installing the old APK by itself cannot satisfy that architecture, while copying it into modern AOSP17 Settings is also unsupported.

## Reviewed implementation hazards

1. **Proximity protection initialization bug in the archived source**: `KeyHandler` declares `private Sensor mProximitySensor;` (initial value null). Inside the constructor it checks `if (mProximitySensor != null)` **before** assigning `mSensorManager`, `mProximitySensor = mSensorManager.getDefaultSensor(...)`, and `mProximityWakeLock`. Unless another initializer exists, this branch cannot be entered from the constructor. No successful proximity detection can be claimed for this old code. This is a *source-level finding*, not an observed mondrian runtime failure.
2. The proximity wakelock is acquired without a supplied timeout inside `processEvent()` and released by sensor callback. Any future implementation needs explicit timeout and safe release on error, cancellation and sensor failure.
3. `KeyHandler` implements `com.android.internal.os.DeviceKeyHandler`, uses hidden/internal `PowerManager.wakeUp` and camera gesture broadcasts, `LineageHardwareManager.FEATURE_TOUCHSCREEN_GESTURES`, and receiver-based settings updates. Each relies on framework/vendor APIs that must be audited against genuine Android17 source and device support; they are not public Android APIs.
4. The component exposes a screen-off activity that calls `KeyguardManager.requestDismissKeyguard` before launching user-selected external apps. It must not circumvent secure lockscreen policy, user separation or launcher intent restrictions. The old method calls `finish()` on null intent but then continues to the post/dismiss sequence; avoid copying control flow blindly.
5. The original `SystemSettingSwitchPreference` stores booleans in global `Settings.System`. Define exact owner, per-user rules, permissions and device restore behavior if migrating; avoid duplicated toggles already present in mondrian's device settings.
6. The old dynamic broadcast registration uses a legacy overload; confirm Android17 context receiver export flags/permissions and verify that untrusted apps cannot mutate gesture mappings or initiate locked-device actions.

## Android17 / mondrian gates

- [x] Audit historical app signing, API, manifest, Settings resource coupling and gesture handler.
- [x] Record deterministic proximity-initialization bug and source-only test.
- [x] Preserve no legacy TouchGestures path in staged manifest; require explicit opt-in source branch after device review.
- [ ] Confirm actual hardware key/scancode and touchscreen gestures support on mondrian, against kernel events and real HAL (not device name assumptions).
- [ ] Design correct Android17 replacement for `DeviceKeyHandler`, `LineageHardwareManager` and Settings preference integration. Use one hardware/framework owner, no competing handlers.
- [ ] Fix and unit-test proximity sensor availability, timing, wake locks, torch/camera, setup completion, screen off/Doze interaction and screen lock rules.
- [ ] Verify system UID/signing, manifest permissions, receiver and exported activity policy without blanket privilege grants.
- [ ] Build with Soong on official AOSP17, validate logcat/SensorManager/PowerManager and test on POCO F5 Pro / Redmi K60 (mondrian), including pocket mode and user isolation.

## Decision

The historical component is **not** Android17-ready. This audit branch changes only audit docs, host tests and CI; it is not a production bug fix or a completed feature. The old sources remain intact for precise patch-by-patch review.
