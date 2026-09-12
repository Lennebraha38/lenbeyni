"""Pipecat boru hattı kurulumu (VAD + STT + ZenAI LLM + TTS) — pipecat 1.10.

Ekstra servisler (Silero, whisper/lokal STT, Piper TTS) isteğe bağlıdır;
bu modül onları ``pip install pipecat-ai[<ad>]`` ile lazy alır, test ortamı
bunları gerektirmez.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from pipecat.pipeline.pipeline import Pipeline
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.transcriptions.language import Language

from .zenai_llm import ZenaiLLMService


@dataclass
class SesAyarlar:
    gateway_url: str = field(
        default_factory=lambda: os.environ.get("ZENAI_GATEWAY", "http://127.0.0.1:8787")
    )
    model: str = field(default_factory=lambda: os.environ.get("ZENAI_MODEL", "chat"))
    mode: str = field(default_factory=lambda: os.environ.get("ZENAI_MODE", ""))
    stt: str = field(default_factory=lambda: os.environ.get("ZENAI_STT", "faster-whisper"))
    tts: str = field(default_factory=lambda: os.environ.get("ZENAI_TTS", "piper"))
    tts_sey: str = "tr_TR-dfki-medium"  # Piper'ın kalan tek TR sesi (fahrettin/fettah kaldırıldı)
    stt_model: str = "mihuai/turkish-stt"  # HF'den iner; bozulursa faster-whisper'a dön
    whisper_model: str = "base"
    dil: str = "tr"
    vad_esik: float = 0.5
    bekletme_ms: int = 400
    max_tokens: int = 256
    ortam_ipi: str = ""

    @classmethod
    def from_env(cls) -> "SesAyarlar":
        return cls()


def _getir(bolum: str, ad: str, ekstra: str):
    import importlib

    try:
        return getattr(importlib.import_module(bolum), ad)
    except ImportError as e:
        raise RuntimeError(
            f"'pip install pipecat-ai[{ekstra}]' gerekli: {e}"
        ) from e


def _vad(ayar: SesAyarlar):
    Silero = _getir("pipecat.audio.vad.silero", "SileroVADAnalyzer", "silero")
    from pipecat.audio.vad.vad_analyzer import VADParams

    return Silero(
        params=VADParams(
            start_secs=0.2,
            stop_secs=ayar.bekletme_ms / 1000,
            min_volume=ayar.vad_esik,
        )
    )


def _stt(ayar: SesAyarlar):
    ad = ayar.stt.lower()
    if ad == "turkish-stt":
        Whisper = _getir("pipecat.services.whisper.stt", "WhisperSTTService", "whisper")
        return Whisper(model=ayar.stt_model, language=Language.TR, compute_type="int8")
    if ad == "faster-whisper":
        Whisper = _getir("pipecat.services.whisper.stt", "WhisperSTTService", "whisper")
        return Whisper(model=ayar.whisper_model, language=Language.TR, compute_type="int8")
    raise ValueError(f"STT bilinmiyor: {ayar.stt} (turkish-stt | faster-whisper | yok)")


def _tts(ayar: SesAyarlar):
    ad = ayar.tts.lower()
    if ad == "piper":
        Piper = _getir("pipecat.services.piper.tts", "PiperTTSService", "piper")
        return Piper(voice_id=ayar.tts_sey)
    raise ValueError(f"TTS bilinmiyor: {ayar.tts} (piper)")


def bot_pipeline(ayar: SesAyarlar, transport, baglam=None) -> tuple[Pipeline, LLMContext]:
    """Eksiksiz boru hattı: ses girişi -> STT -> bağlam -> ZenAI LLM -> TTS -> ses çıkışı.

    ``transport``: pipecat Transport (``input()``/``output()`` sağlar).
    ``baglam``: ``LLMContext`` (yoksa taze kurulur). Dönüş: ``(pipeline, context)``.

    Not: pipecat 1.10'da agregatörler ``LLMContextAggregatorPair(context)`` ile
    çift olarak kurulur; pipeline'ın hem başında (user) hem sonunda (assistant)
    yer alırlar.
    """
    context = baglam if isinstance(baglam, LLMContext) else LLMContext()
    user_agg, assistant_agg = LLMContextAggregatorPair(context)

    bilesenler = [transport.input()]
    if ayar.stt.lower() not in ("", "yok", "none"):
        bilesenler.append(_stt(ayar))
    bilesenler.append(user_agg)
    llm = ZenaiLLMService(
        gateway_url=ayar.gateway_url,
        model=ayar.model,
        mode=ayar.mode,
        max_tokens=ayar.max_tokens,
    )
    bilesenler.append(llm)
    if ayar.tts.lower() not in ("", "yok", "none"):
        bilesenler.append(_tts(ayar))
    bilesenler.append(transport.output())
    bilesenler.append(assistant_agg)
    return Pipeline(bilesenler), context