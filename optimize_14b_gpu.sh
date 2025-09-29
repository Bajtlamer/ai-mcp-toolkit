#!/bin/bash

# Optimize 14B model for RTX 3070 Ti (8GB VRAM)
# This script tries different configurations to maximize GPU acceleration

echo "🚀 Optimizing qwen2.5:14b for your RTX 3070 Ti..."

# Stop any running Ollama processes
echo "Stopping existing Ollama processes..."
pkill -f ollama 2>/dev/null || true
sleep 2

# Start Ollama with optimized settings for your 8GB GPU
echo "Starting Ollama with GPU optimizations..."

# Set environment variables for maximum GPU utilization
export OLLAMA_HOST="0.0.0.0"
export OLLAMA_NUM_GPU=1                    # Use single GPU
export OLLAMA_GPU_LAYERS=40                # Try loading more layers on GPU
export OLLAMA_MAX_VRAM=7500                # Reserve 7.5GB for model (leave 0.5GB buffer)
export OLLAMA_FLASH_ATTENTION=1            # Enable flash attention for memory efficiency
export OLLAMA_NUM_CTX=4096                 # Reduce context length to save memory

# Start Ollama server in background
nohup ollama serve > /dev/null 2>&1 &
sleep 3

echo "⏳ Loading qwen2.5:14b with optimized GPU settings..."

# Load the model with optimization
ollama run qwen2.5:14b "" > /dev/null 2>&1

# Test performance
echo "🧪 Testing GPU acceleration..."
echo "Running performance test..."

# Test with a simple prompt
time_output=$(ollama run qwen2.5:14b "Hi! Please respond with exactly 50 words." 2>&1)

echo "✅ Model loaded! Here's the performance:"
echo "$time_output" | grep -E "(eval rate|tokens/s|duration)"

echo ""
echo "💡 Tips for better performance:"
echo "1. Close unnecessary applications to free up GPU memory"
echo "2. Use shorter prompts when possible"  
echo "3. Consider using qwen2.5:7b for faster responses"
echo "4. Monitor GPU usage with: watch -n 1 nvidia-smi"

echo ""
echo "🔍 Current GPU status:"
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits