# AI MCP Toolkit

A comprehensive AI-powered text processing toolkit built on the Model Context Protocol (MCP) standard, designed to work seamlessly with local AI models through Ollama.

## 🌟 Features

### Essential AI Agents
- **Text Cleaner** - Remove special characters and normalize text
- **Diacritic Remover** - Remove accents and diacritical marks
- **Text Analyzer** - Comprehensive text statistics and analysis
- **Grammar Checker** - Fix grammar and spelling mistakes
- **Text Summarizer** - Generate concise summaries
- **Language Detector** - Identify text language
- **Sentiment Analyzer** - Analyze emotional tone
- **Text Translator** - Multi-language translation support
- **Format Converter** - Convert between text formats
- **Readability Scorer** - Assess text complexity and readability

### Key Capabilities
- 🔌 **MCP Protocol Support** - Standard interface for AI applications
- 🦙 **Ollama Integration** - Local AI model support
- 🌐 **Web UI** - Intuitive browser-based interface
- 💬 **Chat Mode** - Conversational AI with tool access
- 🖥️ **CLI Support** - Command-line interface for automation
- 🚀 **Easy Deployment** - Docker and native installation options
- 🔒 **Privacy-First** - All processing happens locally

## 🚀 Quick Start

### Prerequisites
- Python 3.13.7 (recommended) or Python 3.11+
- Ollama installed and running
- Git

### Installation

#### Option 1: Docker (Recommended for Production)
```bash
# Clone and start with Docker
git clone https://github.com/yourusername/ai-mcp-toolkit.git
cd ai-mcp-toolkit
docker-compose up -d

# Pull AI model (after containers start)
docker-compose exec ollama ollama pull llama3.2:3b
```

#### Option 2: Native Installation
```bash
# Clone and install locally
git clone https://github.com/yourusername/ai-mcp-toolkit.git
cd ai-mcp-toolkit
pip install -e .
```

#### Step 2: Install Ollama (if not already installed)
```bash
# On macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a recommended model
ollama pull llama3.2:3b
```

#### Step 3: Configure the System
```bash
# Create default configuration
ai-mcp-toolkit config create

# Check system status
ai-mcp-toolkit status
```

#### Step 4: Optional - Customize Settings
```bash
# Copy environment template
cp .env.example .env

# Edit with your preferences (optional)
nano .env
```

### Running the Application

#### Start the MCP Server
```bash
ai-mcp-toolkit serve
```

#### Launch Web UI (in another terminal)
```bash
ai-mcp-toolkit ui
```

#### Access the Application
- **MCP Server**: http://localhost:8000
- **Web UI**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

### CLI Usage Examples

#### Text Processing Commands
```bash
# Text cleaning and analysis
ai-mcp-toolkit text clean "Your messy text here"
ai-mcp-toolkit text analyze "Sample text for analysis"
ai-mcp-toolkit text summarize "Long text to summarize"
ai-mcp-toolkit text anonymize "John Doe lives in NYC"

# Language and sentiment
ai-mcp-toolkit text detect-language "Bonjour le monde"
ai-mcp-toolkit text sentiment "I love this product!"

# Grammar checking
ai-mcp-toolkit text grammar "This are incorrect grammar"
```

#### System Management
```bash
# Interactive chat
ai-mcp-toolkit chat

# List available agents
ai-mcp-toolkit agents

# System status
ai-mcp-toolkit status

# Configuration management
ai-mcp-toolkit config show
```

## ⚙️ Configuration

The AI MCP Toolkit supports flexible configuration through multiple methods to accommodate different use cases.

### Configuration Priority

1. **Command line arguments** (highest priority)
2. **Environment variables** (`.env` file)
3. **Configuration file** (`config.yaml`)
4. **Default values** (lowest priority)

### Quick Configuration Setup

```bash
# Create default configuration
ai-mcp-toolkit config create

# View current settings
ai-mcp-toolkit config show

# Check system health
ai-mcp-toolkit status
```

### Environment Variables Setup

```bash
# Copy the template
cp .env.example .env

# Edit with your settings
nano .env
```

Example `.env` configuration:
```env
# Server Settings
MCP_HOST=localhost
MCP_PORT=8000

# Ollama Integration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:3b

# Logging
LOG_LEVEL=INFO

# AI Settings
TEMPERATURE=0.1
MAX_TOKENS=2000
MAX_TEXT_LENGTH=100000

# UI Settings
UI_HOST=localhost
UI_PORT=5173

# Caching
ENABLE_CACHE=true
CACHE_TTL=3600
```

### Key Configuration Options

| Category | Setting | Default | Description |
|----------|---------|---------|-------------|
| **Server** | `MCP_HOST` | `localhost` | Server host address |
| **Server** | `MCP_PORT` | `8000` | Server port number |
| **Ollama** | `OLLAMA_HOST` | `localhost` | Ollama server host |
| **Ollama** | `OLLAMA_MODEL` | `llama3.2:3b` | Default AI model |
| **AI** | `TEMPERATURE` | `0.1` | Model creativity (0.0-2.0) |
| **AI** | `MAX_TOKENS` | `2000` | Max response length |
| **Logging** | `LOG_LEVEL` | `INFO` | Logging verbosity |
| **UI** | `UI_PORT` | `5173` | Web UI port |

### Docker Configuration

For Docker deployments, you can customize settings in `docker-compose.yml`:

```yaml
services:
  ai-mcp-toolkit:
    environment:
      - MCP_HOST=0.0.0.0
      - OLLAMA_MODEL=llama3.2:7b  # Use larger model
      - LOG_LEVEL=DEBUG
      - TEMPERATURE=0.05
```

Or create a `.env` file that Docker Compose will automatically use:

```env
MCP_HOST=0.0.0.0
OLLAMA_MODEL=llama3.2:7b
LOG_LEVEL=INFO
TEMPERATURE=0.1
```

For complete configuration documentation, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## 🏗️ Architecture

```
AI MCP Toolkit
├── MCP Server (Core Protocol Implementation)
├── AI Agents (Text Processing Tools)
├── Ollama Integration (Local AI Models)
├── Web UI (Browser Interface)
└── CLI Interface (Command Line Tools)
```

## 📚 Documentation

