"""LenBeyni Tam Zirve Testi — tek komutla tum sistemi calistir.
Akil motoru + model routing + self-correction + cogunluk oyu + meclis hakemi.
Rate-limit aware: aralarda bekleme, kismi sonuc kaydetme, kalan hak sureci.

Kullanim:
  python3 tam_zirve.py                    # varsayilan 50 soru
  python3 tam_zirve.py --soru 10          # ilk 10 soru (hizli test)
  python3 tam_zirve.py --kalan-bekle      # rate-limit bekle, surekli dene
  python3 tam_zirve.py --sadece-skor      # sadece onceki sonuclari skorla
"""
import os, sys, json, time, re, argparse

sys.path.insert(0, os.path.dirname(__file__))

# ── Import ───────────────────────────────────────────────────
try:
    from model_routing import model_sec, konu_aciklama
    from self_correction import self_correction
    from cogunluk_oyu import cogunluk
    from otomatik_skorer import puanla
except ImportError:
    from agentv2.model_routing import model_sec, konu_aciklama
    from agentv2.self_correction import self_correction
    from agentv2.cogunluk_oyu import cogunluk
    from agentv2.otomatik_skorer import puanla

# ── Sorular (karsilastirma.py ile ayni) ──────────────────────
SORULAR = [
    ("kod", "Python ile bir dosyanin ilk 5 satirini okuyan fonksiyon yaz."),
    ("kod", "Basit bir web sunucusu (HTTP) Python ile nasil yazilir? Ornek ver."),
    ("kod", "Bir listeyi kucukten buyuge siralama algoritmasini acikla (quicksort)."),
    ("kod", "SQL'de iki tabloyu birlestirmenin (JOIN) turlerini acikla."),
    ("kod", "Regex ile e-posta adresi dogrulayan ornek yaz."),
    ("matematik", "2+7*3-8/2 isleminin sonucu kactir? Adim adim goster."),
    ("matematik", "Bir dortgenin ic acilarinin toplami neden 360 derecedir?"),
    ("matematik", "Pi sayisinin kesirli yaklasik degerini ve neden dogru oldugunu anlat."),
    ("matematik", "Bir sayinin asal olup olmadigini bulmanin en hizli yolu nedir?"),
    ("matematik", "Olasilik: 6 yuzlu zar 2 kez atilinca iki kez 6 gelme ihtimali?"),
    ("dil", "'Ki' baglacinin yazim kurallarini orneklerle anlat."),
    ("dil", "'Degil' veya 'degil' hangisi dogru? Turkce imla kurallarini acikla."),
    ("dil", "Bu cumledeki anlam bozuklugunu bul ve duzelt: 'Kitap okumayi cok seviyorum ama zamanim olmuyor, arkadaslarim kitap okur'"),
    ("dil", "Bir paragrafi Turkce'den Ingilizce'ye cevir: 'Yaz mevsimi denize girmek icin en guzel zamandir.'"),
    ("dil", "'Elma' kelimesinin mecaz anlamini cumlede kullan."),
    ("mantik", "Bir copcu gunde 3 sokak temizliyor, her sokak 40 dakika suruyor. 5 copcu 2 sokak temizlerse ne kadar surer?"),
    ("mantik", "Bir dunyada tum kuzgunlar siyahtir. Beyaz bir kuzgun bulursak bu onermeyi nasil degisir?"),
    ("mantik", "Sudoku bulmaca cozumune nasil yaklasilir? Adim adim anlat."),
    ("mantik", "Klasik bilmece: Hangi soruyu herkes farkli cevaplar?"),
    ("mantik", "Eger bugun carsamba ise yarin gunlerden ne?"),
    ("bilim", "Fotoelektrik etki nedir ve Einstein bunu nasil acikladi?"),
    ("bilim", "DNA'nin yapisini kisa ve anlasilir sekilde anlat."),
    ("bilim", "Yapay zeka ile makine ogrenmesi arasindaki fark nedir?"),
    ("bilim", "Iki fotonun birbirleriyle dolanik olmasi ne demek?"),
    ("bilim", "Kuantum bilgisayari nerede klasik bilgisayardan ustun olur?"),
    ("tarih", "Osmanli Devleti'nin kurulusu hangi donemde gerceklesti ve kim kurdu?"),
    ("tarih", "Ronesans neden Italya'da basladi?"),
    ("tarih", "Birinci Dunya Savasi'nin ana nedenlerini madde madde yaz."),
    ("tarih", "Cumhuriyet ne zaman ilan edildi ve neyi sembolize eder?"),
    ("tarih", "Tarihte 'Guclu Devlet' kavrami hangi donemde ortaya cikti?"),
    ("yaratici", "Maviden baslayip kizila donen bir sehir manzarasi hikayesi yaz."),
    ("yaratici", "Bir masal kahramani icin benzersiz bir guc tasarla ve acikla."),
    ("yaratici", "Iki kelime: 'feridun', 'telefon'. Ikisini birlestiren komik kisa hikaye yaz."),
    ("yaratici", "Bir logo icin 3 fikir oner: kahve dukkani."),
    ("yaratici", "5 maddelik 'dogayla uyumlu yasam' manifestosu yaz."),
    ("kultur", "Turk kahvesi nasil yapilir? Adim adim anlat."),
    ("kultur", "Maskot kavrami nedir ve neden markalar icin onemlidir?"),
    ("kultur", "Bayrak yarisi nedir? Acikla."),
    ("kultur", "Bir turist icin Istanbul'da 3 gunluk gezi plani oner."),
    ("kultur", "Dunyanin en kalabalik 5 sehrini isimlendir."),
    ("pratik", "Araba lastigi ne zaman degistirilmeli? Abartma, kisa anlat."),
    ("pratik", "Bir dakikada uykuya dalmak icin teknikler oner."),
    ("pratik", "Yemekte limon suyu yerine ne kullanabilirim?"),
    ("pratik", "Sunger sifirlamak icin en hizli yontem nedir?"),
    ("pratik", "Iyi bir sabah rutini icin 3 madde oner."),
    ("teknoloji", "LLM olarak 'context window' nedir? Kisa ve net anlat."),
    ("teknoloji", "Vektorel veritabani ne ise yarar? Ornek ver."),
    ("teknoloji", "Blockchain'in temel calisma mantigi nedir?"),
    ("teknoloji", "GPU neden onemlidir? Performans artisi nasil olur?"),
    ("teknoloji", "Bir yapay zeka modelini nasil egitirsin? Adim adim."),
]

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
                c = r.json()["choices"][0]["message"]["content"]
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

