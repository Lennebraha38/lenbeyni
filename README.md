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

## Kurulum

```bash
pip install requests
export OPENROUTER_KEY="sk-or-v1-..."
python3 agentv2/lenbeyni_zeka.py "sorun" ajan
python3 agentv2/lenbeyni_zeka.py "araştırma konusu" rapor
```

Web paneli için `web/` klasörünü Vercel'e statik deploy et.

## Lisans

MIT