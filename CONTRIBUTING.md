# ZenAI Geliştirme Rehberi

Katkı veren herkes bu kurallara uygun şekilde çalışır.

## Katkı Akışı

1. **Issue aç** — yapacak işi tek cümleyle anlat (hata, özellik, iyileştirme).
2. **Fork/tehdit** → ayrı bir dalda değişiklik yap.
3. **Küçük parçalar** — her commit tek mantıksal değişiklik içersin.
4. **Test ekle/sonra git** — değişiklikle uyumlu test olmadan merge olmaz.
5. **PR'da**: neyi, neden, hangi testle değiştirdiğini yaz.

## Kurulum

```bash
git clone https://github.com/Lennebraha38/lenbeyni
cd lenbeyni
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Ortam değişkenleri (`.env.example` bak):

```bash
export OPENROUTER_KEY="sk-or-v1-..."      # API anahtarı (zorunlu)
export ZENAI_ORIGIN="https://..."         # CORS allowlist (varsayılan Vercel)
export ZIRVE_MODEL="openai/gpt-4o-mini"   # benchmark acil yolu (rate-limit)
```

## Testler

```bash
python3 -m pytest tests/ -q                          # tam paket (160 test)
python3 -m pytest tests/test_guvenlik.py -q          # güvenlik kuralları
python3 -m pytest tests/test_lenbeyni.py -q          # lenbeyni modülü
python3 agentv2/dogrulama.py --adet 10               # bağımsız strict doğrulama (hızlı)
cd web && npm run test:gui                            # Playwright GUI doğrulaması
```

CI her push'ta şu adımları çalıştırır: `py_compile`, `pytest+coverage (≥%40)`, `pip-audit`, `npm audit`. Güvenlik taramaları bu aşamada engellemez ama rapor çıkarır.

## Kod Stili

- Python: açıklayıcı İngilizce değişken adları + modül docstring'i;
  Türkçe dize/durum mesajları (hedef kitle TR).
- Gösterim/ürün katmanı (web, promptlar): Türkçe.
- Yorum yazma; yalnızca "neden" gerekiyorsa açıklama koy.
- Dış bağımlılıkle eklemeden önce `requirements.txt`/`package.json` değiştir.
- Tip hintleri: tüm çekirdek fonksiyonlarda `from typing import Optional, Tuple, List, Dict, Any` ile annotasyon zorunlu.

## Güvenlik Kuralları (Değişmez)

`agentv2/guvenlik.py` ve `web/api/mcp.js`'deki korumalar **taviz verilmaz**:

- `komut()`, `bash_kod()`, `python_kod()` girişleri her zaman ilgili
  doğrulamadan geçmeden çalıştırılamaz.
- Uzak uçlara bağlanan her yeni kod `url_guvenli`/MCP SSRF korumasına takılır.
- Yeni bir güvenlik kuralı eklenince `tests/test_guvenlik.py`'ye regresyon testi ekle.
- GitHub token'ları `.git/config`'de veya commit'te saklama — rotasyon yap.

## Bellek / Kayıt Dosyaları

- Bellek: `~/.zenai_bellek.json` (vektör arama; süresi dolan kayıtlar otomatik silinir)
- Routing istatistiği: `kayit/routing_log.jsonl` — `routing_rapor()` ile özetlenir
- Bunlar repo'ya **işlenmez** (`kayit/` .gitignore'da).

## Sürüm Notları

Değişiklikler `CHANGELOG.md`'ye eklenir (düzeltme/özellik/iyileştirme bölümleri).

## Öneriler

- **CI kırığı** varsa hemen bildir: `.github/workflows/ci.yml` satır 15 `agentv2/zenai_zeka.py`'yi derler.
- OpenRouter URL'leri merkezi `OPENROUTER_URL` sabitinden gelir (`agentv2/model_routing.py`).
- `meclis_hakemi.py`'deki kriter puanlayıcıları gerçek ölçüm tabanlıdır; LLM-as-judge eklenebilir.