- [Configuration Guide](docs/CONFIGURATION.md) - Complete configuration documentation
- [API Reference](http://localhost:8000/docs) - Interactive API documentation
- [Model Management](#-model-management) - AI model switching and monitoring
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute to the project
- [License](LICENSE) - MIT License terms

## 🔍 Troubleshooting

### Common Issues

#### Configuration Issues
```bash
# Check system status
ai-mcp-toolkit status

# Verify configuration
ai-mcp-toolkit config show

# Recreate default config
ai-mcp-toolkit config create
```

#### Ollama Connection Issues
```bash
# Check if Ollama is running
ollama list

# Start Ollama service (if needed)
ollama serve

# Pull required model
ollama pull llama3.2:3b
```

#### Port Conflicts
```bash
# Use different ports
ai-mcp-toolkit serve --port 8001
ai-mcp-toolkit ui --port 5174
```

#### Permission Issues
```bash
# Check directory permissions
ls -la ~/.ai-mcp-toolkit/

# Fix permissions (if needed)
chmod 755 ~/.ai-mcp-toolkit/
```

### Getting Help

- Check the [Configuration Guide](docs/CONFIGURATION.md)
- Run `ai-mcp-toolkit --help` for command help
- Check system status with `ai-mcp-toolkit status`
- Review logs for error messages

## 🔧 Development

### Setup Development Environment
```bash
git clone https://github.com/yourusername/ai-mcp-toolkit.git
cd ai-mcp-toolkit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Tests
```bash
pytest tests/
```

### Code Quality
```bash
black src/
flake8 src/
mypy src/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md) for details.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the standard
- [Ollama](https://ollama.ai/) for local AI model support
- The open-source AI community

## 🤖 Model Management

The AI MCP Toolkit provides comprehensive model management capabilities, allowing you to easily switch between different AI models and monitor their status in real-time.

### 📋 Getting Current Model Information

#### Check Currently Active Model
```bash
# Check what models are currently running
ollama ps

# Get model via the toolkit's API
curl -s http://localhost:5173/api/gpu/health | jq -r '.ollama_model'

# List all available models
ollama list

# Using the model management script
cd /home/roza/ai-mcp-toolkit
./switch-model.sh
```

#### Example Output
```bash
$ ollama ps
NAME           ID              SIZE     PROCESSOR          CONTEXT    UNTIL              
qwen2.5:14b    7cdf5a0187d5    10 GB    31%/69% CPU/GPU    4096       4 minutes from now

$ curl -s http://localhost:5173/api/gpu/health | jq -r '.ollama_model'
qwen2.5:14b
```

### 🔄 Switching Models

#### Method 1: Using the Model Management Script (Recommended)
The toolkit includes a convenient script for easy model switching:

```bash
cd /home/roza/ai-mcp-toolkit

# View current status and available models
./switch-model.sh

# Switch to a specific model
./switch-model.sh qwen2.5:7b     # Switch to Qwen 2.5 7B
./switch-model.sh qwen2.5:14b    # Switch to Qwen 2.5 14B
./switch-model.sh llama3.1:8b    # Switch to Llama 3.1 8B
./switch-model.sh llama3.2:3b    # Switch to Llama 3.2 3B
```

#### Method 2: Manual Command Line
```bash
# Stop current model
ollama stop qwen2.5:14b

# Start new model
echo "Hello" | ollama run qwen2.5:7b > /dev/null 2>&1 &

# Verify the switch
ollama ps
```

#### Method 3: Web Interface
1. Navigate to the Settings page: http://localhost:5173/settings
2. Find the "AI Model Management" section
3. Click on any available model to switch to it
4. Monitor the switch status with real-time feedback

### 🌐 Model Management API

The toolkit provides RESTful API endpoints for programmatic model management:

#### List Available Models
```bash
GET /api/models/switch
```

**Example Request:**
```bash
curl -s http://localhost:5173/api/models/switch | jq
```

**Example Response:**
```json
{
  "success": true,
  "available": [
    {
      "name": "qwen2.5:7b",
      "id": "845dbda0ea48",
      "size": "4.7",
      "modified": "GB 2 hours ago"
    },
    {
      "name": "qwen2.5:14b",
      "id": "7cdf5a0187d5",
      "size": "9.0",
      "modified": "GB 2 hours ago"
    },
    {
      "name": "llama3.1:8b",
      "id": "46e0c10c039e",
      "size": "4.9",
      "modified": "GB 25 hours ago"
    }
  ],
  "current": "qwen2.5:14b"
}
```

#### Switch Model
```bash
POST /api/models/switch
Content-Type: application/json
```

**Example Request:**
```bash
curl -X POST http://localhost:5173/api/models/switch \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:7b"}'
```

**Success Response:**
```json
{
  "success": true,
  "message": "Successfully switched to model: qwen2.5:7b",
  "model": "qwen2.5:7b"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Model 'invalid-model' not found. Available models: qwen2.5:7b, qwen2.5:14b, llama3.1:8b"
}
```

#### Get GPU/Model Health Status
```bash
GET /api/gpu/health
```

**Example Request:**
```bash
curl -s http://localhost:5173/api/gpu/health | jq
```

**Example Response:**
```json
{
  "gpu_name": "NVIDIA GeForce RTX 3070 Ti",
  "gpu_utilization": 45,
  "gpu_memory_used": 8192,
  "gpu_memory_total": 8192,
  "gpu_temperature": 65,
  "ollama_model": "qwen2.5:14b",
  "ollama_gpu_accelerated": true,
  "system_load": 2.1,
  "inference_speed": 12.5
}
```

### 📊 GPU Metrics API

Monitor real-time GPU performance and model metrics:

#### Get Current GPU Metrics
```bash
GET /api/gpu/metrics
```

**Example Request:**
```bash
curl -s http://localhost:5173/api/gpu/metrics | jq
```

**Example Response:**
```json
{
  "timestamp": "2025-01-18T15:59:27.123Z",
  "gpu_utilization": 65,
  "gpu_memory_used": 7340,
  "gpu_memory_total": 8192,
  "gpu_temperature": 68,
  "power_usage": 180,
  "inference_speed": 15.2,
  "tokens_per_second": 25.8
}
```

### 🖥️ Real-Time Model Status

The toolkit automatically detects model changes and updates the UI in real-time:

- **GPU Monitoring Page**: Shows current model with live metrics
- **Chat Interface**: Displays active model in header and message labels
- **Settings Page**: Model management interface with status indicators
- **API Endpoints**: Always return current system state

### 📝 Model Management Script Features

The included `switch-model.sh` script provides:

- ✅ **Current Status Display**: Shows running models and app detection
- ✅ **Available Models List**: Lists all downloaded models with sizes
- ✅ **Automatic Validation**: Verifies model exists before switching
- ✅ **Progress Feedback**: Shows switching progress and completion status
- ✅ **Error Handling**: Provides clear error messages and suggestions
- ✅ **Usage Examples**: Built-in help with command examples

#### Script Usage Examples
```bash
# Make script executable (first time only)
chmod +x /home/roza/ai-mcp-toolkit/switch-model.sh

# Show current status and help
./switch-model.sh

# Switch to different models
./switch-model.sh qwen2.5:7b
./switch-model.sh llama3.1:8b
./switch-model.sh llama3.2:3b
```

### 🔧 Troubleshooting Model Management

#### Model Won't Switch
```bash
# Check if Ollama is running
sudo systemctl status ollama

# Restart Ollama service
sudo systemctl restart ollama

# Check model availability
ollama list

# Force stop all models
ollama ps | grep -v "NAME" | awk '{print $1}' | xargs -I {} ollama stop {}
```

#### Model Not Appearing in UI
```bash
# Refresh the browser page
# Or check browser console for errors

# Verify API endpoints
curl -s http://localhost:5173/api/gpu/health
curl -s http://localhost:5173/api/models/switch
```

#### Performance Issues
```bash
# Check GPU memory usage
nvidia-smi

# Monitor system resources
htop

# Check model size vs available memory
ollama list
```

### 📚 API Quick Reference

| Endpoint | Method | Description | Example |
|----------|---------|-------------|---------|
| `/api/gpu/health` | GET | Get current GPU and model status | `curl -s http://localhost:5173/api/gpu/health` |
| `/api/gpu/metrics` | GET | Get real-time GPU performance metrics | `curl -s http://localhost:5173/api/gpu/metrics` |
| `/api/models/switch` | GET | List all available models and current model | `curl -s http://localhost:5173/api/models/switch` |
| `/api/models/switch` | POST | Switch to a different model | `curl -X POST http://localhost:5173/api/models/switch -d '{"model":"qwen2.5:7b"}'` |

### 💴 Model Management Commands Cheat Sheet

```bash
# Quick Status Check
ollama ps                                    # Show running models
curl -s localhost:5173/api/gpu/health | jq  # Get model via API
./switch-model.sh                           # Show status with script

# Model Switching
./switch-model.sh qwen2.5:7b                # Switch using script (recommended)
ollama stop current_model && ollama run new_model  # Manual switch
curl -X POST localhost:5173/api/models/switch -d '{"model":"qwen2.5:7b"}'  # API switch

# Monitoring
watch -n 2 ollama ps                         # Monitor model status
watch -n 5 "curl -s localhost:5173/api/gpu/metrics | jq"  # Monitor GPU metrics
nvidia-smi -l 5                             # Monitor GPU usage
```

## 📞 Support

- 📚 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/yourusername/ai-mcp-toolkit/issues)
- 💬 [Discussions](https://github.com/yourusername/ai-mcp-toolkit/discussions)