def tek_soru_test(soru_no, konu, soru, key, cogunluk_modu=False):
    """Tek bir soruyu tam test pipeline'indan gecir."""
    secilen_model, maxt = model_sec(konu)
    
    # 1. Tek cevap (routing ile dogru model)
    sonuc = api_iste(
        [{"role": "system", "content": "Turkce, net ve dogru cevap ver."},
         {"role": "user", "content": soru}],
        secilen_model, key, maxt
    )
    
    # 2. Self-correction (kod/matematik icin)
    duzeltilen = 0
    if sonuc.get("kelime", 0) > 0 and konu in ("kod", "matematik", "mantik"):
        cevap, tur, not_ = self_correction(
            soru, sonuc["cikti"], konu,
            lambda msg: api_iste(msg, secilen_model, key, maxt)["cikti"] if api_iste(msg, secilen_model, key, maxt).get("kelime") else None
        )
        if tur > 0:
            sonuc["cikti"] = cevap
            sonuc["kelime"] = len(cevap.split())
            duzeltilen = tur
    
    # 3. Cogunluk oyu (opsiyonel, extra token harcar)
    cog_bilgi = None
    if cogunluk_modu and sonuc.get("kelime", 0) > 0:
        try:
            cog = cogunluk(soru, tekrar=2, model=secilen_model)
            cog_bilgi = {"guven": cog["guven"], "kazanan": cog["en_sik_ozet"][:60]}
        except Exception:
            pass
    
    return {
        "no": soru_no, "konu": konu, "soru": soru,
        "model": secilen_model, "max_tokens": maxt,
        "duzeltme": duzeltilen,
        "cogunluk": cog_bilgi,
        **sonuc
    }

def tam_zirve(sayi=50, cogunluk=False, kalan_bekle=False, sadece_skor=False):
    key = os.environ.get("OPENROUTER_KEY", "")
    
    # Sadece skor modu
    if sadece_skor:
        yol = os.environ.get("LB_CIKTI", "/tmp/opencode/zirve_sonuc.json")
        if os.path.exists(yol):
            with open(yol) as f: d = json.load(f)
            rapor = puanla(d.get("sonuclar", []))
            print(f"\n  ONCEKI SONUCLAR: {rapor['genel_puan']}/100 ({rapor['basarili_soru']} basarili)")
        else:
            print(" Onceki sonuc yok")
        return
    
    sorular = SORULAR[:sayi]
    sonuclar = []
    basarili = 0
    
    print(f"\n{'='*65}")
    print(f"  LENBEYNI TAM ZIRVE TESTI — {len(sorular)} soru")
    print(f"  Routing: AKTIF | Self-Correction: AKTIF | Cogunluk: {'AKTIF' if cogunluk else 'PASIF'}")
    print(f"{'='*65}\n")
    
    for i, (konu, soru) in enumerate(sorular, 1):
        print(f"[{i}/{len(sorular)}] {konu}: {soru[:50]}...")
        
        # Rate-limit bekleme modu
        if kalan_bekle:
            test = api_iste([{"role":"user","content":"test"}], "dots-studio/dots-3-note-preview:free", key, 10)
            if test.get("cikti", "").startswith("[429"):
                print(f"  [rate-limit beklemede] 60sn...")
                time.sleep(60)
                continue
        
        sonuc = tek_soru_test(i, konu, soru, key, cogunluk_modu=cogunluk)
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
                _kaydet(sonuclar, sayi)
                print(f"  [kismi kaydedildi: {i}/{len(sorular)}]")
    
    _kaydet(sonuclar, sayi)
    
    # Skor raporu
    rapor = puanla(sonuclar)
    print(f"\n{'='*65}")
    print(f"  ZIRVE RAPORU")
    print(f"{'='*65}")
    print(f"  Genel: {rapor['genel_puan']}/100 (basarili: {rapor['basarili_soru']}, hatali: {rapor['hatali_soru']})")
    for konu, bilgi in sorted(rapor['konu_ozet'].items()):
        etiket = "YUKSEK" if bilgi['ortalama'] >= 0.7 else "ORTA" if bilgi['ortalama'] >= 0.4 else "DUSUK"
        print(f"    {konu:12s} {bilgi['ortalama']*100:5.1f} [{etiket}]")
    print(f"{'='*65}")

def _kaydet(sonuclar, toplam):
    cikti = os.environ.get("LB_CIKTI", "/tmp/opencode/zirve_sonuc.json")
    with open(cikti, "w") as f:
        json.dump({"toplam": toplam, "sonuclar": sonuclar}, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--soru", type=int, default=50)
    p.add_argument("--cogunluk", action="store_true")
    p.add_argument("--kalan-bekle", action="store_true")
    p.add_argument("--sadece-skor", action="store_true")
    args = p.parse_args()
    tam_zirve(args.soru, args.cogunluk, args.kalan_bekle, args.sadece_skor)
