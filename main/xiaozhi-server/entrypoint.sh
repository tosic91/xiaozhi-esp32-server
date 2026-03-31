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

# Start the Python app (HTTP+WS proxy on port 8000, internal WS on 8001)
exec python app.py
