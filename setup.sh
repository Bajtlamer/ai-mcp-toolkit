#!/bin/bash

# AI MCP Toolkit Setup Script
echo "🤖 AI MCP Toolkit Setup"
echo "======================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python 3.11+ is installed
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.11 or later.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then 
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}Python $PYTHON_VERSION found, but version 3.11+ is required${NC}"
    exit 1
fi

# Check if Node.js is installed for UI
echo -e "${BLUE}Checking Node.js version...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Warning: Node.js not found. UI will not be available.${NC}"
    echo "Install Node.js 18+ to use the web interface."
else
    NODE_VERSION=$(node -v | cut -d'v' -f2)
    echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"
fi

# Create virtual environment
echo -e "${BLUE}Creating Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -e .
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Install UI dependencies if Node.js is available
if command -v node &> /dev/null; then
    echo -e "${BLUE}Installing UI dependencies...${NC}"
    cd ui
    npm install
    echo -e "${GREEN}✓ UI dependencies installed${NC}"
    cd ..
fi

# Check if Ollama is installed
echo -e "${BLUE}Checking for Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama found${NC}"
    
    # Check if a model is available
    if ollama list | grep -q "llama3.2:3b"; then
        echo -e "${GREEN}✓ Default model (llama3.2:3b) is available${NC}"
    else
        echo -e "${YELLOW}Default model not found. Pulling llama3.2:3b...${NC}"
        ollama pull llama3.2:3b
        echo -e "${GREEN}✓ Default model downloaded${NC}"
    fi
else
    echo -e "${RED}Ollama not found!${NC}"
    echo "Please install Ollama from https://ollama.ai/"
    echo "After installing Ollama, run: ollama pull llama3.2:3b"
fi

# Create default configuration
echo -e "${BLUE}Creating default configuration...${NC}"
if [ ! -f "$HOME/.ai-mcp-toolkit/config.yaml" ]; then
    python3 -c "from src.ai_mcp_toolkit.utils.config import create_default_config; create_default_config()"
    echo -e "${GREEN}✓ Default configuration created at $HOME/.ai-mcp-toolkit/config.yaml${NC}"
else
    echo -e "${YELLOW}Configuration already exists${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo -e "${BLUE}Quick Start:${NC}"
echo "1. Start the MCP server:"
echo -e "   ${YELLOW}ai-mcp-toolkit serve${NC}"
echo ""
if command -v node &> /dev/null; then
    echo "2. In another terminal, start the UI:"
    echo -e "   ${YELLOW}cd ui && npm run dev${NC}"
    echo ""
    echo "3. Open http://localhost:5173 in your browser"
    echo ""
fi
echo "4. Or use the CLI directly:"
echo -e "   ${YELLOW}ai-mcp-toolkit analyze 'Hello world!'${NC}"
echo -e "   ${YELLOW}ai-mcp-toolkit anonymize 'John Doe at john@email.com'${NC}"
echo ""
echo -e "${BLUE}Using Docker:${NC}"
echo -e "   ${YELLOW}docker-compose up -d${NC}"
echo ""
echo -e "${BLUE}For help:${NC}"
echo -e "   ${YELLOW}ai-mcp-toolkit --help${NC}"
echo ""
echo -e "${GREEN}Happy text processing! 🚀${NC}"
