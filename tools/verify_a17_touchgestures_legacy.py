#!/usr/bin/env python3
"""Historical TouchGestures invariants and risk markers, not Android17 proof."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
A = "{http://schemas.android.com/apk/res/android}"


def require(ok: bool, name: str) -> None:
    if not ok:
        raise AssertionError(name)
    print("PASS INVENTORY: " + name)


def main() -> None:
    bp = (ROOT / "Android.bp").read_text()
    manifest = ET.parse(ROOT / "AndroidManifest.xml").getroot()
    handler = (ROOT / "src/com/android/touch/gestures/KeyHandler.java").read_text()
    gestures = (ROOT / "src/com/android/touch/gestures/TouchscreenGestureSettings.java").read_text()
    activity = (ROOT / "src/com/android/touch/gestures/ScreenOffLaunchGestureActivity.java").read_text()
    require('name: "TouchGestures"' in bp and 'defaults: ["SettingsLibDefaults"]' in bp,
            "legacy Soong module and old SettingsLib dependency")
    require('certificate: "platform"' in bp and "privileged: true" in bp,
            "privileged platform-signed app needs explicit review")
    require(manifest.get(A+"sharedUserId") == "android.uid.system", "legacy shared UID")
    uses = manifest.find("uses-sdk")
    require(uses is not None and uses.get(A+"targetSdkVersion") == "29",
            "legacy Android10 target SDK")
    require("com.android.internal.os.DeviceKeyHandler" in handler
            and "com.android.internal.custom.hardware.LineageHardwareManager" in gestures,
            "legacy internal/framework HAL dependencies")
    declare = handler.find("private Sensor mProximitySensor;")
    guarded = handler.find("if (mProximitySensor != null)", declare)
    init = handler.find("mProximitySensor = mSensorManager.getDefaultSensor", guarded)
    require(declare >= 0 and guarded > declare and init > guarded,
            "legacy sensor initialization appears behind non-null guard (BUG, NOT FIXED)")
    require("mProximityWakeLock.acquire()" in handler,
            "proximity wakelock without timeout requires redesigned lifecycle")
    require("requestDismissKeyguard" in activity,
            "lockscreen dismissal uses privileged activity; policy review needed")
    print("PASS: archived behavior inventoried; security/Soong/mondrian tests NOT RUN.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ET.ParseError) as e:
        print("FAIL:", e, file=sys.stderr)
        sys.exit(1)
