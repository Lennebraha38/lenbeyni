"""ZenAI Voice — Pipecat konuşma botu katmanı.

* ``zenai_llm.ZenaiLLMService`` — Pipecat LLM servisi olarak gateway SSE akışı.
* ``pipeline.SesAyarlar`` / ``bot_pipeline`` — VAD + STT + LLM + TTS boru hattı.
* ``run`` — yerel // sunucu başlatıcı (WebRTC/kulaklık uçları ekstraları gerektirir).
"""