#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/sync_konu_modelleri.py

`agentv2/model_routing.py` icindeki `KONU_MODELLERI` tek kaynak; bu script
`web/app.js` icindeki `const KONU_MODELLERI = {...}` blogunu ayni degerlerle
yeniden uretir. Boylece Python ve JS konu->model haritasinin cogalmasi onlenir.

Kullanim:
  python3 scripts/sync_konu_modelleri.py            # senkronize et
  python3 scripts/sync_konu_modelleri.py --kontrol  # sadece fark kontrol (CI)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY_SRC = ROOT / "agentv2" / "model_routing.py"
JS_SRC = ROOT / "web" / "app.js"

sys.path.insert(0, str(ROOT / "agentv2"))
import model_routing as _mr  # noqa: E402

def js_block() -> str:
    """model_routing.py'deki KONU_MODELLERI'ni JS nesnesi metnine cevirir."""
    satirlar = ["const KONU_MODELLERI = {"]
    en_genis = max(len(k) for k in _mr.KONU_MODELLERI)
    for konu, (model, maxt, _) in _mr.KONU_MODELLERI.items():
        bosluk = " " * (en_genis - len(konu))
        satirlar.append(f"  {konu}:{bosluk} [\"{model}\", {maxt}],")
    satirlar.append("};")
    return "\n".join(satirlar)

def main() -> int:
    if not PY_SRC.exists() or not JS_SRC.exists():
        print("Kaynak dosya bulunamadi.", file=sys.stderr)
        return 1
    js = JS_SRC.read_text(encoding="utf-8")
    pat = re.compile(r"const KONU_MODELLERI = \{.*?\};", re.S)
    m = pat.search(js)
    if not m:
        print("app.js icinde KONU_MODELLERI blogu bulunamadi.", file=sys.stderr)
        return 1
    yeni = js_block()
    js_yeni = js[:m.start()] + yeni + js[m.end():]

    if js_yeni == js:
        print("OK: web/app.js senkron.")
        return 0

    if "--kontrol" in sys.argv:
        print("FARK VAR: python3 scripts/sync_konu_modelleri.py calistirilmali.", file=sys.stderr)
        return 1

    JS_SRC.write_text(js_yeni, encoding="utf-8")
    print(f"OK: web/app.js senkronize edildi ({len(_mr.KONU_MODELLERI)} konu).")
    return 0

if __name__ == "__main__":
    sys.exit(main())