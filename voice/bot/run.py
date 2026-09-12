"""ZenAI Voice bot — başlatıcı / kontrol.

  python -m voice.bot.run bak        # yapı + bağımlılık sağlık kontrolü
  python -m voice.bot.run --transport kulaklik --model chat

Sesli uçlar (``kulaklik``: TCPTransport; ``webrtc``: FastAPI+WS) `pipecat-ai`
ekstra paketlerini gerektirir:  pip install "pipecat-ai[webrtc,fastapi-webrtc,silero,whisper,piper]"
Bunlar olmadan "bak" modu çalışır; test ortamı ekstraları gerektirmez.
"""
from __future__ import annotations

import argparse
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("zenai.bot")


def _arguman():
    p = argparse.ArgumentParser(prog="zenai-bot", description="ZenAI Voice botu")
    p.add_argument("islem", nargs="?", default="bak", help="bak | run")
    p.add_argument("--model", default="chat", choices=["chat", "ajan", "rapor"])
    p.add_argument("--mode", default="", help="boşsa otomatik (ajan/rapor zorlanır)")
    p.add_argument("--gateway", default="http://127.0.0.1:8787")
    p.add_argument("--stt", default="turkish-stt",
                   choices=["turkish-stt", "faster-whisper", "yok"])
    p.add_argument("--tts", default="piper", choices=["piper", "yok"])
    p.add_argument("--transport", default="kulaklik", choices=["kulaklik", "webrtc"])
    p.add_argument("--port", default="8788", help="TCP/WS sunucu portu")
    return p.parse_args()


def _transport(secim: str, port: int):
    if secim == "kulaklik":
        from pipecat.transports.network.tcp_transport import TCPTransport

        return TCPTransport(host="0.0.0.0", port=port)
    raise RuntimeError(
        "WebRTC ucu için FastAPIWebRTCHandler + `pipecat-ai[webrtc,fastapi-webrtc]` gerekir"
    )


async def _bak(args) -> None:
    from .pipeline import SesAyarlar, bot_pipeline

    ayar = SesAyarlar(gateway_url=args.gateway, model=args.model, mode=args.mode)
    print(f"[bak] ayarlar: model={ayar.model} mode={ayar.mode} gateway={ayar.gateway}")
    EKSIK = ["stt: 'pip install pipecat-ai[whisper]'", "vad: 'pip install pipecat-ai[silero]'",
             "tts: 'pip install pipecat-ai[piper]'"]
    for ad, kurulum in [("STT", EKSIK[0]), ("VAD", EKSIK[1]), ("TTS", EKSIK[2])]:
        try:
            if ad == "STT":
                ayar.stt = "turkish-stt"
                from .pipeline import _stt
                _stt(ayar)
            elif ad == "VAD":
                from .pipeline import _vad
                _vad(ayar)
            else:
                ayar.tts = "piper"
                from .pipeline import _tts
                _tts(ayar)
            print(f"[bak] {ad}: tamam")
        except Exception as e:
            print(f"[bak] {ad}: EKSIK ({e.__class__.__name__}) — {kurulum}")
    # LLM servisi + pipeline iskeleti her zaman derlenebilmeli
    from .zenai_llm import ZenaiLLMService
    svc = ZenaiLLMService(gateway_url=args.gateway, model="chat")
    print(f"[bak] ZenaiLLMService: hazır (uygulama: {svc.name})")


async def _run(args) -> int:
    from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair

    from .pipeline import SesAyarlar, bot_pipeline

    ayar = SesAyarlar(gateway_url=args.gateway, model=args.model, mode=args.mode,
                      stt=args.stt, tts=args.tts)
    transport = _transport(args.transport, int(args.port))
    user_agg, assistant_agg = LLMContextAggregatorPair()
    pipeline = bot_pipeline(ayar, transport, (user_agg, assistant_agg))
    runner = __import__("pipecat.pipeline", fromlist=["AsyncPipelineRunner"]).AsyncPipelineRunner(
        pipeline
    )
    soket = asyncio.create_task(transport.run(transport._ctx))  # tip bağımlı; TCP için
    try:
        await asyncio.gather(soket, runner.run_until_queue_empty())
    finally:
        await transport.stop()
    return 0


def main() -> int:
    args = _arguman()
    if args.islem == "bak":
        asyncio.run(_bak(args))
        return 0
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())