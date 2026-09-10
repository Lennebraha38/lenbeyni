#!/bin/bash
# Arka plan calismasi icin LATIF_AUTORUN.sh
# Rate limit (00:00 UTC) acilana kadar 60sn'de bir bekler,
# sonra tam_zirve.py --soru 50 baslatir.
cd /tmp/opencode/lenbeyni
if [ -z "$OPENROUTER_KEY" ]; then
  echo "[HATA] OPENROUTER_KEY ortam degiskeni yok. Ornek: export OPENROUTER_KEY='sk-or-v1-...'"
  exit 1
fi

echo "[$(date)] Bekleme basladi: rate limit 00:00 UTC'de acilacak"
while true; do
  SONUC=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 \
    -X POST https://openrouter.ai/api/v1/chat/completions \
    -H "Authorization: Bearer $OPENROUTER_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model":"dots-studio/dots-3-note-preview:free","messages":[{"role":"user","content":"ping"}],"max_tokens":5}')
  if [ "$SONUC" = "200" ]; then
    echo "[$(date)] Rate limit acildi! Test baslatiliyor..."
    python3 agentv2/tam_zirve.py --soru 50 2>&1
    echo "[$(date)] Test TAMAMLANDI (exit: $?)"
    exit 0
  fi
  echo "[$(date)] Hala kapali (HTTP $SONUC), 60sn sonra tekrar denenecek..."
  sleep 60
done