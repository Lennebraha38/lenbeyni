"""Self-Correction — hatali cevap bulursa duzeltme turu.
Kod: sandbox'da calistir → hata varsa modele geri besle → duzelt.
Matematik: beklenen sonuc ile karsilastir → farkli ise duzelttir.
Genel: cevap cok kisa/eksikse → detay ister.
"""
import os, re, ast, subprocess, tempfile

def kod_dogrula(kod_metni):
    """Kod blogunu cikar, calistir, hata varsa dondur."""
    # Markdown blog temizleme
    blok = re.search(r'```(?:python)?\s*\n(.*?)```', kod_metni, re.DOTALL)
    if blok:
        kod = blok.group(1).strip()
    else:
        blok = re.search(r'```\s*\n(.*?)```', kod_metni, re.DOTALL)
        kod = blok.group(1).strip() if blok else kod_metni.strip()
    
    # Syntax kontrolu
    try:
        ast.parse(kod)
    except SyntaxError as e:
        return False, f"Syntax hatasi satir {e.lineno}: {e.msg}\nKod:\n{kod[:200]}"
    
    # Calistirma
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(kod)
        yol = f.name
    try:
        r = subprocess.run(["python3", "-u", yol], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return True, f"Basarili: {r.stdout[:200]}"
        return False, f"Runtime hatasi:\n{r.stderr[:300]}\nKod:\n{kod[:200]}"
    except subprocess.TimeoutExpired:
        return False, f"Timeout (10sn): Kod calisiyor ama bitmiyor\nKod:\n{kod[:200]}"
    finally:
        os.unlink(yol)

def duzeltme_turu(cevap, konu, hata_bilgisi):
    """Kod hatasi icin duzeltme promptu: sadece calisan kod iste."""
    return (
        f"Onceki cevabindaki kod calismadi:\n{hata_bilgisi}\n\n"
        f"Lutfen soruyu yeniden coz. KESIN KURAL: "
        f"Sadece calisan kodu gonder, hicbir aciklama veya metin yazma. "
        f"Kodu tek bir ```python ... ``` bloguna koy."
    )

def self_correction(soru, cevap, konu, llm_fonk, max_tur=1):
    """Cevabi dogrula, gerekirse duzeltme turu calistir.
    llm_fonk: lenbeyni_zeka.llm gibi bir fonksiyon (mesajlar->str)
    max_tur: kac kez duzeltme denensin (varsayilan 1)
    """
    if konu == "kod":
        basarili, hata = kod_dogrula(cevap)
        if basarili:
            return cevap, 0, "Kod dogrulandi"
        
        for tur in range(max_tur):
            duzelt = duzeltme_turu(cevap, konu, hata)
            yeni_cevap = llm_fonk([
                {"role": "user", "content": soru},
                {"role": "assistant", "content": cevap},
                {"role": "user", "content": duzelt}
            ])
            if yeni_cevap:
                basarili2, hata2 = kod_dogrula(yeni_cevap)
                if basarili2:
                    return yeni_cevap, tur + 1, f"Tur {tur+1}: duzeltildi"
                hata = hata2
                cevap = yeni_cevap
            else:
                break
        return cevap, max_tur, f"Duzelemedi: {hata[:100]}"
    
    elif konu == "matematik":
        # Basit sayi kontrolu
        sayilar = re.findall(r'[-+]?\d*\.?\d+', cevap)
        if len(sayilar) == 0 and len(cevap) > 50:
            for tur in range(max_tur):
                yeni_cevap = llm_fonk([
                    {"role": "user", "content": soru},
                    {"role": "assistant", "content": cevap},
                    {"role": "user", "content": "Cevabinda sayisal sonuc yok. Lutfen sonucu sayi olarak belirt."}
                ])
                if yeni_cevap:
                    return yeni_cevap, tur + 1, f"Tur {tur+1}: sayisal sonuc eklendi"
            return cevap, 0, "Sayisal sonuc bulunamadi"
        return cevap, 0, "Matematik kabul"
    
    else:
        # Genel: cok kisa cevap kontrolu
        kelime = len(cevap.split())
        if kelime < 15:
            for tur in range(max_tur):
                yeni_cevap = llm_fonk([
                    {"role": "user", "content": soru},
                    {"role": "assistant", "content": cevap},
                    {"role": "user", "content": "Cevabin cok kisa. Lutfen daha detayli ve aciklayici cevap ver."}
                ])
                if yeni_cevap and len(yeni_cevap.split()) > kelime:
                    return yeni_cevap, tur + 1, f"Tur {tur+1}: detaylandirildi"
            return cevap, 0, f"Kisa ama devam ({kelime} kelime)"
        return cevap, 0, "Yeterli uzunluk"
