"""ZenAI Guvenlik Katmani.

Tum guvenlik kurallari tek yerde:
- SSRF onleme (url_guvenli / ip_ozel_mi)
- Komut bloklistesi (komut_tehlikeli)
- Python AST tabanli tehlikeli islem engelleme (python_tehlikeli)
- Dosya yolu kisiti (yorl_guvenli)
- Prompt injection bilgi kirligi tespiti (sinsilik_tespit)

Bu modul AGENTS.md/CODEOWNERS ne olursa olsun degismez kural setidir.
"""
import ipaddress, re, socket

# ── Basit sabitler ──
TEHLIKELI_KOMUT_KALIPLARI = [
    r"\brm\s+-rf\b", r"\bmkfs\b", r"\bdd\s+of=", r"\b>\/dev\/sd", r"\bif=/dev/",
    r"\bmknod\b", r"\bshutdown\b", r"\breboot\b", r"\bhalt\b", r"\bpoweroff\b",
    r"\bsudo\b", r"\bsu\s+-", r"\bchmod\s+777\b", r"\bchown\b", r"\bpasswd\b",
    r"\brmmod\b", r"\binsmod\b", r"\bwget.*\|.*sh\b", r"\bcurl.*\|.*sh\b",
    r"\bcurl.*\|.*bash\b", r"\bapt(-get)?\s+(install|purge|remove)\b",
    r"\bpip(\d|3)?\s+install\s+--(no-deps|force|upgrade)", r"\bdd\b.*\bbs=\b",
    r"\bgit\s+push\b", r"\bgit\s+remote\s+add\b", r"\bopenssl\s+genrsa\b",
    r"\bscp\b", r"\bssh\b", r"\bftp\b", r"\btelnet\b", r"\bnc\b|netcat",
    r"\bdocker\b", r"\bkubectl\b", r"\bterraform\b",
    r"(\.\.|;|&&|\|\|).*\./", r"\brm\s+-\S*[\d]*\s+/", r"dev/null.*\brm\b",
    r"\bkill\s+-9\b", r"\bkillall\b", r"\bwget\b\s+http", r"\bcurl\s+-k\b",
    r"/etc/\s*(passwd|shadow|sudoers|ssh)", r"\bsystemctl\b", r"\bservice\b",
    r"\bmount\b", r"\bumount\b", r"\bfdisk\b", r"\bparted\b",
]
TEHLIKELI_KOMUT_REGEX = re.compile(r"|".join(TEHLIKELI_KOMUT_KALIPLARI), re.I)

# Python AST bloklistesi
TEHLIKELI_ATTRLER = {
    "subprocess", "os.system", "os.popen", "os.spawn", "os.fork", "os.exec",
    "pty", "multiprocessing", "signal", "socket", "fcntl", "posix", "commands",
    "webbrowser", "smtplib", "ftplib", "telnetlib", "imaplib", "nntplib",
    "poplib", "xmlrpc", "cgi", "wsgiref",
}
TEHLIKELI_IMPORTLAR = {
    "socket", "subprocess", "multiprocessing", "threading", "pexpect", "pty",
    "fcntl", "signal", "mmap", "shutil", "pickle", "shelve", "marshal", "copy",
    "sqlite3", "importlib", "ctypes", "cffi", "base64", "hmac", "hashlib",
    "bcrypt", "sys", "atexit", "builtins",
}
# sys/builtins: üst düzey erişim için işlemi bloklamak istiyoruz; not: json, re vb. serbest
TEHLIKELI_CAGRILAR = {
    "system", "popen", "exec", "eval", "compile", "__import__", "input",
    "execfile", "globals", "locals", "vars", "open",
}

def ip_ozel_mi(host):
    """Host IP'si ozel/ic-alan (local, tutucu, CGNAT, multicast) ise True."""
    if not host:
        return True
    try:
        info = socket.getaddrinfo(host, None, socket.AF_INET)
    except Exception:
        try:
            info = socket.getaddrinfo(host, None, socket.AF_INET6)
        except Exception:
            return True  # cozumlenemiyor -> blokla
    for adres in info:
        ip = adres[4][0]
        a = ipaddress.ip_address(ip)
        if (a.is_private or a.is_loopback or a.is_link_local or a.is_multicast
                or a.is_reserved or a.is_unspecified):
            return True
        # CGNAT 100.64.0.0/10
        if a.version == 4 and ipaddress.ip_network("100.64.0.0/10").supernet_of(
                ipaddress.ip_network(f"{ip}/32")):
            return True
    return False

def url_guvenli(url):
    """SSRF onleme: sadece http/https, ozel/girilen alan ip'leri bloklanir."""
    from urllib.parse import urlparse
    if not url or len(url) > 2048:
        return False
    if "\x00" in url or " " in url:
        return False
    p = urlparse(url if "://" in url else "https://" + url)
    if p.scheme not in ("http", "https"):
        return False
    if p.username or p.password:
        return False
    if p.port and p.port not in (80, 443):
        return False
    host = p.hostname or ""
    # Protoxolo-relative / kisisellestirilmis
    if host in ("", "localhost", "127.0.0.1", "::1"):
        return False
    # Yildiz/rakam karmasina izin deme; IPv6 ve sayisal kontrol
    try:
        ipaddress.ip_address(host)  # dogrudan IP ise birak
    except ValueError:
        pass  # domain -> cozumlemede kontrol
    if ip_ozel_mi(host):
        return False
    return True

