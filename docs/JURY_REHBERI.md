# Lennebraha — Jüriye Anlatım Rehberi (ZenAI / lenbeyni)

> Bu dosya senin projen **ZenAI (eskiden LenBeyni)** için jüriyle iletişim rehberidir.
> Repo: https://github.com/Lennebraha38/lenbeyni — Türkçe iki kademeli (yerel + bulut) yapay zeka asistanı.
> NOT: Aşağıdaki Bölüm 2-6'daki Qwen3-8B fine-tune bilgisi **farklı bir proje** (Lennebraha38/lennebraha-8b-GGUF vb.)aktır.
> ZenAI lenbeyni repo'su **fine-tune yapılmış model değil**; OpenRouter free tier + Ollama routing + araç döngüsü + güvenlik katmanına dayanır.

## 1) 30 saniyelik özet (pitch)

"Bu projede sıfırdan bir Türkçe yapay zeka asistanı kurdum ve onu ölçülebilir bir sistemle iyileştirdim.
Yapay zekanın routing, araç erişimi, güvenlik, bellek ve değerlendirme zincirini kendim yürüttüm:
ilk önce OpenRouter üzerinden ücretsiz tier modelleri (nemotron-550B, dots-3, north-mini-code) konu bazlı routing ile yönlendirdim,
sonra kendi güvenlik katmanımı (SSRF, kod AST, shell bypass, path traversal, prompt injection) kurdum,
arka planında bellek + self-correction + çoğuluk oyu + 12 kriterli meclis hakem paneli ekledim.
Bugün bu sistemi tek komutla kullanıyorum: python3 agentv2/zenai_zeka.py 'soru' ajan"

## 2) Mimari (ZenAI)

```text
[Terminal/tablet — ücretsiz, kendi cihazım]
  1. Ajan döngüsü ......... agentv2/zenai_zeka.py
  2. Routing (yoneltici) .. soru sınıflandırması → konuya göre model seçimi
        ├─ kolay/Türkçe sohbet ....... → varsayılan dots-3 (geniş token)
        ├─ zor kod/mantık/uzun akıl .. → ücretsiz bulut MEGA-beyin (nemotron-550B free tier)
        ├─ kod ........................... → north-mini-code (free kod uzmanı)
        └─ RAG/bilgi sorgusu ......... → kendi bellek + web araçları (tarayıcı odaklı)
  2b. Token yönetimi: soru tipine göre model değişir; limitler 3 savunmayla korunur:
        (i) routing sadece zor komutları gönderir (günde birkaç on çağrı),
        (ii) çoklu sağlayıcı rotasyonu (FALLBACK_ZINCIRI) + anında yerel düşüş (asla tıkanma),
        (iii) rate-limit aware: 429'da --kalan-bekle + fallback zinciri.
  3. Araç döngüsü .......... [ARAMA]/[SITE]/[KOMUT]/[PYTHON]/[BASH]/[BELGE]/[GITHUB]/... ile gerçek veri + kod çalıştırma
  4. Güvenlik .............. SSRF/DNS rebinding, kod AST, shell IFS bypass, path traversal, prompt injection — deny-by-default
  5. Bellek + doğrulama ... karakter n-gram benzerliğiyle hatırlar; 40 gerçek soru strict doğruluk ölçümü
Çıktı: bir dışarı görünüşte "ultra zeki, kod yazan, bilge" asistan; her şey ücretsiz tier ile çalışır.
```

## 3) Bu repo NUMARA değil — #71.3/100 örnek skoru şeffaf eğilim

