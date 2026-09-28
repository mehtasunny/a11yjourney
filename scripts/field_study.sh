#!/usr/bin/env bash
# Run the field study on a connected emulator. Usage: scripts/field_study.sh OUT_DIR
set -uo pipefail
OUT="${1:-field-study}"
mkdir -p "$OUT"
echo "# Field study run $(date -u +%Y-%m-%dT%H:%MZ)" > "$OUT/RUN.md"
adb shell getprop ro.build.version.release | sed 's/^/Android /' >> "$OUT/RUN.md"

grep -v '^#' field/apps.txt | awk 'NF {print $1}' | while read -r pkg; do
  echo "== $pkg"
  code=$(curl -sf "https://f-droid.org/api/v1/packages/$pkg" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["suggestedVersionCode"])') \
    || { echo "- $pkg: skipped (not found on F-Droid)" >> "$OUT/RUN.md"; continue; }
  if ! curl -sfL -o /tmp/app.apk "https://f-droid.org/repo/${pkg}_${code}.apk"; then
    echo "- $pkg: skipped (download failed)" >> "$OUT/RUN.md"; continue
  fi
  if ! adb install -r -g /tmp/app.apk > /tmp/install.log 2>&1; then
    echo "- $pkg: skipped (install failed: $(tail -1 /tmp/install.log))" >> "$OUT/RUN.md"; continue
  fi
  adb shell monkey -p "$pkg" -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1
  sleep 8
  dir="$OUT/$pkg"
  if timeout 900 a11yjourney explore --out "$dir" --max-screens 3 --keyboard > "$dir.explore.log" 2>&1; then
    a11yjourney report "$dir" --format json --review-sheet "$dir/review.csv" > "$dir/report.json" || true
    a11yjourney report "$dir" > "$dir/report.txt" || true
    echo "- $pkg $code: $(grep -c '' "$dir/review.csv" | awk '{print $1-1}') findings to review" >> "$OUT/RUN.md"
  else
    echo "- $pkg $code: exploration failed ($(tail -1 "$dir.explore.log"))" >> "$OUT/RUN.md"
  fi
  mv "$dir.explore.log" "$dir/explore.log" 2>/dev/null || true
  adb uninstall "$pkg" > /dev/null 2>&1 || true
done
cat "$OUT/RUN.md"
