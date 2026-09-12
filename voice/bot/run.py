"""ZenAI Voice bot — başlatıcı (pipecat 1.10).

  python -m voice.bot.run bak                          # bağımlılık sağlık kontrolü
  python -m voice.bot.run --transport webrtc           # SmallWebRTC sunucusu (tarayıcı HUD ↔ bot)
  python -m voice.bot.run --transport kulaklik         # cihaz mikrofonu/hoparlörü
  python -m voice.bot.run --transport websocket        # WS tabanlı özel istemci

Uçlar:
  * ``webrtc``  : SmallWebRTC — POST /offer (SDP) ile tarayıcıdan canlı ses,
                  0 maliyet (TURN gerekmez, p2p/host adayları).
  * ``kulaklik``: yerel cihaz sesi (sunucusuz test).
  * ``websocket``: protobuf serileştiricili WS sunucusu.
"""
from __future__ import annotations

import argparse
import asyncio
import logging

from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("zenai.bot")


def _arguman():
    p = argparse.ArgumentParser(prog="zenai-bot", description="ZenAI Voice botu")
    p.add_argument("islem", nargs="?", default="run", help="bak | run")
    p.add_argument("--model", default="chat", choices=["chat", "ajan", "rapor"])
    p.add_argument("--mode", default="", help="boşsa otomatik (ajan/rapor zorlanır)")
    p.add_argument("--gateway", default="http://127.0.0.1:8787")
    p.add_argument("--stt", default="faster-whisper",
                   choices=["turkish-stt", "faster-whisper", "yok"])
    p.add_argument("--tts", default="piper", choices=["piper", "yok"])
    p.add_argument("--transport", default="webrtc", choices=["webrtc", "kulaklik", "websocket"])
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8788)
    return p.parse_args()


class _Istek(BaseModel):
    """``SmallWebRTCRequest`` dataclass'tır; FastAPI body'si için pydantic sarmalayıcı."""

    sdp: str
    type: str
    pc_id: str | None = None
    restart_pc: bool | None = None


# ── Sağlık kontrolü ────────────────────────────────────────────────────
async def _bak(args) -> None:
    from .pipeline import SesAyarlar, _stt, _tts, _vad

    ayar = SesAyarlar(gateway_url=args.gateway, model=args.model, mode=args.mode)
    print(f"[bak] ayarlar: model={ayar.model} mode={ayar.mode} gateway={ayar.gateway_url}")
    for ad, kur in [("STT", "pipecat-ai[whisper]"), ("VAD", "pipecat-ai[silero]"),
                    ("TTS", "pipecat-ai[piper]")]:
        try:
            if ad == "STT":
                _stt(ayar)
            elif ad == "VAD":
                _vad(ayar)
            else:
                _tts(ayar)
            print(f"[bak] {ad}: tamam")
        except Exception as e:
            print(f"[bak] {ad}: EKSIK ({e.__class__.__name__}) — pip install '{kur}'")
    from .zenai_llm import ZenaiLLMService
    svc = ZenaiLLMService(gateway_url=args.gateway, model="chat")
    print(f"[bak] ZenaiLLMService: hazır ({svc.name})")


# ── Ortak: pipeline + worker çalıştır ─────────────────────────────────
async def _calistir(ayar, transport) -> None:
    """PipelineWorker + WorkerRunner ile botu sürekli çalıştırır."""
    from pipecat.pipeline.worker import PipelineWorker
    from pipecat.workers.runner import WorkerRunner

    from .pipeline import bot_pipeline

    pipeline, _ = bot_pipeline(ayar, transport)
    worker = PipelineWorker(pipeline)
    runner = WorkerRunner()
    await runner.add_workers(worker)
    log.info("pipeline calisiyor (%s)", type(transport).__name__)
    await runner.run()