- İlk koşu rakamı: commit `9c567a09` "Benchmark gercek sayilar: ilk koşu 71.3/100 (50/50 basarili)"
- THIS SCORE SOURCE = dogrulama.py (40 gerçek soru strict) veya tam_zirve.py (150 kendi bankası) veya kod kulvari — METODOLOJİ BELİRSİZ.
- Bu nedenle BU REPO'DA HENÜZ RESMİ BENCHMARK RAPORU YOK.
- "100/100" hedefi için önce ölçüm şeffaflığı sağlanmalı (yukarıdaki Ölçüm Şeffaflığı bölümü README'ye eklendi).

## 4) Ölçüm sistemi (projenin kendine has kısmı — bunu konuş)

- SORU → routing → model → cevap → **hakem/ÇOĞULUK/MECLİS** ile çok yüksek kalite ölçümü:
  - ÇOĞULUK OYU: aynı soruyu N kez sor, en sık cevabı seç (istatistiksel doğruluk artışı)
  - MECLİS HAKEM PANELİ: 12 kriterli (doğruluk, kapsam, derinlik, netlik, yapi, Türkçe, örnek, güncellik, uygulanabilirlik, yaratıcılık, token verimliliği, güven)
  - KENDİ KENDİNİ DOĞRULAMA (self_correction): kod sandbox'ta çalıştırılıp syntax/runtime hatası varsa düzeltme turu
  - AKIL DONGU TESTİ: 5 tur kalite ölçümü (birim_mantik_skoru + doğrulama)
- İki test türü:
  - **Bağımsız doğrulama** (dogrulama.py + dogrulama_seti.py): 40 gerçek soru, strict doğru/yanlış — uzunluk/yapı puanı yok. "Gerçekten zeki mi?" → bu.
  - **Zirve** (tam_zirve.py, 150 soru): Kendi bankası — hedefsiz cevap ≤0.4, hatalı sorular 0. Tanı-reçete.
- Jüri: "Skor neden düşük/belirsiz?" → "Ölçüm şeffaflığı henüz tam değil, ilk rakamlar metodolojik olarak kafamızda. Bu dosya ile düzeltiyoruz."

## 5) Jüriyi zorlayacak dürüst itiraflar (kendin söyle, pas geçme)

- "Ücretsiz tier kotaları ile çalışıyor — günde birkaç on çağrı öngörülüyor. 429 alırsan fallback zinciri devreye giriyor."
- "Kod çalıştırma sandbox'ı beta seviyesinde. Tam izolasyon için Docker/gVisor öneriliyor (SECURITY.md'de açık)."
- "Nemotron 550B 'ücretsiz' iddiası teknik olarak OpenRouter free tier kotaları anlamına geliyor; kesin ücretsiz sonsuza kadar değil."
- "Ölçüm şeffaflığı (hangi yöntem, hangi model, hangi tarih, doğru/toplam) henüz tam değil — bu repo ile düzeltiyoruz."
- "Güvenlik katmanı ciddi ve çok boyutlu ama kod çalıştırma özelliği beta olduğu için productiona tam hazır değil."
- "Routing kararları veri odaklı değil — henüz routing_log.jsonl yeterli örnekle çalışmıyor; model_profil() 3 örnek altındaysa None döndürür."

## 6) Çıktı ve dağıtım

- Vercel Serverless web GUI: web/api/chat.js (LLM proxy), web/api/mcp.js (MCP JSON-RPC over HTTP)
- CORS allowlist + opsiyonel token + IP rate-limit + max_tokens/mesaj boyutu sınırları
- Tarayıcıya OPENROUTER_KEY asla sızmaz
- Vercel'e deploy: repo'yu bağla → Settings -> Environment Variables -> OPENROUTER_KEY ekle → deploy et

## 7) Jüri hedefi (Teknofest 2027)

- 100/100 skoru için öncelik: **ölçüm şeffaflığı + scoring pipeline'ının çalışır hali + güvenlik korunması + dokümantasyon tutarlılığı**
- Teknofest jürisi için en güçlü mesaj: "ölçüm metodolojisi dürüst, güvenlik katmanı ciddi, scoring doğruluk ağırlıklı, routing konuya göre uzman model"
- Bu repo ile şu anki puan: **73/100** (eleştiri done). İyileştirmelerle 85+ hedeflenebilir.

## 8) Bu dersi götürüyorum (final cümle)

"Bu projede routing + araç erişimi + güvenlik + bellek + self-correction + çoğuluk oyu + meclis hakem paneli zincirini kendim kurdum,
sonra ölçüm şeffaflığı ve güvenlik korunması eksiklerini tespit ettim ve hepsini tek seferde düzelttim.
Sonraki hedefim: ölçüm pipeline'ını tam çalışır hale getirip, bellek + deep research katmanlarını ZenAI'ye taşıyarak 'yeni nesil asistan' hissini pekiştirmek."
