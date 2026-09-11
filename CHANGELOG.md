# Changelog

Tüm önemli değişiklikler bu dosyada toplanır.

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