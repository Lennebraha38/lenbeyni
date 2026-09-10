# 7-Gün Kamp: Yapay Zeka Ajanına Giden Yol

Bir haftada, sıfırdan **Gemini API** ile çalışan, konuşan, bağlam hatırlayan ve internette araştırma yapabilen **AI ajanı**na dönüşümcü bir yolculuk. Her gün bir kavram, her gün çalışan kod.

## Gün 1 — İlk Sohbet
`chatbot.py` · Gemini ile ilk konuşma
`deney.py` · sıcaklık parametresi (0.0/0.7/1.5) karşılaştırması

## Gün 2 — Alet Kullanan Model
`arac.py` · fonksiyon çağırma (function calling): saat (Türkiye saati), toplama işlemi

## Gün 3 — Anlam Vektöre Dönüşür
`vektor.py` · metin embedding (384 boyut) + kosinüs benzerliği
`vdb.py` · ChromaDB ile kalıcı vektör deposu

## Gün 4 — RAG: Bilginin Gücü
`parcala.py` · belge bölümleme (chunking) deneyleri
`ornek.txt` · örnek belge
`rag.py` · tam RAG boru hattı: parçala → vektöre çevir → sakla → getir → üret

**Ders:** küçük modelle Türkçe sorgu yanlış getiri yapıyor — embedding dili kritik. Cevaplar bağlam uzunluğuna takılıyor → `thinkingBudget: 128`.

## Gün 5 — Model Seçimi ve İnce Ayar
`karsilastir.py` · model + 3 sıcaklık değeri karşılaştırması
`ft_olustur.py` · Gemini tuning API denemesi (key'de kapalı → 501, kavram öğrenildi)

## Gün 6 — Kendi Kendine Düşünen Ajan
`agent.py` · 4 araçlı + hafızalı ajan (saat, selamlaşma, not al, hatırla)
`agent2.py` · Wikipedia üzerinden bilgi getiriciler
`agent3.py` · DuckDuckGo ile web araması
`agent3_react.py` · **ReAct döngüsü** — her aracı çağrısını görünür yapan, doğrulanmış cevap veren ajan

## Gün 7 — Portfolyo
Bu depo: kavramdan çalışan ürüne bir hafta.

## Çalıştırma
```bash
pip install -r requirements.txt   # google-genai, chromadb, sentence-transformers, ddgs, openai, python-dotenv
echo "GEMINI_API_KEY=..." > .env
python agent3_react.py            # → webde_ara aracını çağırır, kaynak getirir
```

> **Ne öğrenildi:** Hallucination kalıcı değildir — agent'i araca *çağırmaya* zorlayın, aracın izini görün, kaynaktan doğrulanmış cevap isteyin.
