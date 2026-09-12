"""OpenAI-uyumlu streaming gateway — ZenAI Voice için HTTP katmanı.

`POST /v1/chat/completions`
  - girdi: OpenAI mesaj formatı (+ isteğe bağlı başlık `x-zenai-mode`: chat|ajan|rapor)
  - çıktı (stream=true): SSE; her olay `choices[0].delta` içinde:
      {"type":"answer","role":"assistant","content":"..."}   -> konuşulacak token
      {"type":"faz","faz":"<ad>","durum":"<durum>","detay":""}  -> HUD durum makinesi
  - beynin modelleri (yönlendirme / ajan / araştırma) streamer üzerinden aynen kullanılır.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .modes import mod_tanima
from . import streamer

APP = FastAPI(title="ZenAI Voice", version="0.1.0")

DEFAULT_ORIGIN = "*"
_IZIN_ORIGIN = [s.strip() for s in
                os.environ.get("ZENAI_ORIGIN", DEFAULT_ORIGIN).split(",") if s.strip()]

APP.add_middleware(
    CORSMiddleware,
    allow_origins=_IZIN_ORIGIN,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "x-zenai-mode"],
)

# ── Basit pencere throttling (repo güvenlik stiline uygun) ────────────────
_SERBEST = int(os.environ.get("ZENAI_IP_DAKIKA", "60"))
_PENCERE: dict = {}


def _ip(istek: Request) -> str:
    return (istek.headers.get("x-forwarded-for") or "").split(",")[0].strip(
    ) or istek.client.host if istek.client else "?"


def _sinir(istek: Request) -> bool:
    ip = _ip(istek)
    simdi = time.time()
    esik = simdi - 60
    gelen = [t for t in _PENCERE.get(ip, []) if t > esik]
    if len(gelen) >= _SERBEST:
        _PENCERE[ip] = gelen
        return True
    _PENCERE[ip] = gelen + [simdi]
    return False


class Kanal:
    """Thread -> asyncio kuyruğu köprüsü; threade-safe ``call_soon_threadsafe``."""

    def __init__(self, model: str):
        self._loop = None
        self._kuyruk = None
        self._model = model
        self._kimlik = "chatcmpl-zenai-" + uuid.uuid4().hex[:12]
        self._sahes = int(time.time())

    def bagla(self, loop, kuyruk):
        self._loop = loop
        self._kuyruk = kuyruk

    def _olay(self, delta: dict, kuyruk) -> None:
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(
            kuyruk.put_nowait, {
                "id": self._kimlik, "object": "chat.completion.chunk",
                "created": self._sahes, "model": self._model,
                "choices": [{"index": 0, "delta": delta}],
            })

    def yayinla_delta(self, tur: str, icerik: str) -> None:
        d = {"type": tur}
        if tur in ("answer", "thought"):
            d["role"] = "assistant"
            d["content"] = icerik
        else:
            d["content"] = ""
        self._olay(d, self._kuyruk)

    def yayinla_faz(self, faz: str, durum: str, detay: str = "") -> None:
        self._olay({"type": "faz", "faz": faz, "durum": durum, "detay": detay}, self._kuyruk)

    def yayinla_bitir(self) -> None:
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._kuyruk.put_nowait, None)


def _calistir(mod: str, soru: str, kanal: Kanal) -> None:
    try:
        streamer.akis_uret(mod, soru, kanal.yayinla_faz, kanal.yayinla_delta)
    except Exception as e:  # genel güvenlik: asla istek düşürme
        try:
            kanal.yayinla_faz("hata", "hata", str(e)[:200])
        except Exception:
            pass
    finally:
        kanal.yayinla_bitir()


def _istek_ozet(govde: dict, model: str, messages: list) -> dict:
    """OpenAI istek gövdesini ZenAI sesli katman isteğine çevirir."""
    son_kullanici = ""
    for m in reversed(messages):
        if m.get("role") in ("user", "system") and str(m.get("content") or "").strip():
            son_kullanici = str(m["content"]).strip()
            break
    bas = model.lower()
    mod = "chat"
    if bas in ("ajan", "rapor"):  # açık zorlama; "chat"/boş -> otomatik tespit
        mod = bas
    else:
        mod = mod_tanima(son_kullanici)
    return {"soru": son_kullanici, "mod": mod}


@APP.get("/")
async def kok():
    return {"adi": "ZenAI Voice", "ucretli": False,
            "endpoint": "/v1/chat/completions (OpenAI uyumlu, SSE)"}


@APP.get("/healthz")
async def saglik():
    return {"durum": "ok"}


@APP.post("/v1/chat/completions")
async def chat_completions(istek: Request):
    try:
        govde = await istek.json()
    except Exception:
        govde = {}
    messages: list = govde.get("messages") or []
    if not messages or not isinstance(messages, list):
        return JSONResponse({"error": "messages (liste) gerekli"}, status_code=400)

    o = _istek_ozet(govde, str(govde.get("model") or "chat"), messages)
    if not o["soru"]:
        return JSONResponse({"error": "kullanıcı mesajı girildi"}, status_code=400)

    mod = (istek.headers.get("x-zenai-mode") or govde.get("zenai_mode") or o["mod"])
    if mod not in ("chat", "ajan", "rapor"):
        mod = o["mod"]

    if _sinir(istek):
        return JSONResponse({"error": "Çok fazla istek, 60 saniye sonra tekrar dene"},
                            status_code=429)

    stream_flag = bool(govde.get("stream"))
    ai_kimlik = "zenai-voice-" + mod

    import asyncio
    loop = asyncio.get_running_loop()
    kuyruk = asyncio.Queue()
    kanal = Kanal(ai_kimlik)
    kanal.bagla(loop, kuyruk)

    t = threading.Thread(target=_calistir, args=(mod, o["soru"], kanal), daemon=True)
    t.start()

    if stream_flag:
        async def _gen():
            while True:
                olay = await kuyruk.get()
                if olay is None:
                    break
                yield "data: " + json.dumps(olay, ensure_ascii=False) + "\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(
            _gen(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # stream=false: kuyruk topla, tek cevap dön
    metin: List[str] = []
    while True:
        olay = await kuyruk.get()
        if olay is None:
            break
        d = olay["choices"][0]["delta"]
        if d.get("type") in ("answer", "thought") and d.get("content"):
            metin.append(d["content"])
    return {
        "id": kanal._kimlik, "object": "chat.completion",
        "created": kanal._sahes, "model": ai_kimlik,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "".join(metin)}}],
    }