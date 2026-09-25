"""Shared helpers for building small accessibility trees and screenshots."""
from __future__ import annotations

from typing import Any


def tree(nodes: list[dict[str, Any]], density: float | None = 3.0,
         width: int = 1080, height: int = 2160) -> str:
    """Build uiautomator-style XML. Each node dict may hold: cls, text, desc, rid,
    clickable, enabled, scrollable, bounds (x1, y1, x2, y2), children."""

    def one(n: dict[str, Any]) -> str:
        x1, y1, x2, y2 = n["bounds"]
        attrs = {
            "text": n.get("text", ""),
            "resource-id": f"org.example:id/{n['rid']}" if n.get("rid") else "",
            "class": "android.widget." + n.get("cls", "TextView"),
            "content-desc": n.get("desc", ""),
            "clickable": "true" if n.get("clickable") else "false",
            "enabled": "false" if n.get("enabled") is False else "true",
            "focusable": "true",
            "scrollable": "true" if n.get("scrollable") else "false",
            "bounds": f"[{x1},{y1}][{x2},{y2}]",
        }
        a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        kids = "".join(one(c) for c in n.get("children", []))
        return f"<node {a}>{kids}</node>"

    dens = f' density="{density}"' if density else ""
    body = "".join(one(n) for n in nodes)
    return (f'<?xml version="1.0" encoding="UTF-8"?><hierarchy rotation="0"{dens}>'
            f'<node class="android.widget.FrameLayout" bounds="[0,0][{width},{height}]">'
            f"{body}</node></hierarchy>")
