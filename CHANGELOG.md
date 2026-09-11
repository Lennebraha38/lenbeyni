# Changelog

Tüm önemli değişiklikler bu dosyada toplanır.

## [2.2.0] — Devam ediyor

### Ölçüm dürüstleştirme (bağımsız doğrulama)
- `agentv2/otomatik_skorer.py`: `puan_dil`, `puan_konu`, `puan_mantik` artık
  doğruluk ağırlıklı — HEDEFLER kavramı yoksa/tutmadıysa en fazla **0.4**;
  uzunluk/yapı tek başına puana çevrilmiyor. `puanla()`: hatalı/başarısız
  sorular **0 sayılır**, `ortalama_cevaplanan` ayrı raporlanır.
- `agentv2/dogrulama_seti.py` (YENİ): HEDEFLER'den tamamen bağımsız **40 gerçek
  soru** (matematik 8, bilim 5, tarih 5, kültür 6, dil 5, teknoloji 5, pratik 4,
  mantık 2) — mutlak cevaplı, sızma (leak) riski yok.
- `agentv2/dogrulama.py` (YENİ): strict koşucu — `puan_strict` (ya doğru ya
  yanlış, uzunluk/puan yapısı yok), binlik ayıracı normalizasyonu
  ("300.000"→"300000"), fallback zinciri, `--adet`, `--kalan-bekle`,
  `kayit/dogrulama.json` çıktısı.
- README benchmark bölümü yeniden yazıldı: ana ölçünün bağımsız `dogrulama.py`
  olduğu, `tam_zirve`nin tanı/reçete amaçlı kaldığı netleştirildi.

### Web rölesi güvenliği (chat.js / mcp.js)
- CORS wildcard kaldırıldı: yalnız `ZENAI_ORIGIN` allowlist'i
  (varsayılan `https://zenai-two.vercel.app`); `web/vercel.json` da wildcard
  içermiyor.
- Opsiyonel `ZENAI_ACCESS_TOKEN` (Bearer veya `x-zenai-token`).
- IP bazlı bellek-içi rate limit: 60 sn'de chat 30 / MCP 60 istek.
- `max_tokens` ≤16K, mesaj ≤60K, MCP argümanları ≤20K karakter.

### Repo temizliği
- `out.png` izlemeden çıkarıldı, `.db`/test-sonuç artıkları silindi.
- `agentv2/lenbeyni_zeka.py` → `agentv2/zenai_zeka.py` (tüm import/başvurular
  güncellendi; `test_lenbeyni`, `cogunluk_oyu`, `meclis_hakemi`,
  `akil_dongu_test`, `self_correction`, README, ENTEGRASYON_MATRISI).

### Not: önceki 92.7/100 iddiası
Self-skor (92.7, 71.3) yalnızca kendi `HEDEFLER` tablosuna göre üretilmişti;
yetersiz ölçümdü. Bağımsız not **65/100** (2026 genel değerlendirme). Bu
sürümde skorlayıcı dürüstleştirildi ve gerçek doğruluk için bağımsız set
eklendi. Kotalar açılınca (~12 Eylül sonrası) canlı `dogrulama.py` koşusu
yayınlanacak.

## [2.1.0] — Devam ediyor

### Puan 71.3 → 92.7/100 (ikinci gerçek benchmark)
- Skorlayıcı soru-bazlı beklenen yanıt tablosuyla güçlendirildi
  (`soru_bankasi.HEDEFLER`): matematik tam sayı/kesir/ondalık eşleşmesi,
  mantik/dil anahtar kavram eşleşmesi + LaTeX `\sqrt`/kök normalizasyonu.
- `tam_zirve.py`: `BENCH_SISTEM` promptu — her cevapta en az 3 madde ve
  "Sonuç: <değer>" satırı; self-correction tüm konularda çalışır.
- Yeni koşu (50 soru, gpt-4o-mini): **92.7/100, 50/50 başarılı, 0 hata**.
  Konu bazlı: dil 100.0, matematik 95.0, kod 88.0, mantik 77.0.
  (İlk koşudaki matematik 50.0'i skorlayıcı artefaktıydı: ölçüm tablosu eski
  soru numaralarına kilitliydi; yanıtlar zaten doğruydu.)
- Testler: beklenen-hesapli skorlama senaryoları (matematik doğru/yanlış,
  mantik kavram varlığı) eklendi.

### İlk gerçek benchmark ölçümü
- 50 soruluk koşu (gpt-4o-mini override) → **71.3/100, 50/50 başarılı, 0 hata**.
  Konu bazlı: kod 87.0, dil 84.0, matematik 50.0, mantik 50.0.
- `tam_zirve.py`: `ZIRVE_MODEL` ortam değişkeni — ücretsiz modeller 429 ile
  kotalandığında acil yol olarak belirli bir modelle tüm soruları koşar.

### Güvenlik (yeni)
- `agentv2/guvenlik.py`: SSRF (özel/CGNAT/metadata IP bloğu), tehlikeli komut
  blok listesi, Python AST taraması, path traversal engeli, prompt-injection
  tespiti (EN+TR).
- `agentv2/araclar/kod_sandbox.py`: `python_kod`/`bash_kod`/`node_kod` artık
  güvenlik taramasından geçmeden çalışmaz; temp cwd + `-I` izole mod + RLIMIT
  (CPU/memory) + temiz env.
- `agentv2/araclar/arac_katmani.py`: `sayfa()` URL güvenliği, `komut()` blok kontrolü.
- `agentv2/araclar/__init__.py`: `[BELGE]`/`[LISTE]` yolları izinli kökle sınırlı.
- `web/api/mcp.js`: SSRF koruması (protokol/port/özel IP DNS doğrulaması).
- `SECURITY.md`: risk modeli ve sorumlu açıklama politikası.

### Bellek (iyileştirme)
- `agentv2/bellek_vektor.py`: karakter n-gram TF-IDF kosinüs benzerliği,
  zaman damgası + süre (TTL), kullanıcı izolasyonu, `unut` komutu.
- Bellek yolu: `~/.lenbeyni_bellek.json` → `~/.zenai_bellek.json`.

### Benchmark (genişletme)
- `agentv2/soru_bankasi.py`: 50 → **150 soru**, 10 konu × 15, zorluk seviyeleri
  (kolay/orta/zor).
- `agentv2/tam_zirve.py`: `--kategori`, `--zorluk` filtreleri; skorların
  `kayit/routing_log.jsonl`'e otomatik kaydı.
- `agentv2/model_routing.py`: veri odaklı izleme (`routing_logla`, `routing_rapor`, `model_profil`).

### CI / Test
- Test paketi 29 → **41 test** (`tests/test_guvenlik.py`, vektör bellek, zirve filtreleri).
- `.github/workflows/ci.yml`: coverage (≥%30), `pip-audit`, `npm audit`,
  node-20 kurulumu, yeni modüllerin derleme kontrolü.
- `web/package.json` + `package-lock.json` eklendi.

### Dokümantasyon
- `CONTRIBUTING.md`, `CHANGELOG.md`, `.env.example` genişletildi.
- README: test sayıları, benchmark 150 soru, `~/.zenai_bellek.json` yolu güncellendi.

## [2.0.0] — ZenAI rebrand + Vercel deploy
- LenBeyni → **ZenAI** marka değişimi (web, agentv2, docs).
- Canlı adres: `https://zenai-two.vercel.app`
- Design System 2.0 (tokens, nebula arkaplan, cam paneller).
- Rebrand öncesi tüm geliştirme tarihçesi `git log` içindedir.