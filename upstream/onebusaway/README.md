# OneBusAway for Android: accessibility audit

This folder holds an accessibility audit of [OneBusAway for Android](https://github.com/OneBusAway/onebusaway-android),
an open-source real-time transit app, and proposed fixes for the problems found.

- `patches/`: proposed fixes, one file per finding (OBA-S1 to OBA-S9), written against OneBusAway
  commit `476cf18`. They are proposals only until the OneBusAway maintainers review them.
- `journeys/`, `run_audit.sh`, `ci_audit.sh`, `instrument.sh`, `compare.py`: the audit harness.
  The `oba-audit` workflow builds OneBusAway twice (as published, and with the patches), checks the
  patched build the way OneBusAway's own CI does (Spotless, Kotlin warnings as errors, unit tests,
  Android Lint), audits both builds on an Android 14 emulator with A11yJourney at normal and 200%
  text with keyboard focus measured on the device, and runs the new instrumented tests.

Results are published to the `oba-audit-results` branch. Automated findings are candidates until a
person confirms them on a device with TalkBack and large text.
