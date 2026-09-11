"""Model Routing — konuya göre doğru modeli seç + tokeni bol tut.
Claude "az token + yüksek mantık" yapiyor. Bizim formulumuz:
  yüksek mantık + rakip'ten çok token = üstün çözüm

Token limitlerini yüksek tut (Claude 128K'dan 2x-4x daha fazla çıktı).
Kod modülü: free tier ağırlıklı; önceki deepseek hesabı (bakiye sona erdi) → free kod uzmanına geri dönüldü.
"""
import os

# Konu bazlı model haritası: (model_id, max_tokens, açıklama)
KONU_MODELLERI = {
    "kod": (
        "cohere/north-mini-code:free",
        65536,  # kod uzmanı + geniş token (free tier)
        "Kod uzmanı (free): syntax + çalışan kod üret"
    ),
    "matematik": (
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        65536,  # 4x Claude seviyesi — adım adım göster, hata bul
        "Büyük model: mantık ağırlıklı, uzun CoT çıktısı için"
    ),
    "mantik": (
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        65536,  # 4x — karmaşık problem çözümleri için
        "Büyük model: soyut düşünce, karmaşık mantık ağırlıklı"
    ),
    "bilim": (
        "dots-studio/dots-3-note-preview:free",
        48000,  # 3x — bilimsel açıklama için geniş metin
        "Geniş bağlam: bilimsel bilgi + örnek + detay"
    ),
    "tarih": (
        "dots-studio/dots-3-note-preview:free",
        48000,  # 3x — tarihsel olay zinciri için uzun anlatım
        "Tarihsel olaylar: neden-sonuç zinciri + dönem bağlamı"
    ),
    "dil": (
        "dots-studio/dots-3-note-preview:free",
        24000,  # 2x — dil bilgisi açıklama + örnek
        "Türkçe dilbilgisi: kural + örnek + karşı örnek"
    ),
    "yaratici": (
        "dots-studio/dots-3-note-preview:free",
        40000,  # 2.5x — uzun hikaye/masal için
        "Yaratıcı yazı: uzun anlatım + detay + atmosfer"
    ),
    "kultur": (
        "dots-studio/dots-3-note-preview:free",
        24000,  # 2x — bilgi + örnek + bağlamsal
        "Genel kültür: detaylı bilgi + güncel örnekler"
    ),
    "pratik": (
        "dots-studio/dots-3-note-preview:free",
        16000,  # 1.5x — pratik ama yeterli
        "Pratik bilgi: uygulanabilir, kısa ama tam"
    ),
    "teknoloji": (
        "dots-studio/dots-3-note-preview:free",
        48000,  # 3x — teknik derinlik için
        "Teknoloji: derin analitik, teknik terim + örnek"
    ),
}

DEFAULT_MODEL = "dots-studio/dots-3-note-preview:free"
DEFAULT_MAX = 32768

def model_sec(konu):
    """Konuya göre model ve max_tokens döndür."""
    model, maxt, _ = KONU_MODELLERI.get(konu, (DEFAULT_MODEL, DEFAULT_MAX, "Varsayılan"))
    return model, maxt

# ── Fallback zinciri (429/401/404 durumunda otomatik geçiş) ──────────────
FALLBACK_ZINCIRI = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "openrouter/auto",
    "qwen/qwen-3-coder-flash",
    "meta-llama/llama-3.3-70b-instruct:free",
]

def model_fallback(model):
    """Verilen modelin ardındaki denenebilir yedek modelleri döndürür.
    (model, maxt) girdisine model adı verilir; kalan linkler paylaşılır."""
    sira = []
    for m in FALLBACK_ZINCIRI:
        if m != model:
            sira.append(m)
    return sira

def model_sec_hepsi(konu):
    """Konu için (birincil + fallback) model listesi döndürür.
    Tam zirve akışında 429/402/404 görürse sıralamayı deneler."""
    birincil, maxt, _ = KONU_MODELLERI.get(konu, (DEFAULT_MODEL, DEFAULT_MAX, "Varsayılan"))
    return [birincil] + [m for m in FALLBACK_ZINCIRI if m != birincil], maxt

def konu_aciklama(konu):
    """Konunun neden o modelde seçildiğini açıkla."""
    _, _, aciklama = KONU_MODELLERI.get(konu, (DEFAULT_MODEL, DEFAULT_MAX, "Varsayılan model"))
    return aciklama

# ── Veri odaklı routing: her gerçek sonucu logla ──
def routing_logla(konu, soru, model, skor, sure=None, kelime=None):
    """Test sonucunu kayıta işler; routing kuralları veriyle güncellenebilir."""
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
    """Loglardan hangi model hangi konuda kazanıyor özetler."""
    import os, glob, json
    sayilar = {}
    dizin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kayit")
    dosyalar = glob.glob(os.path.join(dizin, "routing_log.jsonl")) or glob.glob("kayit/routing_log.jsonl")
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
    """Loglara göre konu için en iyi modeli öner (veri varsa)."""
    rapor = routing_rapor().get(konu or "")
    if rapor and rapor[0]["adet"] >= 3:
        return rapor[0]["model"]
    return None
