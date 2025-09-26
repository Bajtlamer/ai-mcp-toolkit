#!/bin/bash

# Keep the configured AI model warm and loaded in GPU memory
# This prevents cold start delays and survives sleep/wake cycles

# Read model from .env file or use fallback
if [ -f ".env" ]; then
    MODEL=$(grep "^OLLAMA_MODEL=" .env | cut -d'=' -f2 | tr -d '"')
fi

# Fallback to default if not found
if [ -z "$MODEL" ]; then
    MODEL="qwen2.5:7b"
fi

KEEP_ALIVE="24h"  # Keep loaded for 24 hours (maximum supported)
PING_INTERVAL=900  # Ping every 15 minutes (900 seconds)

echo "🔥 Starting persistent model keep-alive for: $MODEL"
echo "📊 Ping interval: ${PING_INTERVAL}s ($(($PING_INTERVAL/60)) minutes)"
echo "⏰ Keep-alive setting: $KEEP_ALIVE"

# Function to load model with retry logic
load_model() {
    local retries=3
    local count=0
    
    while [ $count -lt $retries ]; do
        echo "$(date): Loading $MODEL (attempt $((count+1))/$retries)..."
        
        # Use a more reliable method to load the model
        if echo "Hello" | ollama run $MODEL --keepalive $KEEP_ALIVE >/dev/null 2>&1; then
            echo "$(date): ✅ Model $MODEL loaded successfully"
            return 0
        else
            echo "$(date): ❌ Failed to load model $MODEL (attempt $((count+1)))"
            count=$((count+1))
            sleep 5
        fi
    done
    
    echo "$(date): 🚨 Failed to load model after $retries attempts"
    return 1
}

# Function to check if model is loaded
check_model_loaded() {
    ollama ps | grep -q "$MODEL"
}

# Initial load
load_model

# Keep-alive loop
while true; do
    if check_model_loaded; then
        echo "$(date): ✅ Model $MODEL is loaded and ready"
        # Send lightweight ping to maintain keep-alive
        echo "ping" | ollama run $MODEL --keepalive $KEEP_ALIVE >/dev/null 2>&1
    else
        echo "$(date): ⚠️  Model $MODEL not loaded, attempting to reload..."
        load_model
    fi
    
    # Wait before next check
    sleep $PING_INTERVAL
done
