# Real Jetpack Compose captures

Captured by CI in [a11yjourney-compose](https://github.com/mehtasunny/a11yjourney-compose)
from its demo app on an Android 14 emulator (320x640, density 1.0) with
`a11yjourney capture`. The demo shows no personal data.

They are regression fixtures for how Compose exposes its accessibility tree,
which differs from classic Views:

- A button is a clickable `View` whose role sits on an empty child `Button` node,
  and whose label is a child `TextView`.
- A text field's label is a child `TextView` of the `EditText`.
- A `ScrollView` is only marked scrollable when its content overflows.

The first run of A11yJourney 0.2.0 on these captures reported 20 conformance
findings, all false positives caused by those differences. They are fixed, and
`tests/test_compose_captures.py` keeps them fixed while checking that real
defects in the same trees are still found.
