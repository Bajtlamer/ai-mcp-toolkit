# Cross-Platform Setup Guide

The AI MCP Toolkit now includes **intelligent environment detection and automatic configuration** for seamless deployment across different platforms and hardware configurations.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/your-repo/ai-mcp-toolkit.git
cd ai-mcp-toolkit

# Run the enhanced setup script
./setup.sh
```

The setup script will automatically:
- 🔍 **Detect your platform** (Linux, macOS, Windows)
- 🎮 **Identify GPU capabilities** (NVIDIA, Apple Silicon, AMD, Intel, CPU-only)
- 🧠 **Select optimal AI model** based on your hardware
- ⚙️ **Generate platform-specific configuration**
- 📦 **Install required dependencies**
- 🦙 **Setup Ollama with the right model**

## 🌍 Supported Environments

### Linux Platforms
- **Ubuntu/Debian** with NVIDIA RTX/GTX GPUs ✅
- **RHEL/CentOS/Fedora** with NVIDIA GPUs ✅  
- **Arch Linux** with NVIDIA GPUs ✅
- **Any Linux** with AMD GPUs (limited support) ⚠️
- **CPU-only Linux systems** ✅

### macOS Platforms  
- **Apple Silicon** (M1/M2/M3/M4) with Metal acceleration ✅
- **Intel Mac** with discrete GPU ⚠️
- **Intel Mac** CPU-only ✅

### Windows Platforms
- **Windows 10/11** with NVIDIA GPUs ✅
- **Windows 10/11** CPU-only ✅
- **Windows with AMD GPUs** (experimental) ⚠️

## 🛠 What Gets Configured

### Environment Detection Results
The setup script detects and optimizes for:

```
🔍 Environment Detection:
   • Platform: linux (ubuntu) / macos / windows
   • Architecture: x86_64 / arm64
   • GPU: nvidia / apple-silicon / amd / intel / cpu
   • RAM: 8GB / 16GB / 32GB+ (affects model selection)
```

### Configuration Profiles Created

| Profile | Platform | GPU | Model | Performance |
|---------|----------|-----|-------|-------------|
| `linux-nvidia` | Linux | NVIDIA RTX/GTX | qwen2.5:7b-14b | High |
| `macos-apple-silicon` | macOS | M1/M2/M3/M4 | llama3.2:3b-qwen2.5:7b | High |
| `windows-nvidia` | Windows | NVIDIA | qwen2.5:7b | Medium |
| `linux-amd` | Linux | AMD | llama3.2:3b | Medium |
| `cpu` | Any | None | llama3.2:3b | Basic |

### Generated Files Structure

```
ai-mcp-toolkit/
├── .env                           # Active configuration
├── .env.example.backup           # Original example (backed up)
├── configs/
│   └── templates/
│       ├── .env.linux-nvidia     # NVIDIA optimized
│       ├── .env.macos-apple-silicon # Apple Silicon optimized  
│       ├── .env.windows          # Windows optimized
│       └── .env.cpu              # CPU fallback
├── setup.sh                      # Enhanced cross-platform setup
└── switch-environment.sh         # Environment switcher
```

## 🔧 Manual Configuration Switching

If you need to switch between environments (e.g., testing different configurations):

```bash
# Interactive environment switcher
./switch-environment.sh
```

This will show you available configurations and let you switch between them.

### Manual Template Selection

You can also manually copy any configuration template:

```bash
# Example: Switch to CPU-only configuration
cp configs/templates/.env.cpu .env

