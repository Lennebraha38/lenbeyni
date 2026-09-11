"""ZenAI Soru Bankasi — 150 soru, 10 konu, 3 zorluk (kolay/orta/zor).

Her kayit: (konu, soru, zorluk)
Zorluk seviyeleri benchmark'in istatistiksel gucunu artirir ve
kategori bazli yetkinlik raporu uretmemizi saglar.
"""

SORULAR = [
    # ── kod ──
    ("kod", "Python ile bir dosyanin ilk 5 satirini okuyan fonksiyon yaz.", "kolay"),
    ("kod", "Basit bir web sunucusu (HTTP) Python ile nasil yazilir? Ornek ver.", "orta"),
    ("kod", "Bir listeyi kucukten buyuge siralama algoritmasini acikla (quicksort).", "orta"),
    ("kod", "SQL'de iki tabloyu birlestirmenin (JOIN) turlerini acikla.", "orta"),
    ("kod", "Regex ile e-posta adresi dogrulayan ornek yaz.", "kolay"),
    ("kod", "Python'da bir sözlüğü anahtarlara göre sıralayıp ilk 3 değeri döndüren kod yaz.", "kolay"),
    ("kod", "Bir metnin tam tersini (reverse) döndüren Python fonksiyonu yaz ve karmaşıklığını söyle.", "kolay"),
    ("kod", "HTTP GET ile bir API'den JSON çekip alanları filtreleyen Python kodu yaz.", "orta"),
    ("kod", "Bir sınıfın özel metotlarını (dunder) 3 örnekle açıkla ve hangi durumda tetiklendiğini anlat.", "orta"),
    ("kod", "Python'da 'yield' nedir? Generatörler belleği neden verimli kullanır?", "orta"),
    ("kod", "Özyinelemeli (recursive) bir Fibonacci fonksiyonu yaz ve iteratif sürümle karşılaştır.", "orta"),
    ("kod", "SQL injection'dan korunmak için parametrik sorgu örneği yaz (Python).", "zor"),
    ("kod", "Çok iş parçacıklı (threading) iki görevi paralel çalıştıran Python örneği ver.", "orta"),
    ("kod", "Bir deque (iki uçlu kuyruk) kullanarak pencere (sliding window) ortalaması hesaplayan kod yaz.", "zor"),
    ("kod", "Python'da asyncio ile eşzamanlı 3 HTTP isteği atan örnek ver.", "zor"),
    # ── matematik ──
    ("matematik", "2+7*3-8/2 isleminin sonucu kactir? Adim adim goster.", "kolay"),
    ("matematik", "Bir dortgenin ic acilarinin toplami neden 360 derecedir?", "kolay"),
    ("matematik", "Pi sayisinin kesirli yaklasik degerini ve neden dogru oldugunu anlat.", "orta"),
    ("matematik", "Bir sayinin asal olup olmadigini bulmanin en hizli yolu nedir?", "orta"),
    ("matematik", "Olasilik: 6 yuzlu zar 2 kez atilinca iki kez 6 gelme ihtimali?", "kolay"),
    ("matematik", "%20 zam yapılan 150 TL'lik ürün, sonra %20 indirimle kaç TL olur?", "kolay"),
    ("matematik", "f(x)=3x+2 doğrusunun grafiğinin eğimi ve y-keseni nedir? Açıkla.", "kolay"),
    ("matematik", "Üslerle çalışma: 2^10 u 2^3 un uslu yonunden ifade edip hesapla.", "orta"),
    ("matematik", "Bir küpün köşegen uzunluğu formülünü türet.", "orta"),
    ("matematik", "Ortalama değer teoremini bir örnekle açıkla (kalkülüs).", "zor"),
    ("matematik", "log2(64) + log3(81) kactir? Adim adim coz.", "orta"),
    ("matematik", "Bir aritmetik dizinin ilk 50 terimini toplayan formülü ver (n=50, a1=3, d=2).", "orta"),
    ("matematik", "Pascal üçgeni ile (a+b)^4 açılımını yaz.", "orta"),
    ("matematik", "Karmaşık sayılar: (3+4i)(3-4i) işleminin sonucu ve anlamı nedir?", "orta"),
    ("matematik", "Bayes teoremini tıbbi bir test örneğiyle açıkla (yanlış pozitif olgusunu içersin).", "zor"),
    # ── dil ──
    ("dil", "'Ki' baglacinin yazim kurallarini orneklerle anlat.", "kolay"),
    ("dil", "'Degil' veya 'degil' hangisi dogru? Turkce imla kurallarini acikla.", "kolay"),
    ("dil", "Bu cumledeki anlam bozuklugunu bul ve duzelt: 'Kitap okumayi cok seviyorum ama zamanim olmuyor, arkadaslarim kitap okur'", "orta"),
    ("dil", "Bir paragrafi Turkce'den Ingilizce'ye cevir: 'Yaz mevsimi denize girmek icin en guzel zamandir.'", "kolay"),
    ("dil", "'Elma' kelimesinin mecaz anlamini cumlede kullan.", "kolay"),
    ("dil", "'da/de' bağlacının bitişik mi ayrı mı yazıldığını 2 örnekle ve gerekçesiyle anlat.", "kolay"),
    ("dil", "'Oysa' ve 'oysaki' arasındaki kullanım farkını örneklerle açıkla.", "orta"),
    ("dil", "'Gitme' ve 'gitmem' kelimelerindeki anlam farkını olumsuzluk ve kipsellik yönünden anlat.", "orta"),
    ("dil", "Bir iş mektubunda resmi dile örnek 3 cümle yaz (hitap, gövde, kapanış).", "orta"),
    ("dil", "Noktalama: 'gelmedi dedi' ile 'gelmedi, dedi' arasındaki farkı açıkla.", "orta"),
    ("dil", "Bir reklam sloganına virgülün etkisini iki karşıtlık örneğiyle göster.", "zor"),
    ("dil", "Dolaylı ve doğrudan anlatımı iki cümleyle karşılaştır.", "kolay"),
    ("dil", "'Beni, eve giderken aradı' cümlesindeki virgülün anlamı nasıl değiştirdiğini yaz.", "orta"),
    ("dil", "Türkçede 'büyük ünlü uyumu' kuralını 10 kelimelik bir liste üzerinde göster.", "kolay"),
    ("dil", "Bir haber metni ile köşe yazısı arasındaki dil farkını 3 örnekle açıkla.", "orta"),
    # ── mantik ──
    ("mantik", "Bir copcu gunde 3 sokak temizliyor, her sokak 40 dakika suruyor. 5 copcu 2 sokak temizlerse ne kadar surer?", "orta"),
    ("mantik", "Bir dunyada tum kuzgunlar siyahtir. Beyaz bir kuzgun bulursak bu onermeyi nasil degisir?", "orta"),
    ("mantik", "Sudoku bulmaca cozumune nasil yaklasilir? Adim adim anlat.", "orta"),
    ("mantik", "Klasik bilmece: Hangi soruyu herkes farkli cevaplar?", "kolay"),
    ("mantik", "Eger bugun carsamba ise yarin gunlerden ne?", "kolay"),
    ("mantik", "3 musluk, 10 dakikada 90 litre dolduruyor. 6 musluk aynı debide 30 dakikada kaç litre doldurur?", "kolay"),
    ("mantik", "Bir otelde 100 oda var, hepsi kapalı. 1. turda tüm kapılar açılır, 2. turda her 2. kapı kapatılır, 3. turda her 3. kapı açılırsa kapatılır... 100. turda hangi kapılar açık kalır?", "zor"),
    ("mantik", "Eğer A => B ve B => C doğruysa, A => C geçerliliğini doğruluk tablosuyla göster.", "orta"),
    ("mantik", "Bir saat 12:00'da doğru kuruldu, 3 saatte 5 dakika geri kalıyor. Gerçek saat 21:00 iken saat kaçı gösterir?", "orta"),
    ("mantik", "Köpek, kedi ve kuş taşıyan bir adam nehri geçmek istiyor; kedi köpeği yiyor, kuş kediyi. Sıralama nedir?", "orta"),
    ("mantik", "'Bu cümle yanlıştır.' cümlesinin doğruluk değeri nedir? Paradoksu açıkla.", "zor"),
    ("mantik", "Üç kutu: biri yalnız elma, biri yalnız portakal, biri karışık. Hepsi yanlış etiketli. Tek elmayla bakarak kutuları bul.", "zor"),
    ("mantik", "Saatte 90 km giden bir tren 270 km'lik yolu kaç saatte alır? Formülü ver.", "kolay"),
    ("mantik", "Bir sayının 3 katının 6 eksiği, o sayının 2 katının 4 fazlasına eşit. Sayı kaç?", "orta"),
    ("mantik", "Bilardo topu ağırlık sorusu: 9 top var, biri ağır, eşit kollu teraziyle en az kaç tartımda bulunur?", "zor"),
    # ── bilim ──
    ("bilim", "Fotoelektrik etki nedir ve Einstein bunu nasil acikladi?", "orta"),
    ("bilim", "DNA'nin yapisini kisa ve anlasilir sekilde anlat.", "kolay"),
    ("bilim", "Yapay zeka ile makine ogrenmesi arasindaki fark nedir?", "kolay"),
    ("bilim", "Iki fotonun birbirleriyle dolanik olmasi ne demek?", "zor"),
    ("bilim", "Kuantum bilgisayari nerede klasik bilgisayardan ustun olur?", "orta"),
    ("bilim", "Fotosentezde klorofilin rolünü kısaca açıkla.", "kolay"),
    ("bilim", "Newton'un üçüncü yasasını roket veya rekolt örneğiyle anlat.", "kolay"),
    ("bilim", "Ozmoz nedir? İki yarı geçirgen örnekle açıkla.", "orta"),
    ("bilim", "CRISPR-Cas9 gen düzenlemesi nasıl çalışır? Adımlarıyla anlat.", "zor"),
    ("bilim", "Görünür ışık spektrumunda en yüksek frekans hangi renktir? Gerekçelendir.", "kolay"),
    ("bilim", "Termodinamiğin ikinci yasasını bir kupa kahve örneğiyle açıkla.", "orta"),
    ("bilim", "Evrenin genişlemesi kanıtlarından ikisini yaz (kırmızıya kayma, kozmik mikrodalga).", "orta"),
    ("bilim", "Asit ve baz arasındaki pH ölçeğinde limon ve sabun nerede durur?", "kolay"),
    ("bilim", "Yerçekimi dalgaları nereden gelir ve nasıl tespit edilir?", "zor"),
    ("bilim", "Plakalar tekraiği: depremlerin levha hareketiyle ilişkisi.", "orta"),
    # ── tarih ──
    ("tarih", "Osmanli Devleti'nin kurulusu hangi donemde gerceklesti ve kim kurdu?", "kolay"),
    ("tarih", "Ronesans neden Italya'da basladi?", "orta"),
    ("tarih", "Birinci Dunya Savasi'nin ana nedenlerini madde madde yaz.", "orta"),
    ("tarih", "Cumhuriyet ne zaman ilan edildi ve neyi sembolize eder?", "kolay"),
    ("tarih", "Tarihte 'Guclu Devlet' kavrami hangi donemde ortaya cikti?", "orta"),
    ("tarih", "İpek Yolu'nun tarihsel önemini 3 sonuçla özetle.", "kolay"),
    ("tarih", "Sanayi Devrimi'nin toplumsal etkilerinden üçünü yaz.", "orta"),
    ("tarih", "Magna Carta'nın 1215'teki anlamı bugünkü hukuk sisteme nasıl yansıdı?", "orta"),
    ("tarih", "Sami Fransız Devrimi'nin üç ana sloganını ve nedenlerini açıkla.", "kolay"),
    ("tarih", "Soğuk Savaş döneminde Berlin Duvarı'nın işlevi neydi?", "kolay"),
    ("tarih", "Roma İmparatorluğu'nun çöküş nedenlerinden ikisini derinlemesine analiz et.", "zor"),
    ("tarih", "Türk Dil Devrimi'nin amaçlarını ve etkilerini özetle.", "orta"),
    ("tarih", "Haçlı Seferleri'nin ekonomi ve kültür üzerindeki iki etkisini yaz.", "orta"),
    ("tarih", "İnka veya Aztek uygarlıklarından birinin tarım yöntemlerini anlat.", "zor"),
    ("tarih", "1950 Sonrası Avrupa Birliği'nin doğuş sürecini adım adım özetle.", "orta"),
    # ── yaratici ──
    ("yaratici", "Maviden baslayip kizila donen bir sehir manzarasi hikayesi yaz.", "orta"),
    ("yaratici", "Bir masal kahramani icin benzersiz bir guc tasarla ve acikla.", "orta"),
    ("yaratici", "Iki kelime: 'feridun', 'telefon'. Ikisini birlestiren komik kisa hikaye yaz.", "orta"),
    ("yaratici", "Bir logo icin 3 fikir oner: kahve dukkani.", "kolay"),
    ("yaratici", "5 maddelik 'dogayla uyumlu yasam' manifestosu yaz.", "kolay"),
    ("yaratici", "Bir deniz fenerinin gözünden 24 saatlik bir günü 5 cümleyle anlat.", "orta"),
    ("yaratici", "Bir zaman makinesiyle 2090'a giden bir öğrencinin günlüğünden 3 kayıt yaz.", "orta"),
    ("yaratici", "'Sessizlik' temasını somut bir nesne (ör. boş tabak) üzerinden şiirsel anlat.", "zor"),
    ("yaratici", "Bir süper kahramanın zayıf noktasını beklenmedik bir şey yap (ör. merdiven korkusu) ve hikaye kur.", "orta"),
    ("yaratici", "Bir ürün için beş duyuya birden hitap eden reklam metni yaz: yeni bir kahve.", "zor"),
    ("yaratici", "Bir bilim kurgu hikayesine açılış paragrafı yaz: 'Kapı açıldığında...'", "kolay"),
    ("yaratici", "Bir şehrin kıştan ilkbahara geçişini metaforlarla anlat.", "orta"),
    ("yaratici", "İki rakip şirketin yapay zekası insanlaştırılırsa neler konuşur? Diyalog yaz.", "zor"),
    ("yaratici", "Bir çocuk için 4 maddelik 'büyümenin kuralları' listesi yaz.", "kolay"),
    ("yaratici", "Kayıp bir notanın peşindeki bir müzisyenin mini öyküsünü yaz.", "orta"),
    # ── kultur ──
    ("kultur", "Turk kahvesi nasil yapilir? Adim adim anlat.", "kolay"),
    ("kultur", "Maskot kavrami nedir ve neden markalar icin onemlidir?", "kolay"),
    ("kultur", "Bayrak yarisi nedir? Acikla.", "orta"),
    ("kultur", "Bir turist icin Istanbul'da 3 gunluk gezi plani oner.", "orta"),
    ("kultur", "Dunyanin en kalabalik 5 sehrini isimlendir.", "kolay"),
    ("kultur", "Nevruz'un kültürel anlamını ve coğrafyasını açıkla.", "orta"),
    ("kultur", "Bir ülkenin milli mutfağında üç vazgeçilmez sosta ne bulunur? Örnek ver.", "orta"),
    ("kultur", "Cami, kilise ve sinagog mimarisinde ortak sembolik öğe nedir?", "kolay"),
    ("kultur", "'Mevlevi dönüşü' (sema) ritüelini saygılı ve bilimsel bir dille anlat.", "orta"),
    ("kultur", "Atasözü ve deyim farkını iki çift örnekle açıkla.", "kolay"),
    ("kultur", "Bir UNESCO Dünya Mirası'nı ve korunma nedenini seçip anlat.", "orta"),
    ("kultur", "Ramazan davulu geleneği nereden gelir ve günümüzde nasıl yaşar?", "orta"),
    ("kultur", "Bir halk oyununun (ör. horon, zeybek) ritim ve figür özelliğini açıkla.", "orta"),
    ("kultur", "Çayın bir ülke kültüründeki yerini örneklerle (Japon seremonisi gibi) karşılaştır.", "zor"),
    ("kultur", "Karikatürün siyasi tarihteki bir rolünü örnek olayla anlat.", "zor"),
    # ── pratik ──
    ("pratik", "Araba lastigi ne zaman degistirilmeli? Abartma, kisa anlat.", "kolay"),
    ("pratik", "Bir dakikada uykuya dalmak icin teknikler oner.", "kolay"),
    ("pratik", "Yemekte limon suyu yerine ne kullanabilirim?", "kolay"),
    ("pratik", "Sunger sifirlamak icin en hizli yontem nedir?", "kolay"),
    ("pratik", "Iyi bir sabah rutini icin 3 madde oner.", "kolay"),
    ("pratik", "Bir odayı küçük bütçeyle ferahlatmanın 4 yolu.", "orta"),
    ("pratik", "Seyahat ederken valiz hazırlamanın 5 kuralı.", "kolay"),
    ("pratik", "Islak telefonu kurtarma adımlarını yaz.", "kolay"),
    ("pratik", "Ev ofiste dikkat dağınıklığını azaltacak 3 teknik.", "orta"),
    ("pratik", "Sebzeleri buzdolabında taze tutmanın püf noktaları.", "kolay"),
    ("pratik", "Bir toplantıyı 15 dakikada etkili yönetme planı yaz.", "orta"),
    ("pratik", "Kıyafetteki çay lekesini evde çıkarma yöntemleri.", "kolay"),
    ("pratik", "Yeni başlayan için adım adım koşu programı (4 hafta).", "orta"),
    ("pratik", "Bütçe tutmanın en sade 3 yöntemi (kalem-kağıt dahil).", "kolay"),
    ("pratik", "Sürekli erteliyorsan deneyebileceğin '2 dakika' tekniğini açıkla.", "kolay"),
    # ── teknoloji ──
    ("teknoloji", "LLM olarak 'context window' nedir? Kisa ve net anlat.", "kolay"),
    ("teknoloji", "Vektorel veritabani ne ise yarar? Ornek ver.", "orta"),
    ("teknoloji", "Blockchain'in temel calisma mantigi nedir?", "orta"),
    ("teknoloji", "GPU neden onemlidir? Performans artisi nasil olur?", "kolay"),
    ("teknoloji", "Bir yapay zeka modelini nasil egitirsin? Adim adim.", "orta"),
    ("teknoloji", "HTTP ile HTTPS arasındaki farkı sertifika/şifreleme yönünden anlat.", "kolay"),
    ("teknoloji", "DNS'in çalışma adımlarını (tarayıcıdan siteye) özetle.", "orta"),
    ("teknoloji", "Edge computing neden bulut bilişimin yerine değil de tamamlayıcısıdır?", "orta"),
    ("teknoloji", "Sabit disk ile SSD arasındaki temel farkı hız/özen yönünden açıkla.", "kolay"),
    ("teknoloji", "Mikroservis mimarisinin tek parçalı (monolith) yapıya göre artı/eksisini yaz.", "zor"),
    ("teknoloji", "Bir CAPTCHA'nın amacı ve zayıf örnekleri nelerdir?", "kolay"),
    ("teknoloji", "OAuth 2.0 akışını (ör. üçüncü parti uygulama) sadeleştirilmiş adımlarla anlat.", "zor"),
    ("teknoloji", "Konteyner (Docker) ile geleneksel sanal makina farkı.", "orta"),
    ("teknoloji", "RAG (retrieval-augmented generation) nedir ve neden kullanılır?", "orta"),
    ("teknoloji", "Bir sunucunun ölçeklenmesi: dikey mi yatay mı? Koşullarıyla anlat.", "zor"),
]

