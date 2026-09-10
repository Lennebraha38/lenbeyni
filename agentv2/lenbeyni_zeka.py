"""LenBeyni - yerel + mega beyin. Ajan dongusu ve Deep Research."""
import os, re, sys

ENV_KEY = os.environ.get("OPENROUTER_KEY", "")
OPENROUTER_KEY = ENV_KEY

try:
    from araclar.arac_katmani import sayfa, web_ara, derin_arastirma, komut, Bellek
except ImportError:
    from agentv2.araclar.arac_katmani import sayfa, web_ara, derin_arastirma, komut, Bellek

MEGA_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
PLAN_MODEL = "cohere/north-mini-code:free"

def llm(mesajlar, model=MEGA_MODEL, max_tokens=4096):
    if not OPENROUTER_KEY:
        return None
    import requests
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", json={
        "model": model, "messages": mesajlar, "temperature": 0.7, "max_tokens": max_tokens
    }, headers={"Authorization": f"Bearer {OPENROUTER_KEY}"}, timeout=90)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    return None

def ajan(soru):
    belleklik = Bellek()
    ilgili = belleklik.ara(soru)
    baglam = "\n\n".join(f"{k}: {v}" for k, v in ilgili) if ilgili else ""
    mesajlar = [{"role": "system", "content": (
        "Sen LenBeyni ajanisin. Isi bitirmek icin araclarini kullan. "
        "[ARAMA]soru[/ARAMA] web arar, [SITE]url[/SITE] site okur, [KOMUT]cmd[/KOMUT] komut calistirir."
        + (f"\nHatirla (bellekten):\n{baglam}" if baglam else ""))},
        {"role": "user", "content": soru}]
    for tur in range(5):
        cevap = llm(mesajlar)
        if not cevap:
            return "Mega beyin yanit vermedi (OPENROUTER_KEY ayarla)."
        aramalar = re.findall(r"\[ARAMA\]([^\[]*)\[/ARAMA\]", cevap)
        siteler = re.findall(r"\[SITE\]([^\[]*)\[/SITE\]", cevap)
        komutlar = re.findall(r"\[KOMUT\]([^\[]*)\[/KOMUT\]", cevap)
        if not (aramalar or siteler or komutlar):
            if len(cevap) > 3000:
                belleklik.ozet_ata(llm, cevap, "yanit_" + re.sub(r"[^a-z0-9]", "_", soru.lower())[:40])
            return cevap
        sonuclar = []
        for s in aramalar: sonuclar.append("ARAMA: " + web_ara(s.strip()))
        for s in siteler: sonuclar.append("SITE: " + sayfa(s.strip()))
        for s in komutlar: sonuclar.append("KOMUT: " + komut(s.strip()))
        mesajlar += [{"role": "assistant", "content": cevap},
                     {"role": "user", "content": "ARAC SONUCLARI:\n" + "\n".join(sonuclar) + "\nDevam et ve kullaniciya cevap ver."}]
    return "Araclar islendi."

def rapor(soru):
    belleklik = Bellek()
    sonuc = derin_arastirma(llm, soru)
    belleklik.ozet_ata(llm, sonuc, "rapor_" + re.sub(r"[^a-z0-9]", "_", soru.lower())[:40])
    return sonuc

def chat(soru):
    return ajan(soru)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: python3 lenbeyni_zeka.py <soru> [ajan|rapor|chat]")
        sys.exit(1)
    if len(sys.argv) == 2:
        soru, mod = sys.argv[1], "ajan"
    else:
        soru, mod = " ".join(sys.argv[1:-1]), sys.argv[-1]
    if mod == "rapor":
        print(rapor(soru))
    elif mod == "chat":
        print(chat(soru))
    else:
        print(ajan(soru))