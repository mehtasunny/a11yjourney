#!/usr/bin/env bash
# Runs inside the emulator step: audit baseline and patched builds, then the instrumented tests.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
bash "$HERE/run_audit.sh" apks/baseline.apk oba-audit/baseline
bash "$HERE/run_audit.sh" apks/patched.apk oba-audit/patched
bash "$HERE/instrument.sh" apks/patched.apk apks/patched-test.apk oba-audit/instrumented-tests.txt
cat oba-audit/baseline/RUN.md oba-audit/patched/RUN.md | sed 's/^/::notice title=run::/'
exit 0
