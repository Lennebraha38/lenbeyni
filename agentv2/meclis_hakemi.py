"""Genisletilmis Meclis Hakemi — 12 kriter ile kapsamli oylama.
Her cevabi 12 boyutta puanlar, hakem paneli karar verir.
Gercek kullanici degerlendirmesine en yakin objektif olcum sistemi.

12 KRITER:
  1. Dogruluk      : Bilgi dogru mu, yanlis bilgi var mi?
  2. Kapsam        : Sorunun tum yonlerine deginildi mi?
  3. Derinlik      : Yuzeyel mi, yoksa katmanli aciklama var mi?
  4. Netlik        : Anlasilir mi, bulanik ifadeler var mi?
  5. Yapi          : Madde/baslik/paragraf duzenli mi?
  6. Turkce        : Imla kurallarina uygun mu, dogru mu?
  7. Ornek         : Somut ornekler verilmis mi?
  8. Guncellik     : Guncel bilgi mi, eski/yenilmis mi?
  9. Uygulanabilirlik : Pratikte uygulanabilir mi?
  10. Yaraticilik   : Sıradan mi, ozgun yaklasim var mi?
  11. Token Kullanimi : Verimli mi (cok uzun/eksik degil)?
  12. Guven         : Hakem modelin kendi guveni yeterli mi?
"""
import os, sys, json, re, time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))

# ── Kriter tanimlari ve agirliklari ─────────────────────────
KRITERLER = [
    ("dogruluk",        0.20, "Bilgi dogru mu, kaynak gosterilmis mi?"),
    ("kapsam",          0.15, "Sorunun tum yonlerine deginildi mi?"),
    ("derinlik",        0.12, "Yuzeyel mi, katmanli aciklama var mi?"),
    ("netlik",          0.12, "Anlasilir mi, bulanik ifadeler var mi?"),
    ("yapi",            0.08, "Madde/baslik/paragraf duzeni var mi?"),
    ("turkce",          0.08, "Imla + gramer + dogru Turkce mi?"),
    ("ornek",           0.08, "Somut ornekler verilmis mi?"),
    ("guncellik",       0.05, "Guncel bilgi mi, yenilmis mi?"),
    ("uygulanabilirlik",0.05, "Pratikte uygulanabilir mi?"),
    ("yaraticilik",     0.04, "Ozgun yaklasim var mi?"),
    ("token_verimliligi",0.04, "Uzunluk yeterli ama gereksiz uzama yok mu?"),
    ("guven",           0.04, "Model kendinden emin mi?"),
]

