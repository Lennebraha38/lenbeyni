import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agentv2"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# ── Akil Motoru ─────────────────────────────────────────────
def test_akil_motoru_konu_yontemleri():
    from agentv2.akil_motoru import KONU_YONTEM
    assert "matematik" in KONU_YONTEM
    assert "mantik" in KONU_YONTEM
    assert "kod" in KONU_YONTEM
    # hepsi Turkce ipucu içeriyor
    for konu, y in KONU_YONTEM.items():
        assert len(y) > 30

def test_akil_motoru_sistem_promptu():
    from agentv2.akil_motoru import sistem_promptu
    s = sistem_promptu("matematik", "uzun")
    assert "5000" in s  # kapsam hedefi
    assert "ADIM ADIM" in s  # CoT talimati
    assert ("Turkce" in s) or ("Türkçe" in s) or ("TÜRKÇE" in s)
    s_kisa = sistem_promptu(None, "normal")
    assert "2500" in s_kisa

def test_akil_motoru_mantik_skoru():
    from agentv2.akil_motoru import birim_mantik_skoru, KAPSAM
    # 4+ madde + 300+ kelime + sonuc kelimesi -> yuksek
    metin = "- Adim 1: parcala\n- Adim 2: coz\n- Adim 3: kontrol\n- Adim 4: bitir\nSonuc: dogru\n" + "detay "*150
    assert birim_mantik_skoru(metin) >= 0.4
    # Kisa cevap dusuk skor
    assert birim_mantik_skoru("kisa cevap") < 0.4
    # Kapsam daneleri
    assert KAPSAM["uzun"] >= KAPSAM["normal"] >= KAPSAM["kisa"]

# ── Model Routing ───────────────────────────────────────────
def test_model_routing_konular():
    from agentv2.model_routing import model_sec, KONU_MODELLERI
    # 10 konu tanimli olmali
    assert len(KONU_MODELLERI) == 10
    # Kod modeli free-tier kod uzmani olmali (deepseek 402 veriyor)
    kod_model, kod_max = model_sec("kod")
    assert "free" in kod_model
    assert kod_max >= 16384
    # Matematik modeli 550B olmali
    mat_model, mat_max = model_sec("matematik")
    assert "nemotron" in mat_model
    assert mat_max >= 32768
    # CoT token butceleri rakipten cok (Claude ~128K cikti -> biz hedef 2-4x)
    for konu, (_m, mt, _a) in KONU_MODELLERI.items():
        assert mt >= 16000, f"{konu} token butcesi cok dusuk: {mt}"

def test_model_routing_bilinmeyen():
    from agentv2.model_routing import model_sec
    m, mt = model_sec("bilinmeyen_konu")
    assert "dots" in m
    assert mt > 0

# ── Self-Correction ─────────────────────────────────────────
def test_kod_dogrula_basarili():
    from agentv2.self_correction import kod_dogrula
    ok, mesaj = kod_dogrula("print(2+2)")
    assert ok is True
    assert "4" in mesaj

def test_kod_dogrula_syntax_hatasi():
    from agentv2.self_correction import kod_dogrula
    ok, mesaj = kod_dogrula("def f(:\n print")
    assert ok is False
    assert "Syntax" in mesaj or "hatasi" in mesaj

def test_kod_dogrula_runtime_hatasi():
    from agentv2.self_correction import kod_dogrula
    ok, mesaj = kod_dogrula("x = 1/0")
    assert ok is False
    assert "Runtime" in mesaj

def test_kod_dogrula_markdown():
    from agentv2.self_correction import kod_dogrula
    markdown = "Aciklamasi:\n```python\nimport time\nprint('ok')\n```"
    ok, mesaj = kod_dogrula(markdown)
    assert ok is True

def test_self_correction_kod_duzeltir():
    from agentv2.self_correction import self_correction
    # once hatali ver, duzeltme turunda dogru kodu dondur
    def sahte_llm(mesajlar):
        return "def f():\n    return 42\n```python\ndef f():\n    return 42\n```"
    sonuc, tur, not_ = self_correction(
        "fonksiyon yaz", "def f(:\n   đçkıO", "kod",
        sahte_llm, max_tur=1)
    assert tur >= 1 or "duzelt" in not_

