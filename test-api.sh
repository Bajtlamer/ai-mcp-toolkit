#!/bin/bash

# Test script for AI MCP Toolkit API endpoints
echo "🧪 Testing AI MCP Toolkit API Endpoints"
echo "======================================="

# Test 1: MCP Server Health
echo "1. Testing MCP Server (localhost:8000)..."
MCP_HEALTH=$(curl -s http://localhost:8000/health)
if echo "$MCP_HEALTH" | grep -q "healthy"; then
    echo "   ✅ MCP Server is healthy"
else
    echo "   ❌ MCP Server is not responding"
fi

# Test 2: Chat Completion
echo "2. Testing Chat API..."
CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Say hello in one sentence"}],"model":"qwen2.5:7b","temperature":0.1,"max_tokens":50}')

if echo "$CHAT_RESPONSE" | grep -q "choices"; then
    echo "   ✅ Chat API is working"
    CONTENT=$(echo "$CHAT_RESPONSE" | jq -r '.choices[0].message.content' 2>/dev/null || echo "Could not parse content")
    echo "   📝 Response: $CONTENT"
    TOKENS_PER_SEC=$(echo "$CHAT_RESPONSE" | jq -r '.usage.tokens_per_second' 2>/dev/null || echo "N/A")
    echo "   ⚡ Speed: $TOKENS_PER_SEC tokens/sec"
else
    echo "   ❌ Chat API is not working"
fi

# Test 3: Model Status
echo "3. Testing Model Status..."
ollama ps
echo ""

# Test 4: GPU Status
echo "4. Testing GPU Status..."
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits

echo ""
echo "🏁 API Test Complete"