def yorl_guvenli(yol, kokler=None):
    """Dosya okuma/calistirmani izin verilen koklere sabitler (path traversal onleme)."""
    if not yol:
        return None
    import os
    boluk = yol.replace("\\", "/")
    if any(p == ".." for p in boluk.split("/")):
        return None  # traversal kodu reddet
    kokler = kokler or [
        os.getcwd(), os.path.expanduser("~/.zenai"),
        "/tmp", "/tmp/opencode", ".",
    ]
    tam = os.path.abspath(os.path.expanduser(yol))
    for kok in kokler:
        k = os.path.abspath(kok)
        if tam == k or tam.startswith(k + os.sep):
            return tam
    return None

def komut_tehlikeli(emir):
    """Bash/komut metni tehlikeli kalipla eslesiyor mu?"""
    if not emir or len(emir) > 5000:
        return True
    if TEHLIKELI_KOMUT_REGEX.search(emir):
        return True
    # ic ag hedefleyen ag araclari (SSRF benzeri)
    if re.search(r"\b(curl|wget|nc|ncat|telnet|ssh|ftp)\b.*(127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|169\.254\.|0\.0\.0\.0|localhost)", emir, re.I):
        return True
    # kritik dosya/kok erisimleri
    if re.search(r"(^|[\s;&|])(rm|mv|cp|chmod|chown|ln|touch)\s+\S*(/|\.\.)", emir):
        return True
    return False

def python_tehlikeli(kod):
    """AST ile tehlikeli import/cagri/attr analizi. Tehlikeli ise True."""
    import ast
    if not kod or len(kod) > 8000:
        return True
    try:
        agac = ast.parse(kod)
    except SyntaxError:
        return False  # syntax hatasi zaten sandbox'ta yakalanir; guvenlik icin sorun degil
    for dugum in ast.walk(agac):
        # from X import ... : hassas moduller
        if isinstance(dugum, ast.ImportFrom):
            if (dugum.module or "").split(".")[0] in TEHLIKELI_IMPORTLAR:
                return True
        if isinstance(dugum, ast.Import):
            if any((a.name or "").split(".")[0] in TEHLIKELI_IMPORTLAR for a in dugum.names):
                return True
        # os.system, os.popen, subprocess.* vb.
        if isinstance(dugum, ast.Attribute):
            nitel = dugum.attr
            if nitel in ("system", "popen", "spawn", "fork", "exec", "pipe", "Popen", "run", "call", "check_call", "check_output"):
                return True
        # Cagri seviyesi: eval( / exec( / __import__(
        if isinstance(dugum, ast.Call):
            hedef = dugum.func
            if isinstance(hedef, ast.Name) and hedef.id in TEHLIKELI_CAGRILAR:
                return True
            if isinstance(hedef, ast.Attribute) and hedef.attr in ("system", "popen", "exec", "eval"):
                return True
    return False

def sinsilik_tespit(metin):
    """Model ciktisinda/icerikte yaygin prompt-injection kaliplarini koku."""
    if not metin:
        return False
    kaliplar = [
        r"ignore(\s+all)?\s+(the\s+)?(previous|prior|above)\s+(instructions|prompts?)",
        r"system\s*prompt\s*(\=|\:|---)",
        r"you\s+are\s+now\s+(an?\s+)?\w+\s+without\s+(any\s+)?restrictions",
        r"reveal\s+(your\s+)?(system\s+)?(prompt|instructions)",
        r"disregard\s+(previous|prior)",
        r"do\s+not\s+follow\s+(the\s+)?(above|these|any)",
        r"print\s+(your|the)\s*(system)?\s*(prompt|instructions)",
        r"\[SYSTEM\]|\[BAZLAMA\]|\[OVERLAY\]|OTTHD_|H:\s*smartass",
        r"developer\s+mode\s+enabled",
        r"simulate\s+(an?\s+)?(unrestricted|jailbreak)",
        # Turkce kaliplar
        r"kuralları?\s*(ını|ı|in)\s*(yok\s*say|dikkate\s*alma|unut|salla|sil)",
        r"(onceki|önceki|tum|tüm)\s*(kurallar|talimatlar)\s*(ı|i|ü|u)?\s*(yok)\s*say",
        r"kısıtlama|kisitlama\s*(tanımıyorum|tanimiyorum|yok|yoktur|kaldır|kaldir)",
        r"sistem\s*(prompt|talimatit|talimatı)\s*(söyle|yaz|acıkla|açıkla|gor)",
        r"iki\s*kosullu|dual\s*mode",
    ]
    return any(re.search(k, metin, re.I) for k in kaliplar)