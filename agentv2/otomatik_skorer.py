"""Otomatik Skorer — test cevaplarini makineyle puanlar.
Kod: sandbox'da calistir, matematik: beklenen sonucla karsilastir, dil: yapiskan metrik.
Kullanim: python3 otomatik_skorer.py karsilastirma.json
"""
import os, sys, json, re, ast, subprocess, tempfile, math

# ── Sabit beklenen sonuclar ──────────────────────────────────────────
MATEMATIK_BEKLENEN = {
    6:  "19",    # 2+7*3-8/2: operator onceligi: 7*3=21, 8/2=4, 2+21=23, 23-4=19
    7:  "360",   # dortgen ic aci toplami
    10: "1/36",  # 6 yuzlu zar 2 kez 6: 1/36
}
# Asagidaki soru indeksleri 1-bazlidir (JSON'daki 'no' alanina eslesir)

def kod_ayarla(kod_metni):
    """Markdown/karma metinden Python kod blogunu cikar."""
    # ```python ... ``` blogunu bul
    blok = re.search(r'```(?:python)?\s*\n(.*?)```', kod_metni, re.DOTALL)
    if blok:
        return blok.group(1).strip()
    # Tekli ``` ... ``` (yakalama)
    blok = re.search(r'```\s*\n(.*?)```', kod_metni, re.DOTALL)
    if blok:
        return blok.group(1).strip()
    return kod_metni

