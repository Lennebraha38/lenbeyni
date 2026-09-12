"""Coklu-saglayici LLM ara katmani — tek key bagimliligini kirmak.

Zincir: OpenRouter -> Groq -> Google AI Studio (Gemini).
Her saglayici kendi env anahtarini bekler; anahtar yoksa veya
429/5xx/okunmaz cevap verirse siradaki saglayiciya gecilir.

Kullanim:
    from llm_provider import sira_sor
    cevap = sira_sor(mesajlar, model="openrouter/model:id", max_tokens=16384)

Not: yedek saglayicilarin modelleri sabittir (buradan gelen Or-model
OpenRouter'a ozeldir); Groq/Gemini icin burada tanimli modeller kullanilir.
"""
import os
from typing import Any, Dict, List, Optional, Sequence

OPENROUTER_URL = os.environ.get("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
GROQ_URL = os.environ.get("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")
GEMINI_URL = "generativelanguage.googleapis.com"

ANAHTAR_OR = os.environ.get("OPENROUTER_KEY", "")
ANAHTAR_GROQ = os.environ.get("GROQ_API_KEY", "")
ANAHTAR_GEMINI = os.environ.get("GEMINI_API_KEY", "")

# Yedek saglayicilarin varsayilan modelleri (OpenRouter id'lere ozgu model gecersiz)
MODEL_GROQ = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MODEL_GEMINI = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")


def _openai_compat(mesajlar: List[Dict[str, str]], model: str,
                   max_tokens: int, api_key: str, taban_url: str) -> Optional[str]:
    """OpenAI uyumlu /chat/completions son noktasi (OpenRouter, Groq)."""
    import requests
    r = requests.post(
        taban_url,
        json={"model": model, "messages": mesajlar, "temperature": 0.7,
              "max_tokens": max_tokens, "stream": False},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=90,
    )
    if r.status_code != 200:
        return None
    try:
        icerik = r.json().get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        return None
    return icerik if isinstance(icerik, str) and icerik.strip() else None


def _gemini(mesajlar: List[Dict[str, str]], model: str,
            max_tokens: int, api_key: str) -> Optional[str]:
    """Google AI Studio Gemini REST (OpenAI mesaj seklini parts'a cevirir)."""
    import json
    from urllib.request import Request, urlopen
    icerik = ""
    for m in mesajlar:
        rol = "user" if m["role"] in ("user", "system") else "model"
        icerik += f"{m.get('content', '')}\n"
    govde = {
        "contents": [{"role": "user", "parts": [{"text": icerik.strip()}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7},
    }
    url = (f"https://{GEMINI_URL}/v1beta/models/{model}:generateContent"
           f"?key={api_key}")
    try:
        istek = Request(url, data=json.dumps(govde).encode(),
                        headers={"Content-Type": "application/json"})
        with urlopen(istek, timeout=90) as yanit:
            veri = json.loads(yanit.read().decode())
        parcalar = veri["candidates"][0]["content"]["parts"]
        metin = "".join(p.get("text", "") for p in parcalar).strip()
    except Exception:
        return None
    return metin or None


def _probat_sirasi(mesajlar: List[Dict[str, str]], model: str,
                   max_tokens: int) -> List[Any]:
    """Kullanilabilir (anahtarli) saglayici yetenek listesi, oncelik sirasiyla."""
    adimlar = []
    if ANAHTAR_OR.strip():
        adimlar.append(lambda: _openai_compat(mesajlar, model, max_tokens, ANAHTAR_OR, OPENROUTER_URL))
    if ANAHTAR_GROQ.strip():
        adimlar.append(lambda: _openai_compat(mesajlar, MODEL_GROQ, max_tokens, ANAHTAR_GROQ, GROQ_URL))
    if ANAHTAR_GEMINI.strip():
        adimlar.append(lambda: _gemini(mesajlar, MODEL_GEMINI, max_tokens, ANAHTAR_GEMINI))
    return adimlar


def sira_sor(mesajlar: List[Dict[str, str]], model: str,
             max_tokens: int = 16384,
             adimlar: Optional[Sequence[Any]] = None) -> Optional[str]:
    """Anahtari olan saglayicilari sirayla dener; ilk basarili cevabi dondurur."""
    deneme = list(adimlar) if adimlar is not None else _probat_sirasi(mesajlar, model, max_tokens)
    hatalar = []
    for adim in deneme:
        try:
            sonuc = adim()
        except Exception as e:  # ag/hata durumu: digerine gec
            hatalar.append(repr(e))
            continue
        if sonuc:
            return sonuc
        hatalar.append("bos-ya-da-kota")
    return None