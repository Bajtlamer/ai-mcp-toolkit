#!/bin/bash

echo "🔄 Restarting AI MCP Toolkit servers..."

# Find and kill existing processes
echo "Stopping existing servers..."
pkill -f "python.*main.py" || true
pkill -f "npm.*run.*dev" || true
sleep 2

echo "✅ Servers stopped"
echo ""
echo "To start the servers again, run:"
echo "  Backend:  python main.py"
echo "  Frontend: cd ui && npm run dev"
