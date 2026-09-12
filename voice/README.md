# ZenAI Voice — sesli asistan katmanı

Metin tabanlı ZenAI beyninin (`agentv2`) üzerine kurulmuş, tamamen ücretsiz
(0 ₺), açık kaynak ses + HUD katmanı. Beyin **değişmez**; bu katman beyni
sarmalar ve akışkan sesli sohbet sunar.

## İçerik

| Dizin | Ne? |
|-------|-----|
| `server/` | SSE gateway: `/v1/chat/completions` (OpenAI-uyumlu), chat/ajan/rapor akışları |
| `hud/` | JARVIS tarzı tarayıcı HUD (canvas orb + mikro ses görselleştirme + PTT) |
| `bot/` | Pipecat sesli bot (WebRTC/WS: VAD + STT + TTS, barge-in) |
| `tests/` | Gateway + streamer + bot + HUD testleri (ağ yok) |
| `docker/` | 0-maliyet dağıtım (gateway + HUD + opsiyonel bot) |
| `docs/` | MİMARİ · SIFIR_MALIYET · LİSANS |

## Hızlı başlangıç

```bash
# 1. gateway bağımlılıkları
pip install -r voice/requirements.txt

# 2. gateway + beyin testleri
python -m pytest voice/tests/test_streamer.py voice/tests/test_gateway.py -q
node voice/tests/test_hud.js

# 3. gateway'i başlat
python -m voice.server.run            # http://127.0.0.1:8787

# 4. HUD'u aç (herhangi bir statik sunucu)
cd voice/hud && python -m http.server 8080   # http://127.0.0.1:8080
```

## HUD ile konuşma (metin modu)

1. `voice/hud/index.html` açın.
2. Gateway adresi ayar çubuğunda varsayılan `http://127.0.0.1:8787`.
3. Yazıp **▶** gönderin → orb DÜŞÜNÜYOR → KONUŞUYOR akışını yansıtır;
   yanıt aşağıdaki sohbet kaydında token token belirir.
4. **🗣 KONUŞ** düğmesini veya **Boşluk**'u basılı tut = push-to-talk
   (`dinliyor` durumu); ses köprüsü ayarlandığında WebRTC ile canlıya geçer.

## Sesli mod (WebRTC, opsiyonel)

`voice/bot` Pipecat kullanır; ekstra paketler:

```bash
pip install "pipecat-ai[webrtc,silero,whisper,piper]>=1.10"
python -m voice.bot.run bak                       # bağımlılık sağlık kontrolü
python -m voice.bot.run --transport webrtc --port 8788
```

STT varsayılanı **`mihuai/turkish-stt`** (Türkçe, CPU streaming);
TTS **Piper TR**. Barge-in Silero VAD ile yönetilir
(`voice/bot/zenai_llm.py` InterruptionFrame iptali).

## Sözleşme (OpenAI-uyumlu SSE)

`POST /v1/chat/completions {model:"chat", messages:[...], stream:true}`

```
data: {"choices":[{"delta":{"type":"faz","faz":"hazirlaniyor","durum":"dusunuyor"}}]}
data: {"choices":[{"delta":{"type":"answer","content":"Merhaba "}}]}
data: [DONE]
```

- `x-zenai-mode: chat|ajan|rapor` (isteğe bağlı) akış modunu zorlar.
- `stream:false` → tek `chat.completion` nesnesi.
- Ağ yok: başarısız sağlayıcıda fallback zinciriyle devam eder.

## Testler

| Test | Komut | Kapsam |
|------|-------|--------|
| Streamer + Gateway | `pytest voice/tests/test_streamer.py voice/tests/test_gateway.py` | sözleşme, modlar, fallback |
| Bot (Pipecat) | `pytest voice/tests/test_bot.py` | uçtan uca SSE → `LLMTextFrame` |
| HUD | `node voice/tests/test_hud.js` | durum makinesi + SSE ayrıştırıcı |

## 0 maliyet

Tam rehber: `voice/docs/SIFIR_MALIYET.md`. Kısaca: OpenRouter `:free`,
yerel STT/VAD/TTS (CPU), HUD için Vercel/Cloudflare ücretsiz, gateway için
kendi makineniz ya da Fly.io/Oracle ücretsiz tier.