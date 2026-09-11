"""Model Routing — konuya gore dogru modeli sec + tokeni bol tut.
Claude "az token + yuksek mantik" yapiyor. Bizim formulumuz:
  yuksek mantik + rakipten cok token = ustun cozum

Token limitlerini yuksek tut (Claude 128K'dan 2x-4x daha fazla cikti).
"""
import os

# Konu bazli model haritasi: (model_id, max_tokens, aciklama)
# Kod: free-tier anahtarda deepseek 402 (bakiye yok) -> free kod uzmanina geri.
KONU_MODELLERI = {
    "kod": (
        "cohere/north-mini-code:free",
        65536,  # kod uzmani + genis token (deepseek bakiye olunca 402 -> free'ye don)
        "Kod uzmani (free): syntax + calisan kod uret"
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
    model, maxt, _ = KONU_MODELLERI.get(konu, (DEFAULT_MODEL, DEFAULT_MAX, "Varsayilan"))
    return model, maxt

def konu_aciklama(konu):
    """Konunun neden o modelde secildigini acikla."""
    _, _, aciklama = KONU_MODELLERI.get(konu, (DEFAULT_MODEL, DEFAULT_MAX, "Varsayilan model"))
    return aciklama

# ── Veri odakli routing: her gercek sonucu logla ──
def routing_logla(konu, soru, model, skor, sure=None, kelime=None):
    """Test sonucunu kayide isler; routing kurallari veriyle guncellenebilir."""
    import os, time, json
    dizin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kayit")
    os.makedirs(dizin, exist_ok=True)
    dosya = os.path.join(dizin, "routing_log.jsonl")
    satir = {
        "zaman": time.time(), "konu": konu, "soru": soru[:80],
        "model": model, "skor": round(float(skor), 3),
        "sure": sure, "kelime": kelime,
    }
    try:
        with open(dosya, "a") as f:
            f.write(json.dumps(satir, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return satir

def routing_rapor():
    """Loglardan hangi model hangi konuda kazaniyor ozetler."""
    import os, glob, json
    sayilar = {}
    dosyalar = glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kayit", "routing_log.jsonl")) or glob.glob("kayit/routing_log.jsonl")
    for dosya in dosyalar:
        try:
            with open(dosya) as f:
                for satir in f:
                    try:
                        d = json.loads(satir)
                    except Exception:
                        continue
                    ana = (d.get("konu"), d.get("model"))
                    k, n, s = sayilar.get(ana, (0, 0, 0.0))
                    sayilar[ana] = (k + 1, n + d.get("kelime") or 0, s + (d.get("skor") or 0))
        except Exception:
            continue
    rapor = {}
    for (konu, model), (k, n, s) in sorted(sayilar.items()):
        rapor.setdefault(konu, []).append({
            "model": model, "adet": k, "ortalama": round(s / k, 3), "toplam_kelime": n})
    for konu in rapor:
        rapor[konu].sort(key=lambda x: x["ortalama"], reverse=True)
    return rapor

def model_profil(konu):
    """Loglara gore konu icin en iyi modeli oner (veri varsa)."""
    rapor = routing_rapor().get(konu or "")
    if rapor and rapor[0]["adet"] >= 3:
        return rapor[0]["model"]
    return None