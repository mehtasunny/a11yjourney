#!/usr/bin/env bash
set -uo pipefail
D=upstream/atf-scan/scanner/build/outputs/apk
adb install -r -g $D/debug/scanner-debug.apk && adb install -r -g $D/androidTest/debug/scanner-debug-androidTest.apk
adb shell am start -W -a android.settings.SETTINGS >/dev/null 2>&1; sleep 8
adb logcat -c
adb shell am instrument -w -e class io.github.mehtasunny.atfscan.ScanTest -e screen settings \
  io.github.mehtasunny.atfscan.test/androidx.test.runner.AndroidJUnitRunner | tail -5 | sed 's/^/::notice title=instrument::/'
adb logcat -d -s ATFSCAN:I -v raw | grep '^{' | head -40 | sed 's/^/::notice title=ATFSCAN::/'
adb logcat -d | grep -iE "atfscan|AndroidRuntime|Exception" | head -20 | sed 's/^/::warning title=logcat::/'
exit 0
