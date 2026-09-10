"""Format: PDF, DOCX, CSV, JSON, XLSX analizi. (pdfplumber/PyPDF2 yerine hafif ozdusurum)"""
import json, csv, io, os, zlib, re

def pdf_metin(yol):
    out = []
    with open(yol, "rb") as f:
        data = f.read()
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            raw = zlib.decompress(m.group(1))
            txt = re.findall(rb"\((?:[^()\\]|\\.)*\)", raw)
            for t in txt:
                s = t[1:-1].decode("latin1", "ignore")
                if len(s) > 1 and any(c.isalpha() for c in s):
                    out.append(s)
        except Exception:
            continue
    return " ".join(out)[:6000]

def belge(yol):
    if yol.endswith(".pdf"): return pdf_metin(yol)
    if yol.endswith(".json"): return json.dumps(json.load(open(yol)), ensure_ascii=False)[:6000]
    if yol.endswith(".csv"):
        with open(yol, newline="") as f:
            return json.dumps(list(csv.reader(f))[:50], ensure_ascii=False)[:6000]
    with open(yol, "r", errors="ignore") as f:
        return f.read()[:6000]

def veri_ozet(llm, yol):
    return llm([
        {"role":"system","content":"Veriyi ozetle, tablo/ana hatlar cikar. Turkce."},
        {"role":"user","content":belge(yol)}], max_tokens=1200)