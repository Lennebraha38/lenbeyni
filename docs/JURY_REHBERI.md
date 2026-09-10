# Lennebraha — Jüriye Anlatım Rehberi

> Bu dosya senin projen. Jüri sorarsa buradan konuş. Her teknik terimin yanında
> "kısa açıklama" ve "jüri şöyle sorarsa..." var.

## 1) 30 saniyelik özet (pitch)

"Bu projede sıfırdan bir Türkçe yapay zeka asistanı eğittim ve onu ölçülebilir
bir sistemle iyileştirdim. Yapay zekanın veri toplama, eğitim, kantileme, dağıtım
ve değerlendirme zincirinin tamamını kendim yürüttüm: önce 376 elle yazılmış
Türkçe soru-cevap örneğiyle açık kaynaklı 8B parametreli Qwen3 modelini adapter
ile ince ayar yaptım, sonra modeli 4-bit GGUF formatına çevirip yerel bilgisayarımda
(Ollama) çalıştırılabilir hale getirdim ve Hugging Face'te yayınladım. Bugün o modeli
geliştirmek için 2000+ örneklik otomatik veri üretim hattı (distillation) kuruyorum."

## 2) Akış haritası (juride kroki için)

```
Türkçe soru-cevap verisi (elle 376 + gemini damıtması 2000+)
        │
        ▼
Qwen3-8B tabanı + QLoRA adapter eğitimi (Unsloth, Kaggle T4×2)
        │
        ▼
Adapter → modele merge (BF16) → GGUF Q4_K_M kantileme
        │
        ▼
Hugging Face'e yükleme → Ollama ile yerel çalıştırma
        │
        ▼
Hakemli değerlendirme (grounding / relevant / kaynak) → iyileştirme döngüsü
```

## 3) Veri

- `veri_seti2.json`: 376 örnek, kendi yazdığım Türkçe Q/A'lar.
  Format: `messages = [{"role":"user", ...}, {"role":"assistant", ...}]` (modern sohbet formatı).
- Kategoriler: rag, düşünme, araç, sohbet, yazı.
- `veri_uret.py`: **distillation** — büyük/ücretli bir modelden (Gemini ücretsiz kotası)
  binlerce kaliteli örnek üretip kendi modelime eğitim verisi yapıyorum.
  Jüri: "Neden elle değil?" → "El yazım günde 100 örnek üretir; damıtma saatte 2000.
  Kaliteyi büyük modelden, çeşitliliği kategori kontrolünden alıyorum; ayrıca aynı
  başlık asla çift girmez (dedup)."

## 4) Yöntem terimleri (sen bunları söyleyebilmelisin)

| Terim | Kısa açıklama senin ağzından |
|---|---|
| **QLoRA** | Quantized Low-Rank Adaptation: modelin ağırlıklarının %99'unu 4-bit'e sıkıştırıp DONDURUYORUZ, sadece küçük "adapter" (düşük rank) matrislerini öğretiyoruz. Adapter küçük olduğu için tek GPU'ya sığıyor. |
| **LoRA r=16** | Adapter'ın rank'ı. r küçük = daha az parametre (hızlı, hafif), ama öğrenme gücü düşük. r=16 makul orta. |
| **merge** | Eğitim bitti, adapter'a ağırlıkları tabana geri ekliyoruz → yeni tam model. |
| **GGUF** | llama.cpp ekosisteminin dosya formatı; modeli CPU/yerelde verimli çalıştırır. |
| **Q4_K_M** | 4-bit kantileme adı (K=ölçek grupları, M=orta boyut). Dosya 5.03 GB → RAM'e sığıyor. |
| **Unsloth** | Açık kaynak eğitim kütüphanesi; QLoRA'yı ~2x hızlı ve 60-70% az RAM ile çalıştırır. |
| **enable_thinking** | Qwen3'ün R1 tarzı "önce iç düşün, sonra cevap ver" modunu açmak için. Yeni nesil hissin anahtarı. |

