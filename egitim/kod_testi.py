#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kod modeli degerlendirmesi: pass@1 (ve opsiyonel retry pass@3).
Kodda LLM hakem YOK; birim test calisir. Bu jürinin kanit setidir.

Kullanim:
  MODEL=hf.co/Lennebraha38/lennebraha-coder:Q4_K_M RETRY=2 python3 kod_testi.py   (yerel ollama)
  MODEL=openrouter RETRY=1 python3 kod_testi.py       (bulut mega-beyin; OPENROUTER_API_KEY gerekir)

Cikti: ekrana tablo + kod_sonuc.json
"""
import json, os, re, subprocess, sys, tempfile, urllib.request, time

OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL_AD = os.environ.get("MODEL", "hf.co/Lennebraha38/lennebraha-coder:Q4_K_M")
RETRY = int(os.environ.get("RETRY", "0"))
OR_MODEL = os.environ.get("OPENROUTER_MODEL", "qwen/qwen3-235b-a22b-instruct:free")
OR_KEY = os.environ.get("OPENROUTER_API_KEY", "")

GOREVLER = [
 {"soru": "Faktoriyel hesaplayan bir fonksiyon yaz: faktor(n) n! dondurmeli.",
  "test": "assert faktor(5)==120\nassert faktor(0)==1"},
 {"soru": "Fibonacci sayisi: fib(n) n. Fibonacci sayisini dondurmeli (fib(0)=0, fib(1)=1).",
  "test": "assert fib(10)==55\nassert fib(1)==1"},
 {"soru": "Bir metin palindrom mu diye kontrol eden is_palindrome(metin) yaz. Bosluk/rakam yok.",
  "test": "assert is_palindrome('kapi')==True\nassert is_palindrome('kazak')==False"},
 {"soru": "1'den n'e kadar (dahil) sayilari listeye donen fizzbuzz_list(n) yaz: 3'un kati 'Fizz', 5'in kati 'Buzz', "
         "hem 3 hem 5'in kati 'FizzBuzz', digerleri sayinin kendisi.",
  "test": "assert fizzbuzz_list(15)[-1]=='FizzBuzz'\nassert fizzbuzz_list(3)[-1]=='Fizz'\nassert fizzbuzz_list(5)[-2]=='4'"},
 {"soru": "Bir cumledeki kelimeleri ters sirala: reverse_words(cumle) -> kelimelerin sirasi ters.",
  "test": "assert reverse_words('Merhaba dunya')=='dunya Merhaba'\nassert reverse_words('a b c')=='c b a'"},
 {"soru": "Bir listedeki tekrarlari sil butun siralasi koru: dedupe(liste) -> yeni liste.",
  "test": "assert dedupe([1,2,1,3,1,2])==[1,2,3]\nassert dedupe([])==[]"},
 {"soru": "Bir sayi asal mi? is_prime(n) -> bool. n>=2.",
  "test": "assert is_prime(17)==True\nassert is_prime(1)==False\nassert is_prime(4)==False"},
 {"soru": "Bir cumledeki en uzun kelimeyi donduren longest_word(cumle) yaz. Esitlikte ilk olani al.",
  "test": "assert longest_word('kisa uzun cok daha uzun kelime')=='uzun'\nassert longest_word('abc')=='abc'"},
 {"soru": "Ikili arama: binary_search(liste, hedef) -> indeks veya -1. Liste sirali kabul et.",
  "test": "assert binary_search([1,3,5,7,9],7)==3\nassert binary_search([1,3,5],2)==-1"},
 {"soru": "Daire alani: area_circle(yaricap) -> pi*yaricap^2, 2 ondalige yuvarlanmis float.",
  "test": "assert round(area_circle(1),2)==3.14\nassert round(area_circle(2),2)==12.57"},
 {"soru": "Sozlukten deger-degerlere gore en buyuk 3 anahtari donduren top3(s) yaz.",
  "test": "assert top3({'a':1,'b':3,'c':2,'d':4})==['d','b','c']"},
 {"soru": "Bir string'de en cok gecen karakteri donduren most_common_char(metin) yaz. "
         "Esitlikte alfabede ilk olani al.",
  "test": "assert most_common_char('zzzzabc')=='z'\nassert most_common_char('ababb')=='b'"},
]

def istem(konu):
    return [{"role": "user", "content": "Sadece saf Python kodunu yaz, aciklama yazma. Fonksiyon adi "
             "ve imzasi aynen korunmali.\n" + konu + "\nKodu ```python ... ``` icinde ver."}]

def cagir(mesajlar):
    """Ollama veya OpenRouter ile cagri. Turkce cevap metnini dondur."""
    if MODEL_AD == "openrouter":
        govde = {"model": OR_MODEL, "messages": mesajlar, "temperature": 0.2, "max_tokens": 800}
        istek = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(govde).encode(), headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + OR_KEY,
                "HTTP-Referer": "https://github.com/Lennebraha38/7-gun-kamp",
            }, method="POST")
        with urllib.request.urlopen(istek, timeout=240) as r:
            j = json.loads(r.read().decode())
        return j["choices"][0]["message"]["content"]
    # Ollama yerel
    govde = {"model": MODEL_AD, "messages": mesajlar, "stream": False, "options": {"temperature": 0.2, "num_predict": 800}}
    if "qwen3" in MODEL_AD and "coder" not in MODEL_AD:
        govde["think"] = False
    istek = urllib.request.Request(OLLAMA, data=json.dumps(govde).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(istek, timeout=600) as r:
        j = json.loads(r.read().decode())
    return j["message"]["content"]

def ayikla(metin):
    m = re.search(r"```python(.*?)```", metin, re.S)
    if m:
        return m.group(1).strip()
    if "def " in metin:
        return metin.strip()
    return None

def kos(kod_birlestir_test):
    """Kod + testi /tmp'de calistir. (True/False, hata msg)"""
    with tempfile.TemporaryDirectory() as d:
        yol = os.path.join(d, "gorev.py")
        with open(yol, "w", encoding="utf-8") as f:
            f.write(kod_birlestir_test)
        try:
            r = subprocess.run(["python3", yol], capture_output=True, text=True, timeout=25, cwd=d)
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT"
        if r.returncode == 0:
            return True, ""
        hata = (r.stderr or "").strip().splitlines()
        return False, (hata[-1] if hata else "HATA")

