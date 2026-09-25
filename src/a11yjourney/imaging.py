"""Minimal PNG reading and writing, standard library only.

Enough to read what Android's ``screencap -p`` produces (8-bit, non-interlaced
RGB or RGBA, plus grayscale variants) and to write simple test fixtures. Kept
dependency-free so the core engine stays installable anywhere.
"""
from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

_SIG = b"\x89PNG\r\n\x1a\n"
_CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}  # gray, RGB, gray+alpha, RGBA

RGB = tuple[int, int, int]


class ImageError(ValueError):
    """Raised for PNG files this reader does not support."""


@dataclass(frozen=True)
class Image:
    width: int
    height: int
    rows: tuple[bytes, ...]  # packed RGB, 3 bytes per pixel

    def pixel(self, x: int, y: int) -> RGB:
        i = x * 3
        r = self.rows[y]
        return (r[i], r[i + 1], r[i + 2])

    def region(self, x1: int, y1: int, x2: int, y2: int) -> list[RGB]:
        """Pixels inside a rectangle, clipped to the image."""
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(self.width, x2), min(self.height, y2)
        out: list[RGB] = []
        for y in range(y1, y2):
            r = self.rows[y]
            for x in range(x1, x2):
                i = x * 3
                out.append((r[i], r[i + 1], r[i + 2]))
        return out


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _unfilter(raw: bytes, width: int, height: int, bpp: int) -> list[bytearray]:
    stride = width * bpp
    rows: list[bytearray] = []
    prev = bytearray(stride)
    pos = 0
    for _ in range(height):
        ftype = raw[pos]
        line = bytearray(raw[pos + 1: pos + 1 + stride])
        pos += 1 + stride
        if ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                upleft = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, prev[i], upleft)) & 0xFF
        elif ftype != 0:
            raise ImageError(f"unknown PNG filter type {ftype}")
        rows.append(line)
        prev = line
    return rows


def _to_rgb(line: bytearray, width: int, ctype: int) -> bytes:
    if ctype == 2:
        return bytes(line)
    out = bytearray(width * 3)
    if ctype == 6:  # drop alpha; screenshots are opaque
        out[0::3], out[1::3], out[2::3] = line[0::4], line[1::4], line[2::4]
    elif ctype == 0:
        out[0::3] = out[1::3] = out[2::3] = line
    else:  # 4: gray + alpha
        g = line[0::2]
        out[0::3] = out[1::3] = out[2::3] = g
    return bytes(out)


def decode(data: bytes) -> Image:
    """Decode PNG bytes into an :class:`Image`."""
    if not data.startswith(_SIG):
        raise ImageError("not a PNG file")
    pos, idat = len(_SIG), bytearray()
    width = height = depth = ctype = interlace = -1
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos: pos + 4])
        kind = data[pos + 4: pos + 8]
        chunk = data[pos + 8: pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"IDAT":
            idat += chunk
        elif kind == b"IEND":
            break
    if depth != 8 or ctype not in _CHANNELS or interlace != 0:
        raise ImageError(
            f"unsupported PNG (bit depth {depth}, color type {ctype}, interlace {interlace}); "
            "expected an 8-bit non-interlaced screenshot such as `adb exec-out screencap -p`"
        )
    bpp = _CHANNELS[ctype]
    rows = _unfilter(zlib.decompress(bytes(idat)), width, height, bpp)
    return Image(width, height, tuple(_to_rgb(r, width, ctype) for r in rows))


def read(path: str) -> Image:
    with open(path, "rb") as fh:
        return decode(fh.read())


def encode(width: int, height: int, pixels: list[RGB]) -> bytes:
    """Encode RGB pixels (row-major) as a PNG. Used for fixtures and tests."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for r, g, b in pixels[y * width: (y + 1) * width]:
            raw += bytes((r, g, b))

    def chunk(kind: bytes, body: bytes) -> bytes:
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (_SIG + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw)))
            + chunk(b"IEND", b""))


# --------------------------------------------------------------------------
# Color science (WCAG 2.x definitions)
# --------------------------------------------------------------------------

def _channel(c: int) -> float:
    s = c / 255.0
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def luminance(rgb: RGB) -> float:
    """WCAG relative luminance."""
    r, g, b = rgb
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast(a: RGB, b: RGB) -> float:
    """WCAG contrast ratio between two colors (1.0 to 21.0)."""
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)
