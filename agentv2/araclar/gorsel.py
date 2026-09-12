"""Gorsel: gercek calisan PNG uretici (saf python, zlib). SVG uretici."""
import struct, zlib

from typing import Optional, Tuple, List, Dict, Any, Callable, Union
def _png(genislik: int, yukseklik: int, piksel_verisi) -> bytes:
    def kismet(tip: str, veri: str) -> str:
        k = tip + veri
        return struct.pack(">I", len(veri)) + k + struct.pack(">I", zlib.crc32(k) & 0xffffffff)
    ustd = b""
    for y in range(yukseklik):
        ustd += b"\x00"
        satir = piksel_verisi[y * genislik * 3:(y + 1) * genislik * 3]
        ustd += satir
    return (b"\x89PNG\r\n\x1a\n"
            + kismet(b"IHDR", struct.pack(">IIBBBBB", genislik, yukseklik, 8, 2, 0, 0, 0))
            + kismet(b"IDAT", zlib.compress(ustd))
            + kismet(b"IEND", b""))

def fraktal_png(boyut: int = 128, max_it: int = 40, yol_: str = "fraktal.png") -> str:
    import math, os
    data = bytearray()
    for y in range(boyut):
        for x in range(boyut):
            zx = zy = 0.0
            cx = (x - boyut / 2) / (boyut / 4)
            cy = (y - boyut / 2) / (boyut / 4)
            c = 0
            while zx*zx + zy*zy < 4 and c < max_it:
                zx, zy = zx*zx - zy*zy + cx, 2*zx*zy + cy
                c += 1
            t = int((c / max_it) ** 0.5 * 255)
            data += bytes([t, max(0, 255 - 2*t), (t ^ 0x88) & 0xff])
    os.makedirs(os.path.dirname(yol_) or ".", exist_ok=True)
    with open(yol_, "wb") as f:
        f.write(_png(boyut, boyut, bytes(data)))
    return yol_

def svg_ureteci(baslik: str, renk: str = "#3b82f6", genislik: int = 400, yukseklik: int = 200) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{genislik}" height="{yukseklik}">'
            f'<rect width="100%" height="100%" fill="{renk}"/>'
            f'<text x="50%" y="50%" font-size="28" fill="white" text-anchor="middle" '
            f'dy=".3em" font-family="sans-serif">{baslik}</text></svg>')

def ikon(yazi: str, yol_: str = "ikon.svg") -> str:
    import os
    os.makedirs(os.path.dirname(yol_) or ".", exist_ok=True)
    with open(yol_, "w") as f:
        f.write(svg_ureteci(yazi[:8]))
    return yol_