def test_self_correction_kod_zaten_dogru():
    from agentv2.self_correction import self_correction
    def sahte_llm(mesajlar):
        return None  # duzeltme gerekmemeli
    sonuc, tur, not_ = self_correction(
        "test", "```python\nprint(1)\n```", "kod", sahte_llm)
    assert tur == 0
    assert "dogrulandi" in not_

def test_self_correction_genel_kisa_cevap():
    from agentv2.self_correction import self_correction
    def sahte_llm(mesajlar):
        return "uzun detayli cevap " * 20
    sonuc, tur, not_ = self_correction(
        "kisa soru", "kisa", "bilim", sahte_llm, max_tur=1)
    assert len(sonuc.split()) > 15

# ── Otomatik Skorer ─────────────────────────────────────────
def test_skorer_kod_puanlar():
    from agentv2.otomatik_skorer import puanla
    sonuclar = [
        {"no": 1, "konu": "kod", "cikti": "def f():\n    return 1", "kelime": 4},
        {"no": 2, "konu": "kod", "cikti": "def hatalı(:\n   print", "kelime": 2},
    ]
    rapor = puanla(sonuclar)
    assert rapor["basarili_soru"] == 2
    # birinci yuksek, ikinci dusuk
    assert rapor["sonuclar"][0]["puan"] > rapor["sonuclar"][1]["puan"]

def test_skorer_hatali_atlanir():
    from agentv2.otomatik_skorer import puanla
    sonuclar = [
        {"no": 1, "konu": "kod", "cikti": "[HTTP 429: rate", "kelime": 0},
        {"no": 2, "konu": "kod", "cikti": "print(1)", "kelime": 1},
    ]
    rapor = puanla(sonuclar)
    assert rapor["hatali_soru"] == 1
    assert rapor["basarili_soru"] == 1

def test_skorer_matematik():
    from agentv2.otomatik_skorer import puanla
    sonuclar = [
        {"no": 6, "konu": "matematik", "cikti": "- 7*3=21\n- 8/2=4\n- 2+21=23\n- 23-4=19\nSonuc: **19**", "kelime": 10},
    ]
    rapor = puanla(sonuclar)
    assert rapor["sonuclar"][0]["puan"] >= 0.5

def test_skorer_beklenen_matematik():
    from agentv2.otomatik_skorer import puanla
    soru = "2+7*3-8/2 isleminin sonucu kactir? Adim adim goster."
    dogru = [{"no": 1, "konu": "matematik", "soru": soru,
              "cikti": "7*3=21\n8/2=4\n2+21=23\n23-4=19\nSonuc: 19", "kelime": 8}]
    yanlis = [{"no": 1, "konu": "matematik", "soru": soru,
               "cikti": "7*3=21\nSonuc: 41", "kelime": 4}]
    assert puanla(dogru)["sonuclar"][0]["puan"] == 1.0
    assert puanla(yanlis)["sonuclar"][0]["puan"] <= 0.6

def test_skorer_beklenen_mantik():
    from agentv2.otomatik_skorer import puanla
    soru = "Eger bugun carsamba ise yarin gunlerden ne?"
    yerinde = [{"no": 1, "konu": "mantik", "soru": soru,
                "cikti": "Yarin persembe. Günler: Çarşamba -> Perşembe.", "kelime": 8}]
    belirsiz = [{"no": 1, "konu": "mantik", "soru": soru,
                 "cikti": "Gün sıralamasına bakarız, haftanın dördüncü günü.", "kelime": 8}]
    # dogru kavram gorunen cevap, gormeyenden yuksek puan alir
    assert puanla(yerinde)["sonuclar"][0]["puan"] > puanla(belirsiz)["sonuclar"][0]["puan"]

# ── Cogunluk Oyu ────────────────────────────────────────────
def test_cogunluk_ozet_cevir():
    from agentv2.cogunluk_oyu import cevap_ozet
    assert cevap_ozet("cevap 42 burada 7 de var") == "sayi:42|7"
    assert cevap_ozet("Evet, bu dogru") == "karar:evet"

