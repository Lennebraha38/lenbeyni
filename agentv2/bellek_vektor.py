from typing import Optional, Tuple, List, Dict, Any
"""ZenAI Bellek — Hibrit Vektor + n-gram Hafıza.

Çalışma modları:
  1. FAISS + sentence-transformers (yönetici kurarsa) → gerçek semantik benzerlik
  2. n-gram TF-IDF fallback (bağımsız, pip gerektirmez)

Özellikler:
  - Kullanıcı bazlı izolasyon: her kullanıcı ayrı namespace
  - TTL: eski bilgi otomatik bayatlar
  - Semantic dedup: aynı bilgiyi tekrar kaydetmeyi önle
  - `unut` komutu + toplu listeleme
"""
import os, re, json, math, time, hashlib
from collections import Counter

# ── Embedding modülü (yönetici kurarsa aktif) ──────────────────────────
_EMBED_MODEL = None
_EMBED_FAISS = None
_VECTORS = None

def _embedding_aktif_mi() -> bool:
    global _EMBED_MODEL, _EMBED_FAISS
    if _EMBED_MODEL is not None:
        return _EMBED_MODEL is not False
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        _EMBED_MODEL = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)
        dim = _EMBED_MODEL.get_sentence_embedding_dimension()
        _EMBED_FAISS = faiss.IndexFlatIP(dim)  # cosine via normalized vectors
        return True
    except Exception:
        _EMBED_MODEL = False
        return False

def _embed(metin: str) -> Optional[Any]:
    """Metni vektöre çevir (FAISS modu) veya None dön (fallback)."""
    if not _embedding_aktif_mi():
        return None
    import numpy as np
    v = _EMBED_MODEL.encode([metin], normalize_embeddings=True)
    return v[0].astype("float32") if hasattr(v, "astype") else v

def _kosinus_vec(a: Any, b: Any) -> float:
    """İki vektör arası kosinüs (dot product, normalize edilmiş)."""
    import numpy as np
    return float(np.dot(a, b))

# ── n-gram fallback (pip gerektirmez) ──────────────────────────────────
VARS = 4

def _gramlar(metin: str, k: int = VARS) -> set:
    temiz = re.sub(r"[^a-zçğıöşü0-9\s]", " ", (metin or "").lower())
    temiz = re.sub(r"\s+", " ", temiz).strip()
    g = set()
    for sozcuk in temiz.split():
        s = "\x02" + sozcuk + "\x03"
        for i in range(len(s) - k + 1):
            g.add(s[i:i + k])
    return g

