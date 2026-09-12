# Sıfır Maliyet Kılavuzu

Bu projenin **koşulsuz kuralı**: çalışan sistem hiçbir yerde **TL/kuruş veya
kart** ödeme gerektirmez. Aşağısı her bileşenin nasıl `0 ₺` çalıştığını gösterir.

## Bileşen başına maliyet tablosu

| Bileşen | Ne kullanıyor | Maliyet | Not |
|---------|---------------|---------|-----|
| Akıl/model | OpenRouter `:free` modelleri (beyin `KONU_MODELLERI`) | `0 ₺` | Kotası biten free model fallback zinciriyle (`llm_provider`) değişir |
| Metin web arayüzü | Vercel serverless (elle, mevcut) | `0 ₺` | Hobby/ücretsiz tier |
| HUD (ses görseli) | Vercel statik ya da Cloudflare Pages | `0 ₺` | `voice/hud/vercel.json` ile |
| Gateway (SSE) | FastAPI + uvicorn (kendi sunucunuz / Fly.io ücretsiz / Oracle Always-Free ARM) | `0 ₺` | Fly.io ücretsiz tier: küçük makine |
| STT (Türkçe) | `mihuai/turkish-stt` (66M, CPU streaming) — yerel | `0 ₺` | Hugging Face'te ücretsiz |
| VAD | SileroVAD (MIT) — yerel | `0 ₺` | |
| TTS (Türkçe) | Piper TR (MIT) — yerel | `0 ₺` | `voice/bot` seçeneği |
| Wake/PTT | PTT düğmesi (HUD) | `0 ₺` | Porcupine TR yok; Türkçe STT kicker alternatifi |
| TURN (WebRTC) | Aynı sunucu → host SC. Ücretsiz sınırlar yetersizse Cloudflare TURN | `0 ₺` | Self-host edilen gateway zaten ortaklanır |
| BTN/veri | GitHub Actions (upstream CI) | `0 ₺` | |

## Sistemik maliyet sınırları

- **Kural**: sadece ücretsiz/open kaynak modeller, ücretli API anahtarı yok.
- OpenRouter free kotayı doldurursa: yerel Ollama (yoksa) veya başka free katman.
- Sesli ajan/rapor istendiğinde **açık onay** gerekir (ucuza token yer).
- Tüm ses işleme yerel CPU'da çalışır; GPU gerektirmez.

## Kayıt/ölçüm

- Aylık tahmini API maliyeti test koşucusunda `0 USD`.
- Vercel kotası yetmezse Fly.io'un ücretsiz process kotasında gateway çalışır
  (2 vCPU/512MB makine tier sınırı dahilinde).

## İstisna ilkesi

Bir bileşen ücretli tier'a kayarsa (ör. Vercel serverless soğuk başlangıç ya da
kotası), **projeyi ücretsiz bir alt uca taşı**: gateway'i Fly.io/Oracle
Always-Free'e, HUD'u Cloudflare Pages'e al. Bu dosya oyun planı değişimlerini
güncel tutar.