# Configuration Guide

The AI MCP Toolkit supports multiple configuration methods to accommodate different use cases and deployment scenarios.

## Configuration Priority

The configuration system follows this priority order (highest to lowest):

1. **Command line arguments** (highest priority)
2. **Environment variables** (`.env` file or system environment)
3. **Configuration file** (`config.yaml`)
4. **Default values** (lowest priority)

## Configuration Methods

### 1. Command Line Arguments

Override any setting directly from the command line:

```bash
ai-mcp-toolkit serve --host 0.0.0.0 --port 8080 --log-level DEBUG
```

### 2. Environment Variables

Create a `.env` file or set system environment variables:

```bash
# Copy the example file
cp .env.example .env

# Edit the file with your preferred settings
nano .env
```

### 3. Configuration File

Create and edit the YAML configuration file:

```bash
# Create default config
ai-mcp-toolkit config create

# View current configuration
ai-mcp-toolkit config show

# Edit the config file
nano ~/.ai-mcp-toolkit/config.yaml
```

## Configuration Options

### Server Settings

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `host` | `MCP_HOST` | `localhost` | Server host address |
| `port` | `MCP_PORT` | `8000` | Server port number |
| `enable_cors` | `ENABLE_CORS` | `true` | Enable CORS support |
| `cors_origins` | `CORS_ORIGINS` | `*` | Allowed CORS origins |

### Ollama Integration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `ollama_host` | `OLLAMA_HOST` | `localhost` | Ollama server host |
| `ollama_port` | `OLLAMA_PORT` | `11434` | Ollama server port |
| `ollama_model` | `OLLAMA_MODEL` | `llama3.2:3b` | Default AI model |

### Web UI Settings

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `ui_host` | `UI_HOST` | `localhost` | Web UI host |
| `ui_port` | `UI_PORT` | `8501` | Web UI port |

### Logging Configuration

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `log_level` | `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `log_file` | `LOG_FILE` | `null` | Optional log file path |

### Text Processing

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `max_text_length` | `MAX_TEXT_LENGTH` | `100000` | Maximum text length for processing |
| `chunk_size` | `CHUNK_SIZE` | `1000` | Text chunk size for large documents |

### AI Model Settings

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `temperature` | `TEMPERATURE` | `0.1` | AI model temperature (0.0-2.0) |
| `max_tokens` | `MAX_TOKENS` | `2000` | Maximum tokens per AI response |

### Caching

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `enable_cache` | `ENABLE_CACHE` | `true` | Enable response caching |
| `cache_ttl` | `CACHE_TTL` | `3600` | Cache TTL in seconds |

### Data Directories

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `data_dir` | `DATA_DIR` | `~/.ai-mcp-toolkit` | Main data directory |
| `cache_dir` | `CACHE_DIR` | `~/.ai-mcp-toolkit/cache` | Cache storage directory |
| `models_dir` | `MODELS_DIR` | `~/.ai-mcp-toolkit/models` | Model storage directory |

## Configuration Examples

### Example 1: Development Setup

Create a `.env` file for development:

```env
LOG_LEVEL=DEBUG
OLLAMA_MODEL=llama3.2:3b
TEMPERATURE=0.2
MAX_TOKENS=4000
UI_PORT=3000
```

### Example 2: Production Setup

Create a `config.yaml` for production:

```yaml
# Production Configuration
host: 0.0.0.0
port: 8000
log_level: INFO
log_file: /var/log/ai-mcp-toolkit/server.log

ollama_host: ollama-server
ollama_port: 11434
ollama_model: llama3.2:7b

enable_cache: true
cache_ttl: 7200

data_dir: /opt/ai-mcp-toolkit/data
cache_dir: /opt/ai-mcp-toolkit/cache
```

### Example 3: Docker Deployment

Use environment variables in `docker-compose.yml`:

```yaml
services:
  ai-mcp-toolkit:
    build: .
    environment:
      - MCP_HOST=0.0.0.0
      - OLLAMA_HOST=ollama
      - LOG_LEVEL=INFO
      - ENABLE_CACHE=true
    ports:
      - "8000:8000"
      - "5173:5173"
```

## Configuration Validation

The system validates all configuration values on startup:

```bash
# Check current configuration
ai-mcp-toolkit config show

# Validate system status
ai-mcp-toolkit status
```

### Common Validation Errors

1. **Invalid Port Numbers**: Must be between 1-65535
2. **Invalid Log Level**: Must be DEBUG, INFO, WARNING, ERROR, or CRITICAL
3. **Invalid Temperature**: Must be between 0.0 and 2.0
4. **Invalid Directories**: Must be valid, writable paths

## Advanced Configuration

### Custom Agent Settings

You can configure individual agents by creating agent-specific config files:

```yaml
# ~/.ai-mcp-toolkit/agents/text_anonymizer.yaml
anonymization:
  default_level: "aggressive"
  replacement_strategy: "placeholder"
  preserve_structure: true

patterns:
  custom_patterns:
    - "\\b[A-Z]{2}\\d{6}\\b"  # Custom ID format
```

### Model-Specific Settings

Configure different settings for different models:

```yaml
models:
  "llama3.2:3b":
    temperature: 0.1
    max_tokens: 2000
    
  "llama3.2:7b":
    temperature: 0.05
    max_tokens: 4000
```

## Troubleshooting

### Configuration Not Loading

1. Check file permissions
2. Validate YAML syntax
3. Verify file paths
4. Check environment variable names

### Performance Tuning

1. Adjust `chunk_size` for large documents
2. Tune `temperature` for better results
3. Enable caching for repeated operations
4. Increase `max_tokens` for complex tasks

### Security Considerations

1. Never commit `.env` files to version control
2. Use restrictive CORS origins in production
3. Set appropriate file permissions on config files
4. Use secure directories for data storage

## CLI Configuration Commands

```bash
# Configuration management
ai-mcp-toolkit config create          # Create default config
ai-mcp-toolkit config show            # View current config  
ai-mcp-toolkit config edit            # Edit config file

# System status
ai-mcp-toolkit status                 # Check system health
ai-mcp-toolkit agents                 # List available agents
ai-mcp-toolkit version                # Show version info
```
