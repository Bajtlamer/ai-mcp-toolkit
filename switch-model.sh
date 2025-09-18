#!/bin/bash

# AI MCP Toolkit - Model Switcher
# Usage: ./switch-model.sh [model_name]

echo "🤖 AI MCP Toolkit - Model Manager"
echo "=================================="

# Function to show current status
show_status() {
    echo "📊 Current Status:"
    echo "==================="
    
    # Show running models
    echo "🔄 Running models:"
    ollama ps
    echo
    
    # Show what the app sees
    echo "🌐 App detects:"
    if curl -s http://localhost:5173/api/gpu/health >/dev/null 2>&1; then
        APP_MODEL=$(curl -s http://localhost:5173/api/gpu/health | jq -r '.ollama_model // "None"')
        GPU_ACCEL=$(curl -s http://localhost:5173/api/gpu/health | jq -r '.ollama_gpu_accelerated // false')
        echo "   Model: $APP_MODEL"
        echo "   GPU Accelerated: $GPU_ACCEL"
    else
        echo "   ❌ App not running or not accessible"
    fi
    echo
}

# Function to list available models
list_models() {
    echo "📦 Available models:"
    echo "===================="
    ollama list
    echo
}

# Function to switch model
switch_model() {
    local target_model="$1"
    
    echo "🔄 Switching to model: $target_model"
    echo "====================================="
    
    # Stop all running models
    echo "⏹️  Stopping current models..."
    ollama ps --format json 2>/dev/null | jq -r '.[].name' 2>/dev/null | while read -r model; do
        if [[ -n "$model" && "$model" != "null" ]]; then
            echo "   Stopping: $model"
            ollama stop "$model" >/dev/null 2>&1
        fi
    done
    
    # Start the target model
    echo "▶️  Starting model: $target_model"
    echo "Hello" | ollama run "$target_model" >/dev/null 2>&1 &
    
    # Wait a moment for it to load
    echo "⏳ Loading model..."
    sleep 5
    
    echo "✅ Model switch complete!"
    echo
    show_status
}

# Main logic
if [[ $# -eq 0 ]]; then
    # No arguments - show status and available models
    show_status
    list_models
    
    echo "💡 Usage examples:"
    echo "   ./switch-model.sh qwen2.5:7b     # Switch to Qwen 2.5 7B"
    echo "   ./switch-model.sh qwen2.5:14b    # Switch to Qwen 2.5 14B"
    echo "   ./switch-model.sh llama3.1:8b    # Switch to Llama 3.1 8B"
    echo "   ./switch-model.sh llama3.2:3b    # Switch to Llama 3.2 3B"
    echo
else
    # Model name provided - switch to it
    target_model="$1"
    
    # Check if model exists
    if ollama list | grep -q "^$target_model"; then
        switch_model "$target_model"
    else
        echo "❌ Model '$target_model' not found!"
        echo
        list_models
        echo "💡 Use one of the models listed above."
    fi
fi