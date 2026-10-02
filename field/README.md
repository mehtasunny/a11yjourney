# Field study on real apps

This folder defines a repeatable study of A11yJourney on open-source Android apps
from [F-Droid](https://f-droid.org), chosen for the sectors this project serves:
transit, health, government services, and scheduling.

`.github/workflows/field-study.yml` runs it on demand. For each app in `apps.txt` it
downloads the current release from F-Droid, installs it on an Android emulator,
opens it, and runs `a11yjourney explore` (a few screens, measured keyboard focus,
normal and 200% text). It writes captures, reports, and a review sheet per app to the
`field-study` branch.

## Runs so far

- **2026-09-29, first full run:** all six apps installed and explored on an Android 14
  emulator, 44 findings written to review sheets on the `field-study` branch. The
  runs before it exposed problems in the tool itself (list items sharing an id, Tab
  cycles starting mid-screen, emoji contrast, exploration following a permission prompt
  into system settings); each is fixed with a regression test (see CHANGELOG 0.3.0).
  Superseded by the rerun below.
- **2026-09-29, rerun with 0.3.1:** exploration now stays inside the app under test and
  skips system toggles. 6 apps, 13 screens, 40 findings (26 WCAG 2.1 AA, 14 advisory)
  in the review sheets on the `field-study` branch, which this run replaced. Awaiting
  manual review.

## Why the numbers are not published yet

A finding is only right or wrong once a person has checked it. Precision and recall
come from the review sheets (`review.csv`), after each finding is checked on a device
with TalkBack, large text, and a keyboard, and every real problem the tool missed is
added as a `missed` row. Then:

```bash
a11yjourney score field-study/*/review.csv
```

Until that review is done, this project makes no accuracy claims about real apps.
Results will be added here, per app and per check kind, with the app versions used.

## Notes

- Apps are used as a new user would see them: no accounts, no personal data.
- Exploration skips controls that look consequential (delete, pay, send, sign out).
- Some apps may not run on an x86_64 emulator; the run notes which ones were skipped.
