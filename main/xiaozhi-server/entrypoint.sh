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
export PORT="${PORT:-8080}"
echo "🔄 Starting Caddy on port $PORT..."
if command -v caddy &> /dev/null; then
  # Start Caddy and wait for it to be ready
  caddy start --config Caddyfile --adapter caddyfile 2>&1
  CADDY_EXIT=$?
  if [ $CADDY_EXIT -eq 0 ]; then
    echo "✅ Caddy started successfully on port $PORT"
    sleep 1  # Give Caddy time to bind
  else
    echo "❌ Caddy failed to start (exit code: $CADDY_EXIT)"
    echo "⚠️ Falling back to direct app on port $PORT"
    # If Caddy fails, make Python app listen on PORT directly
    # Update config to use PORT for websocket
    if [ -f "$CONFIG_FILE" ]; then
      sed -i "s/port: 8000/port: $PORT/" "$CONFIG_FILE"
    fi
  fi
else
  echo "⚠️ Caddy not found, Python app will listen on port 8000"
fi

# Start the Python app (WS on 8000, HTTP on 8001 when Caddy is fronting)
exec python app.py
