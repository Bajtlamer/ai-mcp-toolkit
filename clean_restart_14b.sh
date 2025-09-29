#!/bin/bash

echo "🧹 Cleaning up for optimal 14B model performance on RTX 3070 Ti"
echo "========================================================"

# Step 1: Stop all Ollama processes
echo "1️⃣ Stopping all Ollama processes..."
sudo pkill -f ollama
sleep 3

# Step 2: Clear GPU memory
echo "2️⃣ Checking GPU memory after cleanup..."
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits

# Step 3: Set optimal environment variables for 14B model
echo "3️⃣ Setting RTX 3070 Ti optimizations..."
export OLLAMA_HOST="0.0.0.0"
export OLLAMA_NUM_GPU=1
export OLLAMA_MAX_VRAM=7500          # Use 7.5GB of 8GB (leave 512MB buffer)
export OLLAMA_FLASH_ATTENTION=1      # Memory efficiency
export OLLAMA_NUM_CTX=3072          # Reduce context to save memory
export OLLAMA_NUMA=false             # Disable NUMA for single GPU

# Step 4: Start fresh Ollama with optimizations
echo "4️⃣ Starting optimized Ollama server..."
nohup ollama serve > ollama_14b_optimized.log 2>&1 &
sleep 5

echo "5️⃣ Loading qwen2.5:14b with GPU optimizations..."
# Pre-load the model to GPU
ollama run qwen2.5:14b "Hi" > /dev/null 2>&1

echo "6️⃣ Performance test..."
echo "Running GPU acceleration test..."

# Test performance
result=$(timeout 15 ollama run qwen2.5:14b "Hello! Please respond with exactly 30 words about GPU acceleration." 2>&1)

# Extract performance metrics
eval_rate=$(echo "$result" | grep "eval rate" | grep -o '[0-9.]*' | head -1)
gpu_usage=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)
memory_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)

echo ""
echo "📊 PERFORMANCE RESULTS:"
echo "================================"
if [ -n "$eval_rate" ]; then
    echo "🚀 Speed: $eval_rate tokens/second"
    
    rate_num=$(echo $eval_rate | cut -d'.' -f1)
    if [ "$rate_num" -gt 15 ]; then
        echo "✅ EXCELLENT! GPU acceleration is working well"
        echo "🎯 Your 14B model is properly GPU accelerated!"
    elif [ "$rate_num" -gt 8 ]; then
        echo "⚡ GOOD! Partial GPU acceleration"
        echo "💡 Consider closing more applications for better performance"
    else
        echo "🐌 SLOW! Likely CPU fallback"
        echo "❌ GPU memory insufficient - try 7B model instead"
    fi
else
    echo "❌ Could not measure performance - check logs"
fi

echo "💾 GPU Memory Used: ${memory_used}MB / 8192MB"
echo "⚡ GPU Utilization: ${gpu_usage}%"

echo ""
echo "💡 TIPS FOR BEST PERFORMANCE:"
echo "• Close web browsers and unnecessary applications"
echo "• Use shorter conversation histories"
echo "• Monitor with: watch -n 1 nvidia-smi"
echo "• For fastest performance, use qwen2.5:7b instead"

echo ""
echo "✅ Optimization complete! Your 14B model should now have better GPU acceleration."