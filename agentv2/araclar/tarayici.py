"""Tarayici otomasyonu (browser-use tarzi).
- Playwright kuruluysa: gercek tikla/yaz/ekran al.
- Degilse: hafif komut modu (xdg-open, curl, screenshot araclari).
Komut formatlari:
  [TARAYICI]ac,url[/TARAYICI]          site ac
  [TARAYICI]yaz,kutu,deger[/TARAYICI]   inputa yaz
  [TARAYICI]tikla,metin[/TARAYICI]      metinle dugme/eleman bul ve tikla
  [TARAYICI]ekran,yol.png[/TARAYICI]    ekran gorseli al
  [TARAYICI]soru,soru-metni[/TARAYICI]  sayfayi oku ve ozetle (LLM ile)
"""
import subprocess, os, sys

HAFIF = True   # Playwright yoksa True

from typing import Optional, Tuple, List, Dict, Any, Callable, Union
def _pw() -> Any:
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except Exception:
        return None

def otomatik(parcalar, llm: Optional[Callable] = None) -> str:
    islem = parcalar[0].strip().lower() if parcalar else ""
    hedef = parcalar[1].strip() if len(parcalar) > 1 else ""
    ek = parcalar[2].strip() if len(parcalar) > 2 else ""

    if islem == "ac" and hedef.startswith("http"):
        from agentv2.guvenlik import pinli_hedef
        if not pinli_hedef(hedef):
            return "[GUVENLIK Bloklandi: ic-alan/metin-disi hedef (SSRF)]"

    pw = _pw()
    if pw:
        try:
            return _playwright(pw, islem, hedef, ek)
        except Exception as e:
            return f"[Playwright hatasi, hafif moda gecildi: {e}]-> {_hafif(islem, hedef)}"

    if islem == "soru" and llm:
        return llm([
            {"role": "system", "content": "Sayfa icerigini ozetle, ana basliklari ver. Turkce."},
            {"role": "user", "content": hedef[:6000]}], max_tokens=2000) or "ozetleme yok"
    return _hafif(islem, hedef)

def _playwright(pw, islem: str, hedef: str, ek) -> str:
    with pw() as p:
        tar = p.chromium.launch(headless=True)
        sayfa = tar.new_page()
        if islem == "ac":
            sayfa.goto(hedef if hedef.startswith("http") else "https://" + hedef, timeout=20000)
            metin = sayfa.inner_text("body")[:4000]
            tar.close()
            return metin
        if islem == "yaz":
            sayfa.goto(hedef if hedef.startswith("http") else "https://" + hedef, timeout=20000)
            sayfa.fill("input, textarea", ek)
            tar.close()
            return f"{ek} yazildi"
        if islem == "tikla":
            sayfa.goto(hedef if hedef.startswith("http") else "https://" + hedef, timeout=20000)
            sayfa.get_by_text(ek, exact=False).first.click()
            metin = sayfa.inner_text("body")[:3000]
            tar.close()
            return metin
        if islem == "ekran":
            sayfa.goto(hedef if hedef.startswith("http") else "https://" + hedef, timeout=20000)
            sayfa.screenshot(path=ek or "ekran.png")
            tar.close()
            return f"Ekran: {ek or 'ekran.png'}"
        tar.close()
        return "[TARAYICI] bilinmeyen islem"

def _hafif(islem: str, hedef: str = "") -> str:
    if islem == "ac" and hedef.startswith("http"):
        try:
            from agentv2.guvenlik import pinli_hedef
            pinlu = pinli_hedef(hedef)
            if not pinlu:
                return "[GUVENLIK Bloklandi: ic-alan/metin-disi hedef (SSRF)]"
            gercek_url, host = pinlu
            komut = ["curl", "-sL", "-A", "Mozilla/5.0", "--max-time", "15", "-o", "/tmp/lb_sayfa.html"]
            if host:
                komut += ["-H", f"Host: {host}"]
            komut.append(gercek_url)
            r = subprocess.run(komut, timeout=20)
            if r.returncode == 0:
                import re
                h = open("/tmp/lb_sayfa.html", "r", errors="ignore").read()[:20000]
                metin = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>", " ", h)
                metin = re.sub(r"\s+", " ", metin).strip()
                return metin[:4000]
        except Exception as e:
            return f"[hafif tarayici: {e}]"
    if islem == "ekran":
        try:
            out = ek or "ekran.png"
            subprocess.run(["import", "-window", "root", out] if os.name != "nt" else ["true"], timeout=10)
            return f"Ekran: {out} (ImageMagick 'import' gerekir)"
        except Exception:
            return "[ekran hafif modda alinamadi; ImageMagick kur ya da Playwright kullan]"
    return ("[TARAYICI hafif mod] Cihazda Playwright yok. "
            "Kurulus: pip install playwright && playwright install chromium. "
            "Simdilik: 'ac' curl ile sayfa metni ceker, 'ekran' ImageMagick ister.")