import requests, json, sys, os, re, time, hashlib
from urllib.parse import quote_plus, unquote

OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "")
MEGA_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
PLAN_MODEL = "cohere/north-mini-code:free"
BASLIK = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36"}
BELLEK = os.path.expanduser("~/.lenbeyni_bellek.json")

def llm(mesajlar, model=MEGA_MODEL, max_tokens=4096, temperature=0.7, deneme=1):
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", json={
            "model": model, "messages": mesajlar,
            "temperature": temperature, "max_tokens": max_tokens
        }, headers={"Authorization": f"Bearer {OPENROUTER_KEY}"}, timeout=90)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return None
    except Exception:
        return None

def ara(sorgu):
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

def site(sayfa, maxlen=3500):
    if not sayfa.startswith("http"): sayfa = "https://" + sayfa
    try:
        r = requests.get(sayfa, timeout=20, headers=BASLIK, allow_redirects=True)
        metin = re.sub(r"<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<footer.*?</footer>", "", r.text, flags=re.S)
        metin = re.sub(r"<[^>]+>", " ", metin)
        metin = re.sub(r"&[a-z]+;", " ", metin)
        metin = re.sub(r"\s+", " ", metin).strip()
        return f"[{r.status_code}] {r.url}\n" + metin[:maxlen]
    except Exception as e:
        return ""

# ============ 1) BELLEK (OpenClaw/LocalRAG fikri: projeleri hatirlama) ============
def bellek_yukle():
    try:
        with open(BELLEK) as f: return json.load(f)
    except Exception: return {}

def bellek_kaydet(kayit):
    b = bellek_yukle()
    b.update(kayit)
    try:
        with open(BELLEK, "w") as f: json.dump(b, f, ensure_ascii=False, indent=1)
    except Exception: pass

def bellek_olustur(metin, anahtar):
    ozet = llm([{"role":"system","content":"Bu metni 3 maddede ozetle, Turkce."},{"role":"user","content":metin[:4000]}], max_tokens=400)
    bellek_kaydet({anahtar: ozet})
    return ozet

# ============ 2) DEEP RESEARCH (gpt-researcher dongusu) ============
def deep_research(soru, derinlik=3):
    rapor = []
    plan = llm([{"role":"system","content":(
        "Sen bir arastirma uzmanisin. Kullanici sorusunu en fazla 3 alt-basligina ayir. "
        "Format: satir basina [SORU] ...")},
        {"role":"user","content":soru}], model=PLAN_MODEL, max_tokens=300)
    if not plan: plan = f"[SORU] {soru}"
    alt_sorular = re.findall(r"\[SORU\]\s*(.+)", plan)
    if not alt_sorular: alt_sorular = [soru]

    for i, alt in enumerate(alt_sorular[:derinlik]):
        print(f"  [{i+1}/{min(len(alt_sorular),derinlik)}] arastiriliyor: {alt[:60]}...")
        arama = ara(alt or soru)
        linkler = re.findall(r"https?://[^\s|)]+", arama)
        icerikler = []
        for link in linkler[:3]:
            veri = site(link.split("?")[0])
            if len(veri) > 200:
                icerikler.append(f"--- {link} ---\n{veri[:2500]}")
        kaynak = "\n\n".join(icerikler) or arama
        if not kaynak: continue
        rapor.append(("ALT: " + alt, kaynak))

    if not rapor:
        return "Arastirma icin kaynak bulunamadi."

    bloc = "\n\n".join([alt + "\n" + kaynak[:3000] for alt, kaynak in rapor])
    butun = llm([{"role":"system","content":(
        "Sen derin arastirma raporu yazan LenBeyni'sin. Kaynaklardan yola cikarak kurumsal bir rapor yaz: "
        "1) Ozet 2) Bulgular (kaynakli) 3) Sonuc 4) Kaynaklar. Turkce, detayli.")},
        {"role":"user","content":f"SORU: {soru}\n\nTOPLANAN VERI:\n{bloc[:14000]}"}], max_tokens=5000)
    if not butun:
        butun = bloc[:2000]
    bellek_olustur(butun, "rapor_" + soru[:40])
    return butun

# ============ 3) AGENT DONGUSU (OpenCLI/browser-use fikri) ============
def ajan(soru):
    mesajlar = [{"role":"system","content":(
        "Sen LenBeyni ajanisin. Isi tamamlamak icin araclarini sirasiyla kullan: "
        "[ARAMA]soru[/ARAMA] web arar, [SITE]url[/SITE] site okur. "
        "Once isi yap, sonuclari bekle, sonuc yoksa daha fazla arac dene, sonunda kullaniciya Turkce cevap ver.")},
        {"role":"user","content":soru}]
    for tur in range(5):
        cevap = llm(mesajlar)
        if not cevap: return "Mega beyin yanit vermedi."
        emirler = re.findall(r"\[(ARAMA|SITE)\]([^\[]*)\[/\1\]", cevap)
        if not emirler:
            return cevap
        for emir, hedef in emirler:
            hedef = hedef.strip()
            sonuc = ara(hedef) if emir == "ARAMA" else site(hedef)
            mesajlar += [{"role":"assistant","content":cevap},
                         {"role":"user","content":f"[{emir} SONUCU]\n{sonuc or 'Bos'}\nDevam et."}]
    return "Araclar islendi ama sonuc okunamadi."

def bellekle_konus(soru):
    kayit = bellek_yukle()
    if not kayit: return None, None
    sorunun = soru.lower()
    ilgili = [(k,v) for k,v in kayit.items() if any(w in sorunun for w in re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]{4,}", k))]
    if not ilgili: return None, None
    baglam = "\n\n".join(f"{k}:\n{v}" for k,v in ilgili[:3])
    yanit = llm([{"role":"system","content":"Bellekteki bilgiyi kullan, eksikse guncel web ara. Turkce cevap ver."},
                 {"role":"user","content":f"SORU: {soru}\n\nBELLEK:\n{baglam}"}])
    return yanit, [k for k,_ in ilgili]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: python3 lenbeyni_zeka.py <soru> [mod: rapor|ajan|chat]")
        sys.exit(1)
    soru = " ".join(sys.argv[1:-1]) if len(sys.argv) > 2 else " ".join(sys.argv[1:])
    mod = sys.argv[-1] if len(sys.argv) > 2 and sys.argv[-1].lower() in ("rapor","ajan","chat","bellek") else "ajan"
    if mod == "rapor":
        print(deep_research(soru))
    elif mod == "bellek":
        yanit, hangi = bellekle_konus(soru)
        print((hangi or []) , "\n" , yanit)
        if not yanit: print("Bellek bos veya ilgisiz.")
    else:
        print(ajan(soru))