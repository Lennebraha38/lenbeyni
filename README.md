# LenBeyni

**Yerel + Mega Beyin mimarisiyle çalışan Türkçe yapay zeka asistan projesi.**

Tabletten buluta uzanan iki kademeli beyin sistemi:
- **Yerel beyin** (Ollama): 7B/14B kod modeli — offline, kendi donanımında
- **Mega beyin** (OpenRouter): 550B Nemotron — bulutta, ücretsiz

## Modüller

| Modül | Dosya | Ne yapar |
|---|---|---|
| Ajan döngüsü | `agentv2/lenbeyni_zeka.py` | `[ARAMA]` / `[SITE]` komutlarıyla web'i talimatla tarar |
| Deep Research | `agentv2/lenbeyni_zeka.py` (`rapor` modu) | Soruyu alt-başlıklara böler, kaynakları toplar, kaynaklı kurumsal rapor yazar |
| Bellek | `agentv2/lenbeyni_zeka.py` (`bellek` modu) | Araştırma sonuçlarını hatırlar (`~/.lenbeyni_bellek.json`) |
| Web GUI | `web/` | Tarayıcıdan erişilen ajan paneli (AI Meclisi modu dahil) |
| Kod eğitimi | `egitim/` | QLoRA ile 7B/14B kod modeli fine-tune (Kaggle) |
| Cihaz beyni | `ciday/` (tablet) | Ollama tabanlı, offline sohbet/kod |
| Arac katmanı | `agentv2/araclar/` | 10+ yetenek: belge, kod sandbox, sistem, github, haber, hava, gorsel, guvenlik (browser-use/gpt-researcher/OpenCLI ozleri) |

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