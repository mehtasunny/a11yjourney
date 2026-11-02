#!/usr/bin/env bash
# Audit one OneBusAway build on a connected emulator.
# Usage: run_audit.sh APK OUT_DIR
set -uo pipefail
APK="$1"; OUT="$2"; PKG=com.joulespersecond.seattlebusbot
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
log() { echo "$*" | tee -a "$OUT/RUN.md"; }
log "# OneBusAway audit: $(basename "$APK") $(date -u +%Y-%m-%dT%H:%MZ)"
log "Android $(adb shell getprop ro.build.version.release | tr -d '\r')"
# Downtown Seattle, so the app picks the Puget Sound region on its own
adb emu geo fix -122.3361 47.6080 >/dev/null 2>&1 || true
adb uninstall "$PKG" >/dev/null 2>&1 || true
if ! adb install -r -g "$APK" > /tmp/install.log 2>&1; then
  log "- install failed: $(tail -1 /tmp/install.log)"; exit 0
fi
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep 25
adb emu geo fix -122.3361 47.6080 >/dev/null 2>&1 || true
run() { # name, command...
  local name="$1"; shift
  if timeout 600 "$@" > "$OUT/$name.log" 2>&1; then log "- $name: ok"; else log "- $name: failed ($(tail -1 "$OUT/$name.log"))"; fi
}
cap() { echo a11yjourney capture --name "$1" --out "$OUT/screens" --keyboard; }
# First launch asks "Are you in the Puget Sound region?"; answer Yes when it is showing.
answer_region() { a11yjourney journey "$HERE/journeys/region-yes.txt" --out "$OUT/.region" > /dev/null 2>&1 || true; }
# 1. Home (map and chrome)
answer_region
run home $(cap home)
# 2. Stop arrivals through the app's own deep link
adb shell am start -W -a android.intent.action.VIEW -d "onebusaway://view-stop?stopID=1_75403" "$PKG" >/dev/null 2>&1
sleep 15
answer_region
run arrivals $(cap arrivals)
# 3 and 4. Scripted journeys
adb shell am force-stop "$PKG"
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; sleep 10; answer_region
run settings a11yjourney journey "$HERE/journeys/settings.txt" --out "$OUT/settings"
adb shell am force-stop "$PKG"
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; sleep 10; answer_region
run feedback a11yjourney journey "$HERE/journeys/feedback.txt" --out "$OUT/feedback"
# 5. Bounded exploration from the stop arrivals screen
adb shell am force-stop "$PKG"
adb shell am start -W -a android.intent.action.VIEW -d "onebusaway://view-stop?stopID=1_75403" "$PKG" >/dev/null 2>&1
sleep 15
run explore a11yjourney explore --out "$OUT/explore" --max-screens 5 --keyboard --package "$PKG"
for d in "$OUT/screens" "$OUT/settings" "$OUT/feedback" "$OUT/explore"; do
  [ -d "$d" ] || continue
  a11yjourney report "$d" --format json --review-sheet "$d/review.csv" > "$d/report.json" 2>/dev/null || true
  a11yjourney report "$d" > "$d/report.txt" 2>/dev/null || true
done
adb shell am force-stop "$PKG"
exit 0
