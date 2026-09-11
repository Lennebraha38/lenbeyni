"""ZenAI Bagimsiz Dogrulama Seti — disaridan bilinen gercekler, mutlak cevap.

HEDEFLER'den tasarlanmis ana benchmarktan tamamen bagimsizdir (soru sizmasi
leak'i onlenir). Her cevap strict eslestirmeyle puanlanir: ya dogru ya yanlis.
Bu set "gercekten zeki mi" sorusuna puff verir; uzunluk/yapi puani vermez.

Her kayit: (konu, soru, kabul_listesi)
"""

INDEPENDENT = [
    # ── matematik ──
    ("matematik", "2 + 2 isleminin sonucu kactir?", ["4", "dort"]),
    ("matematik", "144'un karekoku kactir?", ["12", "on iki"]),
    ("matematik", "Bir kenari 5 cm olan karenin alani kac cm karedir?", ["25", "yirmi bes"]),
    ("matematik", "200 TL'nin yuzde 15'i kac TL'dir?", ["30", "otuz"]),
    ("matematik", "17 sayisi asal midir? (Evet mi Hayir mi?)", ["evet", "asaldir", "asalde", "asal"]),
    ("matematik", "Bir dortgenin ic acilarinin toplami kac derecedir?", ["360", "360 derece", "360°", "uc yuz altmis"]),
    ("matematik", "8 ile 6'nin carpimi kactir?", ["48", "kirk sekiz"]),
    ("matematik", "Pi sayisinin en bilinen yaklasik degeri nedir?", ["3.14", "3,14", "22/7", "3.14159"]),
    # ── bilim ──
    ("bilim", "Suyun kimyasal formulu nedir?", ["h2o", "h20"]),
    ("bilim", "Gunes sisteminde kac gezegen vardir?", ["8", "sekiz"]),
    ("bilim", "Fotosentezde bitkiler hangi gazi uretir?", ["oksijen", "o2", "oksijendir"]),
    ("bilim", "Suyun deniz seviyesinde kaynama sicakligi kac derecedir?", ["100", "100 derece", "100°", "yuz derece"]),
    ("bilim", "Isigin bosluktaki yaklasik hizi kac km/saniyedir?", ["300000", "299792"]),
    # ── tarih ──
    ("tarih", "Osmanli Devleti'nin kurulus yili neydir?", ["1299"]),
    ("tarih", "Turkiye Cumhuriyeti hangi yil ilan edildi?", ["1923"]),
    ("tarih", "Istanbul hangi yil fethedildi?", ["1453"]),
    ("tarih", "2. Dunya Savasi hangi yil sona erdi?", ["1945"]),
    ("tarih", "TBMM hangi yil acildi?", ["1920"]),
    # ── kultur / cografya ──
    ("kultur", "Turkiye'nin baskenti hangi sehirdir?", ["ankara"]),
    ("kultur", "Turkiye'nin en kalabalik sehri hangisidir?", ["istanbul"]),
    ("kultur", "Dunyanin en uzun nehri hangisidir?", ["nil"]),
    ("kultur", "Turkiye'nin kara komşusu olan ulke sayisi kactir?", ["8"]),
    ("kultur", "Iki kita uzerinde kurulu tek Turk sehri hangisidir?", ["istanbul"]),
    ("kultur", "Turkiye'nin en yuksek dagi hangisidir?", ["agri", "ararat", "agri dagi", "agri dagidir"]),
    # ── dil ──
    ("dil", "Turk alfabesinde kac harf vardir?", ["29", "yirmi dokuz", "yirmi dokuzdur"]),
    ("dil", "'kitap' kelimesinin cogulu nedir?", ["kitaplar", "kitaplardir"]),
    ("dil", "'gitmek' fiilinin gelecek zaman 1. tekil kisi hali nedir?", ["gidecegim", "gideceğim"]),
    ("dil", "'elmalar' kelimesindeki '-lar' ekinin adi nedir?", ["cogul", "cogul eki", "cokluk", "cokluk eki"]),
    ("dil", "'benim kitap__' cumlesinde kitap kelimesinin iyelik 1. tekil hali nedir?", ["kitabim", "kitabım"]),
    # ── teknoloji ──
    ("teknoloji", "HTTP protokolunun varsayilan portu kactir?", ["80", "seksen"]),
    ("teknoloji", "1 GB kac MB eder?", ["1024"]),
    ("teknoloji", "1 MB kac KB eder?", ["1024"]),
    ("teknoloji", "Bir IPv4 adresi kac bitten olusur?", ["32", "otuz iki"]),
    ("teknoloji", "ASCII tablosunda 'A' harfinin ondalik karsiligi kactir?", ["65", "altmis bes"]),
    # ── pratik ──
    ("pratik", "Bir duzine kac adettir?", ["12", "on iki"]),
    ("pratik", "Bir haftada kac gun vardir?", ["7", "yedi"]),
    ("pratik", "1 kilogram kac gram eder?", ["1000", "bin"]),
    ("pratik", "1 saatte kac dakika vardir?", ["60", "altmis"]),
    # ── mantik ──
    ("mantik", "Ali, Ayse'den buyuk. Ayse, Veli'den buyuk. En kucuk kim?", ["veli", "velidir"]),
    ("mantik", "Butun kuslar tuyludur. Serce bir kustur. Serce tuylu mudur?", ["evet", "tuylu", "tuyludur", "dogru"]),
]