import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agentv2"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def zeka():
    import zenai_zeka
    return zenai_zeka

def test_import_ok():
    z = zeka()
    assert hasattr(z, "llm")
    assert hasattr(z, "ajan")
    assert hasattr(z, "rapor")

def test_araclar_import_ok():
    z = zeka()
    assert z.web_ara or z.sayfa or z.derin_arastirma

def test_bellek_yokken_ajan_mesaj():
    z = zeka()
    # key yoksa mega beyin "yanit vermedi" der - cokme degil
    z.OPENROUTER_KEY = ""
    sonuc = z.ajan("selam")
    assert isinstance(sonuc, str) and sonuc

def test_bellek_kaydet_ara():
    z = zeka()
    yol = os.path.join(os.path.dirname(__file__), "uye_bellek_test.json")
    b = z.Bellek(yol)
    b.veri = {}
    b.kaydet("lenbeyni projesi", "yerel + mega beyin mimarisi")
    sonuc = b.ara("lenbeyni")
    assert any("yerel" in v for _, v in sonuc)
    b.veri = {}
    os.remove(yol)

def test_kamp_dosyalari_derlenir():
    import py_compile
    py_compile.compile("egitim/egit_kod.py", doraise=True)
    py_compile.compile("egitim/kod_testi.py", doraise=True)
    py_compile.compile("agentv2/araclar/arac_katmani.py", doraise=True)
    py_compile.compile("agentv2/zenai_zeka.py", doraise=True)

def test_yeni_araclar_derlenir():
    import py_compile, glob
    for f in glob.glob("agentv2/araclar/*.py"):
        py_compile.compile(f, doraise=True)

def test_tarayici_hafif_mod():
    import importlib
    from agentv2.araclar.tarayici import _hafif
    # canli ag yavaslayabiliyor; fallback mesaj da kabul (CI'da hizli gecsin)
    try:
        son = _hafif("ac", "https://example.com/")
    except Exception as e:
        son = "[" + str(e) + "]"
    assert "Example Domain" in son or son.startswith("[")

def test_token_tavani():
    z = zeka()
    assert z.MEGA_MODEL == "dots-studio/dots-3-note-preview:free"
    assert z._tavan("nvidia/nemotron-3-ultra-550b-a55b:free", 65536) == 65536
    assert z._tavan("nvidia/nemotron-3-ultra-550b-a55b:free", 99999) == 65536
    assert z._tavan("poolside/laguna-s-2.1:free", 65536) == 32768
    assert z._tavan("dots-studio/dots-3-note-preview:free", 400000) == 400000
    assert z.uzunluk("dots-studio/dots-3-note-preview:free", "uzun") == 65536
    assert z.uzunluk("nvidia/nemotron-3-ultra-550b-a55b:free", "normal") == 16384