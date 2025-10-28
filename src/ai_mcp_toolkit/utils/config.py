"""Configuration management for AI MCP Toolkit."""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Configuration class for AI MCP Toolkit."""
    
    # Server configuration
    host: str = field(default_factory=lambda: os.getenv("MCP_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("MCP_PORT", "8000")))
    
    # Ollama configuration
    ollama_host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "localhost"))
    ollama_port: int = field(default_factory=lambda: int(os.getenv("OLLAMA_PORT", "11434")))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:14b"))
    
    # GPU backend configuration
    gpu_backend: str = field(default_factory=lambda: os.getenv("GPU_BACKEND", "auto"))  # auto, cuda, metal, cpu
    
    # Embedding configuration
    embedding_provider: str = field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "ollama"))  # ollama or openai
    embedding_model: Optional[str] = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL"))  # Auto-detected per provider if not set
    embedding_chunk_size: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_CHUNK_SIZE", "1000")))
    embedding_enabled: bool = field(default_factory=lambda: os.getenv("EMBEDDING_ENABLED", "true").lower() == "true")
    
    # UI configuration
    ui_host: str = field(default_factory=lambda: os.getenv("UI_HOST", "localhost"))
    ui_port: int = field(default_factory=lambda: int(os.getenv("UI_PORT", "8501")))
    
    # Logging configuration
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: Optional[str] = field(default_factory=lambda: os.getenv("LOG_FILE"))
    
    # Text processing configuration
    max_text_length: int = field(default_factory=lambda: int(os.getenv("MAX_TEXT_LENGTH", "1000000")))  # 1M chars (~1MB text)
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "1000")))
    
    # Model configuration
    temperature: float = field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.1")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "2000")))
    
    # Cache configuration
    enable_cache: bool = field(default_factory=lambda: os.getenv("ENABLE_CACHE", "true").lower() == "true")
    cache_ttl: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL", "3600")))  # 1 hour
    
    # Security configuration
    enable_cors: bool = field(default_factory=lambda: os.getenv("ENABLE_CORS", "true").lower() == "true")
    cors_origins: list = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))
    
    # Data directories
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "~/.ai-mcp-toolkit")).expanduser())
    cache_dir: Path = field(default_factory=lambda: Path(os.getenv("CACHE_DIR", "~/.ai-mcp-toolkit/cache")).expanduser())
    models_dir: Path = field(default_factory=lambda: Path(os.getenv("MODELS_DIR", "~/.ai-mcp-toolkit/models")).expanduser())
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Convert string paths to Path objects if needed
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir).expanduser()
        if isinstance(self.cache_dir, str):
            self.cache_dir = Path(self.cache_dir).expanduser()
        if isinstance(self.models_dir, str):
            self.models_dir = Path(self.models_dir).expanduser()
        
        # Ensure data directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}")
        
        if self.ollama_port < 1 or self.ollama_port > 65535:
            raise ValueError(f"Invalid Ollama port number: {self.ollama_port}")
        
        if self.ui_port < 1 or self.ui_port > 65535:
            raise ValueError(f"Invalid UI port number: {self.ui_port}")
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.log_level}")
        
        if self.max_text_length <= 0:
            raise ValueError(f"Invalid max_text_length: {self.max_text_length}")
        
        if self.chunk_size <= 0:
            raise ValueError(f"Invalid chunk_size: {self.chunk_size}")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Invalid temperature: {self.temperature}")
        
        if self.max_tokens <= 0:
            raise ValueError(f"Invalid max_tokens: {self.max_tokens}")
    
    @classmethod
    def from_file(cls, config_file: Path) -> 'Config':
        """Load configuration from a YAML file."""
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    def to_file(self, config_file: Path) -> None:
        """Save configuration to a YAML file."""
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
        
        # Convert Path objects to strings for serialization
        for key, value in data.items():
            if isinstance(value, Path):
                data[key] = str(value)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, indent=2)
    
    def get_ollama_url(self) -> str:
        """Get the full Ollama URL."""
        return f"http://{self.ollama_host}:{self.ollama_port}"
    
    def get_server_url(self) -> str:
        """Get the full server URL."""
        return f"http://{self.host}:{self.port}"
    
    def get_ui_url(self) -> str:
        """Get the full UI URL."""
        return f"http://{self.ui_host}:{self.ui_port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
    
    def update(self, **kwargs) -> None:
        """Update configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
        
        # Re-validate after updates
        self._validate_config()


def load_config(config_file: Optional[Path] = None) -> Config:
    """Load configuration from file or environment variables."""
    if config_file and config_file.exists():
        return Config.from_file(config_file)
    
    # Try default config file locations
    default_locations = [
        Path("config.yaml"),
        Path("config.yml"),
        Path("~/.ai-mcp-toolkit/config.yaml").expanduser(),
        Path("/etc/ai-mcp-toolkit/config.yaml"),
    ]
    
    for location in default_locations:
        if location.exists():
            return Config.from_file(location)
    
    # Fallback to environment variables and defaults
    return Config()


def get_default_config_path() -> Path:
    """Get the default configuration file path."""
    return Path("~/.ai-mcp-toolkit/config.yaml").expanduser()


def create_default_config() -> None:
    """Create a default configuration file."""
    config = Config()
    config_path = get_default_config_path()
    config.to_file(config_path)
    # Configuration created successfully - caller will handle messaging
