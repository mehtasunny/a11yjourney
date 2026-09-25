"""Capture a screen from a connected Android device with adb.

One command produces everything the checks need, side by side:

* ``NAME.xml``      the accessibility tree (``uiautomator dump``), with the
                    device's screen density written into it
* ``NAME.png``      a screenshot taken at the same moment (contrast checks)
* ``NAME.large.xml``the tree again at 200% font scale (resize-text check)
* ``NAME.json``     a small manifest: device, Android version, density, time

The font scale is restored afterwards, even if a step fails.

Screens in health, transit, and government apps often show personal data.
Captures stay on your machine; use test accounts where you can, and do not
commit captures of real records.
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass

Adb = Callable[[list[str]], bytes]

_REMOTE = "/sdcard/a11yjourney_dump.xml"
_DENSITY = re.compile(r"(Physical|Override) density:\s*(\d+)")


class CaptureError(RuntimeError):
    pass


def adb_runner(serial: str | None = None, adb: str = "adb") -> Adb:
    """Return a function that runs an adb command and returns its stdout."""

    def run(args: list[str]) -> bytes:
        cmd = [adb] + (["-s", serial] if serial else []) + args
        try:
            done = subprocess.run(cmd, capture_output=True, timeout=60, check=False)
        except FileNotFoundError as exc:
            raise CaptureError(
                f"'{adb}' not found. Install Android platform-tools and put adb on PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise CaptureError(f"adb timed out: {' '.join(args)}") from exc
        if done.returncode != 0:
            msg = (done.stderr or done.stdout).decode(errors="replace").strip()
            raise CaptureError(f"adb {' '.join(args)} failed: {msg}")
        return done.stdout

    return run


def read_density(adb: Adb) -> float:
    """Screen density as a scale factor (dpi / 160). Override wins over physical."""
    out = adb(["shell", "wm", "density"]).decode(errors="replace")
    found = dict(_DENSITY.findall(out))
    dpi = found.get("Override") or found.get("Physical")
    if not dpi:
        raise CaptureError(f"could not read screen density from: {out.strip()!r}")
    return int(dpi) / 160.0


def _prop(adb: Adb, name: str) -> str:
    return adb(["shell", "getprop", name]).decode(errors="replace").strip()


def dump_tree(adb: Adb, density: float, attempts: int = 5) -> str:
    """Dump the accessibility tree and stamp the density onto the root element."""
    last = ""
    for _ in range(attempts):
        # "2>&1" runs on the device, so uiautomator's error text comes back too
        out = adb(["shell", "uiautomator", "dump", _REMOTE, "2>&1"]).decode(errors="replace")
        if "dumped to" in out.lower():
            xml = adb(["shell", "cat", _REMOTE]).decode("utf-8", errors="replace")
            adb(["shell", "rm", "-f", _REMOTE])
            if "<hierarchy" not in xml:
                raise CaptureError("uiautomator produced no hierarchy")
            return re.sub(r"<hierarchy\b", f'<hierarchy density="{density:g}"', xml, count=1)
        last = out.strip()
        time.sleep(1.5)  # usually "could not get idle state" during animation
    raise CaptureError(
        f"uiautomator dump failed after {attempts} attempts: {last or 'no output'}. "
        "If the screen has ongoing animation or video, pause it and try again.")


def screenshot(adb: Adb) -> bytes:
    data = adb(["exec-out", "screencap", "-p"])
    if not data.startswith(b"\x89PNG"):
        raise CaptureError("screencap did not return a PNG")
    return data


@dataclass(frozen=True)
class Capture:
    tree: pathlib.Path
    screenshot: pathlib.Path
    large: pathlib.Path | None
    manifest: pathlib.Path


def capture(
    adb: Adb,
    out_dir: str,
    name: str,
    large_text: bool = True,
    settle: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
) -> Capture:
    """Capture the current screen (and, optionally, the same screen at 200% text)."""
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    density = read_density(adb)

    tree = out / f"{name}.xml"
    tree.write_text(dump_tree(adb, density), encoding="utf-8")
    shot = out / f"{name}.png"
    shot.write_bytes(screenshot(adb))

    large: pathlib.Path | None = None
    original = ""
    if large_text:
        original = adb(["shell", "settings", "get", "system", "font_scale"]).decode().strip()
        try:
            adb(["shell", "settings", "put", "system", "font_scale", "2.0"])
            sleep(settle)
            large = out / f"{name}.large.xml"
            large.write_text(dump_tree(adb, density), encoding="utf-8")
        finally:
            restore = original if original not in ("", "null") else "1.0"
            adb(["shell", "settings", "put", "system", "font_scale", restore])

    manifest = out / f"{name}.json"
    manifest.write_text(json.dumps({
        "name": name,
        "captured_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "device": _prop(adb, "ro.product.model"),
        "android": _prop(adb, "ro.build.version.release"),
        "density": density,
        "font_scale_default": original or None,
        "font_scale_large": "2.0" if large_text else None,
        "files": [p.name for p in (tree, shot, large) if p],
    }, indent=2) + "\n", encoding="utf-8")
    return Capture(tree, shot, large, manifest)


def siblings(tree_path: str) -> tuple[str | None, str | None]:
    """Find the screenshot and large-text capture that sit next to a tree dump."""
    p = pathlib.Path(tree_path)
    stem = p.name[:-len(".xml")] if p.name.endswith(".xml") else p.stem
    if stem.endswith(".large"):
        return None, None
    png = p.with_name(stem + ".png")
    large = p.with_name(stem + ".large.xml")
    return (str(png) if png.exists() else None, str(large) if large.exists() else None)
