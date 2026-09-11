"""Akıl Motoru — Claude'un "az token + yüksek mantık" felsefesini ZenAI'ne taşır.
Mantığı keskinleştiren akıl yürütme katmanı + rakip'ten çok token.

Formül:
  Adım 1: COT (Düşunce Zinciri) — model önce adım adım düşünür (12 sn büyüklüğü)
  Adım 2: ÜRETİM — düşüncelerine dayanarak KAPSAMLI ve TÜRKÇE cevap üretir
  Adım 3: DOĞRULAMA — kendi cevabını kontrol eder, kaçak hata varsa düzeltir

Sonuç: Hem mantık (adım 1+3) hem token (adım 2) kazandırır.

NOT: Claude "az token + yüksek mantık" yapıyor; biz ise "yüksek mantık + rakip'ten çok token"
şeklinde yaklaşımımızla üstün çözüm hedefliyoruz. Sistem promptu hedef olarak bu_formula'yı
tavsiye eder, zorlamaz.
"""
import time, re

# CoT promptları: konuya göre "önce düşün sonra yaz" talimatı.
# Bunlar modelin adım adım düşünmesini ve yazarken mantık taşımasını sağlar.
KONU_YONTEM = {
    "matematik": (
        "YONTEM: Önce problemi parçala ve adım adım çöz (adımları yaz, hesapla). "
        "Son adımda sonucu **büyük ve net** yaz. Yanlışsa bile adımında görünür olsun."
    ),
    "mantik": (
        "YONTEM: Önce onermeleri ayır, küçük dizilimlerle çöz. "
        "Sonra genel sonuç çıkar. Her adımı gerekçelendir."
    ),
    "kod": (
        "YONTEM: Önce ne isteniyor analiz et. Sonra algoritmalarla community'de en iyi örneği düşün. "
        "Kodu yaz, **çalıştıği doğru kurallara** uy (syntax + mantık)."
    ),
    "dil": (
        "YONTEM: Cümleyi parçala, kuralı hatırla, örnekle pekiştir."
    ),
    "bilim": (
        "YONTEM: Önce temel prensibi hatırla, sonra detaylandır, sonra kısa örnek ver."
    ),
    "tarih": (
        "YONTEM: Dönemi hatırla, neden-sonuç zincirini kur."
    ),
    "yaratici": (
        "YONTEM: Önce temayı kur (kim/neden/hangi ortam), sonra kategori ve ton. "
        "Sonra yaz, her paragraf ana ders üzerine kursun."
    ),
    "kultur": (
        "YONTEM: Bilgiyi hatırla, basit ve pratik cevap al, örnekle aç."
    ),
    "pratik": (
        "YONTEM: Kısa, net, uygulanabilir. Üç adımlı cevap ver."
    ),
    "teknoloji": (
        "YONTEM: Önce temel prensip, sonra nasıl çalıştığı, sonra neden önemli."
    ),
}

# Kapsam (uzunluk) seviyeleri: Claude kısa yazar, biz rakip'ten çok yazacağız.
# "uzun" seviyesi = rakip detay seviyesinden > 2x çıktı tokensi üretir.
KAPSAM = {
    "kisa": 1200,
    "normal": 2500,
    "uzun": 5000,
}

def yontem(konu):
    """Konuya göre CoT yöntem talimatı."""
    return KONU_YONTEM.get(konu, KONU_YONTEM["pratik"])

# SISTEM PROMPTU: modele ÖZEL akıl yürütme talimatı içerir.
def sistem_promptu(konu=None, kapsam="uzun", seviye="duzgun"):
    """Akıl motoru sistem promptu: CoT + kapsam + doğrulama."""
    y = yontem(konu) if konu else yontem("pratik")
    butce = KAPSAM.get(kapsam, 2500)
    hedef = "Claude benzeri detay ve kapsam"
    return (
        "Sen ZenAI'sin, akıl yürütme paketi. Türkçe konuşuyorsun.\n\n"
        + y + "\n\n"
        + f"HEDEF: Cevapların {hedef} olsun. Kısa kesme aramadan, tüm yönlerini açıkla. "
        f"Cevabın yaklaşık {butce} kelimeden az olmamalı.\n"
        "ADIM ADIM: (1) önce düşün, (2) cevabı KAPSAMLI yaz, "
        "(3) kendi cevabını yeniden oku, mantık hatası / eksik var mı, varsa düzelt.\n"
        f"TÜRKÇE cevap ver, bol madde, başlık ve örnek kullan. Seviye: {seviye}."
    )

def birim_mantik_skoru(cevap):
    """Cevabın mantık tamamlayıcılığı: adım sayısı + net sonuç."""
    skor = 0.0
    # Madde/başlık yapısı = adımlar toplam
    adimlar = len(re.findall(r'(?m)^[\s]*[-\*\d]+[\.\)\s]', cevap))
    if adimlar >= 4: skor += 0.4
    elif adimlar >= 2: skor += 0.2
    # Sonuç/açık büyük ifade var mı
    if re.search(r'(\*\*sonuç|sonuç\s*:|\bet sonuc\b|son hali|\bfinal\b)', cevap, re.I):
        skor += 0.3
    # Uzun ve dolu ise
    kelime = len(cevap.split())
    if kelime >= 800: skor += 0.3
    elif kelime >= 300: skor += 0.15
    return min(skor, 1.0)
