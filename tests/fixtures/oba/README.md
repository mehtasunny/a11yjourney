# OneBusAway captures

Real captures of [OneBusAway for Android](https://github.com/OneBusAway/onebusaway-android)
(Apache License 2.0) on an Android 14 emulator, 320 x 640 dp, Puget Sound region with live data,
from the `oba-audit` workflow (October 2, 2026; OneBusAway commit `476cf18`). Only accessibility
trees and keyboard focus traces are kept, no screenshots.

- `dialog.*`: the "What's New?" dialog with a single Close button. Tab keeps focus on Close,
  which is expected for a one-button dialog. A11yJourney 0.3 reported it as a keyboard trap.
- `home.*`: the home screen tree while a dialog opened during the keyboard walk, so focus sat on a
  control that is not in the captured tree. 0.3 reported a keyboard trap.
- `arrivals.*`: stop arrivals with a live countdown. The label changed ("48min" to "40min")
  between the tree capture and the Tab walk, and 0.3 reported the row and pill as unreachable.
  The same tree has two disabled, non-focusable views beside the arrival pills that 0.3 reported
  as unnamed with small targets.
- `settings-published.xml`, `settings-fixed.xml`: Settings on the published app (a switch that is
  a separate, unnamed focus stop) and with the proposed fix (one checkable row). The published
  tree must still be flagged; the fixed one must not.
