# OneBusAway audit summary

Baseline findings: 7
Patched findings: 7
Resolved by the patches: 2
New in patched build: 2
Unchanged: 5

## Resolved

- [explore/screen-00-start] 1.4.3 10:18 AM: Text contrast is about 3.6:1 (#CEE6CB on #108500); this passes only if the text is large-scale (WCAG's 18pt, or 14pt bold).
- [settings/settings] 4.1.2 View: View is actionable but has no accessible name.

## New

- [explore/screen-00-start] 2.1.1 40min 10:18 AM: Pressing Tab cycles through the screen without ever reaching this control, so keyboard and switch users cannot activate it.
- [explore/screen-00-start] 2.1.1 67 Northgate Station Roosevelt Station 40min 10:18 AM: Pressing Tab cycles through the screen without ever reaching this control, so keyboard and switch users cannot activate it.

## Unchanged

- [explore/screen-00-start] 2.5.5 View: Target is 34x52dp; below 44dp it is hard to hit for people with tremors or limited dexterity (Android guidance is 48dp).
- [explore/screen-00-start] 4.1.2 View: View is actionable but has no accessible name.
- [explore/screen-01-67-northgate-station-roosevelt] 4.1.2 View: View is actionable but has no accessible name.
- [screens/arrivals] 2.1.2 Close: Keyboard focus stays on this element when Tab is pressed again, so keyboard users cannot move past it.
- [screens/home] 2.1.2 Close: Keyboard focus stays on this element when Tab is pressed again, so keyboard users cannot move past it.
