# Zenai Geliştirme Rehberi

Katkı veren herkes bu kurallara uyar.

## Katkı Akışı

1. **Issue aç** — yapılacak işi tek cümleyle anlat (hata, özellik, iyileştirme).
2. **Fork/tehdit** → ayrı bir dalda değişiklik yap.
3. **Küçük parçalar** — her commit tek mantıksal değişiklik içersin.
4. **Test ekle/sonra git** — değişikliğe uyan test olmadan merge olmaz.
5. PR'da: neyi, neden, hangi testle değiştirdiğini yaz.

## Testler

```bash
python3 -m pytest tests/ -q          # tam paket (41 test)
python3 -m pytest tests/test_guvenlik.py -q   # güvenlik kuralları
cd web && npm run test:gui            # Playwright GUI doğrulaması
```

CI her push'ta şu adımları çalıştırır: py_compile, pytest+coverage (≥%30),
pip-audit, npm audit. Güvenlik taramaları bu aşamada engellemez ama rapor çıkarır.

## Kod Stili

- Python: açıklayıcı İngilizce değişken adları + modül docstring'i;
  Türkçe dize/durum mesajları (hedef kitle TR).
- Gösterim/ürün katmanı (web, promptlar): Türkçe.
- Yorum yazma; yalnızca "neden" gerektiğinde açıklama koy.
- Dış bağımlılık eklemeden önce `requirements.txt`/`package.json` güncelle.

## Güvenlik Kuralları (Değişmez)

`agentv2/guvenlik.py` ve `web/api/mcp.js`'deki korumalar **taviz verilmaz**:
- `komut()`, `bash_kod()`, `python_kod()` girişleri her zaman ilgili
  doğrulamadan geçmeden çalıştırılamaz.
- Uzak uçlara bağlanan her yeni kod `url_guvenli`/MCP SSRF korumasına takılır.
- Yeni bir güvenlik kuralı eklenince `tests/test_guvenlik.py`'ye regresyon testi ekle.

## Bellek / Kayıt Dosyaları

- Bellek: `~/.zenai_bellek.json` (vektör arama; süresi dolan kayıtlar otomatik silinir)
- Routing istatistiği: `kayit/routing_log.jsonl` — `routing_rapor()` ile özetlenir
- Bunlar repo'ya **işlenmez** (`kayit/` .gitignore'da).

## Sürüm Notları

Değişiklikler `CHANGELOG.md`'ye eklenir (düzeltme/özellik/iyileştirme bölümleri).