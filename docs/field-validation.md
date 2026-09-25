# Field validation on real apps

Synthetic benchmarks show that the checks work as designed. They do not show
that the tool is useful. This protocol is how A11yJourney is tested on real,
openly licensed Android apps, and how results are reported without
overstating them.

## Choosing apps

* Openly licensed Android apps (for example from F-Droid) with public issue
  trackers, so findings can be reported to the people who can fix them.
* Priority to the sectors this project is for: health and medication,
  public transit, and civic or government services.
* Use the app as a normal user would. No reverse engineering, no bypassing
  logins, and test accounts or demo data only.

## Capturing

For each app, pick two or three core tasks (plan a trip, book an
appointment, find a form) and capture every screen in the task:

```bash
a11yjourney capture --name <app>-<task>-<step> --out field/<app>
a11yjourney field/<app>/<app>-<task>-<step>.xml --format json > field/<app>/<step>.json
```

Record the app version, device, Android version, and date. The capture
manifest (`NAME.json`) records the device details automatically.

Do not commit screenshots that show personal data. Captures from demo data
may be committed so others can reproduce the results.

## Confirming each finding by hand

Every finding is checked on the device with TalkBack (and, for contrast, a
color picker or Accessibility Scanner) and recorded as one row:

| app | version | screen | element | wcag | tool severity | verdict | notes |
|---|---|---|---|---|---|---|---|
| | | | | | | confirmed / false positive / unclear | |

Also record problems found by hand that the tool missed. Without them, recall
cannot be measured.

## Reporting results

* Publish per-app counts: findings, confirmed, false positives, and issues
  missed, plus precision and recall with the number of screens behind them.
* Keep field results separate from the synthetic benchmark.
* Report false positives as bugs in this repository and fix them.

## Reporting to app maintainers

Only report findings you have confirmed on a device. One issue per problem,
or one grouped issue per screen, written for a busy maintainer:

```
Title: [Accessibility] "Plan trip" button text is clipped at the largest font size

What happens: With Android font size at maximum (Settings > Display > Font size),
the "Plan trip" button keeps its height and the label is cut off.
Who it affects: people with low vision who use large text.
Standard: WCAG 2.1 SC 1.4.4 Resize Text (Level AA).
Steps: 1) Set font size to maximum. 2) Open Plan trip. 3) Look at the button.
Device / app version: Pixel 7, Android 15, app 3.2.1
Suggested fix: let the button height wrap its content (minHeight instead of height).
Found with A11yJourney and confirmed by hand with TalkBack.
```

Be patient and courteous, and do not open pull requests or issues in bulk.
Whether maintainers confirm, fix, or decline an issue is part of the result
and gets recorded honestly.
