"""LenBeyni 50-konu karsilastirma testi.
Her konuda bir soru sorar, sure/kelime/cikti kaydeder, JSON rapor yazar.
Rate-limit aware: her istek arasinda bekleme + 429'da exponential backoff.
"""
import os, sys, json, time, re

SORULAR = [
    # 1-5: Kod
    ("kod", "Python ile bir dosyanin ilk 5 satirini okuyan fonksiyon yaz."),
    ("kod", "Basit bir web sunucusu (HTTP) Python ile nasil yazilir? Ornek ver."),
    ("kod", "Bir listeyi kucukten buyuge siralama algoritmasini acikla (quicksort)."),
    ("kod", "SQL'de iki tabloyu birleştirmenin (JOIN) turlerini acikla."),
    ("kod", "Regex ile e-posta adresi dogrulayan ornek yaz."),
    # 6-10: Matematik
    ("matematik", "2+7*3-8/2 isleminin sonucu kactir? Adim adim goster."),
    ("matematik", "Bir dortgenin ic acilarinin toplami neden 360 derecedir?"),
    ("matematik", "Pi sayisinin kesirli yaklasik degerini ve neden dogru oldugunu anlat."),
    ("matematik", "Bir sayinin asal olup olmadigini bulmanin en hizli yolu nedir?"),
    ("matematik", "Olasilik: 6 yuzlu zar 2 kez atilinca iki kez 6 gelme ihtimali?"),
    # 11-15: Dil / Turkce
    ("dil", "'Ki' baglacinin yazim kurallarini orneklerle anlat."),
    ("dil", "'Degil' veya 'değil' hangisi dogru? Turkce imla kurallarini acikla."),
    ("dil", "Bu cumledeki anlam bozuklugunu bul ve duzelt: 'Kitap okumayi cok seviyorum ama zamanim olmuyor, arkadaslarim kitap okur'"),
    ("dil", "Bir paragrafi Turkce'den Ingilizce'ye cevir: 'Yaz mevsimi denize girmek icin en guzel zamandir.'"),
    ("dil", "'Elma' kelimesinin mecaz anlamini cumlede kullan."),
    # 16-20: Mantik / Akil yurutme
    ("mantik", "Bir copcu günde 3 sokak temizliyor, her sokak 40 dakika suruyor. 5 copcu 2 sokak temizlerse ne kadar surer? Yanlis varsayimlari da belirt."),
    ("mantik", "Bir dunyada tum kuzgunlar siyahtir. Beyaz bir kuzgun bulursak bu onermeyi nasil degisir?"),
    ("mantik", "Sudoku bulmaca cozumune nasil yaklasilir? Adim adim anlat."),
    ("mantik", "Klasik bilmece: Hangi soruyu herkes farkli cevaplar?"),
    ("mantik", "Eger bugun carsamba ise yarin gunlerden ne? Ama 'yarin' kelimesi pazartesi anlamina gelebilir mi?"),
    # 21-25: Bilim / Teknoloji
    ("bilim", "Fotoelektrik etki nedir ve Einstein bunu nasil acikladi?"),
    ("bilim", "DNA'nin yapisini kisa ve anlasilir sekilde anlat."),
    ("bilim", "Yapay zeka ile makine ogrenmesi arasindaki fark nedir?"),
    ("bilim", "Iki fotonun birbirleriyle dolanik olmasi ne demek? Ornek ver."),
    ("bilim", "Kuantum bilgisayary nerede klasik bilgisayardan ustun olacak?"),
    # 26-30: Tarih
    ("tarih", "Osmanli Devleti'nin kurulusu hangi donemde gerceklesti ve kim kurdu?"),
    ("tarih", "Ronesans neden Italya'da basladi?"),
    ("tarih", "Birinci Dunya Savasi'nin ana nedenlerini madde madde yaz."),
    ("tarih", "Cumhuriyet ne zaman ilan edildi ve neyi sembolize eder?"),
    ("tarih", "Tarihte 'Guclu Devlet' kavrami hangi donemde ortaya cikti?"),
    # 31-35: Yaratıcılık
    ("yaratici", "Maviden baslayip kizila donen bir sehir manzarasi hikayesi yaz (3 paragraf)."),
    ("yaratici", "Bir masal kahramani icin benzersiz bir guc tasarla ve acikla."),
    ("yaratici", "Iki kelime veriyorum: 'feridun', 'telefon'. Ikisini birlesitiren komik bir kisa hikaye yaz."),
    ("yaratici", "Bir logo icin 3 fikir oner: kahve dukkani."),
    ("yaratici", "5 maddelik bir 'dogayla uyumlu yasam' manifestosu yaz."),
    # 36-40: Genel Kultur
    ("kultur", "Turk kahvesi nasil yapilir? Adim adim anlat."),
    ("kultur", "Maskot kavrami nedir ve neden markalar icin onemlidir?"),
    ("kultur", "Bayrak yarisi nedir? Acikla."),
    ("kultur", "Bir turist icin Istanbul'da 3 gunluk gezi plani oner."),
    ("kultur", "Dunyanin en kalabalik 5 sehrini isimlendir."),
    # 41-45: Pratik / Gundelik
    ("pratik", "Araba lastigi ne zaman degistirilmeli? Abartma, kisa anlat."),
    ("pratik", "Bir dakikada uykuya dalmak icin teknikler oner."),
    ("pratik", "Yemekte limon suyu yerine ne kullanabilirim?"),
    ("pratik", "Sunger sifirlamak icin en hizli yontem nedir?"),
    ("pratik", "Iyi bir sabah rutini icin 3 madde oner."),
    # 46-50: Teknoloji / Ileri
    ("teknoloji", "LLM olarak 'context window' nedir? Kisa ve net anlat."),
    ("teknoloji", "Vektorel veritabani ne ise yarar? Ornek ver."),
    ("teknoloji", "Blockchain'in temel calisma mantigi nedir?"),
    ("teknoloji", "GPU neden fermliyor? performans artisi nasil olur?"),
    ("teknoloji", "Bir yapay zeka modelini nasil egitirsin? Adim adim."),
]

