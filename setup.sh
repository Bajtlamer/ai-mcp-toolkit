#!/bin/bash

# AI MCP Toolkit Cross-Platform Setup Script
echo "🤖 AI MCP Toolkit Cross-Platform Setup"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global variables
PLATFORM=""
ARCH=""
GPU_TYPE=""
PYTHON_CMD=""
OLLAMA_MODEL=""
CONFIG_SUFFIX=""

# Function to detect operating system and architecture
detect_environment() {
    echo -e "${CYAN}🔍 Detecting environment...${NC}"
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        PLATFORM="linux"
        if command -v lsb_release &> /dev/null; then
            DISTRO=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
            echo -e "${GREEN}✓ Linux ($DISTRO) detected${NC}"
        else
            echo -e "${GREEN}✓ Linux detected${NC}"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
        echo -e "${GREEN}✓ macOS detected${NC}"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        PLATFORM="windows"
        echo -e "${GREEN}✓ Windows detected${NC}"
    else
        echo -e "${RED}❌ Unsupported operating system: $OSTYPE${NC}"
        exit 1
    fi
    
    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64|amd64)
            ARCH="x86_64"
            ;;
        aarch64|arm64)
            ARCH="arm64"
            ;;
        *)
            echo -e "${YELLOW}⚠️  Architecture $ARCH detected, may need manual configuration${NC}"
            ;;
    esac
    echo -e "${GREEN}✓ Architecture: $ARCH${NC}"
    
    # Detect GPU
    detect_gpu
    
    # Set configuration suffix based on platform and GPU
    CONFIG_SUFFIX="${PLATFORM}"
    if [[ -n "$GPU_TYPE" ]]; then
        CONFIG_SUFFIX="${PLATFORM}-${GPU_TYPE}"
    fi
    
    echo -e "${PURPLE}📊 Environment Summary:${NC}"
    echo -e "   Platform: ${YELLOW}$PLATFORM${NC}"
    echo -e "   Architecture: ${YELLOW}$ARCH${NC}"
    echo -e "   GPU: ${YELLOW}$GPU_TYPE${NC}"
    echo -e "   Config Profile: ${YELLOW}$CONFIG_SUFFIX${NC}"
}

# Function to detect GPU capabilities
detect_gpu() {
    echo -e "${CYAN}🎮 Detecting GPU capabilities...${NC}"
    
    if [[ "$PLATFORM" == "linux" ]]; then
        # Check for NVIDIA GPU
        if command -v nvidia-smi &> /dev/null; then
            GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>/dev/null | head -1)
            if [[ -n "$GPU_INFO" ]]; then
                GPU_TYPE="nvidia"
                echo -e "${GREEN}✓ NVIDIA GPU detected: $GPU_INFO${NC}"
                return
            fi
        fi
        
        # Check for AMD GPU
        if lspci | grep -i "vga.*amd\|vga.*radeon" &> /dev/null; then
            GPU_TYPE="amd"
            echo -e "${GREEN}✓ AMD GPU detected${NC}"
            return
        fi
        
        # Check for Intel GPU
        if lspci | grep -i "vga.*intel" &> /dev/null; then
            GPU_TYPE="intel"
            echo -e "${YELLOW}⚠️  Intel GPU detected (limited AI acceleration)${NC}"
            return
        fi
        
    elif [[ "$PLATFORM" == "macos" ]]; then
        # Check for Apple Silicon
        if [[ "$ARCH" == "arm64" ]]; then
            # Check for M1/M2/M3/M4 chips
            CHIP_INFO=$(system_profiler SPHardwareDataType | grep "Chip:" | awk '{print $2}')
            if [[ "$CHIP_INFO" =~ ^Apple ]]; then
                GPU_TYPE="apple-silicon"
                echo -e "${GREEN}✓ Apple Silicon detected: $CHIP_INFO${NC}"
                return
            fi
        fi
        
        # Check for discrete GPU on Intel Macs
        if system_profiler SPDisplaysDataType | grep -i "radeon\|nvidia" &> /dev/null; then
            GPU_TYPE="discrete"
            echo -e "${GREEN}✓ Discrete GPU detected${NC}"
            return
        fi
        
    elif [[ "$PLATFORM" == "windows" ]]; then
        # Windows GPU detection would require different approach
        # For now, assume NVIDIA if nvidia-smi is available
        if command -v nvidia-smi &> /dev/null; then
            GPU_TYPE="nvidia"
            echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
            return
        fi
    fi
    
    # Default to CPU-only
    GPU_TYPE="cpu"
    echo -e "${YELLOW}⚠️  No GPU acceleration detected, using CPU-only${NC}"
}

