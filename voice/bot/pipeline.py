"""Pipecat boru hattı kurulumu (VAD + STT + ZenAI LLM + TTS).

Ekstra servisler (Silero, whisper/lokal STT, Piper/Edge TTS) isteğe bağlıdır;
bu modül onları ``pip install pipecat-ai[<ad>]`` ile lazy alır, test ortamı
bunları gerektirmez.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from pipecat.pipeline.pipeline import Pipeline
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair

from .zenai_llm import ZenaiLLMService


@dataclass
class SesAyarlar:
    gateway_url: str = field(
        default_factory=lambda: os.environ.get("ZENAI_GATEWAY", "http://127.0.0.1:8787")
    )
    model: str = field(default_factory=lambda: os.environ.get("ZENAI_MODEL", "chat"))
    mode: str = field(default_factory=lambda: os.environ.get("ZENAI_MODE", ""))
    stt: str = field(default_factory=lambda: os.environ.get("ZENAI_STT", "turkish-stt"))
    tts: str = field(default_factory=lambda: os.environ.get("ZENAI_TTS", "piper"))
    tts_sey: str = "tr_TR-female-medium"
    stt_model: str = "mihuai/turkish-stt"  # FLEURS-TR ~ %14 WER, CPU streaming
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
    Silero = _getir("pipecat.services.silero", "SileroVADAnalyzer", "silero")
    from pipecat.processors.vad.base import VADAnalyzerParams

    return Silero(
        params=VADAnalyzerParams(
            start_secs=0.2,
            stop_secs=ayar.bekletme_ms / 1000,
            min_volume=ayar.vad_esik,
        )
    )


def _stt(ayar: SesAyarlar):
    ad = ayar.stt.lower()
    if ad == "turkish-stt":
        Whisper = _getir("pipecat.services.whisper", "WhisperSTTService", "whisper")
        whisper = Whisper(model=ayar.stt_model, language=ayar.dil, no_speech_prob=0.6)
        whisper.set_model_params(use_int8_quantization=True, cpu_threads=2)
        return whisper
    if ad == "faster-whisper":
        Whisper = _getir("pipecat.services.whisper", "WhisperSTTService", "whisper")
        whisper = Whisper(model=ayar.whisper_model, language=ayar.dil)
        whisper.set_model_params(use_int8_quantization=True)
        return whisper
    raise ValueError(f"STT bilinmiyor: {ayar.stt} (turkish-stt | faster-whisper | yok)")


def _tts(ayar: SesAyarlar):
    ad = ayar.tts.lower()
    if ad == "piper":
        Piper = _getir("pipecat.services.piper", "TTSService", "piper")
        return Piper(voice=ayar.tts_sey, model_sample_rate=22050)
    if ad == "edge":
        Edge = _getir("pipecat.services.elevenlabs", "CosyVoiceTTSService", "edge-tts")
        raise RuntimeError("Edge-TTS ile epsilon paket henüz: 'pipecat-ai[piper]' önerilir")
    raise ValueError(f"TTS bilinmiyor: {ayar.tts} (piper)")


def bot_pipeline(ayar: SesAyarlar, transport, baglam: LLMContextAggregatorPair) -> Pipeline:
    """Eksiksiz boru hattı: [-Ses girişi VAD->] STT -> bağlam -> ZenAI LLM -> TTS -> ses çıkışı.

    ``transport``: pipecat Transport (``transport.input()``/``transport.output()`` sağlar).
    ``baglam``: ``LLMContextAggregatorPair`` — ``baglam[0]`` kullanıcı, ``baglam[1]`` asistan.
    """
    if ayar.ortam_ipi:
        from pipecat.frames.frames import StartFrame

        transport.start(StartFrame())  # type: ignore  # sunucu katmanı içindir
    bilesenler = [transport.input()]
    if ayar.stt.lower() not in ("", "yok", "none"):
        bilesenler.append(_stt(ayar))
    bilesenler.append(baglam[0])
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
    bilesenler.append(baglam[1])
    return Pipeline(bilesenler)