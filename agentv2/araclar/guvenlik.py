"""Hesap/sifreleme: AES benzeri XOR tabanli kripto, hash, RNG."""
import hashlib, secrets, json, os

from typing import Optional, Tuple, List, Dict, Any, Callable, Union
def hashle(metin: str) -> str:
    return hashlib.sha256(metin.encode()).hexdigest()

def sifre(uzunluk: int = 16) -> str:
    abc = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return "".join(secrets.choice(abc) for _ in range(uzunluk))

def xor_sifrele(veri: str, anahtar: str) -> bytes:
    anahtar = hashlib.sha256(anahtar.encode()).digest()
    out = bytearray()
    for i, b in enumerate(veri.encode() if isinstance(veri, str) else veri):
        out.append(b ^ anahtar[i % len(anahtar)])
    return bytes(out)

def kutuphane_kaydet(ad: str, icerik: str, ulke: str = "tr") -> str:
    os.makedirs("araclar/kutuphane", exist_ok=True)
    yol = f"araclar/kutuphane/{ad}.py"
    with open(yol, "w") as f:
        f.write(icerik)
    return f"Kutuphane kaydedildi: {yol} ({len(icerik)}B)"