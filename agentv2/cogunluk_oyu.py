from typing import Optional, Tuple, List, Dict, Any
"""Coklugun Oyu — ayni soruyu N kez sor, en sik cevabi sec.
Matematik/mantik/kod dogrulugunu istatistiksel olarak artirir.
Cok az extra token harcar (N=3 icin 3x, ama sure onde).

Kullanim:
  python3 cogunluk_oyu.py "soru"              # varsayilan 3 tekrar
  python3 cogunluk_oyu.py "soru" --tekrar 5    # 5 tekrar
  python3 cogunluk_oyu.py "soru" --model X     # model secimi
"""
import os, sys, json, re, time
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from zenai_zeka import llm, MEGA_MODEL

def cevap_ozet(cikti: str) -> str:
    """Cevaptan ozet cek: temel sonuc/anahtar kelime."""
    # Matematik icin: sayi cek
    sayilar = re.findall(r'[-+]?\d*\.?\d+', cikti)
    if sayilar:
        return "sayi:" + "|".join(sayilar[:5])
    # Mantik icin: Evet/Hayir
    if re.search(r'\b(evet|hayir|dogru|yanlis|olmaz|olur)\b', cikti, re.I):
        ilk = re.search(r'\b(evet|hayir|dogru|yanlis|olmaz|olur)\b', cikti, re.I)
        return "karar:" + ilk.group().lower()
    # Kod icin: fonksiyon adi
    fn = re.search(r'def (\w+)', cikti)
    if fn:
        return "fonk:" + fn.group(1)
    # Genel: ilk 100 karakter ozet
    return cikti[:100].replace("\n", " ")

def cogunluk(soru: str, tekrar: int = 3, model: Optional[str] = None) -> Dict[str, Any]:
    """Soruyu tekrar kez sor, en sik ozetli cevabi dondur."""
    model = model or MEGA_MODEL
    cevaplar = []
    ozetler = []
    
    for i in range(tekrar):
        t0 = time.time()
        mesajlar = [
            {"role": "system", "content": "Turkce, net ve dogru cevap ver. Kisa ve oz."},
            {"role": "user", "content": soru}
        ]
        c = llm(mesajlar, model=model, seviye="kisa", stream=False)
        sure = round(time.time() - t0, 1)
        if c:
            cevaplar.append({"cevap": c, "sure": sure, "tur": i+1})
            ozetler.append(cevap_ozet(c))
        else:
            cevaplar.append({"cevap": "[HATA]", "sure": sure, "tur": i+1})
            ozetler.append("hata")
    
    # Oylama: en sik ozeti bul
    sayac = Counter(ozetler)
    en_sik = sayac.most_common(1)[0][0]
    oyu = sayac[en_sik]
    
    # En sik ozete eslesen ilk cevabi sec
    kazanan = None
    for i, oz in enumerate(ozetler):
        if oz == en_sik:
            kazanan = cevaplar[i]
            break
    
    guven = round(oyu / len(cevaplar), 2)
    
    return {
        "soru": soru,
        "kazanan": kazanan["cevap"] if kazanan else cevaplar[0]["cevap"],
        "tekrar_sayisi": tekrar,
        "oy_dagilimi": dict(sayac),
        "guven": guven,
        "tum_cevaplar": cevaplar,
        "en_sik_ozet": en_sik
    }

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("soru")
    p.add_argument("--tekrar", type=int, default=3)
    p.add_argument("--model", default=None)
    args = p.parse_args()
    
    sonuc = cogunluk(args.soru, tekrar=args.tekrar, model=args.model)
    
    print(f"\n{'='*50}")
    print(f"  ÇOĞUNLUK OYU SONUCU")
    print(f"{'='*50}")
    print(f"  Soru: {sonuc['soru'][:60]}")
    print(f"  Güven: %{sonuc['guven']*100:.0f} ({sonuc['oy_dagilimi']})")
    print(f"  En sık: {sonuc['en_sik_ozet'][:60]}")
    print(f"\n--- Kazanan Cevap ---")
    print(sonuc['kazanan'][:500])
    print(f"\n--- Tüm Cevaplar ---")
    for c in sonuc['tum_cevaplar']:
        print(f"  [{c['tur']}] {c['sure']}sn: {c['cevap'][:80].replace(chr(10),' ')}")
