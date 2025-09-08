# AI MCP Toolkit - Quick Start

## 🚀 Get Started in 2 Minutes

### Option 1: Native Installation (Recommended for Development)

```bash
# 1. Install the toolkit
cd ai-mcp-toolkit
pip install -e .

# 2. Create configuration
ai-mcp-toolkit config create

# 3. Check status
ai-mcp-toolkit status

# 4. Start the server
ai-mcp-toolkit serve
```

In another terminal:
```bash
# 5. Start the web UI
ai-mcp-toolkit ui
```

### Option 2: Docker (Recommended for Production)

```bash
# 1. Start everything with Docker
docker-compose up -d

# 2. Pull AI model
docker-compose exec ollama ollama pull llama3.2:3b
```

## 📱 Access Points

- **Web UI**: http://localhost:5173
- **MCP Server**: http://localhost:8000  
- **API Docs**: http://localhost:8000/docs

## 🛠️ Quick Commands

```bash
# Text processing examples
ai-mcp-toolkit text clean "messy text!!!"
ai-mcp-toolkit text analyze "sample text"
ai-mcp-toolkit text anonymize "John Doe lives in NYC"
ai-mcp-toolkit text summarize "long text to summarize"

# Interactive chat
ai-mcp-toolkit chat

# System management
ai-mcp-toolkit status
ai-mcp-toolkit agents
ai-mcp-toolkit config show
```

## ⚙️ Basic Configuration

Create a `.env` file for custom settings:

```env
# Copy the template
cp .env.example .env

# Common settings
MCP_PORT=8000
UI_PORT=5173
OLLAMA_MODEL=llama3.2:3b
LOG_LEVEL=INFO
TEMPERATURE=0.1
```

## 🔍 Troubleshooting

### Check System Status
```bash
ai-mcp-toolkit status
```

### Verify Ollama
```bash
ollama list
ollama serve  # if not running
```

### Reset Configuration
```bash
ai-mcp-toolkit config create
```

### Use Different Ports
```bash
ai-mcp-toolkit serve --port 8001
ai-mcp-toolkit ui --port 5174
```

## 📚 Next Steps

- Explore the Web UI at http://localhost:5173
- Try different text processing agents
- Customize configuration in `.env` file
- Check [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for advanced settings
- Use `ai-mcp-toolkit --help` for all commands

## 🆘 Getting Help

- Run `ai-mcp-toolkit --help` for command help
- Check `ai-mcp-toolkit status` for system health
- View [Configuration Guide](docs/CONFIGURATION.md)
- See the main [README.md](README.md) for complete documentation
