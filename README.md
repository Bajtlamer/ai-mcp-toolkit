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

## 📞 Support

- 📚 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/yourusername/ai-mcp-toolkit/issues)
- 💬 [Discussions](https://github.com/yourusername/ai-mcp-toolkit/discussions)
