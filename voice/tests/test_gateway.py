"""Gateway testleri — OpenAI-uyumlu SSE sözleşmesini doğrular (ağ YOK)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient

from voice.server import gateway


def _fake_akis(mod, soru, on_faz, on_delta, saglayici=None):
    on_faz("hazirlaniyor", "dusunuyor", "")
    on_delta("answer", "Merhaba ")
    on_delta("answer", "dünya")
    on_delta("faz", "bilgi")  # faz deltası gateway tarafından da geçirilir
    on_faz("tamamlandi", "konusuyor", "2")
    return "Merhaba dünya"


def test_istek_ozet_mod_tespit():
    o = gateway._istek_ozet(
        {"model": "chat"}, "chat",
        [{"role": "user", "content": "derin araştırma yap"}])
    assert o["mod"] == "rapor"
    assert o["soru"] == "derin araştırma yap"


def test_istek_ozet_son_kullanici():
    o = gateway._istek_ozet(
        {"model": "chat"}, "chat",
        [{"role": "user", "content": "ilk"}, {"role": "assistant", "content": "x"},
         {"role": "user", "content": "son soru"}])
    assert o["soru"] == "son soru"


def test_sse_akis(monkeypatch):
    monkeypatch.setattr(gateway.streamer, "akis_uret", _fake_akis)
    with TestClient(gateway.APP) as c:
        with c.stream("POST", "/v1/chat/completions", json={
            "model": "chat",
            "messages": [{"role": "user", "content": "selam"}],
            "stream": True,
        }) as r:
            assert r.status_code == 200
            govde = "".join(r.iter_text())
    assert "data: [DONE]\n" in govde
    olaylar = []
    for sat in govde.splitlines():
        if sat.startswith("data: "):
            payload = sat[len("data: "):]
            if payload == "[DONE]":
                continue
            olaylar.append(json.loads(payload))
    icerik = "".join(o["choices"][0]["delta"].get("content", "") for o in olaylar)
    assert "Merhaba dünya" in icerik
    # faz olayı delta da açık
    tip_ex = {o["choices"][0]["delta"].get("type") for o in olaylar}
    assert "answer" in tip_ex and "faz" in tip_ex
    # OpenAI uyumlu chunk şekli
    ilk = olaylar[0]
    assert ilk["object"] == "chat.completion.chunk"
    assert "choices" in ilk and "delta" in ilk["choices"][0]


def test_duz_yanit(monkeypatch):
    monkeypatch.setattr(gateway.streamer, "akis_uret", _fake_akis)
    with TestClient(gateway.APP) as c:
        r = c.post("/v1/chat/completions", json={
            "model": "chat",
            "messages": [{"role": "user", "content": "selam"}],
            "stream": False,
        })
    assert r.status_code == 200
    cevap = r.json()["choices"][0]["message"]["content"]
    assert cevap == "Merhaba dünya"


def test_mesaj_zorunlu():
    with TestClient(gateway.APP) as c:
        r = c.post("/v1/chat/completions", json={})
    assert r.status_code == 400


def test_saglik():
    with TestClient(gateway.APP) as c:
        assert c.get("/healthz").json() == {"durum": "ok"}