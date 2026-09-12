# ZenAI Voice — Mimari

## Özet

ZenAI'nin **metin** tabanlı beyni (`agentv2/`) değiştirilmeden üzerine bir
**sesli konuşma + HUD** katmanı eklenir. Beyin bir monorepo paylaşımı altında
`voice/` alt dizininde yaşar; böylece beyindeki her geliştirme otomatik olarak
sesli katmana da yansır.

```
                    ┌────────────── Vercel (mevcut, değişmedi) ──────────────┐
  Tarayıcı (web/) ──►  api/chat.js ──► OpenRouter (:free modeller, agentv2)
                    └────────────────────────────────────────────────────────┘

  Tarayıcı HUD ──► /v1/chat/completions (SSE)              ──►  agentv2 beyni
  (voice/hud)          │        ▲ (OpenAI-uyumlu sözleşme)   (model_routing,
   durum makinesi      │        │                            llm_provider,
+ ses görselleştirme▼        │                            akil_motoru,
                        voice/server/gateway.py ◄────────────────  araclar/)
                    └─ thread→asyncio Kanal köprüsü
                          ▲
                          │  voice/server/streamer.py
                          │    . chat  : canlı token (fallback: sira_sor/Ollama)
                          │    . ajan  : zz.llm sarmalanır, plan sessiz
                          │    . rapor : kalp atışı + parçalı yayın
                          │
  Sesli uç (voice/bot, Pipecat) ◄────────  WebRTC/WS (STT·VAD·TTS)
```

## Katmanlar

| Katman | Dizin | Görev | Test |
|--------|-------|-------|------|
| HUD (tarayıcı) | `voice/hud/` | Canvas orb, AnalyserNode, durum makinesi, PTT, SSE istemcisi | `voice/tests/test_hud.js` |
| Gateway (HTTP) | `voice/server/gateway.py` | OpenAI-uyumlu `/v1/chat/completions` (SSE + tek cevap), CORS, IP limiti | `test_gateway.py` |
| Akış motoru | `voice/server/streamer.py` | chat/ajan/rapor akışları, fallback zinciri, sarmalama | `test_streamer.py` |
| Mod/konu seçimi | `voice/server/modes.py` | `mod_tanima`, `konu_bul`, `model_sec` | — (streamer üzerinden) |
| Bot (sesli) | `voice/bot/` | Pipecat: `ZenaiLLMService`, VAD+STT+TTS boru hattı | `test_bot.py` |
| Dağıtım | `voice/docker/` | Gateway + HUD compose; sıfır maliyet | — |
| Doküman | `voice/docs/` | Bu dökümanlar | — |

## Kritik tasarım kararları

1. **Beyin el değmemiş.** `streamer.akis_uret` `zenai_zeka.llm`'i sarmalar ve
   her hâlükârda orijinalini geri yükler; ajan/rapor modunda kod değişmez.
2. **OpenAI uyumlu sözleşme.** Gateway `choices[].delta` içinde
   `type: answer|faz` alanı taşır; HUD ve Pipecat aynı zinciri tüketir.
3. **Yavaş modlar ayrık.** Sesli arayüz varsayılan `chat`; `ajan`/`rapor`
   açıkça isteyerek tetiklenir, oylama sesli tarafta atlanır.
4. **0 maliyet.** Ücretli API yok; `:free` OpenRouter modelleri + lokal
   STT/TTS/VAD (beyin rotası) + Vercel ücretsiz + Fly/Oracle ücretsiz yeterli.

## Akış örneği (chat)

```
HUD → POST /v1/chat/completions {model:"chat", messages:[...], stream:true}
gateway → _istek_ozet (mod tespiti) → streamer.akis_uret → kanal.yayinla_*
SSE:  data: {"delta":{"type":"faz","faz":"hazirlaniyo"...}}
      data: {"delta":{"type":"answer","content":"Merhaba "}} ...
      data: [DONE]
HUD:  durum makinesi d.y "faz"→DÜŞÜNÜYOR, "answer"→KONUŞUYOR + orb enerjisi
```