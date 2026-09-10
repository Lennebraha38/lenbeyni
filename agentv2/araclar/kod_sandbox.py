"""Kod calistirma sandbox'i: Python, Bash, Node (grup mode). (OpenCLI / code-interpreter)"""
import subprocess, tempfile, os

def python_kod(kod, timeout=15):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(kod); yol = f.name
    try:
        r = subprocess.run(["python3", yol], capture_output=True, text=True, timeout=timeout)
        cikti = r.stdout[-3000:].strip() or "(cikti yok)"
        hata = r.stderr[-1000:].strip()
        return (hata + "\n" if hata else "") + cikti if hata else cikti
    except Exception as e:
        return f"[Python hatasi: {e}]"
    finally:
        os.remove(yol)

def bash_kod(emir, timeout=20):
    try:
        r = subprocess.run(emir, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "")[-3000:] + (r.stderr or "")[-1000:]
    except Exception as e:
        return f"[Bash hatasi: {e}]"

def node_kod(kod, timeout=15):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(kod); yol = f.name
    try:
        r = subprocess.run(["node", yol], capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "")[-3000:] + (r.stderr or "")[-1000:]
    except Exception as e:
        return f"[Node hatasi: {e}]"