def puan_kod(kod_metni):
    """Kod calistirilabilir mi? Syntax hatasi var mi?"""
    temiz = kod_ayarla(kod_metni)
    try:
        ast.parse(temiz)
    except SyntaxError as e:
        return 0.3, f"Syntax hatasi: {e}"
    # Calistirarak runtime hatasi var mi bak
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(temiz)
        yol = f.name
    try:
        r = subprocess.run(["python3", "-u", yol], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return 1.0, "Calisti"
        return 0.6, f"Runtime hatasi: {r.stderr[:120]}"
    except subprocess.TimeoutExpired:
        return 0.5, "Timeout (sonsuz dongu?)"
    except Exception as e:
        return 0.4, str(e)
    finally:
        os.unlink(yol)

# ── Soru-bazlı beklenti erişimi ────────────────────────────────
_HEDEFLER = None
def _hedef_get(soru):
    """Sorunun beklenen yanıt tablosundaki kaydini dondurur (yoksa None)."""
    global _HEDEFLER
    if _HEDEFLER is None:
        _HEDEFLER = {}
        try:
            from soru_bankasi import HEDEFLER
            _HEDEFLER = HEDEFLER
        except ImportError:
            try:
                from agentv2.soru_bankasi import HEDEFLER
                _HEDEFLER = HEDEFLER
            except ImportError:
                _HEDEFLER = {}
    return _HEDEFLER.get(soru or "")

def _anahtar_esle(cikti, kelimeler):
    """Anahtar kavramlardan en az biri metinde var mi? (LaTeX/kok formlari normalizeli)"""
    kucuk = (cikti or "").lower()
    # sqrt(3), \sqrt{3}, \\sqrt{3}, kök 3 -> √3 kanonik formuna indir
    kucuk = re.sub(r"\\*sqrt\s*\{?\s*([0-9a-zçğıöşü]+)\}?", r"√\1", kucuk)
    kucuk = re.sub(r"k[oö]k\s*([0-9)] )", r"√\1", kucuk)
    return [k for k in kelimeler if k.lower() in kucuk]

def _sayi_esle(cikti, bek_str):
    """Beklenen deger (tam sayi/kesir/ondalik) metinde var mi?"""
    if not bek_str:
        return False
    temiz = re.sub(r"[{}()\\\[\]_]", " ", cikti).replace(" ", "")
    if bek_str in temiz:
        return True
    try:
        if "/" in bek_str and re.fullmatch(r"[0-9]+/[0-9]+", bek_str):
            p, b = bek_str.split("/")
            bek = float(p) / float(b)
        else:
            bek = float(bek_str.replace(",", "."))
        for s in set(re.findall(r"[0-9]+[.,]?[0-9]*", temiz)):
            try:
                sv = float(s.replace(",", "."))
            except ValueError:
                continue
            if abs(sv - bek) < 1e-6 or (bek and abs(sv / bek - 1) < 0.02):
                return True
    except Exception:
        pass
    return False

def puan_matematik(cikti, hedef=None, beklenen=None):
    """Beklenen sonucu (HEDEFLER tablosundan) eslestir; yoksa yapisal puan."""
    if beklenen:  # eski uyumluluk yolu
        if _sayi_esle(cikti, beklenen):
            return 1.0, f"Dogru: {beklenen}"
        return 0.2, f"Bulunamadi (beklenen: {beklenen})"
    if not hedef:
        # sinav tanimsiz -> matematiksel yapi ipudu ile puanla
        if re.search(r"[0-9][0-9.,]*\s*[+\-*/^×÷=]", cikti):
            return 0.6, "Matematiksel islem/item mevcut (beklenti yok)"
        if re.findall(r"[0-9]", cikti):
            return 0.5, "Sayi mevcut (beklenti yok)"
        return 0.3, "Beklenen sonuc tanimsiz"
    if hedef["tur"] == "sayi":
        eslenen = [h for h in hedef["sonuc"] if _sayi_esle(cikti, h)]
        if eslenen:
            return 1.0, "Beklenen deger bulundu: " + ", ".join(eslenen)
        if re.search(r"[0-9][0-9.,]*\s*[+\-*/^×÷=]", cikti):
            return 0.6, "Islem adimlari var ama beklendik sonuc yok"
        return 0.3, "Sayisal cevap bulunamadi"
    # tur == "metin"
    hit = _anahtar_esle(cikti, hedef["sonuc"])
    if hit:
        return 0.9, "Kavram bulundu: " + ", ".join(hit)
    return 0.4, "Beklenen kavramlar yok"

def puan_mantik(cikti, hedef=None):
    """Yapisal + beklenen kavram/dogruluk puani."""
    yapi, not_ = puan_genel(cikti)
    if not hedef or not hedef.get("sonuc"):
        return yapi, not_
    hit = _anahtar_esle(cikti, hedef["sonuc"])
    dogru = 1.0 if hit else 0.0
    not_ = ("Dogru: " + ", ".join(hit) + "; " + not_) if hit else (not_ + "; beklenen yok")
    return round(0.6 * dogru + 0.4 * yapi, 2), not_

def puan_dil(cikti, hedef=None):
    """Dil kalitesi: uzunluk, Turkce harf, yapilandirma (+ beklenen kavram bonusu)."""
    puan = 0.0
    notlar = []
    kelimeler = cikti.split()
    if len(kelimeler) >= 30:
        puan += 0.3
        notlar.append("yeterli uzunluk")
    elif len(kelimeler) >= 10:
        puan += 0.15
        notlar.append("kisa ama yeterli")
    # Turkce harf kontrolu
    turkce_harfler = len(re.findall(r'[çğıöşüÇĞİÖŞÜ]', cikti))
    if turkce_harfler >= 3:
        puan += 0.3
        notlar.append(f"{turkce_harfler} Turkce harf")
    # Yapilandirma (baslik/madde)
    if re.search(r'^\s*[\-\*\d]+[\.\)]', cikti, re.MULTILINE):
        puan += 0.2
        notlar.append("yapistirilmis")
    # En az bir cumle
    if len(cikti) > 30:
        puan += 0.2
        notlar.append("anlasilir")
    # Beklenen kavram bonusu (dogruluk ipucu)
    if hedef and hedef.get("sonuc"):
        hit = _anahtar_esle(cikti, hedef["sonuc"])
        if hit:
            puan = min(1.0, puan + 0.15)
            notlar.append("beklenen kavram")
    return min(puan, 1.0), "; ".join(notlar) if notlar else "yetersiz"

def puan_genel(cikti):
    """Genel kalite: uzunluk + baslik + madde + tutarlilik."""
    skor = 0.0
    notlar = []
    # Uzunluk
    kl = len(cikti.split())
    if kl >= 100:
        skor += 0.3; notlar.append("detayli")
    elif kl >= 50:
        skor += 0.2; notlar.append("orta")
    elif kl >= 15:
        skor += 0.1; notlar.append("kisa")
    # Baslik/madde yapisi
    madde_sayisi = len(re.findall(r'(?m)^[\s]*[\-\*\d]+[\.\)\s]', cikti))
    if madde_sayisi >= 3:
        skor += 0.3; notlar.append(f"{madde_sayisi} madde")
    elif madde_sayisi >= 1:
        skor += 0.15
    # Turkce harf
    if len(re.findall(r'[çğıöşüÇĞİÖŞÜ]', cikti)) >= 5:
        skor += 0.2; notlar.append("zengin Turkce")
    # Kod blogu varsa
    if "```" in cikti:
        skor += 0.2; notlar.append("kod blogu")
    return min(skor, 1.0), "; ".join(notlar) if notlar else "yetersiz"

KONU_PUANLAYICI = {
    "kod": puan_kod,
    "matematik": puan_matematik,
    "dil": puan_dil,
    "mantik": puan_mantik,
    "bilim": puan_genel,
    "tarih": puan_genel,
    "yaratici": puan_genel,
    "kultur": puan_genel,
    "pratik": puan_genel,
    "teknoloji": puan_genel,
}

def puanla(sonuclar):
    """Tum sonuclari puanla, ozet rapor dondur. Basarisizlari atla."""
    rapor = []
    basarili = 0
    hatali = 0
    toplam = 0.0
    for s in sonuclar:
        konu = s.get("konu", "genel")
        cikti = s.get("cikti", "")
        soru = s.get("soru", "")
        no = s.get("no", 0)
        
        # Hata/basarisiz/sıfır kelime kontrol
        if cikti.startswith("[HTTP") or cikti.startswith("[HATA") or cikti.startswith("[ARB") or s.get("kelime", 0) == 0:
            s["puan"] = 0.0
            s["puan_notu"] = "HATA/basarisiz (atlanildi)"
            hatali += 1
            rapor.append(s)
            continue
        
        basarili += 1
        hedef = _hedef_get(soru)
        if konu == "kod":
            p, not_ = puan_kod(cikti)
        elif konu == "matematik":
            p, not_ = puan_matematik(cikti, hedef)
        elif konu == "dil":
            p, not_ = puan_dil(cikti, hedef)
        elif konu == "mantik":
            p, not_ = puan_mantik(cikti, hedef)
        else:
            p, not_ = puan_genel(cikti)
        
        s["puan"] = round(p, 2)
        s["puan_notu"] = not_
        toplam += p
        rapor.append(s)
    
    # Basarili sorularin ortalamasi
    genel_puan = round((toplam / basarili) * 100, 1) if basarili else 0
    
    # Konu bazli ozet (sadece basarili)
    konu_ort = {}
    for s in rapor:
        if s.get("puan", 0) == 0 and "atlanildi" in s.get("puan_notu", ""):
            continue
        k = s.get("konu", "?")
        if k not in konu_ort:
            konu_ort[k] = []
        konu_ort[k].append(s.get("puan", 0))
    konu_ozet = {}
    for k, puanlar in konu_ort.items():
        konu_ozet[k] = {
            "ortalama": round(sum(puanlar) / len(puanlar), 2),
            "en_dusuk": round(min(puanlar), 2),
            "adet": len(puanlar)
        }
    
    return {
        "genel_puan": genel_puan,
        "basarili_soru": basarili,
        "hatali_soru": hatali,
        "konu_ozet": konu_ozet,
        "sonuclar": rapor
    }

def en_iyi_kacinma(soru_no, ciktilar):
    """Ayni sorudan N tane cevap varsa en iyi puanlani sec."""
    if not ciktilar:
        return None
    return max(ciktilar, key=lambda x: x.get("puan", 0))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: python3 otomatik_skorer.py karsilastirma.json")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        veri = json.load(f)
    sonuclar = veri.get("sonuclar", [])
    rapor = puanla(sonuclar)
    
    print(f"\n{'='*55}")
    print(f"  OTOMATIK SKOR RAPORU — {veri.get('model', '?')}")
    print(f"{'='*55}")
    print(f"  GENEL: {rapor['genel_puan']}/100 (basarili: {rapor['basarili_soru']}, hatali: {rapor['hatali_soru']})\n")
    
    for konu, bilgi in sorted(rapor['konu_ozet'].items()):
        emoji = "YUKSEK" if bilgi['ortalama'] >= 0.7 else "ORTA" if bilgi['ortalama'] >= 0.4 else "DUSUK"
        print(f"  {konu.upper():12s} {bilgi['ortalama']*100:5.1f}/100  [{emoji}]  ({bilgi['adet']} soru)")
    
    print(f"\n{'='*55}")
    print("  DETAYLI SONUCLAR:")
    print(f"{'='*55}")
    for s in rapor['sonuclar']:
        p = s.get("puan", 0)
        isaret = "*" if p < 0.5 else "+" if p >= 0.8 else "~"
        print(f"  [{isaret}] #{s['no']:2d} {s['konu']:10s} → {p*100:5.1f}  {s.get('puan_notu','')[:50]}")
    
    # Eksikleri listele
    zayif = [s for s in rapor['sonuclar'] if s.get('puan', 0) < 0.5]
    if zayif:
        print(f"\n  ⚠ ZAYIF ALANLAR ({len(zayif)} soru):")
        for s in zayif:
            print(f"    #{s['no']:2d} {s['konu']:10s} — {s.get('puan_notu','')[:60]}")
    
    # Kaydet
    cikti = sys.argv[1].replace(".json", "_skor.json")
    with open(cikti, "w") as f:
        json.dump(rapor, f, ensure_ascii=False, indent=2)
    print(f"\n  Kaydedildi: {cikti}")
