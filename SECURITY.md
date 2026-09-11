# ZenAI Güvenlik Politikası

ZenAI, kod çalıştırma, web erişimi, dosya okuma ve uzak MCP uçlarına bağlanma
yetenekleri olan bir asistan olduğundan, çok katmanlı güvenlik kuralları uygular.
Bu kurallar **varsayılan olarak reddet** (`deny-by-default`) ilkesine dayanır.

## Risk Modeli

| Vektör | Kötü senaryo | Savunma |
|---|---|---|
| Kod çalıştırma | Ajan/LLM çıktısındaki kod `os.system`, `socket`, `eval` çalıştırır | `agentv2/guvenlik.py` AST bloğu + temp cwd + RLIMIT + izole env |
| Shell | `[KOMUT]` etiketi `rm -rf /`, borulu indirme vb. çalıştırır | `komut_tehlikeli()` blok listesi (RCE/SYSDF hold kalıpları) |
| SSRF | Kullanıcı `uc` (MCP uç noktası) alanına iç ağ/metadata adresi verir, sunucu tarafından fetch edilir | `web/api/mcp.js` DNS çözümleme + özel IP kontrolü |
| Path traversal | `[BELGE]`/`[LISTE]` ile `/etc/passwd` veya `..` içeren yol okunur | `yorl_guvenli()` izinli kök listesi + `..` engeli |
| Prompt injection | Dış içerik sistem promptunu override eder | `sinsilik_tespit()` (EN+TR kalıplar) + araç girdileri yine de tekil olarak doğrulanır |

## Güvenlik Katmanları

### 1. Python/Node sandbox'ı (`agentv2/araclar/kod_sandbox.py`)
- Kodu çalıştırmadan önce `python_tehlikeli()` (AST analizi) ile taranır:
  tehlikeli importlar (`socket`, `subprocess`, `pickle`, `ctypes`, ...), tehlikeli
  attr/çağrılar (`system`, `popen`, `Popen`, `run`, `eval`, `exec`, `open`, ...).
- Çalıştırma `python3 -I` (izole mod), geçici dizin, temiz `PATH`/`HOME`,
  `RLIMIT_CPU=5s` ve `RLIMIT_AS=512MB` kısıtlarıyla yapılır.
- Bash: `komut_tehlikeli()` blok listesi; boru indirme, `sudo`, `git push`,
  iç ağ hedefli `curl/wget`, kritik dosya işlemleri engellenir.
- Not: Bu izolasyon **beta** seviyesindedir. Koşulan koda karşı tam koruma için
  Docker/gVisor/Firecracker gereklidir.

### 2. Ağ erişimi (SSRF koruması)
- Python tarafı `agentv2/guvenlik.py#url_guvenli`:
  sadece `http/https`, port 80/443, özel/loopback/link-local/CGNAT/multicast
  IP'ler DNS çözümlemesi dahil engellenir.
- JS tarafı `web/api/mcp.js`: protokol + port + kimlik bilgisi doğrulama ve
  `dns.lookup` ile çözümlenen adresin özel ağ kontrolü.

### 3. Dosya erişimi (`yorl_guvenli`)
Yalnızca proje kökü (cwd), `~/.zenai` ve `/tmp` altı okunabilir; `..` içeren
yollar reddedilir; mutlak kritik yollar (`/etc`, `/root`, ...) bloklanır.

### 4. Anahtar yönetimi
- `OPENROUTER_KEY` yalnızca Vercel env'inde; `web/api/chat.js` sunucu tarafında
  kullanılır, tarayıcıya asla dönmez.
- Geliştirici modunda kullanıcı kendi key'ini `localStorage`'a koyar; bu key
  istemciden istemciye kalmaz ve sunucuya gönderilmez.
- `.env*` dosyaları `.gitignore` içindedir; anahtar repo'ya işlenmez.

## Sorumlu Açıklama (Responsible Disclosure)

Bir güvenlik açığında:
1. `README.md`'deki proje sahibiyle iletişime geçin (açığı **yayından önce** paylaşmayın),
2. Açığın kanıtını (PoC), etkilenen sürümü ve önerilen düzeltmeyi ekleyin.

Her açık için sıralama: (a) düzelt, (b) regresyon testi yaz, (c) bu bölümü
`.github/workflows/ci.yml`'deki güvenlik adımlarıyla doğrula.

## Testler

```bash
python3 -m pytest tests/test_guvenlik.py -q   # tüm güvenlik kuralları
python3 -m pytest tests/ -q                    # tüm paket (41 test)
```

CI'ta ayrıca `pip-audit` (bağımlılık CVE) ve `npm audit` çalışır.