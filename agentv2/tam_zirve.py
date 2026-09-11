"""ZenAI Tam Zirve Testi — tek komutla tum sistemi calistir.
Akil motoru + model routing + self-correction + cogunluk oyu + meclis hakemi.
Rate-limit aware: aralarda bekleme, kismi sonuc kaydetme, kalan hak sureci.

Kullanim:
  python3 tam_zirve.py                      # varsayilan 150 soru (bankadan)
  python3 tam_zirve.py --soru 20            # ilk 20 soru (hizli test)
  python3 tam_zirve.py --kategori kod       # sadece kod sorulari
  python3 tam_zirve.py --zorluk zor         # sadece zor sorular
  python3 tam_zirve.py --kalan-bekle        # rate-limit bekle, surekli dene
  python3 tam_zirve.py --sadece-skor        # sadece onceki sonuclari skorla
"""
import os, sys, json, time, re, argparse

sys.path.insert(0, os.path.dirname(__file__))

# ── Import ───────────────────────────────────────────────────
try:
    from model_routing import model_sec, konu_aciklama, routing_logla
    from self_correction import self_correction
    from cogunluk_oyu import cogunluk
    from otomatik_skorer import puanla
    from soru_bankasi import SORULAR
except ImportError:
    from agentv2.model_routing import model_sec, konu_aciklama, routing_logla
    from agentv2.self_correction import self_correction
    from agentv2.cogunluk_oyu import cogunluk
    from agentv2.otomatik_skorer import puanla
    from agentv2.soru_bankasi import SORULAR

KONULAR = sorted({k for k, _, _ in SORULAR})
ZORLUKLAR = ("kolay", "orta", "zor")

BENCH_SISTEM = (
    "Turkce; yapilandirilmis, net ve dogru cevap ver.\n"
    "Kurallar:\n"
    "1) Her cevap en az 3 madde veya adim icersin.\n"
    "2) Sayisal/kesin cevapli sorularda islem adimlarini goster ve en sonda "
    "'Sonuc: <deger>' satiri ile bitir (deger mutlaka sayi veya tek kelime olsun).\n"
    "3) Mantik ve dil sorularinda once dogrudan cevabi yaz, sonra gerekceyi madde madde ver.\n"
    "4) Uydurma yapma; emin degilsen 'Emin degilim' diye belirt."
)

def api_iste(mesajlar, model, key, max_tokens=2048, deneme=3):
    """Rate-limit aware API cagirisi."""
    import requests
    for tur in range(deneme):
        t0 = time.time()
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", json={
                "model": model,
                "messages": mesajlar,
                "max_tokens": max_tokens, "temperature": 0.3,
            }, headers={"Authorization": "Bearer " + key}, timeout=120)
            sure = round(time.time()-t0, 1)
            if r.status_code == 200:
                msg = r.json()["choices"][0]["message"]
                c = msg.get("content")
                if isinstance(c, list):  # Gemini part-dizisi formatı
                    c = " ".join(p.get("text", "") for p in c if isinstance(p, dict))
                c = c or ""
                return {"sure": sure, "kelime": len(c.split()), "cikti": c[:5000], "model": model}
            elif r.status_code == 429:
                bekle = (2 ** tur) * 3
                print(f"    [429] {bekle}sn bekleniyor...")
                time.sleep(bekle)
                continue
            return {"sure": sure, "kelime": 0, "cikti": f"[HTTP {r.status_code}]"}
        except Exception as e:
            return {"sure": 0, "kelime": 0, "cikti": f"[HATA: {e}]"}
    return {"sure": 0, "kelime": 0, "cikti": "[429 tum denemeler tukendi]"}

def tek_soru_test(soru_no, konu, soru, key, zorluk="orta", cogunluk_modu=False):
    """Tek bir soruyu tam test pipeline'indan gecir."""
    secilen_model, maxt = model_sec(konu)
    # ZIRVE_MODEL ortam degiskeni varsa tum sorularda o modeli kullan (benchmark acil yol)
    zor_model = os.environ.get("ZIRVE_MODEL", "").strip()
    if zor_model:
        secilen_model = zor_model
        maxt = int(os.environ.get("ZIRVE_MAXTOKENS", "32768"))

    # 1. Tek cevap (routing ile dogru model)
    sistem = BENCH_SISTEM
    if konu == "kod":
        sistem += (
            "\n5) Kod sorularinda SADECE calisan Python kodu ver: tek bir ```python "
            "blogu, aciklama/soz metni yok. Kod 10 saniyede bitmeli, ek kutuphane "
            "yuklemek yok (standart kutuphaneler yeterli), dosya/dis bagimliligina "
            "gerek yok."
        )
    sonuc = api_iste(
        [{"role": "system", "content": sistem},
         {"role": "user", "content": soru}],
        secilen_model, key, maxt
    )

    # 2. Self-correction (yapilandirma icin tum konularda)
    duzeltilen = 0
    if sonuc.get("kelime", 0) > 0:
        def _duzelt_istek(msg):
            r = api_iste(msg, secilen_model, key, maxt)
            return r["cikti"] if r.get("kelime", 0) > 0 else None
        cevap, tur, not_ = self_correction(
            soru, sonuc["cikti"], konu, _duzelt_istek,
            max_tur=2 if konu == "kod" else 1)
        if tur > 0:
            sonuc["cikti"] = cevap
            sonuc["kelime"] = len(cevap.split())
            duzeltilen = tur

    # 3. Cogunluk oyu (opsiyonel, ekstra token harcar)
    cog_bilgi = None
    if cogunluk_modu and sonuc.get("kelime", 0) > 0:
        try:
            cog = cogunluk(soru, tekrar=2, model=secilen_model)
            cog_bilgi = {"guven": cog["guven"], "kazanan": cog["en_sik_ozet"][:60]}
        except Exception:
            pass

    return {
        "no": soru_no, "konu": konu, "soru": soru, "zorluk": zorluk,
        "model": secilen_model, "max_tokens": maxt,
        "duzeltme": duzeltilen,
        "cogunluk": cog_bilgi,
        **sonuc
    }

def sorulari_sec(sayi, kategori=None, zorluk=None):
    """Sorulari filtreler; cok secilirse sayi kadar ornekler."""
    havuz = SORULAR
    if kategori:
        havuz = [s for s in havuz if s[0] == kategori]
    if zorluk:
        havuz = [s for s in havuz if s[2] == zorluk]
    if sayi:
        havuz = havuz[:sayi]
    return havuz

def tam_zirve(sayi=50, cogunluk=False, kalan_bekle=False, sadece_skor=False,
              kategori=None, zorluk=None):
    key = os.environ.get("OPENROUTER_KEY", "")
    cikti_yol = os.environ.get("LB_CIKTI", "/tmp/opencode/zirve_sonuc.json")

    # Sadece skor modu
    if sadece_skor:
        if os.path.exists(cikti_yol):
            with open(cikti_yol) as f: d = json.load(f)
            rapor = puanla(d.get("sonuclar", []))
            print(f"\n  ONCEKI SONUCLAR: {rapor['genel_puan']}/100 ({rapor['basarili_soru']} basarili)")
        else:
            print(" Onceki sonuc yok")
        return

    sorular = sorulari_sec(sayi, kategori, zorluk)
    sonuclar = []
    basarili = 0

    print(f"\n{'='*70}")
    print(f"  ZENAI TAM ZIRVE TESTI — {len(sorular)} soru"
          + (f" | kategori: {kategori}" if kategori else "")
          + (f" | zorluk: {zorluk}" if zorluk else ""))
    print(f"  Routing: AKTIF | Self-Correction: AKTIF | Cogunluk: {'AKTIF' if cogunluk else 'PASIF'}")
    print(f"{'='*70}\n")

    for i, (konu, soru, zor) in enumerate(sorular, 1):
        print(f"[{i}/{len(sorular)}] {konu}({zor}): {soru[:50]}...")

        # Rate-limit bekleme modu
        if kalan_bekle:
            test = api_iste([{"role":"user","content":"test"}], "dots-studio/dots-3-note-preview:free", key, 10)
            if test.get("cikti", "").startswith("[429"):
                print(f"  [rate-limit beklemede] 60sn...")
                time.sleep(60)
                continue

        sonuc = tek_soru_test(i, konu, soru, key, zorluk=zor, cogunluk_modu=cogunluk)
        sonuclar.append(sonuc)

        if sonuc.get("kelime", 0) > 0:
            basarili += 1
            print(f"  -> {sonuc['sure']}sn, {sonuc['kelime']}k, {sonuc['model'].split('/')[-1].split(':')[0]} "
                  f"sc:{sonuc['duzeltme']} {'✓' if sonuc.get('kelime',0)>50 else '~'}")
        else:
            print(f"  -> HATA: {sonuc['cikti'][:80]}")

        # 2sn bekleme (rate-limit korumasi)
        if i < len(sorular):
            time.sleep(2)
            if i % 10 == 0:
                _kaydet(sonuclar, len(sorular), cikti_yol)
                print(f"  [kismi kaydedildi: {i}/{len(sorular)}]")

    _kaydet(sonuclar, len(sorular), cikti_yol)

    # Skor raporu
    rapor = puanla(sonuclar)
    print(f"\n{'='*70}")
    print(f"  ZIRVE RAPORU")
    print(f"{'='*70}")
    print(f"  Genel: {rapor['genel_puan']}/100 (basarili: {rapor['basarili_soru']}, hatali: {rapor['hatali_soru']})")
    for konu, bilgi in sorted(rapor['konu_ozet'].items()):
        etiket = "YUKSEK" if bilgi['ortalama'] >= 0.7 else "ORTA" if bilgi['ortalama'] >= 0.4 else "DUSUK"
        print(f"    {konu:12s} {bilgi['ortalama']*100:5.1f} [{etiket}]")
    print(f"{'='*70}")

    # Veri odakli routing: her sonucu logla
    for s in sonuclar:
        routing_logla(s.get("konu"), s.get("soru", ""), s.get("model", ""),
                      s.get("puan", 0), sure=s.get("sure"), kelime=s.get("kelime"))

def _kaydet(sonuclar, toplam, cikti):
    with open(cikti, "w") as f:
        json.dump({"toplam": toplam, "sonuclar": sonuclar}, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="ZenAI tam zirve testi")
    p.add_argument("--soru", type=int, default=150)
    p.add_argument("--cogunluk", action="store_true")
    p.add_argument("--kalan-bekle", action="store_true")
    p.add_argument("--sadece-skor", action="store_true")
    p.add_argument("--kategori", choices=KONULAR or None)
    p.add_argument("--zorluk", choices=ZORLUKLAR)
    args = p.parse_args()
    tam_zirve(args.soru, args.cogunluk, args.kalan_bekle, args.sadece_skor,
              args.kategori, args.zorluk)