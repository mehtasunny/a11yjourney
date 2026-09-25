from a11yjourney import PROFILES, criterion


def test_wcag21_aa_excludes_22_only_and_aaa():
    p = PROFILES["wcag21-aa"]
    assert p.covers(criterion("4.1.2"))
    assert p.covers(criterion("1.4.11"))  # added in 2.1, level AA
    assert not p.covers(criterion("2.5.8"))  # added in 2.2
    assert not p.covers(criterion("2.5.5"))  # AAA
    assert not p.covers(criterion("android-touch-target"))


def test_wcag22_aa_includes_target_size_minimum():
    p = PROFILES["wcag22-aa"]
    assert p.covers(criterion("2.5.8"))
    assert not p.covers(criterion("2.5.5"))


def test_labels_are_explicit_about_version():
    assert criterion("2.5.8").label.endswith("added in WCAG 2.2")
    assert "Level AA" in criterion("1.4.3").label
