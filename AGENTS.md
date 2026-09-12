# Kural (kullanıcı ile anlaşma)

- **Her değişiklik commit + push edilir.** Bu repoda yapılan her düzenleme,
  dosya ekleme, test/derleme düzeltmesi veya döküman güncellemesi bitecekleri
  noktada ayrı bir commit ile `origin/main`'e pushlanır.
- Commit mesajı kısa ve tanımlayıcı olur (mevcut `P*:` / `fix:` stili).
- Gereksiz dosyalar commit'e girmez (bkz. `.gitignore`: SQLite WAL, anahtar
  dosyaları, sanal ortamlar, `__pycache__`).
- Koşulsuz: "görevi tamamladım" diyorsam değişiklik zaten pushlanmış olmalı.