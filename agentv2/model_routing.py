"""Model Routing — konuya gore dogru modeli sec.
Her konu icin en uygun modeli belirle, hiz/kalite dengesini koru.
"""
import os

# Konu bazli model haritasi: (model_id, max_tokens, aciklama)
KONU_MODELLERI = {
    "kod": (
        "cohere/north-mini-code:free",  # Kod uzmanı (küçük ama kodda iyi)
        16384,
        "Kod uzmani model"
    ),
    "matematik": (
        "nvidia/nemotron-3-ultra-550b-a55b:free",  # 550B, matematik güçlü
        8192,
        "Buyuk model - mantik/matematik icin"
    ),
    "mantik": (
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        8192,
        "Buyuk model - mantik icin"
    ),
    "bilim": (
        "dots-studio/dots-3-note-preview:free",  # 512K ctx, genis bilgi
        16384,
        "Genis baglam - bilim icin"
    ),
    "tarih": (
        "dots-studio/dots-3-note-preview:free",
        16384,
        "Genis baglam - tarih icin"
    ),
    "dil": (
        "dots-studio/dots-3-note-preview:free",
        8192,
        "Dil bilgisi icin"
    ),
    "yaratici": (
        "dots-studio/dots-3-note-preview:free",
        16384,
        "Yaratici yazi icin genis cikti"
    ),
    "kultur": (
        "dots-studio/dots-3-note-preview:free",
        8192,
        "Genel kultur icin"
    ),
    "pratik": (
        "dots-studio/dots-3-note-preview:free",
        4096,
        "Kisa pratik bilgi icin"
    ),
    "teknoloji": (
        "dots-studio/dots-3-note-preview:free",
        16384,
        "Teknoloji icin genis baglam"
    ),
}

# Varsayilan model (taninmayan konular icin)
DEFAULT_MODEL = "dots-studio/dots-3-note-preview:free"
DEFAULT_MAX = 16384

def model_sec(konu):
    """Konuya gore model ve max_tokens dondur."""
    model, maxt, _ = KONU_MODELLERI.get(konu, (DEFAULT_MODEL, DEFAULT_MAX, "Varsayilan"))
    return model, maxt

def konu_aciklama(konu):
    """Konunun neden o modelde secildigini acikla."""
    _, _, aciklama = KONU_MODELLERI.get(konu, (DEFAULT_MODEL, DEFAULT_MAX, "Varsayilan model"))
    return aciklama
