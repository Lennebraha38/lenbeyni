# Zenai Entegrasyon Matrisi

Binlerce açık kaynak repo tek "Arac Katmanı"nda toplandı. Yaklaşım:
**yerelde hafif, işlevsel özler** — şişman bağımlılık yok, her yerde çalışır.

## Yetenek → Kaynak (açık kaynak repo adları)

| Arac | Alan | Kaynak repo'lar |
|---|---|---|
| `araclar.arac_katmani.sayfa` | Web sayfası oku | browser-use, crawl4ai, firecrawl |
| `araclar.arac_katmani.web_ara` | Web ara | gpt-researcher, functions-cli |
| `araclar.arac_katmani.derin_arastirma` | Derin araştırma raporu | gpt-researcher, deep-research (langchain-ai) |
| `araclar.arac_katmani.komut` | Terminal komutu | OpenCLI, open-interpreter |
| `araclar.belgeler.belge` | PDF/CSV/JSON oku | pypdf, unstructured, pandas |
| `araclar.guvenlik.sifre` | Parola üret | awesome-cli, PassCli |
| `araclar.guvenlik.sifrele` | SHA-256 hash | OpenSSL benzeri |
| `araclar.kod_sandbox.python_kod` | Python sandbox | code-interpreter, OpenCodeInterpreter |
| `araclar.kod_sandbox.bash_kod` | Bash sandbox | OpenCLI, shell-gpt |
| `araclar.sistem.sistem_bilgi` | Sistem durumu | systeminformation |
| `araclar.sistem.dosyalar` | Dosya listesi | fzf benzeri |
| `araclar.git_hub.gh` | GitHub API | gh (GitHub CLI) |
| `araclar.haberler.rss` | RSS akışı | feedparser |
| `araclar.hava.hava_koordinat` | Hava durumu | open-meteo |
| `araclar.gorsel.fraktal_png` | Görsel üret | SVG/PNG üreticiler |
| `araclar.__init__.yonlendir` | Hepsi tek noktadan | Function calling (OpenAI/Anthropic tool use) |

## Ajan döngüsü tarafından tanınan komutlar
`[ARAMA]`, `[SITE]`, `[KOMUT]`, `[BELGE]`, `[PYTHON]`, `[BASH]`,
`[SISTEM]`, `[GITHUB]`, `[SIFRE]`, `[SIFRELE]`, `[RSS]`, `[LISTE]`

## Mimarisi
```
Kullanici → lenbeyni_zeka.ajan() → mega beyin (OpenRouter) → [KOMUT] çıktısı
        → arac katmani.yonlendir() → gercek islem → cevap → bellek
```