def degerlendir():
    sonuc = {"model": MODEL_AD, "pass_at_1": 0, "pass_at_" + str(1 + RETRY): 0,
             "gorevler": [], "retry": RETRY}
    toplam = 0
    bas1 = 0
    basR = 0
    for i, g in enumerate(GOREVLER, 1):
        toplam += 1
        msj = istem(g["soru"])
        durum1 = "HATA"
        durumR = "HATA"
        cevap = ""
        deneme = 0
        while deneme <= RETRY:
            try:
                cevap = cagir(msj)
            except Exception as ex:
                print("  hata API: %s" % ex)
                time.sleep(5)
                deneme += 1
                continue
            kod = ayikla(cevap)
            if not kod:
                durumR = "KOD_YOK"
                msj = msj + [{"role": "assistant", "content": cevap[:1200]},
                             {"role": "user", "content": "Python kodu vermedin. Sadece ```python ... ``` dir."}]
                deneme += 1
                continue
            gecti, hata = kos(kod + "\n" + g["test"])
            if deneme == 0:
                durum1 = "PASS" if gecti else "FAIL"
            if gecti:
                durumR = "PASS"
                break
            durumR = "FAIL-" + hata[:40]
            if deneme < RETRY:
                msj = msj + [{"role": "assistant", "content": cevap[:1500]},
                             {"role": "user", "content": "Kod hata verdi, duzelt:\n" + hata}]
            deneme += 1
        if durum1 == "PASS":
            bas1 += 1
        if durumR == "PASS":
            basR += 1
        sonuc["gorevler"].append({"no": i, "pass_1": durum1, "sonunda": durumR})
        print(" %2d) %-8s  sonunda=%s | %s" % (i, durum1, durumR, g["soru"][:55]))
    sonuc["pass_at_1"] = round(bas1 / toplam, 3)
    sonuc["pass_at_" + str(1 + RETRY)] = round(basR / toplam, 3)
    print("\n===== KOD SONUC (%s) =====" % MODEL_AD)
    print("pass@1        : %.0f%% (%d/%d)" % (100 * bas1 / toplam, bas1, toplam))
    if RETRY:
        print("pass@%d (retry): %.0f%% (%d/%d)" % (1 + RETRY, 100 * basR / toplam, basR, toplam))
    with open("kod_sonuc.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=1)
    print("kayit: kod_sonuc.json")

if __name__ == "__main__":
    degerlendir()