# Function to determine optimal Python command
detect_python() {
    echo -e "${CYAN}🐍 Detecting Python installation...${NC}"
    
    # Try different Python commands
    for cmd in python3.12 python3.11 python3.10 python3 python; do
        if command -v "$cmd" &> /dev/null; then
            VERSION=$($cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null)
            if [[ -n "$VERSION" ]]; then
                # Check if version is >= 3.10
                if [ "$(printf '%s\n' "3.10" "$VERSION" | sort -V | head -n1)" = "3.10" ]; then
                    PYTHON_CMD="$cmd"
                    echo -e "${GREEN}✓ Python $VERSION found ($cmd)${NC}"
                    return 0
                fi
            fi
        fi
    done
    
    echo -e "${RED}❌ Python 3.10+ not found${NC}"
    return 1
}


# Function to set optimal Ollama model based on system
set_optimal_model() {
    echo -e "${CYAN}🧠 Determining optimal model for your system...${NC}"
    
    # Get total RAM
    if [[ "$PLATFORM" == "linux" ]]; then
        TOTAL_RAM=$(free -g | grep '^Mem:' | awk '{print $2}')
    elif [[ "$PLATFORM" == "macos" ]]; then
        TOTAL_RAM=$(($(sysctl -n hw.memsize) / 1024 / 1024 / 1024))
    else
        TOTAL_RAM=8  # Default assumption
    fi
    
    # Model selection based on GPU and RAM
    if [[ "$GPU_TYPE" == "nvidia" ]]; then
        if [[ $TOTAL_RAM -ge 32 ]]; then
            OLLAMA_MODEL="qwen2.5:14b"
            echo -e "${GREEN}✓ High-end NVIDIA setup detected - using qwen2.5:14b${NC}"
        elif [[ $TOTAL_RAM -ge 16 ]]; then
            OLLAMA_MODEL="qwen2.5:7b"
            echo -e "${GREEN}✓ Mid-range NVIDIA setup detected - using qwen2.5:7b${NC}"
        else
            OLLAMA_MODEL="llama3.2:3b"
            echo -e "${YELLOW}⚠️  Limited NVIDIA setup detected - using llama3.2:3b${NC}"
        fi
    elif [[ "$GPU_TYPE" == "apple-silicon" ]]; then
        if [[ $TOTAL_RAM -ge 24 ]]; then
            OLLAMA_MODEL="qwen2.5:7b"
            echo -e "${GREEN}✓ High-end Apple Silicon - using qwen2.5:7b${NC}"
        else
            OLLAMA_MODEL="llama3.2:3b"
            echo -e "${GREEN}✓ Apple Silicon detected - using llama3.2:3b${NC}"
        fi
    else
        OLLAMA_MODEL="llama3.2:3b"
        echo -e "${YELLOW}⚠️  CPU/Limited GPU setup - using llama3.2:3b${NC}"
    fi
    
    echo -e "   Selected model: ${CYAN}$OLLAMA_MODEL${NC}"
}

