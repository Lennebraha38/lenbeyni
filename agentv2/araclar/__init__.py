"""LenBeyni Arac Yonlendirici. Tum araclar tek yerden.

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

def yonlendir(metin):
    """Tum [X]...[/X] komutlarini isler, sonuclari biriktirir."""
    sonuc = []

    for m in re.finditer(r"\[BELGE\]([^\[]*)\[/BELGE\]", metin, re.S):
        from .belgeler import belge
        yol = m.group(1).strip()
        sonuc.append(f"BELGE [{yol}]: " + belge(yol)[:2000])

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
        sonuc.append("LISTE:\n" + dosyalar(klasor, kalip)[:1200])

    if not sonuc:
        return ""
    return "\n\n".join(sonuc)