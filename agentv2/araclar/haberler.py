"""Haber / RSS / kaynak akisi. (feedparser mantigi, bagimsiz)"""
import requests, re
from xml.etree import ElementTree as ET

BASLIK = {"User-Agent": "Mozilla/5.0"}

from typing import Optional, Tuple, List, Dict, Any, Callable, Union
def rss(akislar, max_unsur: int = 15) -> str:
    tum = []
    for akis in akislar:
        try:
            r = requests.get(akis, timeout=15, headers=BASLIK)
            root = ET.fromstring(r.content)
            for item in root.iter("item"):
                baslik = item.findtext("title") or ""
                link = item.findtext("link") or ""
                desc = item.findtext("description") or ""
                desc = re.sub(r"<[^>]+>", "", desc)[:150]
                tum.append(f"- {baslik}\n  {link}\n  {desc}")
        except Exception:
            continue
    return "\n".join(tum[:max_unsur]) or "[RSS bos]"

def haber_sistemi(llm, konular) -> str:
    akislar = {
        "teknoloji": ["https://www.hurriyet.com.tr/rss/teknoloji.xml",
                      "https://www.donanimhaber.com/rss.xml",
                      "https://www.engadget.com/rss.xml"],
        "bilim": ["https://www.bilim.org/rss", "https://arstechnica.com/science/feed/"],
        "genel": ["https://www.bbc.com/turkce/sondakika/index.xml"],
    }.get(konular, ["https://www.engadget.com/rss.xml"])
    veri = rss(akislar)
    return veri, llm([
        {"role":"system","content":"Haber akisini kategorize et, en onemli 5 haberi sec, Turkce ozet."},
        {"role":"user","content":veri[:6000]}], max_tokens=1500)