# Function to create platform-specific configuration templates
create_config_templates() {
    echo -e "${CYAN}📝 Creating configuration templates...${NC}"
    
    mkdir -p configs/templates
    
    # Linux NVIDIA configuration
    cat > configs/templates/.env.linux-nvidia << 'EOF'
# AI MCP Toolkit - Linux NVIDIA Configuration
# Optimized for NVIDIA GPU acceleration

# ============================================
# Server Configuration
# ============================================
MCP_HOST=localhost
MCP_PORT=8000

# ============================================
# Ollama Configuration (NVIDIA Optimized)
# ============================================
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=qwen2.5:7b
# NVIDIA GPU settings
OLLAMA_GPU_LAYERS=-1
OLLAMA_NUM_GPU=1

# ============================================
# Web UI Configuration  
# ============================================
UI_HOST=localhost
UI_PORT=5173

# ============================================
# Performance Configuration (NVIDIA)
# ============================================
MAX_TEXT_LENGTH=200000
CHUNK_SIZE=2000
TEMPERATURE=0.1
MAX_TOKENS=4000

# ============================================
# GPU-Specific Settings
# ============================================
ENABLE_GPU_ACCELERATION=true
GPU_MEMORY_FRACTION=0.9
CUDA_VISIBLE_DEVICES=0

# ============================================
# Data Directories
# ============================================
DATA_DIR=~/.ai-mcp-toolkit
CACHE_DIR=~/.ai-mcp-toolkit/cache
MODELS_DIR=~/.ai-mcp-toolkit/models

# ============================================
# Development Configuration
# ============================================
LOG_LEVEL=INFO
ENABLE_CACHE=true
CACHE_TTL=3600
EOF

    # macOS Apple Silicon configuration
    cat > configs/templates/.env.macos-apple-silicon << 'EOF'
# AI MCP Toolkit - macOS Apple Silicon Configuration
# Optimized for Apple M1/M2/M3/M4 chips

# ============================================
# Server Configuration
# ============================================
MCP_HOST=localhost
MCP_PORT=8000

# ============================================
# Ollama Configuration (Apple Silicon Optimized)
# ============================================
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:3b
# Apple Silicon settings
OLLAMA_NUM_THREAD=0

# ============================================
# Web UI Configuration  
# ============================================
UI_HOST=localhost
UI_PORT=5173

# ============================================
# Performance Configuration (Apple Silicon)
# ============================================
MAX_TEXT_LENGTH=150000
CHUNK_SIZE=1500
TEMPERATURE=0.1
MAX_TOKENS=3000

# ============================================
# Apple Silicon Specific Settings
# ============================================
ENABLE_METAL_ACCELERATION=true
PYTORCH_ENABLE_MPS_FALLBACK=1

# ============================================
# Data Directories
# ============================================
DATA_DIR=~/.ai-mcp-toolkit
CACHE_DIR=~/.ai-mcp-toolkit/cache
MODELS_DIR=~/.ai-mcp-toolkit/models

# ============================================
# Development Configuration
# ============================================
LOG_LEVEL=INFO
ENABLE_CACHE=true
CACHE_TTL=3600
EOF

    # Generic CPU-only configuration
    cat > configs/templates/.env.cpu << 'EOF'
# AI MCP Toolkit - CPU-Only Configuration
# Optimized for systems without GPU acceleration

# ============================================
# Server Configuration
# ============================================
MCP_HOST=localhost
MCP_PORT=8000

# ============================================
# Ollama Configuration (CPU Optimized)
# ============================================
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_NUM_THREAD=0

# ============================================
# Web UI Configuration  
# ============================================
UI_HOST=localhost
UI_PORT=5173

# ============================================
# Performance Configuration (CPU)
# ============================================
MAX_TEXT_LENGTH=50000
CHUNK_SIZE=500
TEMPERATURE=0.1
MAX_TOKENS=1000

# ============================================
# CPU-Specific Settings
# ============================================
ENABLE_GPU_ACCELERATION=false

# ============================================
# Data Directories
# ============================================
DATA_DIR=~/.ai-mcp-toolkit
CACHE_DIR=~/.ai-mcp-toolkit/cache
MODELS_DIR=~/.ai-mcp-toolkit/models

# ============================================
# Development Configuration
# ============================================
LOG_LEVEL=INFO
ENABLE_CACHE=true
CACHE_TTL=1800
EOF

    echo -e "${GREEN}✓ Configuration templates created${NC}"
}

# Function to apply platform-specific configuration
apply_configuration() {
    echo -e "${CYAN}⚙️  Applying platform-specific configuration...${NC}"
    
    # Determine which template to use
    TEMPLATE_FILE="configs/templates/.env.$CONFIG_SUFFIX"
    
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        echo -e "${YELLOW}⚠️  Specific template not found, using CPU template${NC}"
        TEMPLATE_FILE="configs/templates/.env.cpu"
    fi
    
    # Copy template to .env
    cp "$TEMPLATE_FILE" .env
    
    # Update the model in the .env file
    if [[ "$PLATFORM" == "macos" ]]; then
        sed -i '' "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=$OLLAMA_MODEL/" .env
    else
        sed -i "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=$OLLAMA_MODEL/" .env
    fi
    
    echo -e "${GREEN}✓ Configuration applied: .env (based on $TEMPLATE_FILE)${NC}"
    
    # Backup original example
    if [[ ! -f ".env.example.backup" ]]; then
        cp .env.example .env.example.backup
        echo -e "${GREEN}✓ Original .env.example backed up${NC}"
    fi
}

# Function to install platform-specific dependencies
install_dependencies() {
    echo -e "${CYAN}📦 Installing platform-specific dependencies...${NC}"
    
    # Check if Python is available
    if ! detect_python; then
        echo -e "${RED}❌ Python 3.10+ is required${NC}"
        exit 1
    fi
    
    # Create virtual environment
    echo -e "${BLUE}Creating Python virtual environment...${NC}"
    if [[ ! -d "venv" ]]; then
        $PYTHON_CMD -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${YELLOW}Virtual environment already exists${NC}"
    fi
    
    # Activate virtual environment
    echo -e "${BLUE}Activating virtual environment...${NC}"
    if [[ "$PLATFORM" == "windows" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
    
    # Install Python dependencies
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    pip install --upgrade pip
    pip install -e .
    
    # Install platform-specific packages
    case "$GPU_TYPE" in
        nvidia)
            echo -e "${CYAN}Installing NVIDIA-specific packages...${NC}"
            pip install nvidia-ml-py3
            ;;
        apple-silicon)
            echo -e "${CYAN}Installing Apple Silicon optimizations...${NC}"
            pip install accelerate
            ;;
    esac
    
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
    
    # Install UI dependencies if Node.js is available
    if command -v node &> /dev/null; then
        echo -e "${BLUE}Installing UI dependencies...${NC}"
        cd ui
        npm install
        echo -e "${GREEN}✓ UI dependencies installed${NC}"
        cd ..
    else
        echo -e "${YELLOW}⚠️  Node.js not found. Install Node.js 18+ for web UI${NC}"
    fi
}