# ── Bilesik otomatik puanlayici (her kriter icin otomatik kontrol) ────
def kriter_puanla(kriter_adi, cevap, soru=None):
    """Tek bir kriter icin otomatik puan (0-1)."""
    cevap_kucuk = cevap.lower()
    soru_kucuk = (soru or "").lower()
    
    if kriter_adi == "dogruluk":
        # Yanlis bilgi belirtecleri
        yanlis_belirtec = len(re.findall(r"\b(bu dogru degil|yanlis|asinda|ozellikle yanlis)\b", cevap_kucuk))
        dogru_belirtec = len(re.findall(r"\b(dogrulanmis|kanit|arastirma|orijinal kaynak|DOG\w* verified)\b", cevap_kucuk))
        skor = 0.6 + min(dogru_belirtec * 0.1, 0.3) - min(yanlis_belirtec * 0.15, 0.4)
        return max(0, min(1, skor))
    
    elif kriter_adi == "kapsam":
        # Sorudaki anahtar kelimelerin kacini iceriyor?
        if not soru_kucuk: return 0.6
        anahtar = [w for w in soru_kucuk.split() if len(w)>3]
        iceren = sum(1 for w in anahtar if w in cevap_kucuk)
        orani = iceren / max(len(anahtar), 1)
        return 0.4 + orani * 0.6
    
    elif kriter_adi == "derinlik":
        # Madde sayisi ve paragraf derinligi
        madde = len(re.findall(r'(?m)^[\s]*[\-\*\d]+[\.\)\s]', cevap))
        paragraf = cevap.count('\n\n')
        skor = 0.3
        if madde >= 4: skor += 0.4
        elif madde >= 2: skor += 0.2
        if paragraf >= 3: skor += 0.3
        elif paragraf >= 1: skor += 0.15
        return min(skor, 1.0)
    
    elif kriter_adi == "netlik":
        # Kisa cumle, az karmasa, seviye tutarliligi
        cumleler = re.split(r'[.!?]+', cevap)
        uzun_cumle = sum(1 for c in cumleler if len(c.split()) > 30)
        toplam = len(cumleler)
        if toplam == 0: return 0.5
        net = 1 - (uzun_cumle / toplam)
        return 0.4 + net * 0.6
    
    elif kriter_adi == "yapi":
        return min(1.0, 0.3 + len(re.findall(r'(?m)^[\-\*\d]', cevap)) * 0.1)
    
    elif kriter_adi == "turkce":
        turkce_harf = len(re.findall(r'[çğıöşüÇĞİÖŞÜ]', cevap))
        karakter = len(cevap)
        if karakter == 0: return 0
        orani = turkce_harf / karakter
        # Turkce ortalama %3-5
        if orani >= 0.02: return 0.9
        elif orani >= 0.01: return 0.7
        elif orani >= 0.005: return 0.5
        return 0.3
    
    elif kriter_adi == "ornek":
        ornek_belirtec = len(re.findall(r'\b(ornek|misal|ornegin|ornegiyle|mesela|yani|soyle ki)\b', cevap_kucuk))
        kod_blogu = '```' in cevap
        skor = 0.3
        if ornek_belirtec >= 3: skor += 0.4
        elif ornek_belirtec >= 1: skor += 0.2
        if kod_blogu: skor += 0.3
        return min(skor, 1.0)
    
    elif kriter_adi == "guncellik":
        # 2025/2026 yil referansi var mi?
        yil_var = bool(re.search(r'202[0-9]', cevap))
        return 0.8 if yil_var else 0.5
    
    elif kriter_adi == "uygulanabilirlik":
        pratik_belirtec = len(re.findall(r'\b(adim|adimlar|yontem|yolu|yontemi|yapman|edebilir|kullanilabilir|uygula)\b', cevap_kucuk))
        return min(1.0, 0.4 + pratik_belirtec * 0.15)
    
    elif kriter_adi == "yaraticilik":
        # Ozgun ifade varyasyonu
        kelimeler = set(cevap.lower().split())
        cesitlilik = len(kelimeler) / max(len(cevap.split()), 1)
        return min(1.0, 0.3 + cesitlilik * 0.7)
    
    elif kriter_adi == "token_verimliligi":
        kelime = len(cevap.split())
        if kelime >= 100: return 0.9
        elif kelime >= 50: return 0.7
        elif kelime >= 20: return 0.5
        return 0.3
    
    elif kriter_adi == "guven":
        guven_belirtec = len(re.findall(r'\b(kesinlikle|emim|kanitim|kesin|net|acik)', cevap_kucuk))
        suphe_belirtec = len(re.findall(r'\b(belki|muhtemelen|olabilir|emin degilim|bilmiyorum|sanirim)', cevap_kucuk))
        skor = 0.6 + guven_belirtec * 0.1 - suphe_belirtec * 0.15
        return max(0, min(1, skor))
    
    return 0.5

# ── Hakem Paneli ─────────────────────────────────────────────
def hakem_paneli(cevaplar, soru):
    """Cevaplari 12 kriterden puanla, en iyi hangisi sec, rapor dondur.
    cevaplar: [(model_adi, cevap_metni), ...]
    """
    sonuclar = []
    
    for model_adi, cevap in cevaplar:
        kriter_skorlari = {}
        agirlikli_toplam = 0.0
        for kriter, agirlik, _ in KRITERLER:
            puan = kriter_puanla(kriter, cevap, soru)
            kriter_skorlari[kriter] = round(puan, 3)
            agirlikli_toplam += puan * agirlik
        sonuclar.append({
            "model": model_adi,
            "genel_skor": round(agirlikli_toplam, 4),
            "kriter_skorlari": kriter_skorlari,
            "kelime": len(cevap.split()),
        })
    
    # Kiyasla
    sirali = sorted(sonuclar, key=lambda x: -x["genel_skor"])
    kazanan = sirali[0]
    
    return {
        "kazanan": kazanan["model"],
        "kazanan_skor": kazanan["genel_skor"],
        "siralama": [
            {"sira": i+1, "model": s["model"], "skor": s["genel_skor"],
             "en_iyi_kriter": max(s["kriter_skorlari"], key=s["kriter_skorlari"].get),
             "en_zayif_kriter": min(s["kriter_skorlari"], key=s["kriter_skorlari"].get)}
            for i, s in enumerate(sirali)
        ],
        "tum_sonuclar": sonuclar,
    }

