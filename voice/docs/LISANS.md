# Lisans ve Uyumluluk

ZenAI Voice açık kaynaktır; lisanslar tek tek bileşen bazında ayrı ayrıdır.
Tüm taban (beyin/`agentv2` + ses katmanı/`voice`) **MIT License** kapsamındadır
(bkz. kök `LICENSE`), telif: Lennebraha38 (2026).

## Bileşen lisansları

| Bileşen | Lisans | Sahip | Ticari kullanım | Not |
|---------|--------|-------|-----------------|-----|
| ZenAI `agentv2` (beyin) | MIT | proje sahibi | ✓ | |
| `voice/server` (gateway/streamer) | MIT | proje sahibi | ✓ | |
| `voice/hud` (HUD) | MIT | proje sahibi | ✓ | |
| `voice/bot` (Pipecat adaptörü) | MIT | proje sahibi | ✓ | |
| OpenRouter | API hizmeti (free tier) | OpenRouter | — | model sağlayıcı şartlarına tabi |
| Pipecat (`pipecat-ai`) | BSD 2-Clause | Daily Co. | ✓ | |
| SileroVAD | MIT | Silero | ✓ | |
| faster-whisper / mihuai/turkish-stt | MIT | Sygil-Dev / Mihuai | ✓ | FLEURS değerlendirme verisi CC |
| Piper TTS | MIT | Rhasspy | ✓ | sesli setler `CC BY-NC`* |
| Edge-TTS | MIT (araç) | rany2 | ⚠ | Microsoft hizmet şartları; üretim için değiştir/çıkar |

* Piper TR kadın/erkek setleri koşullandırırsa ticari üretim için
`CC BY-NC` sürümünü kullanın; ticari istekte ücretsiz/CC-BY setine geçin.

## MIT bildirimi

Referans MIT metni `LICENSE` dosyasındadır. Kullanıma bağlı her dosyanın
başında ayrı bir telif başlığı tutulmaz; proje kökü lisans bildirimi geçerlidir.

## Uyumluluk notları (güvenlik)

- `agentv2` + `voice` birlikte dağıtılabilir; iki lisans uyumludur.
- STT/TTS/VAD modelleri cihaz üzerinde (CPU) indirilir — veri dışarı gitmez.
- Sadece beyin güncel versiyonu zorunludur; ses katmanı `MIT + BSD` toplamıdır.