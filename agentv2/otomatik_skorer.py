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

def puan_matematik(cikti, beklenen=None):
    """Cevap icindeki sayilari bul, beklenen sonucla karsilastir."""
    if not beklenen:
        return 0.5, "Beklenen sonuc tanimsiz"
    # Cevaptaki tum sayilari cek
    sayilar = re.findall(r'[-+]?\d*\.?\d+', cikti.replace(" ", ""))
    bek_num = None
    try:
        bek_num = float(beklenen)
    except ValueError:
        # Kesir 1/36 gibi
        if "/" in beklenen:
            try:
                p, b = beklenen.split("/")
                bek_num = float(p) / float(b)
            except Exception:
                pass
    if bek_num is None:
        return 0.5, "Beklenen sayisal degil"
    for s in sayilar:
        try:
            sv = float(s)
            if abs(sv - bek_num) < 0.01 or (bek_num != 0 and abs(sv/bek_num - 1) < 0.02):
                return 1.0, f"Dogru: {s}"
        except ValueError:
            continue
    return 0.2, f"Bulunamadi (beklenen: {beklenen})"

def puan_dil(cikti):
    """Dil kalitesi: uzunluk, Turkce harf, yapilandirma."""
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
    "mantik": puan_genel,
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
        no = s.get("no", 0)
        
        # Hata/basarisiz/sıfır kelime kontrol
        if cikti.startswith("[HTTP") or cikti.startswith("[HATA") or cikti.startswith("[ARB") or s.get("kelime", 0) == 0:
            s["puan"] = 0.0
            s["puan_notu"] = "HATA/basarisiz (atlanildi)"
            hatali += 1
            rapor.append(s)
            continue
        
        basarili += 1
        
        if konu == "kod":
            p, not_ = puan_kod(cikti)
        elif konu == "matematik":
            p, not_ = puan_matematik(cikti, MATEMATIK_BEKLENEN.get(no))
        elif konu == "dil":
            p, not_ = puan_dil(cikti)
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
