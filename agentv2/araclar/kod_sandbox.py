"""Kod calistirma sandbox'i: Python, Bash, Node (grup mode). (OpenCLI / code-interpreter)

Guvenlik: agentv2/guvenlik.py kurallariyla
- Python: AST bloklistesi -> tehlikeli islemleri baslamadan engeller, arka plan yurutmesi
- Bash: tehlikeli kalip bloklistesi
Aktarilan kod beta kullanim icindir; tam izolasyon icin Docker/gVisor onerilir.
"""
import subprocess, tempfile, os, resource

try:
    from agentv2.guvenlik import komut_tehlikeli as _komut_t, python_tehlikeli as _python_t
except ImportError:
    try:
        from guvenlik import komut_tehlikeli as _komut_t, python_tehlikeli as _python_t
    except ImportError:
        _komut_t = lambda c: False
        _python_t = lambda k: False

from typing import Optional, Tuple, List, Dict, Any, Callable, Union


# ── Docker izolasyonu (kalici cozum: blocklist bypass olsa bile zarar disari cikamaz) ──
import shutil
_DOCKER_VAR = None

def _docker_var() -> bool:
    """Docker uygun mu? (bir kez dene, cache'le) — ZENAI_DOCKER=1 ile etkin."""
    global _DOCKER_VAR
    if _DOCKER_VAR is None:
        _DOCKER_VAR = (shutil.which("docker") is not None
                       and os.environ.get("ZENAI_DOCKER", "").lower() in ("1", "true", "evet"))
    return _DOCKER_VAR


def _docker_calistir(betik: str, uzanti: str, imaj: str,
                     calistir: List[str], timeout: int = 25,
                     max_mem: str = "256m", max_cpu: str = "0.5") -> str:
    """Betigi izole, ag erisimisz, tek-seferlik container'da calistirir.

    Guvenlik: --network=none (egres yok), --memory/--cpus sinirli,
    --pids-limit ile fork bombasi durdurulur; container --rm ile yok edilir.
    Cikti ve hata 3000/1000 karakter sinirli dondurulur.
    """
    tmpdir = tempfile.mkdtemp(prefix="zenai_dk_")
    betik_yolu = os.path.join(tmpdir, "betik" + uzanti)
    try:
        with open(betik_yolu, "w") as f:
            f.write(betik)
        r = subprocess.run(
            ["docker", "run", "--rm",
             "--network", "none",
             "--memory", max_mem,
             "--cpus", max_cpu,
             "--pids-limit", "64",
             "-v", f"{tmpdir}:/mnt:rw",
             "-w", "/mnt",
             imaj] + calistir + ["/mnt/" + os.path.basename(betik_yolu)],
            capture_output=True, text=True, timeout=timeout,
        )
        hata = r.stderr[-1000:].strip()
        cikti = r.stdout[-3000:].strip()
        if r.returncode != 0:
            return ((hata[-1000:] if hata else "") + "\n" + cikti)[:3000]
        return (hata + "\n" if hata else "") + cikti
    except subprocess.TimeoutExpired:
        return "[Docker timeout]"
    except FileNotFoundError:
        return "[Docker bulunamadi]"
    except Exception as e:
        return f"[Docker hatasi: {e}]"
    finally:
        try:
            subprocess.run(["rm", "-rf", tmpdir], capture_output=True)
        except Exception:
            pass


def _kisa_limit() -> Callable[[], None]:
    """Alt islem icin cpu+as limitleri (programin sistemi bogmamasi icin)."""
    def _set() -> None:
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        except Exception:
            pass
    return _set

def python_kod(kod: str, timeout: int = 15) -> str:
    if _python_t(kod):
        return "[GUVENLIK Bloklandi: Python kodunda tehlikeli islem tespit edildi]"
    if _docker_var():
        sonuc = _docker_calistir(kod, ".py", "python:3.11-slim",
                                 ["python3", "-I"], timeout=timeout)
        if not sonuc.startswith("[Docker"):
            return sonuc
        # docker goruntusu yoksa/hataliysa eski guvenli yola don
    tmpdir = tempfile.mkdtemp(prefix="zenai_py_")
    yol = os.path.join(tmpdir, "sifre.py")
    try:
        with open(yol, "w") as f:
            f.write(kod)
        r = subprocess.run(
            ["python3", "-I", yol],
            capture_output=True, text=True, timeout=timeout,
            preexec_fn=_kisa_limit(),
            env={"PATH": "/usr/bin:/bin", "HOME": tmpdir, "TMPDIR": tmpdir},
            cwd=tmpdir,
        )
        hata = r.stderr[-1000:].strip()
        cikti = r.stdout[-3000:].strip() or "(cikti yok)"
        if r.returncode != 0:
            return ((hata[-1000:] if hata else "") + "\n" + cikti)[:3000]
        return (hata + "\n" if hata else "") + cikti
    except subprocess.TimeoutExpired:
        return "[Python timeout]"
    except Exception as e:
        return f"[Python hatasi: {e}]"
    finally:
        try:
            subprocess.run(["rm", "-rf", tmpdir], capture_output=True)
        except Exception:
            pass

def bash_kod(emir: str, timeout: int = 20) -> str:
    if _komut_t(emir):
        return "[GUVENLIK Bloklandi: bash komutu tehlikeli kalip iceriyor]"
    if _docker_var():
        sonuc = _docker_calistir("#!/bin/sh\n" + emir, ".sh", "debian:stable-slim",
                                 ["sh"], timeout=timeout)
        if not sonuc.startswith("[Docker"):
            return sonuc
    try:
        r = subprocess.run(emir, shell=True, capture_output=True, text=True,
                           timeout=timeout, preexec_fn=_kisa_limit(),
                           env={"PATH": "/usr/bin:/bin", "HOME": os.path.expanduser("~/zenai_shell")},
                           cwd=tempfile.mkdtemp(prefix="zenai_sh_"))
        return (r.stdout or "")[-3000:] + (r.stderr or "")[-1000:]
    except subprocess.TimeoutExpired:
        return "[Bash timeout]"
    except Exception as e:
        return f"[Bash hatasi: {e}]"

def node_kod(kod: str, timeout: int = 15) -> str:
    if _python_t(kod):
        return "[GUVENLIK Bloklandi: node kodunda tehlikeli islem tespit edildi]"
    if _docker_var():
        sonuc = _docker_calistir(kod, ".js", "node:20-slim",
                                 ["node"], timeout=timeout)
        if not sonuc.startswith("[Docker"):
            return sonuc
    tmpdir = tempfile.mkdtemp(prefix="zenai_js_")
    yol = os.path.join(tmpdir, "sifre.js")
    try:
        with open(yol, "w") as f:
            f.write(kod)
        r = subprocess.run(
            ["node", yol], capture_output=True, text=True, timeout=timeout,
            preexec_fn=_kisa_limit(), env={"PATH": "/usr/bin:/bin", "HOME": tmpdir},
            cwd=tmpdir,
        )
        return (r.stdout or "")[-3000:] + (r.stderr or "")[-1000:]
    except subprocess.TimeoutExpired:
        return "[Node timeout]"
    except Exception as e:
        return f"[Node hatasi: {e}]"
    finally:
        try:
            subprocess.run(["rm", "-rf", tmpdir], capture_output=True)
        except Exception:
            pass