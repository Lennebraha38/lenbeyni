"""ZenAI Bellek — vektör tarzı hatırlama.

JSON tabanlı, bağımsız (chromadb kurulmadan çalışır) hafıza:
- Karakter n-gram TF-IDF ile kosinüs benzerliği (kelime tabanlı değil -> Türkçe eklemelerde sağlam)
- Zaman damgası + süre (TTL): eski/yanlış bilgi otomatik bayatlar
- Kullanıcı bazlı izolasyon: her kullanıcının kayıtları ayrı tutulur
- `unut` komutu ile silme + toplu listeleme
"""
import os, re, json, math, time, hashlib
from collections import Counter

VARS = 4  # n-gram boyu (alt kelime parçaları)


def _gramlar(metin, k=VARS):
    """Turkce uyumlu karakter n-gramlari."""
    temiz = re.sub(r"[^a-zçğıöşü0-9\s]", " ", (metin or "").lower())
    temiz = re.sub(r"\s+", " ", temiz).strip()
    g = set()
    for sozcuk in temiz.split():
        s = "\x02" + sozcuk + "\x03"
        for i in range(len(s) - k + 1):
            g.add(s[i:i + k])
    return g


def _vektor(gramlar, idf=None):
    """Gram setini sozluk vektore cevir; idf verilirse agirliklandir."""
    say = Counter(gramlar) if isinstance(gramlar, (list, tuple)) else {x: 1 for x in gramlar}
    if idf:
        return {g: w * idf.get(g, 1.0) for g, w in say.items()}
    return dict(say)


def _kosinus(a, b):
    if not a or not b:
        return 0.0
    ortak = set(a) & set(b)
    if not ortak:
        return 0.0
    dot = sum(a[g] * b[g] for g in ortak)
    a2 = math.sqrt(sum(v * v for v in a.values())) or 1.0
    b2 = math.sqrt(sum(v * v for v in b.values())) or 1.0
    return dot / (a2 * b2)


def _ozet(metin, boyut=38):
    m = re.sub(r"\s+", " ", (metin or "")).strip()
    return m[:boyut] + ("…" if len(m) > boyut else "")


class BellekVec:
    """Vektor bellek. Soru/talimat olusturup ara -> en alakali (anahtar, deger, skor)."""

    def __init__(self, yol=None, kullanici="varsayilan"):
        self.yol = yol or os.path.expanduser("~/.zenai_bellek.json")
        self.kullanici = kullanici
        self.veri = {}
        try:
            with open(self.yol) as f:
                self.veri = json.load(f)
        except Exception:
            self.veri = {}
        self._temizle()

    # ── dahili ──
    def _kayitlar(self):
        ana = self.veri.setdefault(self.kullanici, {})
        return ana

    def _temizle(self):
        """Sure dolan kayitlari otomatik temizle."""
        s = time.time()
        ana = self._kayitlar()
        sil = [k for k, v in ana.items() if isinstance(v, dict) and v.get("sure") is not None and s > v.get("zaman", 0) + v["sure"]]
        for k in sil:
            ana.pop(k, None)
        if sil:
            self._yaz()

    def _yaz(self):
        try:
            with open(self.yol, "w") as f:
                json.dump(self.veri, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def _ulastir(self, k):
        v = self._kayitlar()[k]
        if isinstance(v, dict) and "deger" in v:
            return v
        # eski format: duz deger
        return {"deger": v, "zaman": 0, "sure": None, "etiket": None}

    # ── API ──
    def kaydet(self, anahtar, deger, etiket=None, sure=None):
        ana = self._kayitlar()
        ana[anahtar] = {"deger": deger, "zaman": time.time(), "sure": sure, "etiket": etiket}
        self._yaz()

    def ara(self, sorgu, k=3, idf_acik=True, min_skor=0.0):
        """Kosinus benzerligi ile en alakali kayitlari getir.

        Anahtar + deger birlikte indekslenir; sorgu bir anahtarin
        alt dizesiyse o kayit her zaman onceliklidir.
        """
        ana = self._kayitlar()
        if not ana:
            return []
        self._temizle()
        sorgu_gram = _gramlar(sorgu)
        sorgu_l = re.sub(r"\s+", " ", (sorgu or "").lower()).strip()
        # idf butun korpus uzerinden
        idf = None
        if idf_acik and len(ana) > 1:
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
                skor = max(skor, 1.0)  # anahtar alt-dizesi: kesin eslesme
            if skor > min_skor:
                eslesen.append((k_, str(bil["deger"]), round(skor, 3)))
        eslesen.sort(key=lambda t: t[2], reverse=True)
        return [(k, v) for k, v, _ in eslesen[:k]]

    def kayit_listesi(self, etiket=None):
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

    def unut(self, anahtar_veya_icerik, kesin=False):
        """Anahtar soyaciyla sil; icerik eklerse benzerlikle bulup sil."""
        ana = self._kayitlar()
        if anahtar_veya_icerik in ana:
            del ana[anahtar_veya_icerik]
            self._yaz()
            return True
        kac = 0
        for k, _eslesen in self.ara(anahtar_veya_icerik, k=5, min_skor=0.05):
            del ana[k]
            kac += 1
            if not kesin:
                break
        self._yaz()
        return kac > 0

    def baglam(self, sorgu, k=3):
        ilgili = self.ara(sorgu, k=k)
        return "\n\n".join(f"{k}: {v}" for k, v in ilgili) if ilgili else ""

    def ozet_ata(self, llm, metin, anahtar, etiket="ozet"):
        try:
            ozet = llm([{"role": "system", "content": "Bunu 3 maddede ozetle, Turkce."},
                        {"role": "user", "content": str(metin)[:4000]}], max_tokens=400)
        except Exception:
            ozet = None
        if ozet:
            self.kaydet(anahtar, ozet, etiket=etiket)
        return ozet or ((metin[:400] + "…") if metin else "")


# Eski Bellek adlandirmasi uyumlulugu
Bellek = BellekVec

if __name__ == "__main__":
    b = Bellek()
    b.kaydet("test_kaydi", "ZenAI vektor bellek denemesi calisiyor.", etiket="test", sure=3600)
    print("ARASTIRMA:", b.ara("bellegin yetenegi nedir"))
    print("LISTE:", b.kayit_listesi())
    b.unut("test_kaydi")
    print("SILINDI:", b.ara("test_kaydi") == [])