def test_et(o, model, key, deneme=3):
    import requests
    for tur in range(deneme):
        t0 = time.time()
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", json={
                "model": model,
                "messages": [{"role": "system", "content": "Turkce, net ve dogru cevap ver."},
                             {"role": "user", "content": o}],
                "max_tokens": 1024, "temperature": 0.3,
            }, headers={"Authorization": "Bearer " + key}, timeout=120)
            sure = round(time.time()-t0, 1)
            if r.status_code == 200:
                c = r.json()["choices"][0]["message"]["content"]
                return {"sure": sure, "kelime": len(c.split()), "cikti": c[:3000]}
            elif r.status_code == 429:
                bekle = (2 ** tur) * 3  # 3sn, 6sn, 12sn
                print(f"   [429 rate-limit] {bekle}sn bekleniyor... (deneme {tur+1}/{deneme})")
                time.sleep(bekle)
                continue
            return {"sure": sure, "kelime": 0, "cikti": f"[HTTP {r.status_code}: {r.text[:100]}]"}
        except Exception as e:
            return {"sure": round(time.time()-t0,1), "kelime": 0, "cikti": f"[HATA: {e}]"}
    return {"sure": 0, "kelime": 0, "cikti": "[HTTP 429: rate-limit asildi, tum denemeler tükendi]"}

if __name__ == "__main__":
    model = os.environ.get("LB_MODEL", "dots-studio/dots-3-note-preview:free")
    key = os.environ.get("OPENROUTER_KEY", "")
    butun = []
    for i, (k, s) in enumerate(SORULAR, 1):
        print(f"[{i}/50] {k}: {s[:45]}...")
        son = test_et(s, model, key)
        butun.append({"no": i, "konu": k, "soru": s, **son})
        print(f"   -> {son['sure']}sn, {son['kelime']} kelime, {son['cikti'][:40].replace(chr(10),' ')!r}")
        # Her sorudan sonra 2sn bekle (rate-limit korumasi)
        if i < len(SORULAR):
            time.sleep(2)
            # Her 10 soruda aralik kaydet (kismi sonuc)
            if i % 10 == 0:
                cikti_yol = os.environ.get("LB_CIKTI", "karsilastirma.json")
                with open(cikti_yol, "w") as f:
                    json.dump({"model": model, "sonuclar": butun}, f, ensure_ascii=False, indent=1)
                print(f"   [kismi kaydedildi: {i}/50]")
    cikti_yol = os.environ.get("LB_CIKTI", "karsilastirma.json")
    with open(cikti_yol, "w") as f:
        json.dump({"model": model, "sonuclar": butun}, f, ensure_ascii=False, indent=1)
    print(f"\nRapor: {cikti_yol}")