Jüri: "LoRA neyi öğreniyor, tabanı değiştirmiyor mu?" →
"Taban model genel Türkçe/İngilizce biliyor ama bizim konuya (RAG, arama, ajanlar) ve
üsluba ayarlı değil. Adapter bu uzmanlığı öğreniyor. Biliyor'ü baska veri/kimlik
eklemiyor; o yüzden sisteme RAG ile bilgi akışı ekliyorum — model ezberlemez, erişir."

## 5) Eğitim ölçüleri (sayılarına bak, jüri bunları böler)

- 60 adım (step), ~6.5 dakika, Kaggle 2×T4.
- **Loss: 4.54 → 1.07** final (eval: 1.26).
- Jüri: "Loss ne demek?" → "Modelin tahmin hatasının ölçüsü. Düşünce model daha doğru
  sözcük seçiyor. 1.07'de üretim akıcı, Türkçe doğru dili kullanıyor."
- Jüri: "Overfit mi?" → "Eğitim loss'u (1.07) ile doğrulama loss'u (1.26) yakın —
  ikisi de makul; belirti yok. Az adım çalıştım ki small veriyle ezber yapması."
- Jüri: "Neden tam ince ayar değil de LoRA?" → "Tam ince ayar bütün 8B ağırlıklarını
  günceller; 16GB RAM'li ücretsiz GPU'ya sığmaz, aşırı maliyetli ve aşırı eğilimli.
  LoRA ile aynı kaliteyi çok daha az kaynakla alıyorum."

## 6) Ölçüm sistemi (projenin kendine has kısmı — bunu konuş)

- SORU → RAG ile kaynak bilgi + model cevap → **hakem model** 3 boyutta 1-5 puan:
  - **grounding**: cevap kaynak belgeyle çelişiyor mu? (sonu)
  - **relevant**: soruya geri cevap mı?
  - **kaynak**: verilen belgeyi geri kullanıyor mu?
- İki test türü:
  - **in-domain** (eğitim konuları): 3B **4.73/5** → bunu "şişkin" sayarım, konu sızıntısı var.
  - **soğuk test** (eğitim dışı 8 zor soru, kaynak dokümanda bile yok): **3.38/5** →
    skor düşük çünkü retrieval modeli beslemedi; bu "model kötü" değil "ölçüm koşulu zor" demek.
- Jüri: "Skor neden düşük?" → "İki neden: sorular eğitim verisinde de yok, üstüne hakem
  model zayıf — yani ölçümün kendisinin tavanı düşük. Bu yüzden hakemi güçlendirmek ve
  veriyi büyütmek üzerine çalışıyorum."

## 7) Çıktı ve dağıtım

- Eğitim dosyası → merge → GGUF `qwen3-8b.Q4_K_M.gguf` (5.03 GB).
- Hugging Face:
  - `Lennebraha38/lennebraha-3b` (BF16, Qwen2.5-3B tabanlı, 299 indirme)
  - `Lennebraha38/lennebraha-3b-GGUF` (Q8_0, 3.29 GB)
  - `Lennebraha38/lennebraha-8b-GGUF` (Q4_K_M, canlı)
- Ollama local çalıştırma, system prompt ile kimlik görünümü.

## 8) Jüriyi zorlayacak dürüst itiraflar (kendin söyle, pas geçme)

- "Model bilgi eklemez; tarz/bağlam öğrenir." → Bilgiyi RAG + dosya erişimi sağlar.
- "Bellek yok: sohbetten öğrendiğini kaydetmez." → Şu an çözülüyor (not defteri + retrieval).
- "İnternet araması yapamaz." → Bu, araç döngüsü katmanıyla çözülür; modelin değil sistemin işi.
- "Kimlik sorusu eğitilmedi; system prompt ile veriliyor." → Doğru tasarım böyle; veride kimlik yok.

## 9) Bu dersi götürüyorum (final cümle)

"Bu projede veriden dağıtıma kadar üretim zincirini kendim kurdum, modeller eğittim,
Eldeki ölçümle gerçek skoru hakemden ayırt etmeyi öğrendim ve şimdi veriyi büyütüp
düşünme + araç + bellek katmanlarını ekliyorum. Sonraki hedefim: 8B modeli bu üç
katmanla 'yeni nesil asistan' hissine taşımak."