"""ZenAI Voice — Vercel serverless SSE fonksiyonu (Python runtime).

`/api/voice` -> gateway'in birebir kopyasi degil, beynin kendisi:
Vercel Python fonksiyonu olarak calisir, `voice.server.streamer` ile
chat/ajan/rapor akisini SSE olarak yayinlar (streaming varsayilan acik).

Ortam notlari:
  * ZENAI_ONBELLEK -> /tmp (serverless'ta yazilabilir tek dizin)
  * OPENROUTER_KEY -> Vercel env (mevcut chat.js ile ayni anahtar)
  * ajan/rapor modu istenirse model parametresi ile zorlanir.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Repo kökü: api/voice.py -> iki üst dizin
_KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_KOK))
sys.path.insert(0, str(_KOK / "agentv2"))
os.environ.setdefault("ZENAI_ONBELLEK", "/tmp/zenai_onbellek.db")

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from voice.server import streamer  # noqa: E402
from voice.server.modes import mod_tanima  # noqa: E402

app = FastAPI(title="ZenAI Voice (Vercel)")


def _olay_uzdu(delta: dict) -> dict:
    return {
        "id": "chatcmpl-zenai-voice",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": "zenai",
        "choices": [{"index": 0, "delta": delta}],
    }


@app.get("/")
async def kok():
    return {"adi": "ZenAI Voice", "yer": "vercel", "ucretli": False}


def _istek_ozet(govde: dict, model: str, messages: list) -> dict:
    son_kullanici = ""
    for m in reversed(messages):
        if m.get("role") in ("user", "system") and str(m.get("content") or "").strip():
            son_kullanici = str(m["content"]).strip()
            break
    bas = model.lower()
    mod = "chat"
    if bas in ("ajan", "rapor"):
        mod = bas
    else:
        mod = mod_tanima(son_kullanici)
    return {"soru": son_kullanici, "mod": mod}


@app.post("/completions")
async def completions(govde: dict):
    """OpenAI uyumlu SSE: HUD'un baglandigi uc (asli yol /api/voice/completions)."""
    messages = govde.get("messages") or []
    if not messages or not isinstance(messages, list):
        return JSONResponse({"error": "messages (liste) gerekli"}, status_code=400)
    model = str(govde.get("model") or "chat")
    o = _istek_ozet(govde, model, messages)
    if not o["soru"]:
        return JSONResponse({"error": "kullanici mesaji bos"}, status_code=400)

    mod = govde.get("zenai_mode") or o["mod"]
    if mod not in ("chat", "ajan", "rapor"):
        mod = o["mod"]

    async def _gen():
        # streamer generator'u thread yerine dogrudan asenkron akista tuketilir
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        kuyruk: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def on_faz(faz: str, durum: str, detay: str = "") -> None:
            loop.call_soon_threadsafe(
                kuyruk.put_nowait,
                _olay_uzdu({"type": "faz", "faz": faz, "durum": durum, "detay": detay, "content": ""}),
            )

        def on_delta(tur: str, icerik: str) -> None:
            d = {"type": tur}
            if tur in ("answer", "thought"):
                d["role"] = "assistant"
                d["content"] = icerik
            else:
                d["content"] = ""
            loop.call_soon_threadsafe(kuyruk.put_nowait, _olay_uzdu(d))

        havuz = ThreadPoolExecutor(max_workers=1)

        def _calistir():
            try:
                streamer.akis_uret(mod, o["soru"], on_faz, on_delta)
            except Exception as e:  # noqa: BLE001 — asla dusme, hata olayini yay
                loop.call_soon_threadsafe(
                    kuyruk.put_nowait,
                    _olay_uzdu({"type": "faz", "faz": "hata", "durum": "hata",
                                "detay": str(e)[:200], "content": ""}),
                )
            finally:
                loop.call_soon_threadsafe(kuyruk.put_nowait, None)

        havuz.submit(_calistir)
        while True:
            olay = await kuyruk.get()
            if olay is None:
                break
            yield "data: " + json.dumps(olay, ensure_ascii=False) + "\n\n"
        yield "data: [DONE]\n\n"

    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        _gen(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )