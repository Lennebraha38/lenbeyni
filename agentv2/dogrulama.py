"""ZenAI Bagimsiz Dogrulama — gercekler uzerinden strict dogruluk olcumu.

Otomatik-skorer'in uzunluk/yapi puanlarindan etkilenmeden, dogru/yanlis
bazli net sayi verir. Kullanim:
  python3 dogrulama.py                 # 40 soru (varsayilan model)
  python3 dogrulama.py --adet 10       # ilk 10
  python3 dogrulama.py --kalan-bekle   # rate-limit bekle, surekli dene
  ZIRVE_MODEL=openai/gpt-4o-mini:free python3 dogrulama.py   # model override
"""
import os, sys, json, time, argparse

sys.path.insert(0, os.path.dirname(__file__))

from model_routing import model_sec, model_fallback, DEFAULT_MODEL
from otomatik_skorer import puan_strict
from dogrulama_seti import INDEPENDENT

KONULAR = sorted({k for k, _, _ in INDEPENDENT})

STRICT_SISTEM = (
    "Turkce soru sorulacak. Cevabin KISA ve NET olsun: tek sayi, tek kelime "
    "veya tek kisa ifade. Aciklama/gerekce yazma. Emin degilsen 'Bilmiyorum' de."
)


def tek_dogrula(soru, model, key):
    import requests
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", json={
            "model": model,
            "messages": [
                {"role": "system", "content": STRICT_SISTEM},
                {"role": "user", "content": soru},
            ],
            "max_tokens": 40, "temperature": 0.0,
        }, headers={"Authorization": "Bearer " + key}, timeout=90)
    except Exception as e:
        return f"[HATA: {e}]", model
    if r.status_code == 200:
        c = r.json()["choices"][0]["message"].get("content") or ""
        if isinstance(c, list):
            c = " ".join(p.get("text", "") for p in c if isinstance(p, dict))
        return c[:300], model
    return f"[HTTP {r.status_code}]", model


def dogrula(adet=None, kalan_bekle=False):
    key = os.environ.get("OPENROUTER_KEY", "")
    if not key:
        print("OPENROUTER_KEY yok.")
        return
    model = os.environ.get("ZIRVE_MODEL", "").strip() or DEFAULT_MODEL
    sorular = INDEPENDENT[:adet] if adet else INDEPENDENT
    sonuclar = []
    dogru = 0

    print(f"\n{'='*70}")
    print(f"  BAGIMSIZ DOGRULAMA — {len(sorular)} soru | model: {model}")
    print(f"  Strict eslestirme (dogru/yanlis) — uzunluk/yapi puani YOK")
    print(f"{'='*70}\n")

    for i, (konu, soru, kabul) in enumerate(sorular, 1):
        cevap, kullanilan = tek_dogrula(soru, model, key)
        if cevap.startswith("[HTTP 429]") and kalan_bekle:
            print(f"  [rate-limit] 60sn bekleniyor...")
            time.sleep(60)
            cevap, kullanilan = tek_dogrula(soru, model, key)
        if cevap.startswith("[HTTP 4") or cevap.startswith("[HATA"):
            for yedek in model_fallback(model):
                cevap2, kullanilan = tek_dogrula(soru, yedek, key)
                if not cevap2.startswith("[HTTP") and not cevap2.startswith("[HATA"):
                    cevap, kullanilan = cevap2, yedek
                    break
        p, not_ = puan_strict(cevap, kabul)
        if p == 1.0:
            dogru += 1
        sonuclar.append({"konu": konu, "soru": soru, "cevap": cevap,
                         "kabul": kabul, "puan": p, "not": not_, "model": kullanilan})
        isaret = "OK" if p == 1.0 else "XX"
        print(f"  [{isaret}] {konu:10s} {cevap[:45]:45s} -> {not_[:40]}")
        time.sleep(1.5)

    genel = round(dogru / len(sorular) * 100, 1)
    print(f"\n{'='*70}")
    print(f"  SONUC: {dogru}/{len(sorular)} dogru = %{genel}")
    konu_ozet = {}
    for s in sonuclar:
        konu_ozet.setdefault(s["konu"], []).append(s["puan"])
    for k in sorted(konu_ozet):
        puanlar = konu_ozet[k]
        print(f"    {k:12s} {sum(puanlar)}/{len(puanlar)}")
    print(f"{'='*70}")

    # Kaydet (gitignore'li kayit/)
    dizin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kayit")
    os.makedirs(dizin, exist_ok=True)
    with open(os.path.join(dizin, "dogrulama.json"), "w") as f:
        json.dump({"genel": genel, "model": model, "sonuclar": sonuclar},
                  f, ensure_ascii=False, indent=1)
    print(f"  Kaydedildi: kayit/dogrulama.json\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Bagimsiz dogrulama")
    p.add_argument("--adet", type=int, default=None)
    p.add_argument("--kalan-bekle", action="store_true")
    args = p.parse_args()
    dogrula(adet=args.adet, kalan_bekle=args.kalan_bekle)