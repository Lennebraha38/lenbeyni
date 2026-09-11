# Zenai

**Yerel + Mega Beyin mimarisiyle çalışan Türkçe yapay zeka asistan projesi.**
*(eski adı: LenBeyni — rebrand)*

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
| **Otomatik Skorer** | `agentv2/otomatik_skorer.py` | Soru-bazlı beklenen yanıt (`soru_bankasi.HEDEFLER`) eşleştirir: matematik=sayısal, mantik/dil=anahtar kavram; kod=sandbox çalıştırma |
| **Cogunluk Oyu** | `agentv2/cogunluk_oyu.py` | Ayni soruyu N kez sorar, en sik cevabi secer (dogrulugu istatistiksel artirir) |
| Karşılama testi | `karsilastirma.py` | Turkce karsilastirma + rate-limit aware (retry + backoff) |
| Benchmark | `agentv2/tam_zirve.py` + `soru_bankasi.py` | **150 soru** / 10 konu / 3 zorluk; `--kategori`, `--zorluk` filtreleri |
| Deep Research | `agentv2/lenbeyni_zeka.py` (`rapor` modu) | Soruyu alt-başlıklara böler, kaynakları toplar, kaynaklı kurumsal rapor yazar |
| Bellek (vektör) | `agentv2/bellek_vektor.py` | Karakter n-gram benzerliğiyle hatırlar (`~/.zenai_bellek.json`); TTL + kullanıcı izolasyonu |
| Güvenlik | `agentv2/guvenlik.py` + `SECURITY.md` | SSRF / kod / path / prompt-injection koruması — araç girişlerinde deny-by-default |
| Web GUI | `web/` | Gemini/Claude seviyesi arayüz: konu→model yönlendirme rozeti, Akıl Motoru, AI Meclisi, **Skills ekleme**, **MCP bağlama** |
| Kod eğitimi | `egitim/` | QLoRA ile 7B/14B kod modeli fine-tune (Kaggle) |
| Cihaz beyni | `ciday/` (tablet) | Ollama tabanlı, offline sohbet/kod |
| Arac katmanı | `agentv2/araclar/` | 10+ yetenek: belge, kod sandbox, sistem, github, haber, hava, gorsel, guvenlik (browser-use/gpt-researcher/OpenCLI ozleri) |

## Test

```bash
python3 -m pytest tests/ -q          # 41 test (akil katmani + guvenlik + meclis + araclar + token tavani)
python3 agentv2/otomatik_skorer.py karsilastirma.json   # canli test skoru raporu
python3 agentv2/cogunluk_oyu.py "soru" --tekrar 3       # majority vote
python3 agentv2/tam_zirve.py --soru 10                  # zirve testi (ilk 10 soru)
python3 agentv2/tam_zirve.py --kategori kod             # sadece kod sorulari
python3 agentv2/tam_zirve.py --zorluk zor               # sadece zor sorular
python3 agentv2/tam_zirve.py --kalan-bekle              # rate-limit bekle, surekli dene
python3 agentv2/meclis_hakemi.py "soru"                 # genisletilmis hakem paneli (12 kriter)
python3 agentv2/akil_dongu_test.py "soru"               # 5 tur kalite olcumu: baseline/cot/sc/kombinasyon/meclis

> Rate-limit notu: ücretsiz OpenRouter modelleri 429 dönebilir; `--kalan-bekle`
> otomatik bekler. Zirve raporunu `agentv2/tam_zirve.py --sadece-skor` ile gör.

### Benchmark — gerçek ölçüm
Ücretsiz modeller 429 ile kotalı olduğunda benchmark `ZIRVE_MODEL` ile acil
yoldan çalışır (ör. `ZIRVE_MODEL=openai/gpt-4o-mini`). İlk gerçek koşu
(50 soru, gpt-4o-mini, self-correction + routing): **71.3/100**. Skorlayıcı
soru-bazlı beklenen yanıt tablosu (`soru_bankasi.HEDEFLER`) ile güçlendirilip
cevap üretimi "Sonuç: <değer>" disiplinine alındıktan sonra ikinci koşu:
**92.7/100, 50/50 başarılı, 0 hata**. Konu bazlı: dil 100.0, matematik 95.0,
kod 88.0, mantik 77.0. (İlk koşudaki 50.0'lar skorlayıcı artefaktıydı;
matematik yanıtları zaten doğruydu, ölçüm tablosu eski soru numaralarına
kilitliydi.) Her skor `kayit/routing_log.jsonl`'e işlenir ve
`model_routing.routing_rapor()` ile gerçek veri üzerinden model önerisi üretir.

## Kurulum

```bash
pip install requests
export OPENROUTER_KEY="sk-or-v1-..."
python3 agentv2/lenbeyni_zeka.py "sorun" ajan
python3 agentv2/lenbeyni_zeka.py "araştırma konusu" rapor
```

## Web GUI: Gemini/Claude seviyesi arayüz

**ZERO-CONFIG** — kullanıcı tarayıcıda hiçbir key'le uğraşmaz (Gemini gibi):
- **Sunucu rölesi** (`web/api/chat.js`): OpenRouter key'i sadece Vercel env'inde tutulur (`OPENROUTER_KEY`). Tarayıcıya key asla sızmaz.
- **MCP rölesi** (`web/api/mcp.js`): Uzak MCP sunucularına JSON-RPC over HTTP ile alet listeleme/çağırma — key gerekmez.
- Sunucu yoksa kullanıcı kendi key'ini girebilir (geliştirici modu). Key localStorage'da saklanır, sunucuya gitmez.

**Özellikler:**
- **Akıl yönlendirme rozeti** — soruyu okuyup konu tespiti yapar, doğru modeli önerir (kod→north-mini, matematik→nemotron, vb.)
- **Skills** — Yetenekler panelinden mevcut skill'leri aç/kapat, **yeni skill ekle** (ad + sistem talimatı). Aktif skill'ler cevap üretirken sistem talimatına enjekte edilir ve mesajda ✨etiketi olarak görünür.
- **MCP bağlama** — Sağ panelden sunucu adı + uç nokta girerek bağlan. Bağlı aletler listelenir (● bağlı / ! hata). Model ihtiyaç duyarsa `TOOL_CALL:` satırıyla alet çıktırması yapar, sonuç geri beslenir.
- **Modlar** — Sohbet / Akıl Motoru (CoT + kapsamlı) / AI Meclisi (3 model + hakem)
- **Araçlar** — Web araması + site okuma (gerçek veri, sistem promptuna beslenir)
- **Markdown** — Başlık, liste, tablo, kod bloğu (kopyala butonuyla), alıntı
- **Sohbet listesi** — Sol panelde geçmiş konuşmalar, yeni sohbet, temizle

**Test:**
```bash
NODE_PATH=$(npm root -g) node web/web_gui_test.js   # Playwright GUI doğrulaması
```

```bash
# Vercel'e deploy:
# 1. Repo'yu Vercel'e bağla
# 2. Settings -> Environment Variables -> OPENROUTER_KEY ekle
# 3. Deploy et — bitti.
```

## Lisans

MIT