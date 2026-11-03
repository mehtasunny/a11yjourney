#!/usr/bin/env bash
set -uo pipefail
D=upstream/atf-scan/scanner/build/outputs/apk
adb install -r -g $D/debug/scanner-debug.apk && adb install -r -g $D/androidTest/debug/scanner-debug-androidTest.apk
adb shell am start -W -a android.settings.SETTINGS >/dev/null 2>&1; sleep 8
adb logcat -c
adb shell am instrument -w -e class io.github.mehtasunny.atfscan.ScanTest -e screen settings \
  io.github.mehtasunny.atfscan.test/androidx.test.runner.AndroidJUnitRunner | tail -5 | sed 's/^/::notice title=instrument::/'
adb logcat -d -s ATFSCAN:I -v raw | grep '^{' | head -40 | sed 's/^/::notice title=ATFSCAN::/'

# The same scan on OneBusAway (published build): arrivals and Settings
PKG=com.joulespersecond.seattlebusbot
pip install -q -e . >/dev/null 2>&1
adb emu geo fix -122.3361 47.6080 >/dev/null 2>&1
adb install -r -g apks/baseline.apk >/dev/null && adb shell monkey -p $PKG -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep 25
printf 'try tap YES\nwait 3\ntry tap Close\nwait 2\n' > /tmp/dismiss.txt
a11yjourney journey /tmp/dismiss.txt --out /tmp/j >/dev/null 2>&1
scan() {
  adb logcat -c
  adb shell am instrument -w -e class io.github.mehtasunny.atfscan.ScanTest -e screen "$1" \
    io.github.mehtasunny.atfscan.test/androidx.test.runner.AndroidJUnitRunner >/dev/null 2>&1
  adb logcat -d -s ATFSCAN:I -v raw | grep '^{' | head -30 | sed "s/^/::notice title=OBA $1::/"
  adb shell uiautomator dump /sdcard/ui.xml >/dev/null 2>&1
  echo "::notice title=OBA $1::uiautomator nodes $(adb shell cat /sdcard/ui.xml | grep -o '<node' | wc -l)"
}
scan oba-home
adb shell am start -W -a android.intent.action.VIEW -d "onebusaway://view-stop?stopID=1_75403" $PKG >/dev/null 2>&1
sleep 15; a11yjourney journey /tmp/dismiss.txt --out /tmp/j >/dev/null 2>&1
scan oba-arrivals
adb shell am force-stop $PKG
printf 'launch com.joulespersecond.seattlebusbot\nwait 10\ntry tap YES\nwait 2\ntry tap Close\nwait 2\ntap Open navigation drawer\nwait 3\ntap Settings\nwait 5\n' > /tmp/settings.txt
a11yjourney journey /tmp/settings.txt --out /tmp/j2 > /tmp/j2.log 2>&1 || tail -1 /tmp/j2.log | sed 's/^/::warning title=settings journey::/'
scan oba-settings
exit 0
