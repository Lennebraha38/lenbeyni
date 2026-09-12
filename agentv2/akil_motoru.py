from typing import Optional, Tuple, List, Dict, Any
"""Akıl Motoru — Claude'un "az token + yüksek mantık" felsefesini ZenAI'ne taşır.
Mantigi keskinlestiren akil yurutme katmani + rakipten cok token.

Formul:
  Adim 1: COT (Dusunce Zinciri) — model once adim adim dusunur (12 sn butcesi)
  Adim 2: URETIM — dusuncelerine dayanarak KAPSAMLI ve TURKCE cevap uretir
  Adim 3: DOGRULAMA — kendi cevabini kontrol eder, kacak hata varsa duzeltir

Sonuc: Hem mantik (adim 1+3) hem token (adim 2) kazandirir.
"""
import time, re

# CoT promptlari: konuya gore "once dusun sonra yaz" talimati.
# Bunlar modelin adim adim dusunmesini ve yazarken mantik caryurtmesini saglar.
KONU_YONTEM = {
    "matematik": (
        "YONTEM: Once problemi parcala ve adim adim coz (adimlari yaz, hesapla). "
        "Son adimda sonucu **buyuk ve net** yaz. Yanlissa bile adiminda gorunur olsun."
    ),
    "mantik": (
        "YONTEM: Once onermeleri ayir, kucuk dizilimlerle coz. "
        "Sonra genel sonuc cikar. Her adimi gerekcelendir."
    ),
    "kod": (
        "YONTEM: Once ne isteniyor analiz et. Sonra alglarla community'de en iyi ornegi dusun. "
        "Kodu yaz, **calistigi duzgun kurallara** uy (syntax + mantik)."
    ),
    "dil": (
        "YONTEM: Cumleyi parcala, kurali hatirla, ornekle pekistir."
    ),
    "bilim": (
        "YONTEM: Once temel prensibi hatirla, sonra detaylandir, sonra kisa ornek ver."
    ),
    "tarih": (
        "YONTEM: Donemi hatirla, neden-sonuc zincirini kur."
    ),
    "yaratici": (
        "YONTEM: Once temayi kur (kim/neden/hangi ortam), sonra kategori ve ton. "
        "Sonra yaz, her paragraf ana duser uzerine kursun."
    ),
    "kultur": (
        "YONTEM: Bilgiyi hatirla, basit ve praktik cevap al, ornekle ac."
    ),
    "pratik": (
        "YONTEM: Kisa, net, uygulanabilir. Uc adimli cevap ver."
    ),
    "teknoloji": (
        "YONTEM: Once temel prensip, sonra nasil calistigi, sonra neden onemli."
    ),
}

# Kapsam (uzunluk) seviyeleri: Claude kisa yazar, biz rakipten cok yazacagiz.
# "uzun" seviyesi = rakip detay seviyesi > 2x cikti tokeni uretir.
KAPSAM = {
    "kisa": 1200,
    "normal": 2500,
    "uzun": 5000,
}

def yontem(konu: str) -> str:
    """Konuya gore CoT yontem talimati."""
    return KONU_YONTEM.get(konu, KONU_YONTEM["pratik"])

# SISTEM PROMPTU: modele OZEL akil yurutme talimati icerir.
def sistem_promptu(konu: Optional[str] = None, kapsam: str = "uzun", seviye: str = "duzgun") -> str:
    """Akil motoru sistem promptu: CoT + kapsam + dogrulama."""
    y = yontem(konu) if konu else yontem("pratik")
    butce = KAPSAM.get(kapsam, 2500)
    hedef = "claude'den cok daha ayrintili ve kapsamli"
    return (
        "Sen ZenAI'sin, akil yurutme paketi. Turkce konusuyorsun.\n\n"
        + y + "\n\n"
        + f"HEDEF: Cevaplarin {hedef}. Kisa kesme aramadan, tum yonlariyla acikla. "
        f"Cevabin yaklasik {butce} kelimeden az olmamali.\n"
        "ADIM ADIM: (1) once dusun, (2) cevabi KAPSAMLI yaz, "
        "(3) kendi cevabini yeniden oku, mantik hatasi / eksik var mi, varsa duzelt.\n"
        f"TURKCE cevap ver, bol madde, baslik ve ornek kullan. Seviye: {seviye}."
    )

def birim_mantik_skoru(cevap: str) -> float:
    """Cevabin mantik tamamlayiciligi: yapi + muhakeme baglaçlari + net sonuc.
    Sadece madde/kelime saymak yerine muhakeme izlerini arar:
    neden-sonuc, karsilastirma, sartli cikarim ve net sonuc."""
    skor = 0.0
    metin = cevap.lower()

    # 1) Yapi: adim/baslik sayisi (cozum yolunun gorunurlugu)
    adimlar = len(re.findall(r'(?m)^[\s]*[-\*\d]+[\.\)\s]', cevap))
    if adimlar >= 4:
        skor += 0.3
    elif adimlar >= 2:
        skor += 0.15

    # 2) Muhakeme baglaçlari: neden-sonuc / karsilastirma / sart
    baglac = sum(bool(re.search(k, metin)) for k in [
        r'\b(cunku|dolayisiyla|bu yuzden|bu nedenle|sonuc olarak)\b',   # neden-sonuc
        r'\b(ancak|fakat|oysa|buna ragmen)\b',                          # karsitlik
        r'\b(eger|ise|sartli|kosuluyla)\b',                             # sartli cikarim
        r'\b(karsilastir|fark|benzer|ortak)\b',                         # analiz
        r'\b(ornegin|soyle ki|mesela|ornek|misal)\b',                   # somutlama
        r'\b(adim|once|sonra|en sonunda|ardindan|ilk olarak)\b',        # surec
    ])
    skor += min(baglac * 0.08, 0.3)

    # 3) Net sonuc / karar ifadesi
    if re.search(r'(\*\*sonuç|sonuç\s*:|\bet sonuc\b|\bfinal\b|\bkarar\b|\blogical\b)', metin):
        skor += 0.25

    # 4) Icten tutarlilik: zit iddialar ayni cevapta yoksa
    if not re.search(r'\b(evet.*\bhayir|dogru.*\byanlis|var.*\byok)\b', metin):
        skor += 0.15

    # 5) Uzunluk artik kucuk bonus (yapiyla lineer bagimlilik yok)
    kelime = len(cevap.split())
    if kelime >= 300:
        skor += 0.1
    elif kelime >= 120:
        skor += 0.05

    return min(skor, 1.0)