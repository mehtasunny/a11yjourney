#!/usr/bin/env bash
# Run selected instrumented tests from the patched build. Usage: instrument.sh APP_APK TEST_APK OUT_FILE
set -uo pipefail
adb install -r -g "$1" >/dev/null 2>&1; adb install -r -g "$2" >/dev/null 2>&1
CLASSES="org.onebusaway.android.ui.arrivals.EtaPillStatusDescriptionTest,org.onebusaway.android.ui.settings.SwitchPreferenceItemSemanticsTest"
{
  echo "## New tests"; adb shell am instrument -w -e class "$CLASSES" com.joulespersecond.seattlebusbot.test/androidx.test.runner.AndroidJUnitRunner
  echo "## Existing arrivals and settings UI tests"; adb shell am instrument -w -e package org.onebusaway.android.ui.arrivals com.joulespersecond.seattlebusbot.test/androidx.test.runner.AndroidJUnitRunner
  adb shell am instrument -w -e package org.onebusaway.android.ui.settings com.joulespersecond.seattlebusbot.test/androidx.test.runner.AndroidJUnitRunner
} > "$3" 2>&1
grep -E "^OK|FAILURES|Tests run|Error" "$3" | sed 's/^/::notice title=instrumented tests::/' || true
