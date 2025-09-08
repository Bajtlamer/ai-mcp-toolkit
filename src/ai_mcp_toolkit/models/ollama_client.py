"""Ollama client integration for AI model support."""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
import time

from ..utils.config import Config
from ..utils.logger import get_logger


@dataclass
class OllamaModel:
    """Represents an Ollama model."""
    name: str
    size: int
    digest: str
    modified_at: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: str  # 'user', 'assistant', 'system'
    content: str


@dataclass
class CompletionResponse:
    """Represents a completion response."""
    response: str
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, config: Config):
        """Initialize Ollama client."""
        self.config = config
        self.base_url = config.get_ollama_url()
        self.model = config.ollama_model
        self.logger = get_logger(__name__, level=config.log_level)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure session exists."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300)
            )
    
    async def health_check(self) -> bool:
        """Check if Ollama server is healthy."""
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                return response.status == 200
        except Exception as e:
            self.logger.warning(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[OllamaModel]:
        """List available models."""
        await self._ensure_session()
        
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                response.raise_for_status()
                data = await response.json()
                
                models = []
                for model_data in data.get("models", []):
                    models.append(OllamaModel(
                        name=model_data["name"],
                        size=model_data["size"],
                        digest=model_data["digest"],
                        modified_at=model_data["modified_at"],
                        details=model_data.get("details")
                    ))
                
                return models
        
        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            raise
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull/download a model."""
        await self._ensure_session()
        
        try:
            payload = {"name": model_name}
            
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json=payload
            ) as response:
                response.raise_for_status()
                
                # Stream the response to get progress updates
                async for line in response.content:
                    if line:
                        data = json.loads(line.decode())
                        if data.get("status"):
                            self.logger.info(f"Pull status: {data['status']}")
                        if data.get("error"):
                            raise Exception(f"Pull error: {data['error']}")
                
                return True
        
        except Exception as e:
            self.logger.error(f"Failed to pull model {model_name}: {e}")
            raise
    
    async def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> CompletionResponse:
        """Generate text completion."""
        await self._ensure_session()
        
        model_name = model or self.model
        temp = temperature or self.config.temperature
        max_toks = max_tokens or self.config.max_tokens
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temp,
                "num_predict": max_toks
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                
                if stream:
                    # Handle streaming response
                    full_response = ""
                    async for line in response.content:
                        if line:
                            data = json.loads(line.decode())
                            if data.get("response"):
                                full_response += data["response"]
                            
                            if data.get("done", False):
                                return CompletionResponse(
                                    response=full_response,
                                    done=True,
                                    total_duration=data.get("total_duration"),
                                    load_duration=data.get("load_duration"),
                                    prompt_eval_count=data.get("prompt_eval_count"),
                                    eval_count=data.get("eval_count"),
                                    eval_duration=data.get("eval_duration")
                                )
                else:
                    # Handle single response
                    data = await response.json()
                    return CompletionResponse(
                        response=data["response"],
                        done=data.get("done", True),
                        total_duration=data.get("total_duration"),
                        load_duration=data.get("load_duration"),
                        prompt_eval_count=data.get("prompt_eval_count"),
                        eval_count=data.get("eval_count"),
                        eval_duration=data.get("eval_duration")
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to generate completion: {e}")
            raise
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> CompletionResponse:
        """Generate chat completion."""
        await self._ensure_session()
        
        model_name = model or self.model
        temp = temperature or self.config.temperature
        max_toks = max_tokens or self.config.max_tokens
        
        # Convert messages to Ollama format
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": model_name,
            "messages": ollama_messages,
            "stream": stream,
            "options": {
                "temperature": temp,
                "num_predict": max_toks
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                
                if stream:
                    # Handle streaming response
                    full_response = ""
                    async for line in response.content:
                        if line:
                            data = json.loads(line.decode())
                            if data.get("message", {}).get("content"):
                                full_response += data["message"]["content"]
                            
                            if data.get("done", False):
                                return CompletionResponse(
                                    response=full_response,
                                    done=True,
                                    total_duration=data.get("total_duration"),
                                    load_duration=data.get("load_duration"),
                                    prompt_eval_count=data.get("prompt_eval_count"),
                                    eval_count=data.get("eval_count"),
                                    eval_duration=data.get("eval_duration")
                                )
                else:
                    # Handle single response
                    data = await response.json()
                    return CompletionResponse(
                        response=data["message"]["content"],
                        done=data.get("done", True),
                        total_duration=data.get("total_duration"),
                        load_duration=data.get("load_duration"),
                        prompt_eval_count=data.get("prompt_eval_count"),
                        eval_count=data.get("eval_count"),
                        eval_duration=data.get("eval_duration")
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to generate chat completion: {e}")
            raise
    
    async def embeddings(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Generate text embeddings."""
        await self._ensure_session()
        
        model_name = model or self.model
        
        payload = {
            "model": model_name,
            "prompt": text
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("embedding", [])
        
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    async def ensure_model_available(self, model_name: Optional[str] = None) -> bool:
        """Ensure a model is available, pull if necessary."""
        model_name = model_name or self.model
        
        try:
            models = await self.list_models()
            model_names = [m.name for m in models]
            
            if model_name in model_names:
                return True
            
            # Try to pull the model
            self.logger.info(f"Model {model_name} not found locally. Attempting to pull...")
            await self.pull_model(model_name)
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to ensure model {model_name} is available: {e}")
            return False


# Convenience functions
async def create_client(config: Optional[Config] = None) -> OllamaClient:
    """Create and return a configured Ollama client."""
    config = config or Config()
    return OllamaClient(config)


async def quick_completion(
    prompt: str,
    system: Optional[str] = None,
    config: Optional[Config] = None
) -> str:
    """Quick text completion using Ollama."""
    config = config or Config()
    
    async with OllamaClient(config) as client:
        # Ensure model is available
        await client.ensure_model_available()
        
        response = await client.generate_completion(
            prompt=prompt,
            system=system
        )
        return response.response


async def quick_chat(
    messages: List[ChatMessage],
    config: Optional[Config] = None
) -> str:
    """Quick chat completion using Ollama."""
    config = config or Config()
    
    async with OllamaClient(config) as client:
        # Ensure model is available
        await client.ensure_model_available()
        
        response = await client.chat_completion(messages=messages)
        return response.response
