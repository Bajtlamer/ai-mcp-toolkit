#!/bin/bash
# Development server with hot reload

cd "$(dirname "$0")"

echo "🚀 Starting AI MCP Toolkit development server..."
echo "📝 Changes to source code will auto-reload"
echo ""

# Run with uvicorn directly for hot reload
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
python3 -m uvicorn ai_mcp_toolkit.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info
