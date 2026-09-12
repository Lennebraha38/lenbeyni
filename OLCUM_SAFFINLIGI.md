# ZenAI ölçüm şeffaflığı raporu

Her skor raporu şu alanları içerir:

## Biçim

```
Kaynak dosya | Yöntem | Model | Tarih | Doğru/Toplam | Yüzde
```

## Ölçüm türleri

### Kat-1: Bağımsız doğrulama (dogrulama.py)

- **Kaynağı**: dogrulama_seti.py → INDEPENDENT (40 gerçek soru)
- **Yöntem**: strict eşleştirme (doğru/yanlış) — uzunluk/yapı puanı yok
- **Model**: varsayılan (dots-studio/dots-3-note-preview:free) veya ZIRVE_MODEL ile override
- **Tarih**: çalıştırılan session'ın tarihi
- **Çıktı**: dogru/toplam, yüzde, konu bazlı ozet

Yorum: "Gerçekten zeki mi?" sorusunun dürüst cevabı burada. Uzunluk veya yapı puanı vermez.

### Kat-2: Zirve / kendi bankası (tam_zirve.py)

- **Kaynağı**: tam_zirve.py → SORULAR (150 soru, 10 konu, 3 zorluk)
- **Yöntem**: hedef bazlı scoring — hedefsiz cevap ≤0.4, hatalı sorular 0
- **Model**: varsayılan veya ZIRVE_MODEL
- **Tarih**: çalıştırılan session'ın tarihi
- **Çıktı**: genel_puan, cevaplanan ortalaması, konu bazlı ozet

Yorum: Tanı-reçete amaçlı; kendi soru bankasına göre üretilmiş ölçüm. Bağımsız doğrulamanın yerine geçmez.

### Kat-3: Karsilastirma (karsilastirma.py)

- **Kaynağı**: karsilastirma.py → 50-konu karşılaştırma testi
- **Yöntem**: Konuya göre model routing + self-correction; sonuç json olarak kaydedilir (karsilastirma.json)
- **Model**: routing tarafından seçilen (KONU_MODELLERI)
- **Tarih**: çalıştırılan session'ın tarihi
- **Çıktı**: karsilastirma.json → otomatik_skorer.py ile skor raporu

Yorum: Gerçek gebruikscenario — routing + correction + çoğuluk oyu + meclis hakem paneli ile ölçüm.

### Kat-4: Meclis Hakemi (meclis_hakemi.py)

- **Kaynağı**: meclis_hakemi.py → KRITERLER (12 kriter)
- **Yöntem**: Çok modelden cevap alıp 12 kriterde oylama; kazanan seçilir
- **Model**: dots-3 / nemotron / laguna (Vercel env'de veya mock)
- **Tarih**: çalıştırılan session'ın tarihi
- **Çıktı**: hakem_paneli raporu

Yorum: Gerçek kullanıcı değerlendirmesine en yakın ölçüm sistemi.

## Şeffaflık kuralları

1. Her yayınlanan skor: kaynak dosya + yöntem + model + tarih + doğru/toplam + yüzde içerir.
2. "100/100" iddiası için en az bir bağımsız doğrulama (dogrulama.py) sonuç reference olmalıdır.
3. Kendi bankası (tam_zirve) ile bağımsız doğrulama (dogrulama) farklıdır; çoğulatilmamali.
4. Rate-limit: ücretsiz modeller 429 alabilir; bu durumda '--kalan-bekle' ve fallback zinciri devreye girer.
5. Scor kaydedilir (kayit/ dizini, gitignore'lı) ve routing_rapor() ile gerçek veri üzerinden model önerisi üretilir.
