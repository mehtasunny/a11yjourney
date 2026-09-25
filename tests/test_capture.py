import json

import pytest

from a11yjourney.capture import CaptureError, capture, read_density, siblings
from a11yjourney.imaging import encode
from a11yjourney.model import load

DUMP = ('<?xml version="1.0" encoding="UTF-8"?><hierarchy rotation="0">'
        '<node class="android.widget.FrameLayout" bounds="[0,0][1080,2400]">'
        '<node class="android.widget.TextView" text="Hello" bounds="[40,100][600,{h}]"/>'
        '</node></hierarchy>')


class FakeAdb:
    def __init__(self, fail_large=False):
        self.scale = "1.15"
        self.calls = []
        self.fail_large = fail_large
        self.png = encode(2, 2, [(255, 255, 255)] * 4)

    def __call__(self, args):
        self.calls.append(args)
        cmd = " ".join(args)
        if cmd == "shell wm density":
            return b"Physical density: 480\nOverride density: 420\n"
        if cmd.startswith("shell uiautomator dump"):
            if self.fail_large and self.scale == "2.0":
                raise CaptureError("device went to sleep")
            return b"UI hierchary dumped to: /sdcard/a11yjourney_dump.xml\n"
        if cmd.startswith("shell cat"):
            h = 160 if self.scale != "2.0" else 260
            return DUMP.format(h=h).encode()
        if cmd.startswith("shell rm"):
            return b""
        if cmd == "exec-out screencap -p":
            return self.png
        if cmd == "shell settings get system font_scale":
            return self.scale.encode()
        if cmd.startswith("shell settings put system font_scale"):
            self.scale = args[-1]
            return b""
        if cmd.startswith("shell getprop"):
            return b"Pixel 8\n" if "model" in cmd else b"15\n"
        raise AssertionError(f"unexpected adb call: {cmd}")


def test_density_prefers_override():
    assert read_density(FakeAdb()) == 420 / 160


def test_capture_writes_all_files_and_restores_font_scale(tmp_path):
    adb = FakeAdb()
    c = capture(adb, str(tmp_path), "home", sleep=lambda _s: None)
    assert adb.scale == "1.15"
    screen = load(str(c.tree))
    assert screen.density_known and screen.density == pytest.approx(2.625)
    assert c.large and load(str(c.large)).nodes[1].bounds[3] == 260
    manifest = json.loads(c.manifest.read_text())
    assert manifest["device"] == "Pixel 8" and manifest["android"] == "15"
    assert siblings(str(c.tree)) == (str(c.screenshot), str(c.large))


def test_font_scale_restored_even_when_large_pass_fails(tmp_path):
    adb = FakeAdb(fail_large=True)
    with pytest.raises(CaptureError):
        capture(adb, str(tmp_path), "home", sleep=lambda _s: None)
    assert adb.scale == "1.15"
