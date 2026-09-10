"""Model Routing — konuya gore dogru modeli sec + tokeni bol tut.
Claude "az token + yuksek mantik" yapiyor. Bizim formulumuz:
  yuksek mantik + rakipten cok token = ustun cozum

Token limitlerini yuksek tut (Claude 128K'dan 2x-4x daha fazla cikti).
"""
import os

# Konu bazli model haritasi: (model_id, max_tokens, aciklama, neden_bu_model)
KONU_MODELLERI = {
    "kod": (
        "cohere/north-mini-code:free",
        32768,  # 2x Claude seviyesi
        "Kod uzmani + genis token butcesi: syntax ve calisan kod uret"
    ),
    "matematik": (
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        65536,  # 4x Claude seviyesi — adim adim goster, hata bul
        "Buyuk model: mantik agirlikli, uzun CoT cikti icin"
    ),
    "mantik": (
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        65536,  # 4x — karmasik problem cozumleri icin
        "Buyuk model: soyut dusunce, karmasik mantik agirlikli"
    ),
    "bilim": (
        "dots-studio/dots-3-note-preview:free",
        48000,  # 3x — bilimsel aciklama icin genis metin
        "Genis baglam: bilimsel bilgi + ornek + detay"
    ),
    "tarih": (
        "dots-studio/dots-3-note-preview:free",
        48000,  # 3x — tarihsel olay zinciri icin uzun anlatim
        "Tarihsel olaylar: neden-sonuc zinciri + donem baglami"
    ),
    "dil": (
        "dots-studio/dots-3-note-preview:free",
        24000,  # 2x — dil bilgisi aciklama + ornek
        "Turkce dilbilgisi: kural + ornek + karsi ornek"
    ),
    "yaratici": (
        "dots-studio/dots-3-note-preview:free",
        40000,  # 2.5x — uzun hikaye/masal icin
        "Yaratici yazi: uzun anlatim + detay + atmosfer"
    ),
    "kultur": (
        "dots-studio/dots-3-note-preview:free",
        24000,  # 2x — bilgi + ornek + baglami
        "Genel kultur: detayli bilgi + guncel ornekler"
    ),
    "pratik": (
        "dots-studio/dots-3-note-preview:free",
        16000,  # 1.5x — pratik ama yeterli
        "Pratik bilgi: uygulanabilir, kisa ama tam"
    ),
    "teknoloji": (
        "dots-studio/dots-3-note-preview:free",
        48000,  # 3x — teknik derinlik icin
        "Teknoloji: derin analitik, teknik terim + ornek"
    ),
}

DEFAULT_MODEL = "dots-studio/dots-3-note-preview:free"
DEFAULT_MAX = 32768

def model_sec(konu):
    """Konuya gore model ve max_tokens dondur."""
    model, maxt, _, _ = KONU_MODELLERI.get(konu, (DEFAULT_MODEL, DEFAULT_MAX, "Varsayilan", ""))
    return model, maxt

def konu_aciklama(konu):
    """Konunun neden o modelde secildigini acikla."""
    _, _, aciklama, neden = KONU_MODELLERI.get(konu, (DEFAULT_MODEL, DEFAULT_MAX, "Varsayilan", ""))
    return f"{aciklama}. {neden}"