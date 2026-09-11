"""ZenAI Arac Katmani.

GitHub acik kaynak ekolojisinden ilhamla:
- browser-use   -> Tarayici otomasyonu (Selenium/Playwright yerine hafif HTTP tabanli)
- gpt-researcher -> Derin arastirma dongusu
- OpenCLI        -> Komut satiri araclari (curl, grep, python)
- OpenClaw       -> Kanallar (telegram benzeri mesaj raporlama)
- LocalRAG       -> Bellek dosyasi (JSON vektorsuz benzerlik)

Hepsi bagimsiz calisir, mega beyin bu katmani cagirir.
"""
import requests, re, os, json, subprocess, tempfile
from urllib.parse import quote_plus, unquote

try:
    from .guvenlik import url_guvenli, komut_tehlikeli
except Exception:
    try:
        from agentv2.guvenlik import url_guvenli, komut_tehlikeli
    except Exception:
        url_guvenli = lambda u: True
        komut_tehlikeli = lambda c: False

BASLIK = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36"}

# ---------- browser-use: tarayici / site ----------
def sayfa(url, maxlen=4000):
    if not url.startswith("http"): url = "https://" + url
    if not url_guvenli(url):
        return "[GUVENLIK Bloklandi: engellenen URL (ic ag/SSRF onleme)]"
    r = requests.get(url, timeout=20, headers=BASLIK, allow_redirects=True)
    metin = re.sub(r"<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<footer.*?</footer>|<header.*?</header>", "", r.text, flags=re.S)
    metin = re.sub(r"<[^>]+>", " ", metin)
    metin = re.sub(r"&[a-z]+;", " ", metin)
    metin = re.sub(r"\s+", " ", metin).strip()
    return f"[{r.status_code}] {r.url}\n" + metin[:maxlen]

# ---------- gpt-researcher: derin arastirma ----------
def derin_arastirma(llm, soru, derinlik=3):
    plan = llm([{"role":"system","content":"Soruyu max 3 alt-basliga ayir. Format: [SORU] ..."},
                {"role":"user","content":soru}], max_tokens=300)
    altlar = re.findall(r"\[SORU\]\s*(.+)", plan or "") or [soru]
    toplanan = []
    for alt in altlar[:derinlik]:
        arama = web_ara(alt)
        linkler = re.findall(r"https?://[^\s|)]+", arama)
        for link in linkler[:3]:
            veri = sayfa(link, 2500)
            if len(veri) > 200:
                toplanan.append(veri)
    kaynak = "\n\n".join(toplanan)
    rapor = llm([
        {"role":"system","content":"Kaynaklardan kurumsal rapor yaz: Ozet, Bulgular, Sonuc. Turkce."},
        {"role":"user","content":f"SORU: {soru}\n\nVERI:\n{kaynak[:14000]}"}], seviye="uzun")
    return rapor or kaynak[:1500]

def web_ara(sorgu):
    for motor in ["https://html.duckduckgo.com/html/?q=", "https://lite.duckduckgo.com/lite/?q="]:
        try:
            r = requests.get(motor + quote_plus(sorgu), timeout=20, headers=BASLIK)
            son = re.findall(r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r.text, flags=re.S)
            sn = re.findall(r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>', r.text, flags=re.S)
            cikti = []
            for i, (link, baslik_) in enumerate(son[:6]):
                m = re.search(r"uddg=([^&]+)", link)
                if m: link = unquote(m.group(1))
                ozet = re.sub(r"<[^>]+>", "", sn[i]).strip()[:180] if i < len(sn) else ""
                cikti.append(f"{i+1}. {re.sub(r'<[^>]+>', '', baslik_).strip()} | {link} | {ozet}")
            if cikti: return "\n".join(cikti)
        except Exception: continue
    return ""

# ---------- OpenCLI: komut calistirma ----------
def komut(emir, timeout=20):
    if komut_tehlikeli(emir):
        return "[GUVENLIK Bloklandi: tehlikeli komut kalibi]"
    try:
        r = subprocess.run(emir, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "")[-3000:] + (r.stderr or "")[-1000:]
    except Exception as e:
        return f"[Komut hatasi: {e}]"

# ---------- OpenClaw: mesaj raporlama dongusu ----------
def kanal_ozetle(llm, kanal_turu, mesajlar):
    return llm([
        {"role":"system","content":f"{kanal_turu} mesaj akisini ana basliklara odet. Turkce."},
        {"role":"user","content":mesajlar[:6000]}], max_tokens=1000)

# ---------- LocalRAG: dosya belleği ----------
try:
    from ..bellek_vektor import BellekVec
except Exception:
    try:
        from agentv2.bellek_vektor import BellekVec
    except Exception:
        from bellek_vektor import BellekVec

Bellek = BellekVec