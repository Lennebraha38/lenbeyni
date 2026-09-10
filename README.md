# LenBeyni

**Yerel + Mega Beyin mimarisiyle çalışan Türkçe yapay zeka asistan projesi.**

Tabletten buluta uzanan iki kademeli beyin sistemi:
- **Yerel beyin** (Ollama): 7B/14B kod modeli — offline, kendi donanımında
- **Mega beyin** (OpenRouter): 550B Nemotron — bulutta, ücretsiz

## Modüller

| Modül | Dosya | Ne yapar |
|---|---|---|
| Ajan döngüsü | `agentv2/lenbeyni_zeka.py` | `[ARAMA]` / `[SITE]` komutlarıyla web'i talimatla tarar |
| **Akil Motoru** | `agentv2/akil_motoru.py` | Claude'un az-token/yuksek-mantik felsefesi + bizim bol-token: CoT yontemi, 5000 kelime hedefi, kendi kendini dogrulama |
| **Model Routing** | `agentv2/model_routing.py` | Konuya gore uzman model: kod->north-mini-code, matematik/mantik->nemotron-550B, diger->dots-3 (2-4x Claude token butcesi) |
| **Self-Correction** | `agentv2/self_correction.py` | Kod cevaplari sandbox'ta calistirilir -> syntax/runtime hatasi bulunursa model duzeltme turu yapar |
| **Otomatik Skorer** | `agentv2/otomatik_skorer.py` | Test cevaplarini makineyle puanlar: kod=calistir, matematik=hesapla, dil=yapiskan metrikler |
| **Cogunluk Oyu** | `agentv2/cogunluk_oyu.py` | Ayni soruyu N kez sorar, en sik cevabi secer (dogrulugu istatistiksel artirir) |
| Karşılama testi | `karsilastirma.py` | 50 konulu turkce karsilastirma + rate-limit aware (retry + backoff) |
| Deep Research | `agentv2/lenbeyni_zeka.py` (`rapor` modu) | Soruyu alt-başlıklara böler, kaynakları toplar, kaynaklı kurumsal rapor yazar |
| Bellek | `agentv2/lenbeyni_zeka.py` (`bellek` modu) | Araştırma sonuçlarını hatırlar (`~/.lenbeyni_bellek.json`) |
| Web GUI | `web/` | Tarayıcıdan erişilen ajan paneli (tek model, AI Meclisi, Web Ajanı, Akil Motoru modları) |
| Kod eğitimi | `egitim/` | QLoRA ile 7B/14B kod modeli fine-tune (Kaggle) |
| Cihaz beyni | `ciday/` (tablet) | Ollama tabanlı, offline sohbet/kod |
| Arac katmanı | `agentv2/araclar/` | 10+ yetenek: belge, kod sandbox, sistem, github, haber, hava, gorsel, guvenlik (browser-use/gpt-researcher/OpenCLI ozleri) |

## Test

```bash
python3 -m pytest tests/ -q          # 24 test (akil katmani + araclar + token tavani)
python3 agentv2/otomatik_skorer.py karsilastirma.json   # canli test skoru raporu
python3 agentv2/cogunluk_oyu.py "soru" --tekrar 3       # majority vote
```

## Kurulum

```bash
pip install requests
export OPENROUTER_KEY="sk-or-v1-..."
python3 agentv2/lenbeyni_zeka.py "sorun" ajan
python3 agentv2/lenbeyni_zeka.py "araştırma konusu" rapor
```

## Web paneli: ZERO-CONFIG (key gerekmez)

Kullanıcı tarayıcıda hiçbir key'le uğraşmaz — Gemini gibi:
- **Sunucu rölesi** (`web/api/chat.js`): OpenRouter key'i sadece Vercel env'inde tutulur
  (`OPENROUTER_KEY`). Tarayıcıya key asla sızmaz.
- Panel açılır → "⚡ Hazır — key gerekmez" rozetini görür → mesajı yazar → cevap gelir.
- Sunucu yoksa kullanıcı kendi key'ini girebilir (geliştirici modu).

```bash
# Vercel'e deploy:
# 1. Repo'yu Vercel'e bağla
# 2. Settings -> Environment Variables -> OPENROUTER_KEY ekle
# 3. Deploy et — bitti.
```

## Lisans

MIT