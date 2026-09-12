"""Pipecat LLM servisi -> ZenAI Voice gateway (OpenAI-uyumlu SSE).

- ``answer`` tokenları ``LLMTextFrame``, ``faz`` olayları ``ZenaiFazFrame`` olarak akar.
- ``InterruptionFrame`` geldiğinde mevcut yayın arka planda iptal edilir (barge-in).
- Beyin değişmeden, ``agentv2`` üzerinden streaming gateway'i mesaj olarak kullanır.
"""
from __future__ import annotations

import asyncio
import json

import httpx

from pipecat.frames.frames import (
    Frame,
    InterruptionFrame,
    LLMContextFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.llm_service import LLMService


class ZenaiFazFrame(Frame):
    """Ara faz bilgisi (dusunuyor/arastiriyor/yanit/hata); HUD vb. tüketiciler içindir."""

    def __init__(self, faz: str, detay: str = ""):
        self.faz = faz
        self.detay = detay
        super().__init__()


class ZenaiLLMService(LLMService):
    """``/v1/chat/completions`` (SSE) üzerinden bir OpenAI-uyumlu uca gider."""

    def __init__(
        self,
        gateway_url: str = "http://127.0.0.1:8787",
        model: str = "chat",
        mode: str | None = None,
        max_tokens: int | None = None,
        timeout: float = 120.0,
        **kwargs,
    ):
        from pipecat.services.settings import LLMSettings

        super().__init__(
            settings=LLMSettings(
                model=model,
                system_instruction=None,
                temperature=None,
                max_tokens=max_tokens,
                top_p=None,
                top_k=None,
                frequency_penalty=None,
                presence_penalty=None,
                seed=None,
                filter_incomplete_user_turns=None,
                user_turn_completion_config=None,
            ),
            **kwargs,
        )
        self._gateway = gateway_url.rstrip("/")
        self._model = model
        self._mode = mode or ("chat" if model not in ("ajan", "rapor") else model)
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._iptal = asyncio.Event()
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=timeout, write=30.0, pool=30.0)
        )

    async def stop(self, frame: Frame):
        await self._client.aclose()
        await super().stop(frame)

    # ── olay satırlarını pipecat karelerine çevir ────────────────────────
    async def _demet_islem(self, demet: str):
        for sat in demet.split("\n"):
            if not sat.startswith("data: "):
                continue
            gov = sat[6:]
            if gov == "[DONE]":
                return
            try:
                olay = json.loads(gov)
            except ValueError:
                continue
            secim = (olay.get("choices") or [{}])[0]
            delta = secim.get("delta") or {}
            tip = delta.get("type", "")
            if tip == "answer" and delta.get("content"):
                yield LLMTextFrame(delta["content"])
            elif tip == "faz":
                yield ZenaiFazFrame(delta.get("faz", ""), delta.get("detay", ""))
            elif delta.get("content"):
                yield LLMTextFrame(delta["content"])

    async def _zenai_akisi(self, messages: list[dict]):
        govde: dict = {"model": self._model, "stream": True, "messages": messages}
        if self._max_tokens:
            govde["max_tokens"] = self._max_tokens
        baslik = {"Content-Type": "application/json"}
        if self._mode:
            baslik["x-zenai-mode"] = self._mode
        try:
            async with self._client.stream(
                "POST", self._gateway + "/v1/chat/completions", json=govde, headers=baslik
            ) as r:
                if r.status_code != 200:
                    ozet = (await r.aread()).decode(errors="replace")[:300]
                    await self.push_error(
                        error_msg=f"ZenAI gateway {r.status_code}: {ozet}"
                        if r.status_code >= 500
                        else "ZenAI istek reddedildi: " + ozet[:100]
                    )
                    return
                tampon = ""
                async for parca in r.aiter_bytes():
                    tampon += parca.decode(errors="replace")
                    while "\n\n" in tampon:
                        demet, tampon = tampon.split("\n\n", 1)
                        async for kare in self._demet_islem(demet):
                            yield kare
                        if self._iptal.is_set():
                            return
                if tampon:
                    async for kare in self._demet_islem(tampon):
                        yield kare
        except httpx.TransportError as e:
            await self.push_error(error_msg="ZenAI bağlantı hatası", exception=e)

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, InterruptionFrame):
            self._iptal.set()
            await self.push_frame(frame, direction)
            return
        if isinstance(frame, LLMContextFrame):
            self._iptal.clear()
            await self.push_frame(LLMFullResponseStartFrame())
            try:
                sohbet = frame.context.get_messages() or frame.context.messages
                async for kare in self._zenai_akisi(list(sohbet)):
                    await self.push_frame(kare)
            finally:
                await self.push_frame(LLMFullResponseEndFrame())
        else:
            await self.push_frame(frame, direction)