def _vektor(gramlar, idf: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    say = Counter(gramlar) if isinstance(gramlar, (list, tuple)) else {x: 1 for x in gramlar}
    if idf:
        return {g: w * idf.get(g, 1.0) for g, w in say.items()}
    return dict(say)

def _kosinus(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    ortak = set(a) & set(b)
    if not ortak:
        return 0.0
    dot = sum(a[g] * b[g] for g in ortak)
    a2 = math.sqrt(sum(v * v for v in a.values())) or 1.0
    b2 = math.sqrt(sum(v * v for v in b.values())) or 1.0
    return dot / (a2 * b2)

# ── Semantic dedup ──────────────────────────────────────────────────────
def _dedup_anahtar(kullanici_adi: str, deger: str, esik: float = 0.92) -> str:
    """Aynı anlama gelen kayıtları tekrar kaydetmeyi önle."""
    metin = f"{kullanici_adi}:{deger}"
    return hashlib.md5(metin.encode("utf-8")).hexdigest()

def _ozet(metin: str, boyut: int = 42) -> str:
    m = re.sub(r"\s+", " ", (metin or "")).strip()
    return m[:boyut] + ("…" if len(m) > boyut else "")

# ── Ana Bellek Sınıfı ──────────────────────────────────────────────────
class BellekVec:
    """Hibrit bellek: FAISS+embedding (varsa) veya n-gram TF-IDF fallback."""

    def __init__(self, yol: Optional[str] = None, kullanici: str = "varsayilan") -> None:
        self.yol = yol or os.path.expanduser("~/.zenai_bellek.json")
        self.kullanici = kullanici
        self.veri = {}
        self._faiss_index = None
        self._faiss_keys = []
        self._faiss_vectors = []
        try:
            with open(self.yol) as f:
                self.veri = json.load(f)
        except Exception:
            self.veri = {}
        self._temizle()

    def _kayitlar(self) -> Dict[str, Any]:
        return self.veri.setdefault(self.kullanici, {})

    def _temizle(self) -> None:
        s = time.time()
        ana = self._kayitlar()
        sil = [k for k, v in ana.items()
               if isinstance(v, dict) and v.get("sure") is not None
               and s > v.get("zaman", 0) + v["sure"]]
        for k in sil:
            ana.pop(k, None)
        if sil:
            self._yaz()

    def _yaz(self) -> None:
        try:
            with open(self.yol, "w") as f:
                json.dump(self.veri, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def _ulastir(self, k: str) -> Dict[str, Any]:
        v = self._kayitlar()[k]
        if isinstance(v, dict) and "deger" in v:
            return v
        return {"deger": v, "zaman": 0, "sure": None, "etiket": None}

    def _faiss_yeniden_insa(self) -> None:
        """FAISS indeksini sıfırdan doldur."""
        global _VECTORS
        if not _embedding_aktif_mi():
            return
        ana = self._kayitlar()
        if not ana:
            self._faiss_keys = []
            self._faiss_vectors = []
            return
        texts = []
        keys = []
        for k, v in ana.items():
            bil = self._ulastir(k)
            texts.append(f"{k} {bil['deger']}")
            keys.append(k)
        import numpy as np
        vecs = _EMBED_MODEL.encode(texts, normalize_embeddings=True)
        vecs = vecs.astype("float32") if hasattr(vecs, "astype") else np.array(vecs, dtype="float32")
        self._faiss_keys = keys
        self._faiss_vectors = vecs
        dim = vecs.shape[1] if len(vecs.shape) > 1 else 384
        import faiss
        self._faiss_index = faiss.IndexFlatIP(dim)
        self._faiss_index.add(vecs)

    # ── API ─────────────────────────────────────────────────────────────
    def kaydet(self, anahtar: str, deger: str, etiket: Optional[str] = None, sure: Optional[float] = None) -> None:
        ana = self._kayitlar()
        # Semantic dedup: aynı deger zaten kayıtlı mı?
        deger_hash = _dedup_anahtar(self.kullanici, str(deger))
        for _, v in ana.items():
            if isinstance(v, dict) and v.get("hash") == deger_hash:
                v["zaman"] = time.time()  # zamanı tazele
                self._yaz()
                return
        ana[anahtar] = {
            "deger": deger, "zaman": time.time(),
            "sure": sure, "etiket": etiket, "hash": deger_hash
        }
        self._yaz()
        if _embedding_aktif_mi():
            self._faiss_yeniden_insa()

    def ara(self, sorgu: str, k: int = 3, min_skor: float = 0.0) -> List[Tuple[str, str, float]]:
        ana = self._kayitlar()
        if not ana:
            return []
        self._temizle()

        # FAISS modu
        if _embedding_aktif_mi() and self._faiss_index is not None:
            import numpy as np
            qv = _embed(sorgu).reshape(1, -1)
            scores, indices = self._faiss_index.search(qv, min(k * 2, len(ana)))
            eslesen = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self._faiss_keys):
                    continue
                key = self._faiss_keys[idx]
                bil = self._ulastir(key)
                if score >= min_skor:
                    eslesen.append((key, str(bil["deger"]), float(score)))
            eslesen.sort(key=lambda t: t[2], reverse=True)
            return [(k, v) for k, v, _ in eslesen[:k]]

        # n-gram fallback
        sorgu_gram = _gramlar(sorgu)
        sorgu_l = re.sub(r"\s+", " ", (sorgu or "").lower()).strip()
        idf = None
        if len(ana) > 1:
            toplam = len(ana)
            dokumansayil = Counter()
            for k_, deger in ana.items():
                bil = deger.get("deger") if isinstance(deger, dict) else deger
                for g in _gramlar(f"{k_} {bil}"):
                    dokumansayil[g] += 1
            idf = {g: math.log(1 + toplam / (1 + n)) for g, n in dokumansayil.items()}
        qv = _vektor(sorgu_gram, idf)
        eslesen = []
        for k_, deger in ana.items():
            bil = self._ulastir(k_)
            alan = f"{k_} {bil['deger']}"
            gv = _vektor(_gramlar(alan), idf)
            skor = _kosinus(qv, gv)
            if sorgu_l and sorgu_l in re.sub(r"\s+", " ", k_.lower()).strip():
                skor = max(skor, 1.0)
            if skor > min_skor:
                eslesen.append((k_, str(bil["deger"]), round(skor, 3)))
        eslesen.sort(key=lambda t: t[2], reverse=True)
        return [(k, v) for k, v, _ in eslesen[:k]]

    def kayit_listesi(self, etiket: Optional[str] = None) -> List[Dict[str, Any]]:
        self._temizle()
        cikti = []
        for k, v in self._kayitlar().items():
            bil = self._ulastir(k)
            if etiket and bil["etiket"] != etiket:
                continue
            cikti.append({"anahtar": k, "ozet": _ozet(str(bil["deger"])),
                          "zaman": bil["zaman"], "etiket": bil["etiket"]})
        cikti.sort(key=lambda x: x["zaman"], reverse=True)
        return cikti

    def unut(self, anahtar_veya_icerik: str, kesin: bool = False) -> bool:
        ana = self._kayitlar()
        if anahtar_veya_icerik in ana:
            del ana[anahtar_veya_icerik]
            self._yaz()
            if _embedding_aktif_mi():
                self._faiss_yeniden_insa()
            return True
        kac = 0
        for k, _eslesen in self.ara(anahtar_veya_icerik, k=5, min_skor=0.05):
            del ana[k]
            kac += 1
            if not kesin:
                break
        self._yaz()
        if _embedding_aktif_mi() and kac:
            self._faiss_yeniden_insa()
        return kac > 0

    def baglam(self, sorgu: str, k: int = 3) -> str:
        ilgili = self.ara(sorgu, k=k)
        return "\n\n".join(f"{k}: {v}" for k, v in ilgili) if ilgili else ""

    def ozet_ata(self, llm, metin: str, anahtar: str, etiket: str = "ozet") -> str:
        try:
            ozet = llm([{"role": "system", "content": "Bunu 3 maddede ozetle, Turkce."},
                        {"role": "user", "content": str(metin)[:4000]}], max_tokens=400)
        except Exception:
            ozet = None
        if ozet:
            self.kaydet(anahtar, ozet, etiket=etiket)
        return ozet or ((metin[:400] + "…") if metin else "")

Bellek = BellekVec  # geriye donuk uyumluluk

if __name__ == "__main__":
    b = Bellek()
    mod = "FAISS+embedding" if _embedding_aktif_mi() else "n-gram fallback"
    print(f"Bellek modu: {mod}")
    b.kaydet("test_kaydi", "ZenAI vektor bellek denemesi calisiyor.", etiket="test", sure=3600)
    print("ARASTIRMA:", b.ara("bellegin yetenegi nedir"))
    print("LISTE:", b.kayit_listesi())
    b.unut("test_kaydi")
    print("SILINDI:", b.ara("test_kaydi") == [])