# ── Beklenen yanıt tablosu (otomatik skorer için) ─────────────
# tur: "sayi" (sayısal/kesirli cevap) | "metin" (anahtar kavram varlığı)
# sonuc: kabul edilebilir değer/kavram listesi (büyük-küçük harf duyarsız eşleşir)
HEDEFLER = {
    # ── matematik ──
    "2+7*3-8/2 isleminin sonucu kactir? Adim adim goster.":
        {"tur": "sayi", "sonuc": ["19"]},
    "Bir dortgenin ic acilarinin toplami neden 360 derecedir?":
        {"tur": "metin", "sonuc": ["360"]},
    "Pi sayisinin kesirli yaklasik degerini ve neden dogru oldugunu anlat.":
        {"tur": "metin", "sonuc": ["22/7", "3.14", "3,14"]},
    "Bir sayinin asal olup olmadigini bulmanin en hizli yolu nedir?":
        {"tur": "metin", "sonuc": ["karekök", "kare kok", "karekok"]},
    "Olasilik: 6 yuzlu zar 2 kez atilinca iki kez 6 gelme ihtimali?":
        {"tur": "sayi", "sonuc": ["1/36", "0.027", "2.7"]},
    "%20 zam yapılan 150 TL'lik ürün, sonra %20 indirimle kaç TL olur?":
        {"tur": "sayi", "sonuc": ["144"]},
    "f(x)=3x+2 doğrusunun grafiğinin eğimi ve y-keseni nedir? Açıkla.":
        {"tur": "sayi", "sonuc": ["3", "2"]},
    "Üslerle çalışma: 2^10 u 2^3 un uslu yonunden ifade edip hesapla.":
        {"tur": "sayi", "sonuc": ["1024"]},
    "Bir küpün köşegen uzunluğu formülünü türet.":
        {"tur": "metin", "sonuc": ["√3", "kök 3", "karekök 3", "kökü 3"]},
    "Ortalama değer teoremini bir örnekle açıkla (kalkülüs).":
        {"tur": "metin", "sonuc": ["ortalama değer", "türev", "sürekl"]},
    "log2(64) + log3(81) kactir? Adim adim coz.":
        {"tur": "sayi", "sonuc": ["10"]},
    "Bir aritmetik dizinin ilk 50 terimini toplayan formülü ver (n=50, a1=3, d=2).":
        {"tur": "sayi", "sonuc": ["2600"]},
    "Pascal üçgeni ile (a+b)^4 açılımını yaz.":
        {"tur": "metin", "sonuc": ["a^4", "a⁴", "4a", "6a"]},
    "Karmaşık sayılar: (3+4i)(3-4i) işleminin sonucu ve anlamı nedir?":
        {"tur": "sayi", "sonuc": ["25"]},
    "Bayes teoremini tıbbi bir test örneğiyle açıkla (yanlış pozitif olgusunu içersin).":
        {"tur": "metin", "sonuc": ["bayes", "olasılık"]},
    # ── mantik ──
    "Bir dunyada tum kuzgunlar siyahtir. Beyaz bir kuzgun bulursak bu onermeyi nasil degisir?":
        {"tur": "metin", "sonuc": ["yanlış", "yanlis", "karşı örnek", "karsi ornek", "tümel"]},
    "Sudoku bulmaca cozumune nasil yaklasilir? Adim adim anlat.":
        {"tur": "metin", "sonuc": ["satır", "sutun", "kare", "ızgara"]},
    "Eger bugun carsamba ise yarin gunlerden ne?":
        {"tur": "metin", "sonuc": ["perşembe", "persembe"]},
    # ── dil ── (kavram bonusu)
    "'Ki' baglacinin yazim kurallarini orneklerle anlat.":
        {"tur": "metin", "sonuc": ["ayrı yazılır", "bitişik"]},
    "'da/de' bağlacının bitişik mi ayrı mı yazıldığını 2 örnekle ve gerekçesiyle anlat.":
        {"tur": "metin", "sonuc": ["ayrı"]},
    "'Degil' veya 'degil' hangisi dogru? Turkce imla kurallarini acikla.":
        {"tur": "metin", "sonuc": ["değil", "ayrı"]},
    "'Beni, eve giderken aradı' cümlesindeki virgülün anlamı nasıl değiştirdiğini yaz.":
        {"tur": "metin", "sonuc": ["virgül"]},
    "Noktalama: 'gelmedi dedi' ile 'gelmedi, dedi' arasındaki farkı açıkla.":
        {"tur": "metin", "sonuc": ["tırnak", "virgül", "aktarı"]},
}