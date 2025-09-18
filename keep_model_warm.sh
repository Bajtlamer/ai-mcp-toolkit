#!/bin/bash

# Keep the Qwen2.5 14B model warm and loaded in GPU memory
# This prevents cold start delays

MODEL="qwen2.5:14b"
KEEP_ALIVE="60m"  # Keep loaded for 60 minutes

echo "🔥 Keeping $MODEL warm and loaded..."

while true; do
    echo "$(date): Pinging $MODEL to keep it loaded..."
    
    # Send a lightweight request to keep the model active
    ollama run $MODEL --keepalive $KEEP_ALIVE "Hi" >/dev/null 2>&1
    
    # Wait 25 minutes before next ping (before the 30min timeout)
    sleep 1500
done