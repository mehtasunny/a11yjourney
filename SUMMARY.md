# OneBusAway audit summary

Baseline findings: 26
Patched findings: 17
Resolved by the patches: 13
New in patched build: 4
Unchanged: 13

## Resolved

- [explore/screen-00-start] 1.4.3 11:42 PM: Text contrast is about 2.7:1 (#99C5F4 on #006EE5); WCAG AA needs 4.5:1, or 3.0:1 for large text.
- [explore/screen-00-start] 1.4.3 11:43 PM: Text contrast is about 3.6:1 (#CBE1FA on #006EE5); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-00-start] 1.4.3 11:48 PM: Text contrast is about 2.9:1 (#A8CEF6 on #006EE5); WCAG AA needs 4.5:1, or 3.0:1 for large text.
- [explore/screen-00-start] 1.4.3 11:49 PM: Text contrast is about 3.6:1 (#CBE1FA on #006EE5); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-00-start] 1.4.3 11:54 PM: Text contrast is about 3.6:1 (#CBE1FA on #006EE5); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-00-start] 1.4.3 12:13 AM: Text contrast is about 3.6:1 (#CBE1FA on #006EE5); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-00-start] 2.1.1 67 Northgate Station Roosevelt Station NOW 19min Scheduled 1: Pressing Tab cycles through the screen without ever reaching this control, so keyboard and switch users cannot activate it.
- [explore/screen-01-67-northgate-station-roosevelt] 1.4.3 12:32 AM: Text contrast is about 3.6:1 (#CEE6CB on #108500); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-01-67-northgate-station-roosevelt] 1.4.3 12:41 AM: Text contrast is about 3.6:1 (#CEE6CB on #108500); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-01-67-northgate-station-roosevelt] 1.4.3 12:46 AM: Text contrast is about 3.6:1 (#CEE6CB on #108500); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-01-67-northgate-station-roosevelt] 1.4.3 12:48 AM: Text contrast is about 3.6:1 (#CEE6CB on #108500); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-01-67-northgate-station-roosevelt] 2.5.8 Show earlier arrivals: Target is 16x66dp, under 24dp, and too close to other targets for the spacing exception.
- [settings/settings] 4.1.2 View: View is actionable but has no accessible name.

## New

- [explore/screen-00-start] 1.4.3 12:02 AM: Text contrast is about 3.6:1 (#CAE1F9 on #006EE5); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-00-start] 1.4.3 12:16 AM: Text contrast is about 3.6:1 (#CAE1F9 on #006EE5); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-00-start] 1.4.3 12:18 AM: Text contrast is about 3.6:1 (#CBE2F9 on #006EE5); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-00-start] 2.1.1 67 Northgate Station Roosevelt Station 10min Scheduled 12:00: Pressing Tab cycles through the screen without ever reaching this control, so keyboard and switch users cannot activate it.

## Unchanged

- [explore/screen-00-start] 1.4.3 11:52 PM: Text contrast is about 3.6:1 (#CBE2F9 on #006EE5); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-00-start] 1.4.3 12:00 AM: Text contrast is about 3.6:1 (#CAE1F9 on #006EE5); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-00-start] 1.4.3 12:03 AM: Text contrast is about 3.6:1 (#CBE1F9 on #006EE5); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-00-start] 2.1.1 Show later arrivals: Pressing Tab cycles through the screen without ever reaching this control, so keyboard and switch users cannot activate it.
- [explore/screen-00-start] 2.4.6 Add star to route: 3 controls are announced as 'Add star to route'. If they do different things, screen-reader users cannot tell them apart.
- [explore/screen-00-start] 2.4.6 Show later arrivals: 3 controls are announced as 'Show later arrivals'. If they do different things, screen-reader users cannot tell them apart.
- [explore/screen-00-start] android-touch-target Show later arrivals: Target is 44x66dp, under the 48dp Android minimum.
- [explore/screen-01-67-northgate-station-roosevelt] 1.4.3 12:31 AM: Text contrast is about 3.6:1 (#CDE5CA on #108500); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-01-67-northgate-station-roosevelt] 1.4.3 12:33 AM: Text contrast is about 3.6:1 (#CDE5CA on #108500); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [explore/screen-01-67-northgate-station-roosevelt] 1.4.4 Northgate Station Roosevelt Station: Text box did not grow at 200% font size, so the text is likely clipped or truncated. Confirm on the device.
- [explore/screen-01-67-northgate-station-roosevelt] 2.4.6 Add star to route: 3 controls are announced as 'Add star to route'. If they do different things, screen-reader users cannot tell them apart.
- [explore/screen-01-67-northgate-station-roosevelt] 2.4.6 Show earlier arrivals: 3 controls are announced as 'Show earlier arrivals'. If they do different things, screen-reader users cannot tell them apart.
- [explore/screen-01-67-northgate-station-roosevelt] 2.5.5 Show earlier arrivals: Target is 34x66dp; below 44dp it is hard to hit for people with tremors or limited dexterity (Android guidance is 48dp).
