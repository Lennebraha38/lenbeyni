#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kod verisi uretici - OpenRouter ucretsiz devlerle (Gemini kotasindan bagimsiz).
Anahtar: OPENROUTER_API_KEY ortam degiskeni veya openrouter_keys.txt (satir basina bir tane).
Modeller: ucretsiz (:free) devler rotasyonu; 3 arka arkaya hata -> model dusurulur.
Cikti: kod_verisi_ro.jsonl (soru/kod/test/kategori), her parti aninda dosyaya yazilir.
Kullanim: python3 veri_kod_ro.py [HEDEF] [cikti]
"""
import json, os, sys, re, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
import threading

ADET = int(sys.argv[1]) if len(sys.argv) > 1 else 800
CIKTI = sys.argv[2] if len(sys.argv) > 2 else "kod_verisi_ro.jsonl"
BAS = "https://openrouter.ai/api/v1/chat/completions"

MODELS = []
if os.environ.get("OPENROUTER_MODEL"):
    MODELS = os.environ["OPENROUTER_MODEL"].split(",")
if not MODELS:
    MODELS = [
        "cohere/north-mini-code:free",
        "poolside/laguna-s-2.1:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
    ]
DEMET = 12
GUNCELLEME = 30
PARALEL = min(int(os.environ.get("PARALEL", "6")), 10)

def anahtarlar():
    ks = []
    if os.environ.get("OPENROUTER_API_KEY"):
        ks = [os.environ["OPENROUTER_API_KEY"]]
    if os.path.exists("openrouter_keys.txt"):
        ks += [l.strip() for l in open("openrouter_keys.txt") if l.strip()]
    return ks or []

def norm(t):
    return " ".join(t.lower().split())

def mevcut_sorular():
    s = set()
    for yol in [CIKTI, "kod_verisi.jsonl"]:
        try:
            for satir in open(yol, encoding="utf-8"):
                j = json.loads(satir)
                s.add(norm(j.get("soru", "")))
        except FileNotFoundError:
            pass
    return s

ISTEK = """Sen Turkce konusan Python uzmani bir veri ureticisisin.
Bir kod asistanini egitmek icin %d YENI ve farkli ornek uret. Sadece su JSON don:
{"samples": [ {"soru": "gorev (Turkce, sart + ornek girdi/cikti)", "kod": "cozen python fonksiyonu, def ile baslar, aciklamasiz",
 "test": "dogrulayan 1-3 python assert satiri", "kategori": "kod_yaz | hata_ayikla | kod_acikla | kod_cevir | test_yaz"}, ... ]}
