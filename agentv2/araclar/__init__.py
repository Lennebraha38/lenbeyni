"""ZenAI Arac Yonlendirici. Tum araclar tek yerden.

Komut formati:
  [BELGE]dosya_yolu[/BELGE]     - PDF/DOCX/CSV/JSON oku
  [RSS]kategori[/RSS]            - haber akisi (teknoloji/bilim/genel)
  [HAVA]lat,lon[/HAVA]           - hava (koordinat)
  [PYTHON]kod[/PYTHON]           - python calistir
  [BASH]komut[/BASH]             - bash calistir
  [SISTEM]ozet[/SISTEM]          - sistem bilgisi
  [GITHUB]sorgu[/GITHUB]         - github ara
  [SIFRELE]metin[/SIFRELE]       - hash uret
  [SIFRE]10[/SIFRE]              - sifre uret
  [LISTE]klasor,*.py[/LISTE]     - dosya listele
"""
import os, re
from typing import Optional, Callable, List

__all__ = ["yonlendir", "_izinli_yol", "_gorsel_isle", "_gorsel_dosya"]

try:
    from .guvenlik import yorl_guvenli
except Exception:
    try:
        from agentv2.guvenlik import yorl_guvenli
    except Exception:
        yorl_guvenli = lambda p: p

def _izinli_yol(yol: str) -> Optional[str]:
    guvenli = yorl_guvenli(yol)
    return guvenli if guvenli else None

def yonlendir(metin: str) -> str:
    """Tum [X]...[/X] komutlarini isler, sonuclari biriktirir."""
    sonuc = []

    for m in re.finditer(r"\[BELGE\]([^\[]*)\[/BELGE\]", metin, re.S):
        from .belgeler import belge
        yol = m.group(1).strip()
        guvenli = _izinli_yol(yol)
        if not guvenli:
            sonuc.append(f"BELGE [{yol}]: [GUVENLIK Bloklandi: izin verilmeyen yol]")
            continue
        sonuc.append(f"BELGE [{guvenli}]: " + belge(guvenli)[:2000])

    for m in re.finditer(r"\[PYTHON\]([^\[]*)\[/PYTHON\]", metin, re.S):
        from .kod_sandbox import python_kod
        sonuc.append("PYTHON:\n" + python_kod(m.group(1))[:2000])

    for m in re.finditer(r"\[BASH\]([^\[]*)\[/BASH\]", metin, re.S):
        from .kod_sandbox import bash_kod
        sonuc.append("BASH:\n" + bash_kod(m.group(1))[:2000])

    for m in re.finditer(r"\[SISTEM\]([^\[]*)\[/SISTEM\]", metin, re.S):
        from .sistem import sistem_bilgi, disk
        sonuc.append("SISTEM:\n" + sistem_bilgi() + "\n" + disk())

    for m in re.finditer(r"\[GITHUB\]([^\[]*)\[/GITHUB\]", metin, re.S):
        from .github import gh
        sonuc.append("GITHUB:\n" + gh(m.group(1).strip())[:1200])

    for m in re.finditer(r"\[SIFRELE\]([^\[]*)\[/SIFRELE\]", metin, re.S):
        from .guvenlik import hashle
        sonuc.append("HASH: " + hashle(m.group(1).strip()))

    for m in re.finditer(r"\[SIFRE\](\d*)\[/SIFRE\]", metin, re.S):
        from .guvenlik import sifre
        n = int(m.group(1) or 16)
        sonuc.append("SIFRE: " + sifre(n))

    for m in re.finditer(r"\[RSS\]([^\[]*)\[/RSS\]", metin, re.S):
        from .haberler import rss
        k = m.group(1).strip().lower()
        akis = {"teknoloji": "https://www.engadget.com/rss.xml",
                "bilim": "https://arstechnica.com/science/feed/",
                "genel": "https://www.bbc.com/turkce/sondakika/index.xml"}.get(k, "https://www.engadget.com/rss.xml")
        sonuc.append("RSS:\n" + rss([akis])[:1500])

    for m in re.finditer(r"\[LISTE\]([^\[]*)\[/LISTE\]", metin, re.S):
        from .sistem import dosyalar
        par = m.group(1).strip().split(",")
        klasor, kalip = par[0].strip(), (par[1].strip() if len(par) > 1 else "*")
        guvenli = _izinli_yol(klasor)
        if not guvenli:
            sonuc.append(f"LISTE: [GUVENLIK Bloklandi: izin verilmeyen yol]")
            continue
        sonuc.append("LISTE:\n" + dosyalar(guvenli, kalip)[:1200])

    for m in re.finditer(r"\[TARAYICI\]([^\[]*)\[/TARAYICI\]", metin, re.S):
        from .tarayici import otomatik
        par = m.group(1).strip().split(",")
        sonuc.append("TARAYICI:\n" + otomatik(par[:3])[:2000])

    for m in re.finditer(r"\[GORSEL\]\s*(\S+)\s*,\s*([^\[]*)\[/GORSEL\]", metin, re.S):
        from .tarayici import otomatik
        par = m.group(1).strip(), m.group(2).strip()
        sonuc.append("GORSEL:\n" + _gorsel_isle(par))

    for m in re.finditer(r"\[GORUN](\S+?)\[/GORUN]", metin, re.S):
        sonuc.append("GORUNTU:\n" + _gorsel_dosya(m.group(1).strip()))

    for m in re.finditer(r"\[CEVIR]([^\[]*)\[/CEVIR]", metin, re.S):
        from .ceviri import cevir
        sonuc.append("CEVIR: " + cevir(m.group(1).strip()))

    if not sonuc:
        return ""
    return "\n\n".join(sonuc)

__all__ = ["yonlendir", "_izinli_yol", "_gorsel_isle", "_gorsel_dosya"]

def _gorsel_isle(par: Tuple[str, str]) -> str:
    import os, sys
    try:
        from .gorsel import fraktal_png, svg_ureteci
    except Exception:
        return "[gorsel modulu yok]"
    if par[0] == "fraktal":
        try:
            boyut = int(par[1]) if par[1].strip().isdigit() else 128
        except Exception:
            boyut = 128
        return "Gorsel: " + fraktal_png(boyut, 30, "/tmp/lb_fraktal.png")
    return "Gorsel: " + fraktal_png(128, 30, "/tmp/lb_svg.png")

def _gorsel_dosya(yol: str) -> str:
    try:
        if not os.path.exists(yol):
            return f"{yol} dosya yok"
        from .multimodal import gorsel_anla
        return gorsel_anla(None, yol)[:2000]
    except Exception as e:
        return f"[gorsel dosya hata: {e}]"