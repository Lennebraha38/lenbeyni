"""Akil Motoru Dongu Testi — kaliteyi olcum dongusu ile artir.

Ayni soruyu birden fazla turda sorar, her turda:
  Tur 1: Dogrudan soru (baseline)
  Tur 2: CoT (adim adim dusuncenin eklenmesi)
  Tur 3: Self-correction (kendi cevabini kontrol et)tur 4: CoT + self-correction birlesimi
  Tur 5: Meclis oylama (3 cevap uretilip en iyisi secilmesi)Her turda otomatik skorlanir, hangi tur en iyi sonucu verir olculur.
Calistirilmaz: rate-limit cozulene kadar bekler. Mock veriyle test edilir.

Kullanim: python3 akil_dongu_test.py <soru> [canli]   # canli=rate-limit varsa calisir
"""
import os, sys, json, time, re
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))

# ── Mock LLM: rate-limit olmadan test ────────────────────────
class MockLLM:
    """Rate-limit olmadan test icin mock model."""
    def __init__(self, cevap_sablonu):
        self.cevap = cevap_sablonu
        self.cagri = 0
    def sor(self, mesajlar, **kw):
        self.cagri += 1
        son = mesajlar[-1]["content"] if mesajlar else ""
        # Self-correction istenirse duzeltilmis versiyon dondur
        if "kontrol et" in son.lower() or "duzelt" in son.lower():
            return self.cevap + "\n\nSelf-correction: Hatalar duzeltildi, kalite artti."
        return self.cevap

# ── Dongu testi asil mantigi ──────────────────────────────────
def dongu_testi(soru, mock_cevap=None, canli=False):
    """Dongu testi: ayni soruyu farkli tekniklerle test et, karsilastir."""
    if canli:
        # Canli: gercek LLM kullan (rate-limit gerekli)
        try:
            from lenbeyni_zeka import llm, OPENROUTER_KEY
            if not OPENROUTER_KEY:
                print("OPENROUTER_KEY ayarli degil, mock gecisi")
                canli = False
        except ImportError:
            canli = False
    
    if not canli:
        mock_cevap = mock_cevap or (
            "Turkce cevap: Bu sorunun cevabi以下是有用的知"
            "\n\n- Adim 1: Soruyu analiz et"
            "\n- Adim 2: Bilgiyi hatirla"
            "\n- Adim 3: Cevabi yaz"
            "\n- Sonuc: Dogru"
        )
        llm = MockLLM(mock_cevap).sor
    else:
        from lenbeyni_zeka import llm
    
    from otomatik_skorer import puanla, puan_genel, puan_matematik, puan_kod
    
    sonuclar = []
    
    # Tur 1: Dogrudan cevap (baseline)
    mesaj1 = [{"role": "user", "content": soru}]
    t0 = time.time()
    cevap1 = llm(mesaj1) if canli else mock_cevap
    tur1_skor, tur1_not = puan_genel(cevap1)
    sonuclar.append({
        "tur": "dogrudan", "sure": round(time.time()-t0,1),
        "kelime": len(cevap1.split()), "puan": round(tur1_skor,2), "not": tur1_not
    })
    
    # Tur 2: CoT eklenmesi
    cot_prompt = (
        "ONCE DUSUN: Bu soruyu adim adim analiz et. "
        "Ilk olarak soruyu parcala, sonra her adimi goster, "
        "en sonda KAPSAMLI cevabi yaz."
    )
    mesaj2 = [{"role": "user", "content": cot_prompt + "\n\n" + soru}]
    t0 = time.time()
    cevap2 = llm(mesaj2) if canli else mock_cevap + "\n\nCoT dusuncesi: " + cot_prompt
    tur2_skor, tur2_not = puan_genel(cevap2)
    sonuclar.append({
        "tur": "cot", "sure": round(time.time()-t0,1),
        "kelime": len(cevap2.split()), "puan": round(tur2_skor,2), "not": tur2_not
    })
    
    # Tur 3: Self-correction
    mesaj3 = [
        {"role": "user", "content": soru},
        {"role": "assistant", "content": cevap1},
        {"role": "user", "content": (
            "Kendi cevabini kontrol et: eksik bilgi, mantik hatasi veya "
            "yarim kalmis cumle var mi? Varsa kisa duzeltmeleri yap, "
            "sonra tam cevabi ver."
        )}
    ]
    t0 = time.time()
    cevap3 = llm(mesaj3) if canli else mock_cevap + "\n\nSelf-correction sonrasi: Eksikler tamamlandi, kalite artti."
    tur3_skor, tur3_not = puan_genel(cevap3)
    sonuclar.append({
        "tur": "self_correction", "sure": round(time.time()-t0,1),
        "kelime": len(cevap3.split()), "puan": round(tur3_skor,2), "not": tur3_not
    })
    
    # Tur 4: CoT + self-correction kombinasyonu
    mesaj4 = [{"role": "user", "content": cot_prompt + "\n\n" + soru}]
    cevap4_baslangic = llm(mesaj4) if canli else cevap2
    mesaj4_devam = mesaj4 + [
        {"role": "assistant", "content": cevap4_baslangic},
        {"role": "user", "content": "Kendi cevabini kontrol et, eksikleri duzelt."}
    ]
    t0 = time.time()
    cevap4 = llm(mesaj4_devam) if canli else cevap4_baslangic + "\n\nKombinasyon: CoT + SC ile kalite en ust duzeyde."
    tur4_skor, tur4_not = puan_genel(cevap4)
    sonuclar.append({
        "tur": "cot+self_correction", "sure": round(time.time()-t0,1),
        "kelime": len(cevap4.split()), "puan": round(tur4_skor,2), "not": tur4_not
    })
    
    # Tur 5: Meclis oylama (3 cevap uretilip en iyi secme)
    cevaplar_meclis = [cevap1, cevap2, cevap3]
    meclis_skorlar = [puan_genel(c)[0] for c in cevaplar_meclis]
    kazanan_idx = max(range(3), key=lambda i: meclis_skorlar[i])
    tur5_skor = meclis_skorlar[kazanan_idx]
    sonuclar.append({
        "tur": "meclis_oylama", "sure": 0, "kelime": len(cevaplar_meclis[kazanan_idx].split()),
        "puan": round(tur5_skor,2), "kazanan": ["baseline","cot","self_correction"][kazanan_idx]
    })
    
    return sonuclar, soru