Cesitlilik: veri yapilari, dizeler, liste/sozluk, sayilar, tarih, dosya okuma, istatistik.
Kodlar calisir ve hatasiz OLSUN; testler koddan bagimsiz calissin (fonksiyon adi soruda belirli)."""

def istem():
    return ISTEK % DEMET

def cagir(anahtar, model):
    govde = {"model": model, "messages": [{"role": "user", "content": istem()}],
             "temperature": 0.8, "max_tokens": 4000}
    istek = urllib.request.Request(BAS, data=json.dumps(govde).encode(), headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + anahtar,
        "HTTP-Referer": "https://github.com/Lennebraha38/7-gun-kamp",
    }, method="POST")
    with urllib.request.urlopen(istek, timeout=240) as r:
        j = json.loads(r.read().decode())
    if "error" in j:
        raise RuntimeError("model hatasi: " + json.dumps(j.get("error"))[:120])
    c = j["choices"][0]["message"].get("content")
    return c or ""

def ayikla(t):
    if not isinstance(t, str):
        t = "{}"
    m = re.search(r"```json(.*?)```", t, re.S) or re.search(r"```(.*?)```", t, re.S) \
        or re.search(r"`(.*?)`", t, re.S)
    if m:
        t = m.group(1)
    m = re.search(r"\[.*\]", t, re.S)
    if m:
        return m.group(0)
    return t

def dogrula(o):
    if not isinstance(o, dict):
        return None
    soru = str(o.get("soru", "")).strip()
    kod = str(o.get("kod", "")).strip()
    test = str(o.get("test", "")).strip()
    k = str(o.get("kategori", "kod_yaz")).strip()
    if not (soru and kod and test) or not kod.startswith("def"):
        return None
    if "assert " not in test:
        return None
    return {"soru": soru, "kod": kod, "test": test, "kategori": k if k in (
        "kod_yaz", "hata_ayikla", "kod_acikla", "kod_cevir", "test_yaz") else "kod_yaz"}

def ana_akis():
    keys = anahtarlar()
    if not keys:
        print("HATA: OPENROUTER anahtari yok (OPENROUTER_API_KEY=sk-or-v1-... veya openrouter_keys.txt)")
        sys.exit(1)
    lok = threading.Lock()
    que = [(a, m) for a in keys for m in MODELS]
    idx = [0]
    atilan = set()
    hatali = {}
    sorular = mevcut_sorular()
    toplam = [len(sorular)]
    son_donem = [toplam[0] // GUNCELLEME]

    def sir():
        with lok:
            for _ in range(len(que)):
                i = idx[0]
                idx[0] += 1
                a, m = que[i % len(que)]
                if m not in atilan:
                    return a, m
            return None, None

    def isci(_):
        while toplam[0] < ADET:
            anahtar, model = sir()
            if model is None:
                print("  ! tum modeller dusuruldu, duruyorum")
                return
            try:
                metin = cagir(anahtar, model)
            except urllib.error.HTTPError as e:
                govde = e.read().decode("utf-8", "ignore")
                hatali[model] = hatali.get(model, 0) + 1
                if hatali[model] >= 3:
                    with lok:
                        atilan.add(model)
                    print("  [%s] 3 hatali (%d) -> cikarildi" % (model.split("/")[0][:12], e.code))
                    time.sleep(2)
                    continue
                print("  [%s] %d kota/hata -> geciliyor" % (model.split("/")[0][:12], e.code))
                time.sleep(8 if e.code == 429 else 3)
                continue
            except Exception as ex:
                hatali[model] = hatali.get(model, 0) + 1
                if hatali[model] >= 3:
                    with lok:
                        atilan.add(model)
                    print("  [%s] 3 hatali (%s) -> cikarildi" % (model.split("/")[0][:12], str(ex)[:60]))
                    time.sleep(2)
                    continue
                print("  [%s] hata: %s -> geciliyor" % (model.split("/")[0][:12], str(ex)[:60]))
                time.sleep(3)
                continue

            try:
                dizi = json.loads(ayikla(metin))
            except json.JSONDecodeError:
                dizi = []
            if isinstance(dizi, dict):
                dizi = dizi.get("samples", [])
            if not isinstance(dizi, list):
                dizi = []
            yeni_liste = []
            for o in dizi:
                d = dogrula(o)
                if d is None:
                    continue
                n = norm(d["soru"])
                with lok:
                    if n in sorular:
                        continue
                    sorular.add(n)
                    toplam[0] += 1
                yeni_liste.append(d)
            if yeni_liste:
                hatali[model] = 0
                with lok:
                    with open(CIKTI, "a", encoding="utf-8") as f:
                        for o in yeni_liste:
                            f.write(json.dumps(o, ensure_ascii=False) + "\n")
            with lok:
                d = toplam[0] // GUNCELLEME
                if d != son_donem[0]:
                    son_donem[0] = d
                    print("toplam=%d  (%s)" % (toplam[0], model.split("/")[0][:12]))
            if not yeni_liste:
                time.sleep(6)

    n_isci = max(2, min(len(que), PARALEL))
    print("ANAHTAR=%d  MODEL=%d  PARALEL=%d  HEDEF=%d  baslangic=%d" % (
        len(keys), len(MODELS), n_isci, ADET, toplam[0]))
    with ThreadPoolExecutor(max_workers=n_isci) as ex:
        list(ex.map(isci, range(n_isci)))
    print("BITTI: toplam=%d  ->  %s" % (toplam[0], CIKTI))

if __name__ == "__main__":
    ana_akis()