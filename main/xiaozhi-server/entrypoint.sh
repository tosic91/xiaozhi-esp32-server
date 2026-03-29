#!/bin/bash
# Replace placeholders with env vars
CONFIG_FILE="data/.config.yaml"
if [ -f "$CONFIG_FILE" ]; then
  if [ -n "$GEMINI_API_KEY" ]; then
    sed -i "s/__GEMINI_API_KEY__/$GEMINI_API_KEY/g" "$CONFIG_FILE"
  fi
  if [ -n "$GROQ_API_KEY" ]; then
    sed -i "s/__GROQ_API_KEY__/$GROQ_API_KEY/g" "$CONFIG_FILE"
  fi
  echo "✅ Config injected with API keys"
fi

# Start Caddy reverse proxy in background (listens on $PORT from Railway)
if command -v caddy &> /dev/null; then
  echo "🔄 Starting Caddy reverse proxy on port ${PORT:-8080}..."
  caddy start --config Caddyfile --adapter caddyfile 2>&1 &
  CADDY_PID=$!
  echo "✅ Caddy started (PID: $CADDY_PID)"
else
  echo "⚠️ Caddy not found, running without reverse proxy"
fi

# Start the Python app (WS on 8000, HTTP on 8001)
exec python app.py
