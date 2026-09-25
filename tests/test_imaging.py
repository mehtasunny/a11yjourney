import struct
import zlib

import pytest

from a11yjourney.imaging import ImageError, contrast, decode, encode


def _png(width, height, ctype, rows_filtered):
    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, ctype, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(b"".join(rows_filtered))) + chunk(b"IEND", b""))


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def _filter(ftype, line, prev, bpp):
    out = bytearray()
    for i, x in enumerate(line):
        left = line[i - bpp] if i >= bpp else 0
        up = prev[i]
        ul = prev[i - bpp] if i >= bpp else 0
        pred = [0, left, up, (left + up) >> 1, _paeth(left, up, ul)][ftype]
        out.append((x - pred) & 0xFF)
    return bytes([ftype]) + bytes(out)


def test_roundtrip_rgb():
    px = [(x * 10, y * 20, 7) for y in range(4) for x in range(5)]
    img = decode(encode(5, 4, px))
    assert (img.width, img.height) == (5, 4)
    assert img.pixel(3, 2) == (30, 40, 7)


@pytest.mark.parametrize("ftype", [0, 1, 2, 3, 4])
def test_every_filter_type_rgba(ftype):
    width, height, bpp = 6, 5, 4
    raw_rows = []
    for y in range(height):
        line = bytearray()
        for x in range(width):
            line += bytes((x * 40 % 256, y * 50 % 256, (x + y) * 13 % 256, 255))
        raw_rows.append(bytes(line))
    prev = bytes(width * bpp)
    filtered = []
    for line in raw_rows:
        filtered.append(_filter(ftype, line, prev, bpp))
        prev = line
    img = decode(_png(width, height, 6, filtered))
    assert img.pixel(4, 3) == (160, 150, 91)


def test_rejects_palette_png():
    data = _png(1, 1, 3, [b"\x00\x00"])
    with pytest.raises(ImageError):
        decode(data)


def test_wcag_contrast_reference_values():
    assert round(contrast((0, 0, 0), (255, 255, 255)), 1) == 21.0
    assert round(contrast((0x76, 0x76, 0x76), (255, 255, 255)), 2) == 4.54
    assert contrast((10, 10, 10), (10, 10, 10)) == 1.0
