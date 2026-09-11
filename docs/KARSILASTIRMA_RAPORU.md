# ZenAI vs Claude Fable 5.1 / ChatGPT Astra 6 / Gemini 3.1 Pro

## Neden ZenAI Farklı Strateji İzliyor?

| | Rakipler | ZenAI |
|---|---|---|
| **Strateji** | Tek dev model, kendi web hizmeti | **Sistem zekası** + en ucuz en iyi modeller |
| **Token limiti** | Sabit (concise mod düşük token) | **KAPSAM ayarlanabilir** (1200/2500/5000 kelime) |
| **Model seçimi** | Hepsi aynı model | **Konu bazlı routing** (10 model haritası) |
| **Hata kontrolü** | Yok | **Self-correction** (kod sandbox, matematik doğrulama) |
| **Düşünme** | Gizli | **Açık CoT** + 10 konu yöntemi |
| **Oylama** | Tek cevap | **Çoğunluk oyu** + AI Meclisi (3 model) |
| **Kriter** | İnsan değerlendirmesi | **12 kriterli meclis hakemi panosu** |

## Rakip Benchmarklar (Web Araştırma Verisi)

| Benchmark | Claude Fable 5 | GPT-6 Astra | Gemini 3.1 Pro |
|---|---|---|---|
| ECÍ | 162.48 (#1/346) | — | — |
| MMLU Pro | 91.5% | — | 90.99% |
| GPQA Diamond | 93.2% | ~94.1% | 94.3% |
| AIME 2026 | %99.9 | — | — |
| AIA-Codex | — | 67 | — |
| SWE-Bench | — | — | 80.6% |
| ARC-AGI-2 | — | — | 77.1% |
| Intelligence Index | — | 61 | — |

**Anahtar:** Rakipler GPQA/MMLU'da %90+ alıyor. Ama bu testler **bilgi + mantık** ölçer; üretkenlik (yaratıcı hikaye, Türkçe dilbilgisi, pratil) ölçmez. ZenAI 50 soruda konu çeşitliliğiyle gerçek kullanıcı deneyimini hedefliyor.

## ZenAI Gerçek Test Sonuçları (Dots-3)

**35 soru** — 67.2/100 (rate-limit kayıpları hariç). Konu performansı:

| Konu | Puan | Not |
|---|---|---|
| Bilim | 74 | Yüksek |
| Mantık | 82 | En güçlü |
| Tarih | 70 | Ortalama+ |
| Yaratıcı | 71 | Ortalama+ |
| Kültür | 80 | Yüksek |
| Matematik | 64 | Ortalama |
| Dil | 66 | Ortalama |
| Kod | 44 | ZAYIF |
| Pratik/Teknoloji | 0 | rate-limit kurbanı |

**Zayıf noktalar:** Kod 44 (düşük), matematik 64 (ort). → Bu yüzden **routing + self-correction + akıl motoru** eklendi.

## Tahmin: Yeni Katmanlarla Sonuç

| Katman | Beklenen Etki |
|---|---|
| Akıl Motoru (CoT + kelime hedefi) | +5-10 puan |
| Model Routing (kod→north-mini, mat→nemotron) | Kod/mat toparlanması +5 |
| Self-Correction (kod sandbox) | Kod hataları düzelir |
| Çoğunluk Oyu (3x) | +5-15 puan |
| **Toplam Beklenen** | 67 → **75-85** |

## Nasıl Çalışır?

```
Soru → 10 konu sınıflandırma
     → Routing: kod→north-mini / mat→nemotron / diğer→dots-3
     → Akıl Motoru: CoT + "5000 kelimeye kadar detaylandır"
     → Self-correction (kod sandbox'ta çalıştır)
     → (ops) Çoğunluk oyu: 2x daha sor, en sık cevabı seç
     → 12 kriterli meclis hakemi skorlar ve kazananı seçer
```

## Test Durumu

- [x] 50 soru hazır (10 konu × 5)
- [x] Skorer (kod sandbox + matematik + dil metrikleri)
- [x] Akıl Motoru (CoT sistem promptu + hedef kelime)
- [x] Routing (konu→model haritası)
- [x] Self-correction (kod/matematik doğrulama)
- [x] Çoğunluk oyu (Counter tabanlı)
- [x] Döngü testi (5 tur ölçüm)
- [x] Meclis hakemi (12 kriter)
- [x] Tam zirve testi (tek komut, rate-limit aware)
- [ ] **Canlı 50 soru testi** ← rate limit açılınca otomatik çalışacak
- [ ] Skor 75+ doğrulanması

## Karar (Hangi Katman İşe Yaradı?)

Döngü testi (5 tur) canlıda hangi katmanın gerçekten puan artırdığını gösterecek:
1. Baseline (doğrudan cevap) → puan referansı
2. CoT (akıl motoru) → düşünce tarzının etkisi
3. Self-correction → hata yakalama etkisi
4. CoT + SC → kombinasyon
5. Meclis oylama → en iyi cevap seçim etkisi

Hangisi kazandı → o katman **AKTİF** kalır, kazanamayan → kaldırılır.