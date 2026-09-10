# HEDEF — Lennebraha'nın Nihai Amacı

_Kayıt tarihi: 2026-09-07. Kullanıcının net talebi, söylediği gibi._

## Talep (birebir)
"Gerçekten zeki olan — Claude / GPT-6 / Astra seviyesinde — bir ultra-bilgi + kodlama AI'si.
Onu **bir tablette, maksimum ve ücretsiz** kullanabilirim. Uzun zaman sürebilir, sorun değil."

## Gerçek kurgu (pazara denk getiren kısıtlar)
1. Frontier kalitesi = 100B-1T parametre; bir tablet (RAM 4-16GB) en fazla ~8-14B (4-bit) yerel çalıştırır.
   → **Sıfırdan eğitilecek "kendi modelin tablette" = fiziksel imkânsız.**
2. Ama "tablette ücretsiz çalışan gerçekten zeki asistan" **MÜMKÜN**:
   zekâ her zaman aynı cihazda OLMAK zorunda değil; sistem bunu dağıtır.

## Mimari — "LenBeyni" (hedef çözüm)
```
[Tablet/Termux — benim cihazım, ücretsiz]
  1. Yerel beyin ......... Lennebraha-8b / Coder-14B-hybrid (GGUF, offline taban)
  2. Yöneltici (router) .. sorunu sınıflar → zor/soru tipine göre yönlendirir
        ├─ kolay/Türkçe sohbet ....... → yerel (offline, SÜREKLİ)
        ├─ zor kod/mantık/uzun akıl .. → ücretsiz bulut MEGA-beyin (en büyük serbest: DeepSeek-V3 671B / Qwen3-235B-A22B — OpenRouter :free)
        ├─ orta/elektrik ............. → orta bulut (Qwen3-30B / Llama-70B, Groq ücretsiz)
        └─ RAG/bilgi sorgusu ......... → kendi bellek + doküman arkamda
  2b. Dolgu: soru tipine göre model değişir; token limitleri şu üç savunmayla sıfıra yaklaşır:
        (i) yerel beyin ücretsiz/sınırsız, (ii) router sadece zor soruyu gönderir (günde birkaç on çağrı),
        (iii) çoklu sağlayıcı rotasyonu + önbellek + anında yerel düşüş (asla tıkanma).
  3. Bellek + RAG .......... tabletteki notlar/dokümanlar, kalıcı hafıza (retrieve edilir)
  4. Araç döngüsü .......... kod koş + hata gör + düzelt (Termux python, gerçek çalıştırma)
Çıktı: bir dışarı görünüşte "ultra zeki, kod yazan, bilge" asistan; her şey tablette, maliyet 0.
```

## Geliştirme yol haritası
- [x] Yerel konuşma modeli — lennebraha-3b/8b (RG/RAG üslup): tamamlandı
- [ ] Kod modeli — Coder-14B + iki LoRA (türkçe+kod) merge → `lennebraha-coder-hybrid` (devam)
- [ ] Yöneltici — `yoneltici.py`: soru sınıfı + ücretsiz bulut API köprüleri
- [ ] Bellek + RAG — tablet dosya + notlar + retrieve
- [ ] Araç döngüsü — kod çalıştırma/retry (Termux python sandbox)
- [ ] Entegrasyon — tek komutla tablette "LenBeyni"

## Ölçüm/kanıt (jüriye)
Her katman ölçülebilir: yerel offline skoru, yöneltici mutlak doğruluk, bulut-zekâ pas oranı,
RAG cevap zeminleme, kod pass@1/@3. "Gerçekten zeki" = ölçümde gösterilir, iddiada değil.

## Sınır (dürüst)
En zor yenilik gerektiren görevlerde saf frontier'a yetişemez; ama günlük gerçek işlerin
büyük çoğunluğunda anlık fark ayırt edilmez. Amaç budur.