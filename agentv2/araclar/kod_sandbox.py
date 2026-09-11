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

def _kisa_limit():
    """Alt islem icin cpu+as limitleri (programin sistemi bogmamasi icin)."""
    def _set():
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        except Exception:
            pass
    return _set

def python_kod(kod, timeout=15):
    if _python_t(kod):
        return "[GUVENLIK Bloklandi: Python kodunda tehlikeli islem tespit edildi]"
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

def bash_kod(emir, timeout=20):
    if _komut_t(emir):
        return "[GUVENLIK Bloklandi: bash komutu tehlikeli kalip iceriyor]"
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

def node_kod(kod, timeout=15):
    if _python_t(kod):
        return "[GUVENLIK Bloklandi: node kodunda tehlikeli islem tespit edildi]"
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