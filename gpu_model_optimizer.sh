#!/bin/bash

# GPU Model Optimizer for NVIDIA RTX 3070 Ti (8GB VRAM)
# Helps optimize large language models for your specific GPU

echo "🎯 GPU Model Optimizer for RTX 3070 Ti (8GB VRAM)"
echo "=================================================="

# Function to check GPU memory
check_gpu_memory() {
    local memory_info=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits)
    local used=$(echo $memory_info | cut -d',' -f1 | tr -d ' ')
    local total=$(echo $memory_info | cut -d',' -f2 | tr -d ' ')
    local available=$((total - used))
    
    echo "GPU Memory: ${used}MB used / ${total}MB total (${available}MB available)"
    
    if [ $available -lt 6000 ]; then
        echo "⚠️  Warning: Less than 6GB available. Close some applications for better performance."
    fi
    
    return $available
}

# Function to test model performance
test_model_performance() {
    local model=$1
    echo "🧪 Testing $model performance..."
    
    local test_output=$(timeout 30 ollama run $model "Hi, respond with exactly 20 words." 2>&1)
    local eval_rate=$(echo "$test_output" | grep "eval rate" | grep -o '[0-9.]*' | head -1)
    
    if [ -n "$eval_rate" ]; then
        local rate_num=$(echo $eval_rate | cut -d'.' -f1)
        echo "📊 Performance: ${eval_rate} tokens/s"
        
        if [ "$rate_num" -gt 20 ]; then
            echo "✅ Excellent GPU acceleration!"
        elif [ "$rate_num" -gt 10 ]; then
            echo "⚡ Good GPU acceleration"
        else
            echo "🐌 Poor performance - likely CPU fallback"
        fi
    else
        echo "❌ Could not measure performance"
    fi
}

# Function to optimize Ollama settings
optimize_ollama() {
    echo "⚙️  Optimizing Ollama settings for RTX 3070 Ti..."
    
    # Stop existing Ollama
    pkill -f ollama 2>/dev/null || true
    sleep 2
    
    # Set optimal environment variables
    export OLLAMA_HOST="0.0.0.0"
    export OLLAMA_NUM_GPU=1
    export OLLAMA_MAX_VRAM=7000           # Leave 1GB buffer for system
    export OLLAMA_FLASH_ATTENTION=1       # Memory efficiency
    
    # Start optimized Ollama
    nohup ollama serve > ollama_optimized.log 2>&1 &
    sleep 3
    
    echo "✅ Ollama restarted with GPU optimizations"
}

echo ""
echo "1️⃣  Checking current GPU status..."
check_gpu_memory

echo ""
echo "2️⃣  Available models analysis:"
echo ""

# Check available models
models=("qwen2.5:7b" "qwen2.5:14b" "qwen2.5-coder:7b" "llama3.1:8b")

for model in "${models[@]}"; do
    if ollama list | grep -q "$model"; then
        local size=$(ollama list | grep "$model" | awk '{print $3, $4}')
        echo "✅ $model ($size) - Available"
        
        # Show recommendation based on size
        if [[ $model == *"14b"* ]]; then
            echo "   💡 Large model - may need optimization for 8GB GPU"
        elif [[ $model == *"7b"* ]] || [[ $model == *"8b"* ]]; then
            echo "   🚀 Optimal size for RTX 3070 Ti"
        fi
    else
        echo "❌ $model - Not installed"
    fi
done

echo ""
echo "3️⃣  Recommendations for your RTX 3070 Ti (8GB VRAM):"
echo ""
echo "🥇 BEST PERFORMANCE (Fast & GPU accelerated):"
echo "   • qwen2.5:7b - Excellent balance of quality and speed"
echo "   • qwen2.5-coder:7b - Best for coding tasks"
echo "   • llama3.1:8b - Alternative high-quality option"
echo ""
echo "🥈 ACCEPTABLE (May need optimization):"
echo "   • qwen2.5:14b - Higher quality but slower, needs tuning"
echo ""
echo "🥉 MEMORY OPTIMIZATIONS for 14B model:"
echo "   1. Close browser tabs and unnecessary applications"
echo "   2. Reduce context length (OLLAMA_NUM_CTX=2048)"
echo "   3. Use shorter conversation histories"
echo "   4. Enable memory optimizations"

echo ""
read -p "🔧 Would you like to optimize settings for qwen2.5:14b? (y/n): " optimize_choice

if [[ $optimize_choice == "y" || $optimize_choice == "Y" ]]; then
    echo ""
    echo "4️⃣  Optimizing for qwen2.5:14b..."
    optimize_ollama
    
    echo "Loading and testing qwen2.5:14b..."
    # Pre-load the model
    ollama run qwen2.5:14b "" > /dev/null 2>&1
    
    echo ""
    check_gpu_memory
    test_model_performance "qwen2.5:14b"
    
    echo ""
    echo "📝 To make these optimizations permanent, add to your .env file:"
    echo "OLLAMA_MAX_VRAM=7000"
    echo "OLLAMA_FLASH_ATTENTION=1"
    echo "OLLAMA_NUM_CTX=4096"
fi

echo ""
echo "🎯 SUMMARY:"
echo "• For best GPU acceleration: Use qwen2.5:7b or llama3.1:8b"
echo "• For highest quality: Use qwen2.5:14b with optimizations"
echo "• Monitor with: watch -n 2 nvidia-smi"
echo "• Switch models easily: ollama run [model_name]"

echo ""
echo "✅ Optimization complete!"