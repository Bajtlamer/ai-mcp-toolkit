#!/bin/bash

# AI MCP Toolkit Startup Script
echo "🚀 Starting AI MCP Toolkit..."

# Activate virtual environment
source venv/bin/activate

# Check if MCP server should start
if [ "$1" = "server" ]; then
    echo "Starting MCP server on port 8000..."
    ai-mcp-toolkit serve
elif [ "$1" = "ui" ]; then
    echo "Starting Svelte UI on port 5173..."
    cd ui && npm run dev
elif [ "$1" = "both" ]; then
    echo "Starting both MCP server and UI..."
    echo "MCP Server will start on port 8000"
    echo "UI will start on port 5173"
    echo ""
    
    # Start MCP server in background
    ai-mcp-toolkit serve &
    
    # Start UI in foreground
    cd ui && npm run dev
else
    echo "Usage: $0 [server|ui|both]"
    echo ""
    echo "Options:"
    echo "  server  - Start only the MCP server"
    echo "  ui      - Start only the Svelte UI"
    echo "  both    - Start both server and UI"
    echo ""
    echo "Examples:"
    echo "  ./start.sh server"
    echo "  ./start.sh ui"
    echo "  ./start.sh both"
fi
