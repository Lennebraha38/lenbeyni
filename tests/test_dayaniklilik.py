import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agentv2"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# ── SSRF/DNS-rebinding korumasi ─────────────────────────────
def test_pinli_hedef_ic_alan_bloklari(monkeypatch):
    from agentv2.guvenlik import pinli_hedef
    assert pinli_hedef("http://127.0.0.1/") is None
    assert pinli_hedef("http://169.254.169.254/latest/meta-data/") is None
    assert pinli_hedef("http://localhost:8080/admin") is None
    assert pinli_hedef("file:///etc/passwd") is None
    assert pinli_hedef("http://user:pass@host/") is None

def test_pinli_hedef_http_ip_sabitlenir(monkeypatch):
    import socket
    from agentv2.guvenlik import pinli_hedef
    # DNS'i yerine taklit et: "uzak-site.com" -> 1.2.3.4 (alani acik)
    monkeypatch.setattr(socket, "getaddrinfo",
        lambda host, port, *a, **k:
            [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.2.3.4", 0))] if host == "uzak-site.com" else [])
    sonuc, host = pinli_hedef("http://uzak-site.com/yol?s=1")
    assert sonuc == "http://1.2.3.4/yol?s=1"
    assert host == "uzak-site.com"
    # DNS'i ic-alana cevrilen host engellenir
    monkeypatch.setattr(socket, "getaddrinfo",
        lambda host, port, *a, **k:
            [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 0))])
    assert pinli_hedef("http://zararli.com/") is None

def test_tarayici_hafif_ssrf_bloklu():
    from agentv2.araclar.tarayici import _hafif
    son = _hafif("ac", "http://127.0.0.1/*")
    assert "GUVENLIK" in son or "Bloklandi" in son

def test_sayfa_redirect_ssrf_onleme(monkeypatch):
    from agentv2.araclar import arac_katmani as ak
    class Yonlendirme:
        status_code = 302
        headers = {"Location": "http://169.254.169.254/latest/meta-data"}
        text, url = "", "http://site.com/"
    class Son:
        status_code = 200
        headers = {}
        text = "<p>selam</p>"
        url = "http://site.com/sayfa"
    def sahte_get(adres, **kw):
        return Yonlendirme() if kw.get("allow_redirects") is False and "latest" not in adres else Son()
    monkeypatch.setattr(ak.requests, "get", sahte_get)
    son = ak.sayfa("http://site.com/")
    assert "GUVENLIK" in son and "redirect" in son

# ── Coklu-saglayici fallback ────────────────────────────────
def test_sira_sor_fallback_sirasi():
    from agentv2.llm_provider import sira_sor
    cevaplar = []
    def ilk():
        cevaplar.append("ilk-429")
        return None
    def ikinci():
        cevaplar.append("ikinci-kota")
        return None
    def ucuncu():
        cevaplar.append("ucuncu-basarili")
        return "yedek cevap"
    sonuc = sira_sor([{"role": "user", "content": "s"}], "m", 100,
                     adimlar=[ilk, ikinci, ucuncu])
    assert sonuc == "yedek cevap"
    assert cevaplar == ["ilk-429", "ikinci-kota", "ucuncu-basarili"]

def test_sira_sor_hepsi_basarisizsa_none():
    from agentv2.llm_provider import sira_sor
    sonuc = sira_sor([{"role": "user", "content": "s"}], "m", 100,
                     adimlar=[lambda *a: None, lambda *a: None])
    assert sonuc is None

def test_sira_sor_istisna_digerine_gecer():
    from agentv2.llm_provider import sira_sor
    def patlayan(*a):
        raise RuntimeError("ag hatasi")
    def kurtaran(*a):
        return "kurtarildi"
    assert sira_sor([{}], "m", 100, adimlar=[patlayan, kurtaran]) == "kurtarildi"

def test_llm_provider_anahtar_gerekli(monkeypatch):
    from agentv2 import llm_provider as lp
    # Anahtar yoksa adim listesi bos gelir (env kirletilmez)
    monkeypatch.setattr(lp, "ANAHTAR_OR", "")
    monkeypatch.setattr(lp, "ANAHTAR_GROQ", "")
    monkeypatch.setattr(lp, "ANAHTAR_GEMINI", "")
    assert lp._probat_sirasi([], "m", 100) == []
    # Yalnizca Groq anahtari varsa tek adim olur
    monkeypatch.setattr(lp, "ANAHTAR_GROQ", "groq-test")
    assert len(lp._probat_sirasi([], "m", 100)) == 1