def rapor_olustur(sonuclar, soru):
    """Dongu testi sonuclarini raporlayin."""
    print(f"\n{'='*60}")
    print(f"  DONGU TEST RAPORU")
    print(f"{'='*60}")
    print(f"  Soru: {soru[:60]}")
    print(f"{'='*60}")
    
    en_iyi = max(sonuclar, key=lambda x: x["puan"])
    en_kotu = min(sonuclar, key=lambda x: x["puan"])
    
    for s in sonuclar:
        tur = s["tur"]
        p = s["puan"]
        kl = s["kelime"]
        isaret = "*" if s == en_iyi else "~" if s == en_kotu else "+"
        extra = f" (kazanan: {s['kazanan']})" if "kazanan" in s else ""
        print(f"  [{isaret}] {tur:30s} → {p*100:5.1f}/100  {kl:5d} kelime{extra}")
    
    print(f"\n  Kazanan tur: {en_iyi['tur']} ({en_iyi['puan']*100:.1f}/100)")
    print(f"  Basari artisi: {en_kotu['puan']*100:.1f} → {en_iyi['puan']*100:.1f} "
          f"({(en_iyi['puan']-en_kotu['puan'])*100:+.1f} puan)")
    
    # Istatistikler
    puanlar = [s["puan"] for s in sonuclar]
    kelime = [s["kelime"] for s in sonuclar]
    print(f"\n  Ort puan: {sum(puanlar)/len(puanlar)*100:.1f}/100")
    print(f"  Ort kelime: {sum(kelime)//len(kelime)}")
    print(f"  Std sapma: {(sum((p-sum(puanlar)/len(puanlar))**2 for p in puanlar)/len(puanlar))**0.5*100:.1f}")
    
    return en_iyi

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Akil Motoru Dongu Testi")
    p.add_argument("soru")
    p.add_argument("--canli", action="store_true", help="Gercek LLM kullan (rate-limit gerekli)")
    p.add_argument("--mock", default=None, help="Mock cevap sablonu")
    args = p.parse_args()
    
    sonuclar, soru = dongu_testi(args.soru, mock_cevap=args.mock, canli=args.canli)
    rapor = rapor_olustur(sonuclar, soru)
    
    # Kaydet
    cikti = "dongu_test_sonuc.json"
    with open(cikti, "w") as f:
        json.dump({"soru": soru, "sonuclar": sonuclar, "kazanan": rapor["tur"]}, f, ensure_ascii=False, indent=2)
    print(f"\n  Kaydedildi: {cikti}")
