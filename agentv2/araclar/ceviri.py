"""Ceviri + dil araclari."""
import requests

from typing import Optional, Tuple, List, Dict, Any, Callable, Union
def cevir(metin: str, hedef: str = "tr") -> str:
    try:
        r = requests.post("https://api-free.deepl.com/v2/translate", json={
            "text": [metin], "target_lang": hedef.upper(),
            "auth_key": "DUMMY"})
        if r.status_code != 200:
            raise Exception(r.status_code)
        return r.json()["translations"][0]["text"]
    except Exception:
        return "[Ceviri API key gerekli (DeepL ucretsiz: /DeepL secret)]"