# ── Docker izolasyonu ────────────────────────────────────────
def test_kod_sandbox_docker_off_subprocesse_duser(monkeypatch):
    from agentv2.araclar import kod_sandbox as ks
    monkeypatch.setattr(ks, "_docker_var", lambda: False)
    sonuc = ks.python_kod("print('sbox-ok')")
    assert "sbox-ok" in sonuc

def test_kod_sandbox_docker_on_kullanir(monkeypatch):
    from agentv2.araclar import kod_sandbox as ks
    monkeypatch.setattr(ks, "_docker_var", lambda: True)
    monkeypatch.setattr(ks, "_docker_calistir",
                        lambda *a, **k: "docker-cikti")
    assert ks.python_kod("print('x')") == "docker-cikti"
    assert ks.bash_kod("echo x") == "docker-cikti"
    assert ks.node_kod("console.log(1)") == "docker-cikti"

def test_kod_sandbox_docker_hataliysa_fallback(monkeypatch):
    from agentv2.araclar import kod_sandbox as ks
    monkeypatch.setattr(ks, "_docker_var", lambda: True)
    monkeypatch.setattr(ks, "_docker_calistir",
                        lambda *a, **k: "[Docker hatasi: imaj yok]")
    sonuc = ks.python_kod("print('fb-ok')")
    assert "fb-ok" in sonuc

def test_docker_komut_saglamlastirma(monkeypatch):
    from agentv2.araclar import kod_sandbox as ks
    giden = []
    class Cikti:
        returncode = 0
        stdout = "calisti"
        stderr = ""
    def sahte_run(*args, **kw):
        giden.append(args[0])
        return Cikti()
    monkeypatch.setattr(ks.subprocess, "run", sahte_run)
    sonuc = ks._docker_calistir("kod", ".py", "test-imaj", ["python3", "-I"])
    docker_cmd = next(c for c in giden if "docker" in c)
    assert "--network" in docker_cmd and "none" in docker_cmd
    assert "--memory" in docker_cmd and "--pids-limit" in docker_cmd and "--rm" in docker_cmd
    assert docker_cmd[docker_cmd.index("test-imaj") + 1:][0] == "python3"
    assert docker_cmd[-1].startswith("/mnt/betik.py")
    assert sonuc == "calisti"

# ── Bellek: SQLite deposu ────────────────────────────────────
def test_bellek_sqlite_kayit_ara_sil(tmp_path):
    from agentv2.bellek_vektor import BellekVec
    db = str(tmp_path / "bellek.db")
    b = BellekVec(yol=db, kullanici="ali")
    b.kaydet("fav_renk", "mavi", etiket="oy")
    assert b.ara("renk neydi")[:1] and b.ara("renk neydi")[0][1] == "mavi"
    assert b.kayit_listesi(etiket="oy")
    # Yeni ornek ayni db'yi okur (kalicilik)
    b2 = BellekVec(yol=db, kullanici="ali")
    assert b2.ara("renk")[0][1] == "mavi"
    assert b2.unut("fav_renk")
    assert BellekVec(yol=db, kullanici="ali").ara("renk") == []

def test_bellek_json_birkes_goc(tmp_path):
    import json, os
    from agentv2.bellek_vektor import BellekVec
    eski = tmp_path / "yeni.json"
    eski.write_text(json.dumps({"ali": {"not": "json kayit goc tukusu"}}, ensure_ascii=False))
    db = str(tmp_path / "yeni.db")
    b = BellekVec(yol=db, kullanici="ali")
    bul = b.ara("json kayit", min_skor=0.0)
    assert any("goc" in v for _, v in bul)

# ── Semantik onbellek ────────────────────────────────────────
def test_onbellek_hit_ve_miss(monkeypatch, tmp_path):
    monkeypatch.setenv("ZENAI_ONBELLEK", str(tmp_path / "ob.db"))
    import importlib
    from agentv2 import onbellek
    onbellek.onbel_kapat()
    importlib.reload(onbellek)
    assert onbellek.onbel_istek("DNA nedir?") is None
    onbellek.onbel_kaydet("Enerji korunumu nedir?", "Kapali sistemde enerji yok olmaz")
    assert onbellek.onbel_istek("Enerji korunumu nedir") == "Kapali sistemde enerji yok olmaz"
    onbellek.onbel_kapat()

def test_onbellek_similarlik_esikleri():
    from agentv2.onbellek import benzerlik
    assert benzerlik("Enerji korunumu nedir?", "Enerji Korunumu nedir?") >= 0.9
    assert benzerlik("Python list nasil yazilir?", "Salata tarifi ver") < 0.4
    assert benzerlik("", "x") == 0.0