# Example: Switch to NVIDIA configuration  
cp configs/templates/.env.linux-nvidia .env
```

## 📝 Configuration Templates

### Linux NVIDIA Configuration
**File**: `configs/templates/.env.linux-nvidia`
```bash
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_GPU_LAYERS=-1
OLLAMA_NUM_GPU=1
MAX_TEXT_LENGTH=200000
CHUNK_SIZE=2000
MAX_TOKENS=4000
ENABLE_GPU_ACCELERATION=true
GPU_MEMORY_FRACTION=0.9
```

### macOS Apple Silicon Configuration  
**File**: `configs/templates/.env.macos-apple-silicon`
```bash
OLLAMA_MODEL=llama3.2:3b
OLLAMA_NUM_THREAD=0
MAX_TEXT_LENGTH=150000
CHUNK_SIZE=1500
MAX_TOKENS=3000
ENABLE_METAL_ACCELERATION=true
PYTORCH_ENABLE_MPS_FALLBACK=1
```

### CPU-Only Configuration
**File**: `configs/templates/.env.cpu`
```bash
OLLAMA_MODEL=llama3.2:3b
OLLAMA_NUM_THREAD=0
MAX_TEXT_LENGTH=50000
CHUNK_SIZE=500  
MAX_TOKENS=1000
ENABLE_GPU_ACCELERATION=false
```

## 🎯 Model Selection Logic

The setup script automatically selects the optimal model based on your hardware:

### NVIDIA Systems
- **32GB+ RAM**: `qwen2.5:14b` (Best quality)
- **16GB+ RAM**: `qwen2.5:7b` (Good balance) 
- **<16GB RAM**: `llama3.2:3b` (Fast, efficient)

### Apple Silicon Systems
- **24GB+ RAM**: `qwen2.5:7b` (Optimized for Metal)
- **<24GB RAM**: `llama3.2:3b` (Efficient for unified memory)

### CPU/Other Systems
- **All configurations**: `llama3.2:3b` (Lightweight, fast)

## 🐳 Docker Support

The system also works with Docker across all platforms:

```bash
# Works on any platform after setup
docker-compose up -d
```

## 🔄 Updating Your Setup

When you pull updates from the repository:

```bash
# Re-run setup to get latest optimizations
./setup.sh

# Or just update configuration without reinstalling
./switch-environment.sh
```

## 🆘 Troubleshooting

### Setup Script Issues

**Python not found**:
```bash
# Install Python 3.10+ first
# Ubuntu/Debian: sudo apt install python3.11
# macOS: brew install python@3.11  
# Windows: Download from python.org
```

**Node.js not found** (for web UI):
```bash
# Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install nodejs
# macOS: brew install node
# Windows: Download from nodejs.org
```

**Ollama not found**:
```bash
# Linux: curl -fsSL https://ollama.ai/install.sh | sh
# macOS: brew install ollama
# Windows: Download from ollama.ai/download/windows
```

### GPU Issues

**NVIDIA GPU not detected**:
```bash
# Check NVIDIA drivers
nvidia-smi

# Install CUDA toolkit if needed
# Ubuntu: sudo apt install nvidia-cuda-toolkit
```

**Apple Silicon not detected**:
```bash
# Check system info
system_profiler SPHardwareDataType | grep Chip
```

### Configuration Issues

**Wrong model selected**:
```bash
# Switch to different configuration
./switch-environment.sh

# Or manually edit .env file
nano .env
```

**Performance issues**:
```bash
# Try CPU configuration for troubleshooting
cp configs/templates/.env.cpu .env

# Restart services
ai-mcp-toolkit serve
```

## 🤝 Contributing New Platforms

To add support for a new platform:

1. **Add detection logic** in `setup.sh` → `detect_environment()`
2. **Add GPU detection** in `setup.sh` → `detect_gpu()`  
3. **Create configuration template** in `configs/templates/.env.your-platform`
4. **Update model selection** in `setup.sh` → `set_optimal_model()`
5. **Test and submit PR**

## 📋 Platform-Specific Notes

### Linux
- Automatically detects distribution (Ubuntu, CentOS, Arch, etc.)
- Optimizes for NVIDIA CUDA when available
- Falls back gracefully to CPU-only

### macOS  
- Detects Apple Silicon vs Intel automatically
- Optimizes for Metal Performance Shaders on M1/M2/M3/M4
- Handles unified memory architecture properly

### Windows
- Supports both PowerShell and Git Bash
- Automatically adjusts path separators
- Works with Windows Subsystem for Linux (WSL)

---

## 🎉 Success!

After running `./setup.sh`, you should see:

```
🎉 Setup Complete!
==================

Environment Configuration:
  • Platform: linux (ubuntu)
  • GPU: nvidia
  • Model: qwen2.5:7b  
  • Config: .env (from linux-nvidia template)

Quick Start Commands:
  1. Start the MCP server:
     ai-mcp-toolkit serve

  2. Start the web UI (in another terminal):
     cd ui && npm run dev
     Open: http://localhost:5173

  3. Test CLI directly:
     ai-mcp-toolkit analyze 'Hello world!'

Happy AI text processing! 🚀
```

Your AI MCP Toolkit is now optimally configured for your specific hardware and platform! 🎯