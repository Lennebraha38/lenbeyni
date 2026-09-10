"""GitHub / Git islemleri. (gh cli + git)"""
import subprocess, json

def gh(soru):
    """gh CLI denemesi"""
    try:
        r = subprocess.run(["gh", "api", "search/repositories", "-q", "q=" + soru.replace(" ", "+"), "-f", "per_page=5"],
                           capture_output=True, text=True, timeout=15)
        return r.stdout[:2000] or r.stderr[:500]
    except Exception as e:
        return f"[gh hata: {e}]"

def git_log(yol):
    try:
        r = subprocess.run(["git", "-C", yol, "log", "--oneline", "-15"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout
    except Exception as e:
        return f"[git hata: {e}]"

def repo_bilgi(soru):
    destek = gh(soru)
    return destek or "[GitHub aranacak]"

def git_komut(emir):
    try:
        r = subprocess.run(emir.split(), capture_output=True, text=True, timeout=20)
        return (r.stdout or "")[:2000] + (r.stderr or "")[:500]
    except Exception as e:
        return f"[hata: {e}]"