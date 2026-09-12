"""Multimodal: goruntu -> metin anlama, ses -> metin, ve gorsel CINI'ya devir.
- Gorsel anlama: goruntuyu base64'e cevirir, OpenRouter vision modeline gonderir.
- Ses notu: gorsel arac katmanindan gorselle eslesir.
- CINIA gorsel uretimi: [GORSEL]prompt,model(flux)[/GORSEL]
"""
import base64, os, sys

from typing import Optional, Tuple, List, Dict, Any, Callable, Union
def gorsel_anla(llm, yol: str, soru: str = "Bu goruntuyu detayli acikla. Turkce.") -> str:
    """Goruntuyu base64'e cevirip vision destekli mega beyne sorar."""
    try:
        with open(yol, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        import requests
        r = requests.post(os.environ.get("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions"), json={
            "model": "meta-llama/llama-3.2-90b-vision:free",
            "messages": [{"role": "user", "content": "data:image/png;base64," + b64},
                         {"role": "user", "content": soru}],
            "temperature": 0.7, "max_tokens": 1200,
        }, headers={"Authorization": "Bearer " + os.environ.get("OPENROUTER_KEY", "")}, timeout=90)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"][:3000]
        return f"[Gorsel anlama hata: HTTP {r.status_code}]"
    except Exception as e:
        return f"[Gorsel anlama hata: {e}]"

def gorsel_yorumla(llm, yol: str, soru: str) -> str:
    return gorsel_anla(llm, yol, soru)

def analyse_yol(yol: str, soru: str) -> str:
    return gorsel_anla(_dummy_llm, yol, soru)

def _dummy_llm(mesajlar, **kw: Any) -> str:
    return "[key yok]"

def indir_gorsel(url: str, yol: str = "gorsel.png") -> str:
    try:
        import requests
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(yol, "wb") as f:
                f.write(r.content)
            return yol
    except Exception as e:
        return f"[indir hata: {e}]"
    return "[indirilemedi]"