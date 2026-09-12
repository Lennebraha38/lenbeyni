"""Windows / Linux / Android sistem araclari: dosya, klasor, process."""
import os, glob, subprocess, platform, shutil

from typing import Optional, Tuple, List, Dict, Any, Callable, Union
def sistem_bilgi() -> str:
    return (f"OS: {platform.system()} {platform.release()} {platform.machine()}\n"
            f"Python: {platform.python_version()}")

def dosyalar(klasor: str, kalip: str = "*") -> str:
    try:
        son = [f for f in glob.glob(os.path.join(klasor, kalip))][:50]
        return "\n".join(son) or "[dosya yok]"
    except Exception as e:
        return f"[hata: {e}]"

def disk() -> str:
    try:
        s = shutil.disk_usage("/")
        return f"Disk: {s.used/1e9:.1f}GB kullanildi / {s.total/1e9:.1f}GB (bos: {s.free/1e9:.1f}GB)"
    except Exception as e:
        return f"[hata: {e}]"

def oku(yol: str, maxlen: int = 4000) -> str:
    try:
        with open(yol, "r", errors="ignore") as f:
            return f.read()[:maxlen]
    except Exception as e:
        return f"[hata: {e}]"

def yaz(yol: str, icerik: str) -> str:
    try:
        os.makedirs(os.path.dirname(yol) or ".", exist_ok=True)
        with open(yol, "w") as f:
            f.write(icerik)
        return f"Yazildi: {yol} ({len(icerik)}B)"
    except Exception as e:
        return f"[hata: {e}]"

def process_listesi() -> str:
    try:
        r = subprocess.run(["ps", "-eo", "pid,comm,%mem", "--sort=-%mem"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout[:2000]
    except Exception:
        try:
            r = subprocess.run(["ps"], capture_output=True, text=True, timeout=10)
            return r.stdout[:2000]
        except Exception as e:
            return f"[hata: {e}]"