def test_cogunluk_ata():
    from agentv2.cogunluk_oyu import cogunluk
    import agentv2.cogunluk_oyu as co
    co.llm = lambda msg, **kw: "Evet kesinlikle dogru"
    co.MEGA_MODEL = "sahte"
    sonuc = cogunluk("test sorusu", tekrar=3)
    assert sonuc["guven"] >= 0.5
    assert "Evet" in sonuc["kazanan"]

# ── Akil Dongu Testi ────────────────────────────────────────
def test_dongu_testi_mock():
    from agentv2.akil_dongu_test import dongu_testi
    sonuclar, soru = dongu_testi("test sorusu")
    assert len(sonuclar) == 5  # 5 tur
    assert all("puan" in s for s in sonuclar)
    # Kombinasyon en dusukten yuksek olmali (mock veride esit veya yuksek)
    baseline = sonuclar[0]["puan"]
    kombinasyon = sonuclar[3]["puan"]
    assert kombinasyon >= baseline

# ── Genisletilmis Meclis Hakemi ─────────────────────────────
def test_meclis_hakemi_kriter_sayisi():
    from agentv2.meclis_hakemi import KRITERLER, kriter_puanla, hakem_paneli
    assert len(KRITERLER) == 12  # tam 12 kriter

def test_meclis_hakemi_puanlama():
    from agentv2.meclis_hakemi import kriter_puanla
    # Turkce icerik: turkce kriteri yuksek olmali
    p = kriter_puanla("turkce", "DNA yapisi: adenin, timin, guanin ve sitozin. Bu dört baz çiftlesir.")
    assert p >= 0.4

def test_meclis_hakemi_paneli():
    from agentv2.meclis_hakemi import hakem_paneli
    cevaplar = [
        ("model-a", "Detayli Turkce cevap: DNA iki sarmaldan olusur. Adenin-timin, guanin-sitozin eslesir. Ornek: Insan genome'su 3 milyar baz cifti icerir. Bu bilgiyi guncel arastirmalardan dogruladim."),
        ("model-b", "Kisa cevap. DNA vucudda bulunur."),
    ]
    rapor = hakem_paneli(cevaplar, "DNA'nin yapisini anlat")
    assert rapor["kazanan"] == "model-a"
    assert len(rapor["siralama"]) == 2
    assert rapor["kazanan_skor"] > 0.4

# ── Tam Zirve Testi ─────────────────────────────────────────
def test_tam_zirve_sorular():
    from agentv2 import tam_zirve
    assert len(tam_zirve.SORULAR) == 150
    # Tum sorular (konu, soru, zorluk) uclusu
    assert all(len(s) == 3 for s in tam_zirve.SORULAR)
    assert all(s[2] in ("kolay", "orta", "zor") for s in tam_zirve.SORULAR)
    konular = {k for k, _, _ in tam_zirve.SORULAR}
    assert konular == {"kod","matematik","dil","mantik","bilim","tarih","yaratici","kultur","pratik","teknoloji"}
    for z in ("kolay", "orta", "zor"):
        assert any(s[2] == z for s in tam_zirve.SORULAR), f"{z} soru yok"

def test_tam_zirve_filtreleri():
    from agentv2.tam_zirve import sorulari_sec
    kodsiz = sorulari_sec(sayi=0, kategori="kod", zorluk=None)
    assert kodsiz and all(s[0] == "kod" for s in kodsiz)
    zorlar = sorulari_sec(sayi=0, kategori=None, zorluk="zor")
    assert zorlar and all(s[2] == "zor" for s in zorlar)
    # Inis secme: cok secilirse sayi kadar
    az = sorulari_sec(sayi=5, kategori="kod")
    assert len(az) == 5

def test_tam_zirve_skor_modulu():
    from agentv2.tam_zirve import tek_soru_test, api_iste
    # fonksiyonlar mevcut ve callable
    assert callable(tek_soru_test) and callable(api_iste)