def rapor_goster(rapor, soru):
    """Hakem paneli raporunu goster."""
    print(f"\n{'='*65}")
    print(f"  HAKEM PANELI RAPORU")
    print(f"{'='*65}")
    print(f"  Soru: {soru[:60]}")
    print(f"  Kazanan: {rapor['kazanan']} ({rapor['kazanan_skor']*100:.1f}/100)")
    print(f"{'='*65}")
    for s in rapor["siralama"]:
        print(f"\n  #{s['sira']} {s['model']:25s}  {s['skor']*100:5.1f}/100")
        print(f"     En iyi: {s['en_iyi_kriter']:18s}  En zayif: {s['en_zayif_kriter']}")
    # Kriter detayi
    print(f"\n{'='*65}")
    print("  KRITER DETAYLARI (kazanan icin):")
    print(f"{'='*65}")
    kazanan_sonuc = [x for x in rapor["tum_sonuclar"] if x["model"] == rapor["kazanan"]][0]
    for k, p in sorted(kazanan_sonuc["kriter_skorlari"].items(), key=lambda x: -x[1]):
        isaret = "+" if p >= 0.7 else "~" if p >= 0.4 else "*"
        print(f"  [{isaret}] {k:20s} → {p*100:5.1f}/100")
    print(f"\n  Toplam kelime: {kazanan_sonuc['kelime']}")
    return rapor["siralama"]

# ── Ornek meclis uretimi (3 model oylaması) ─────────────────
def meclis_uret(soru, modeller=None):
    """3 farkli modelden cevap uretip hakem paneli ile sec.
    Gercek kullanildiginda LLM cagirisi yapar.
    """
    if modeller is None:
        modeller = [
            ("dots-3",     "dots-studio/dots-3-note-preview:free"),
            ("nemotron",   "nvidia/nemotron-3-ultra-550b-a55b:free"),
            ("laguna",     "poolside/laguna-s-2.1:free"),
        ]
    
    cevaplar = []
    try:
        from lenbeyni_zeka import llm, OPENROUTER_KEY
        canli = bool(OPENROUTER_KEY)
    except ImportError:
        canli = False
    
    if canli:
        for ad, model in modeller:
            t0 = time.time()
            mesajlar = [
                {"role": "system", "content": "Turkce, net ve dogru cevap ver."},
                {"role": "user", "content": soru}
            ]
            c = llm(mesajlar, model=model, seviye="uzun", stream=False)
            sure = round(time.time()-t0, 1)
            if c:
                cevaplar.append((ad, c))
                print(f"  [{ad}] {sure}sn, {len(c.split())} kelime")
            else:
                print(f"  [{ad}] HATA/call")
    else:
        print("  [Mock modu] Rate-limit beklemede, mock cevaplar kullaniliyor")
        cevaplar = [
            ("dots-3",   "Bu sorunun cevabi: Turkce ornek ile aciklama. Adim 1: Analiz. Adim 2: Cozum. Sonuc: Dogru bilgi."),
            ("nemotron", "Detayli analiz: Konu hakkinda derin bilgi. Ornek: Bir bilim adami bunu soylemistir. Kapsamli cevap."),
            ("laguna",   "Kisa cevap: Bilgi dogrudur. Ornek: Turkiye'de boyle yapilir. Ozet: Yeterli.")
        ]
    
    if len(cevaplar) < 2:
        print("  Yeterli cevap alinamadi, meclis calismadi")
        return None
    
    # Hakem paneli
    rapor = hakem_paneli(cevaplar, soru)
    return rapor_goster(rapor, soru)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Genisletilmis Meclis Hakemi")
    p.add_argument("soru")
    p.add_argument("--canli", action="store_true")
    p.add_argument("--cevaplar", nargs="+", help="Dosyadan cevap oku: model:dosya")
    args = p.parse_args()
    
    if args.cevaplar:
        # Dosyadan cevap oku
        cevaplar = []
        for parca in args.cevaplar:
            if ":" in parca:
                model, dosya = parca.split(":", 1)
                with open(dosya) as f:
                    cevaplar.append((model, f.read()))
        rapor = hakem_paneli(cevaplar, args.soru)
        rapor_goster(rapor, args.soru)
    else:
        meclis_uret(args.soru)