# ── WebRTC ucu (tarayıcı HUD) ─────────────────────────────────────────
async def _webrtc_sunucu(args) -> None:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from pipecat.transports.base_transport import TransportParams
    from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
    from pipecat.transports.smallwebrtc.request_handler import (
        SmallWebRTCRequest,
        SmallWebRTCRequestHandler,
    )
    from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

    from .pipeline import SesAyarlar, _vad

    ayar = SesAyarlar(gateway_url=args.gateway, model=args.model, mode=args.mode,
                      stt=args.stt, tts=args.tts)
    handler = SmallWebRTCRequestHandler()

    app = FastAPI(title="ZenAI Voice Bot (SmallWebRTC)")
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
    )

    async def _baglanti_hazir(webrtc_connection: SmallWebRTCConnection) -> None:
        """Her yeni tarayıcı bağlantısı için tam pipeline ayağa kalkar.

        Pipeline worker'ı arka plan görevi olarak başlar; offer cevabı
        bekletilmez (``runner.run()`` bağlantı kapanana kadar dönmeyeceğinden
        burada ``await`` YAPILMAZ).
        """
        transport = SmallWebRTCTransport(
            webrtc_connection,
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                audio_out_sample_rate=16000,
                audio_out_channels=1,
                vad_analyzer=_vad(ayar),
            ),
        )

        @webrtc_connection.event_handler("closed")
        async def _kapandi(conn):
            log.info("webrtc baglanti kapandi: %s", conn.id)

        asyncio.create_task(_calistir(ayar, transport))

    @app.post("/offer")
    async def offer(istek: _Istek):
        yanit = await handler.handle_web_request(
            SmallWebRTCRequest(
                sdp=istek.sdp, type=istek.type,
                pc_id=istek.pc_id, restart_pc=istek.restart_pc,
            ),
            _baglanti_hazir,
        )
        return yanit

    import uvicorn
    print(f"[webrtc] http://{args.host}:{args.port}/offer  (HUD ses modu: bu adrese baglan)")
    config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
    await uvicorn.Server(config).serve()


# ── Yerel cihaz ucu (mikrofon/hoparlör) ────────────────────────────────
async def _kulaklik(args) -> int:
    from pipecat.transports.local.audio import LocalAudioTransport
    from pipecat.transports.base_transport import TransportParams

    from .pipeline import SesAyarlar, _vad

    ayar = SesAyarlar(gateway_url=args.gateway, model=args.model, mode=args.mode,
                      stt=args.stt, tts=args.tts)
    transport = LocalAudioTransport(
        TransportParams(audio_in_enabled=True, audio_out_enabled=True,
                        vad_analyzer=_vad(ayar)),
    )
    await _calistir(ayar, transport)
    return 0


# ── Websocket ucu (özel istemciler) ───────────────────────────────────
async def _websocket(args) -> int:
    from pipecat.transports.websocket.server import (
        SingleClientWebsocketServerParams,
        SingleClientWebsocketServerTransport,
    )
    from pipecat.serializers.protobuf import ProtobufFrameSerializer

    from .pipeline import SesAyarlar, _vad

    ayar = SesAyarlar(gateway_url=args.gateway, model=args.model, mode=args.mode,
                      stt=args.stt, tts=args.tts)
    transport = SingleClientWebsocketServerTransport(
        params=SingleClientWebsocketServerParams(
            host=args.host, port=args.port,
            serializer=ProtobufFrameSerializer(),
            vad_analyzer=_vad(ayar),
        ),
        host=args.host, port=args.port,
    )
    await _calistir(ayar, transport)
    return 0


def main() -> int:
    args = _arguman()
    if args.islem == "bak":
        asyncio.run(_bak(args))
        return 0
    if args.transport == "webrtc":
        asyncio.run(_webrtc_sunucu(args))
        return 0
    if args.transport == "kulaklik":
        return asyncio.run(_kulaklik(args))
    return asyncio.run(_websocket(args))


if __name__ == "__main__":
    raise SystemExit(main())