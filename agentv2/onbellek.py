"""Semantik onbellek (SQLite + hafif benzerlik) — tekrar eden API cagrilarini kes.

Ayni/benzer sorulari tekrar API'ye gondermeyerek gercek istek sayisini dusurur.
Benzerlik: kelime Jaccard + karakter (duzeltis) Jaccard ortalamasi — embedding
gerektirmez (sifir bagimlilik). Dilerseniz tarafta chromadb/embedding ile
degistirilebilir.

Kullanim:
    from onbellek import onbel_istek, onbel_kaydet, onbel_kapat
    yanit = onbel_istek(soru)          # yoksa None
    onbel_kaydet(soru, yanit)          # sonraki cagrilar icin

Depo: ~/.zenai_onbellek.db (name arg ile ozellestirilebilir).
"""
import os, re, sqlite3, time, hashlib
from typing import Optional, Tuple

_DB_KONUM = os.environ.get("ZENAI_ONBELLEK", os.path.expanduser("~/.zenai_onbellek.db"))
_BAG = None


def _bag() -> sqlite3.Connection:
    global _BAG
    if _BAG is None:
        os.makedirs(os.path.dirname(_DB_KONUM) or ".", exist_ok=True)
        _BAG = sqlite3.connect(_DB_KONUM, timeout=5, check_same_thread=False)
        _BAG.execute("PRAGMA journal_mode=WAL")
        _BAG.execute(
            """CREATE TABLE IF NOT EXISTS onbellek(
                noum TEXT PRIMARY KEY,
                normal TEXT NOT NULL,
                yanit TEXT NOT NULL,
                zaman REAL NOT NULL,
                vurus INT NOT NULL DEFAULT 0
            )"""
        )
        _BAG.commit()
    return _BAG


def _norm(metin: str) -> str:
    """Kucuk harf + latin disi karakterleri bosluga indir."""
    m = (metin or "").lower()
    m = (m.replace("ç", "c").replace("ğ", "g").replace("ı", "i")
          .replace("ö", "o").replace("ş", "s").replace("ü", "u")
          .replace("â", "a").replace("î", "i").replace("û", "u"))
    m = re.sub(r"[^a-z0-9\s]", " ", m)
    return re.sub(r"\s+", " ", m).strip()


def _gramlar(metin: str, k: int = 3) -> set:
    s = "\x02" + metin + "\x03"
    return {s[i:i + k] for i in range(len(s) - k + 1)}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    aks = a & b
    bir = a | b
    return len(aks) / len(bir)


def benzerlik(a: str, b: str) -> float:
    """Kelime + karakter gram Jaccard ortalamasi (0..1)."""
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    kel = _jaccard(set(na.split()), set(nb.split()))
    gk = _jaccard(_gramlar(na), _gramlar(nb))
    return round(0.6 * kel + 0.4 * gk, 3)


def _noum(metin: str) -> str:
    return hashlib.sha256(_norm(metin).encode("utf-8")).hexdigest()


def onbel_istek(soru: str, esik: float = 0.82,
                ust_sinir: int = 20) -> Optional[str]:
    """Benzer soru onbellekte varsa yaniti dondurur; yoksa None."""
    normal = _norm(soru)
    if not normal:
        return None
    cur = _bag().execute(
        "SELECT normal, yanit FROM onbellek ORDER BY vurus DESC LIMIT ?",
        (ust_sinir,),
    )
    en_iyi, en_skor = None, 0.0
    for kayit_normal, kayit_yanit in cur.fetchall():
        skor = benzerlik(normal, kayit_normal)
        if skor > en_skor:
            en_iyi, en_skor = kayit_yanit, skor
    if en_iyi is None or en_skor < esik:
        return None
    try:
        _bag().execute("UPDATE onbellek SET vurus = vurus + 1 WHERE normal = ?",
                       (_norm(soru),))
        _bag().commit()
    except Exception:
        pass
    return en_iyi


def onbel_kaydet(soru: str, yanit: str) -> None:
    if not _norm(soru) or not yanit or not str(yanit).strip():
        return
    _bag().execute(
        """INSERT INTO onbellek(noum, normal, yanit, zaman)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(noum) DO UPDATE SET
             yanit=excluded.yanit, zaman=excluded.zaman, vurus=vurus+1""",
        (_noum(soru), _norm(soru), str(yanit), time.time()),
    )
    _bag().commit()


def onbel_kapat() -> None:
    global _BAG
    if _BAG is not None:
        try:
            _BAG.close()
        except Exception:
            pass
        _BAG = None


def onbel_durum() -> Tuple[int, int]:
    """(kayit sayisi, toplam vurus) — izleme icin."""
    cur = _bag().execute(
        "SELECT COUNT(*), COALESCE(SUM(vurus), 0) FROM onbellek")
    sira = cur.fetchone()
    return (int(sira[0]), int(sira[1]))