# Function to setup Ollama and download optimal model
setup_ollama() {
    echo -e "${CYAN}🦙 Setting up Ollama...${NC}"
    
    if command -v ollama &> /dev/null; then
        echo -e "${GREEN}✓ Ollama found${NC}"
        
        # Check if the optimal model is available
        if ollama list | grep -q "$OLLAMA_MODEL"; then
            echo -e "${GREEN}✓ Model ($OLLAMA_MODEL) is already available${NC}"
        else
            echo -e "${YELLOW}Downloading optimal model: $OLLAMA_MODEL...${NC}"
            ollama pull "$OLLAMA_MODEL"
            echo -e "${GREEN}✓ Model downloaded${NC}"
        fi
        
        # Test the model
        echo -e "${CYAN}Testing model...${NC}"
        if echo "Hello" | ollama run "$OLLAMA_MODEL" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Model is working correctly${NC}"
        else
            echo -e "${YELLOW}⚠️  Model test failed, but installation continued${NC}"
        fi
        
    else
        echo -e "${RED}❌ Ollama not found!${NC}"
        echo ""
        echo -e "${YELLOW}Please install Ollama:${NC}"
        case "$PLATFORM" in
            linux)
                echo "  curl -fsSL https://ollama.ai/install.sh | sh"
                ;;
            macos)
                echo "  Download from: https://ollama.ai/download/mac"
                echo "  Or with Homebrew: brew install ollama"
                ;;
            windows)
                echo "  Download from: https://ollama.ai/download/windows"
                ;;
        esac
        echo ""
        echo "After installing Ollama, run this setup script again."
        exit 1
    fi
}

# Function to create default configuration
create_config() {
    echo -e "${CYAN}⚙️  Creating default configuration...${NC}"
    if [[ ! -f "$HOME/.ai-mcp-toolkit/config.yaml" ]]; then
        $PYTHON_CMD -c "from src.ai_mcp_toolkit.utils.config import create_default_config; create_default_config()"
        echo -e "${GREEN}✓ Default configuration created at $HOME/.ai-mcp-toolkit/config.yaml${NC}"
    else
        echo -e "${YELLOW}Configuration already exists${NC}"
    fi
}

# Function to display final setup summary
show_summary() {
    echo ""
    echo -e "${GREEN}🎉 Setup Complete!${NC}"
    echo -e "${PURPLE}==================${NC}"
    echo ""
    echo -e "${CYAN}Environment Configuration:${NC}"
    echo -e "  • Platform: ${YELLOW}$PLATFORM ($ARCH)${NC}"
    echo -e "  • GPU: ${YELLOW}$GPU_TYPE${NC}"
    echo -e "  • Model: ${YELLOW}$OLLAMA_MODEL${NC}"
    echo -e "  • Config: ${YELLOW}.env (from $CONFIG_SUFFIX template)${NC}"
    echo ""
    echo -e "${CYAN}Quick Start Commands:${NC}"
    echo -e "  ${YELLOW}1. Start the MCP server:${NC}"
    echo -e "     ai-mcp-toolkit serve"
    echo ""
    if command -v node &> /dev/null; then
        echo -e "  ${YELLOW}2. Start the web UI (in another terminal):${NC}"
        echo -e "     cd ui && npm run dev"
        echo -e "     Open: http://localhost:5173"
        echo ""
    fi
    echo -e "  ${YELLOW}3. Test CLI directly:${NC}"
    echo -e "     ai-mcp-toolkit analyze 'Hello world!'"
    echo ""
    echo -e "${CYAN}Alternative - Docker:${NC}"
    echo -e "  ${YELLOW}docker-compose up -d${NC}"
    echo ""
    echo -e "${GREEN}Happy AI text processing! 🚀${NC}"
}

# Main execution flow
main() {
    # Step 1: Detect environment
    detect_environment
    
    # Step 2: Set optimal model
    set_optimal_model
    
    # Step 3: Create configuration templates
    create_config_templates
    
    # Step 4: Apply platform-specific configuration
    apply_configuration
    
    # Step 5: Install dependencies
    install_dependencies
    
    # Step 6: Setup Ollama
    setup_ollama
    
    # Step 7: Create default configuration
    create_config
    
    # Step 8: Show summary
    show_summary
}

# Run main function
main "$@"
