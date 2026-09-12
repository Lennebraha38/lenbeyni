"""Streamer testleri — ağ çağrısı YOK; sağlayıcı enjeksiyonu ile çalışır."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from voice.server import streamer as S
from voice.server.modes import mod_tanima, konu_bul, model_sec


def test_kirpil_cumle_sinirlari():
    parca = S.kirpil("Birinci cümle. İkinci cümle. Üçüncü uzun ve doldurma içeren cümle.", 20)
    assert len(parca) >= 2
    assert all(p.strip() for p in parca)


def test_kirpil_bos():
    assert S.kirpil("") == []
    assert S.kirpil(None) == []


def test_mode_tanima():
    assert mod_tanima("derin araştırma yap") == "rapor"
    assert mod_tanima("internette ara, sitesine bak") == "ajan"
    assert mod_tanima("merhaba, nasılsın") == "chat"


def test_konu_bul():
    assert konu_bul("python ile dosya oku") == "kod"
    assert konu_bul("bir hikaye anlat") == "yaratici"
    assert konu_bul("kahve nasıl yapılır") == "pratik"


def test_model_sec_donus():
    model, maxt = model_sec("python kodu yaz")
    assert isinstance(model, str) and model
    assert isinstance(maxt, int) and maxt > 0


def test_chat_stream_canli(monkeypatch):
    monkeypatch.setattr(S, "onbel_istek", lambda *a, **k: None)
    monkeypatch.setattr(S, "onbel_kaydet", lambda *a, **k: None)
    fazlar, deltalar = [], []

    def saglayici(mesajlar, model, mt):
        yield "Merhaba! "
        yield "Ben ZenAI."

    son = S.chat_stream("selam", lambda fz, dr, dt="": fazlar.append((fz, dr)), lambda t, i: deltalar.append((t, i)),
                        saglayici=saglayici)
    assert son == "Merhaba! Ben ZenAI."
    assert "".join(i for _, i in deltalar) == son
    assert all(t == "answer" for t, _ in deltalar)
    assert any(durum == "dusunuyor" for _, durum, *_ in fazlar)


def test_chat_stream_fallback(monkeypatch):
    monkeypatch.setattr(S, "onbel_istek", lambda *a, **k: None)
    monkeypatch.setattr(S, "onbel_kaydet", lambda *a, **k: None)
    monkeypatch.setattr(S, "_duz_cevap", lambda *a, **k: "Yedek cevap yolu.")

    def patlak(mesajlar, model, mt):
        raise S.StreamHatasi("yok")

    deltalar = []
    son = S.chat_stream("selam", lambda *a: None, lambda t, i: deltalar.append((t, i)),
                        saglayici=patlak)
    assert son == "Yedek cevap yolu."
    assert "Yedek cevap yolu." in "".join(i for _, i in deltalar)


def test_ajan_stream_plan_ve_ses(monkeypatch):
    fazlar, deltalar = [], []

    def saglayici(mesajlar, model, mt):
        icerik = " ".join(str(m.get("content", "")) for m in mesajlar)
        if "ARAC SONUCLARI" in icerik:
            yield "Nihai "
            yield "yanıt."
        else:
            yield "[ARAMA]soru[/ARAMA]"

    def fake_ajan(soru):
        plan = S.zz.llm([{"role": "user", "content": "ara: en ucuz telefon"}])
        assert plan == "[ARAMA]soru[/ARAMA]"
        cevap = S.zz.llm([
            {"role": "user", "content": "ARAC SONUCLARI: 1. sonuç"},
            {"role": "assistant", "content": plan},
        ])
        return cevap

    monkeypatch.setattr(S.zz, "ajan", fake_ajan)
    son = S.ajan_stream("ara", lambda fz, dr, dt="": fazlar.append((fz, dr)), lambda t, i: deltalar.append((t, i)),
                        saglayici=saglayici)
    assert son == "Nihai yanıt."
    # plan çağrısı sessiz geçti, yanıt tokenlar akıştı
    assert any(faz == "arac-hazirligi" for faz, *_ in fazlar)
    assert "".join(i for _, i in deltalar) == "Nihai yanıt."


def test_ajan_stream_sarmala_geri_alindi(monkeypatch):
    orijinal = S.zz.llm
    S.zz.ajan = lambda soru: "x"
    S.ajan_stream("selam", lambda *a: None, lambda t, i: None,
                  saglayici=lambda m, mo, mt: iter(["Merhaba"]))
    assert S.zz.llm is orijinal


def test_rapor_stream_kalp_ve_parcalar(monkeypatch):
    monkeypatch.setattr(S.zz, "rapor", lambda soru: "Özet bulgusu a. Bulgu b. Sonuç kelimesi.")
    fazlar, deltalar = [], []
    son = S.rapor_stream("araştır", lambda fz, dr, dt="": fazlar.append((fz, dr)), lambda t, i: deltalar.append((t, i)),
                         kalp_atis=0.01)
    assert son.startswith("Özet bulgusu")
    assert any(faz == "rapor" for faz, *_ in fazlar)
    assert any(faz == "tamamlandi" for faz, *_ in fazlar)
    assert "".join(i for _, i in deltalar) == son