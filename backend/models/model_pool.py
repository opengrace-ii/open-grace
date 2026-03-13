"""
AI Model Clients - Unified interface for multiple LLM providers.

Provides consistent interfaces for:
- Local models via Ollama
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- DeepSeek
"""

import os
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Iterator, Union
from dataclasses import dataclass
from enum import Enum
import httpx
import asyncio


class ModelProvider(Enum):
    """Supported model providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"


@dataclass
class ModelResponse:
    """Standardized response from any model provider."""
    content: str
    provider: ModelProvider
    model: str
    usage: Dict[str, int]
    latency_ms: float
    metadata: Dict[str, Any]


@dataclass
class ModelConfig:
    """Configuration for a model."""
    provider: ModelProvider
    model_name: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    timeout: int = 120
    
    # Cost tracking (per 1K tokens)
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0




class BaseModelClient(ABC):
    """Abstract base class for model clients."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self._client = httpx.AsyncClient(timeout=config.timeout)
    
    async def close(self):
        """Close the underlying HTTP client."""
        await self._client.aclose()
    
    @abstractmethod
    async def generate(self, prompt: str, system: Optional[str] = None) -> ModelResponse:
        """Generate a response from the model."""
        raise NotImplementedError()
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]]) -> ModelResponse:
        """Chat with the model."""
        raise NotImplementedError()
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the model is available."""
        raise NotImplementedError()
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models from this provider."""
        raise NotImplementedError()
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate the cost of a request."""
        input_cost = (input_tokens / 1000) * self.config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * self.config.cost_per_1k_output
        return input_cost + output_cost


class OllamaClient(BaseModelClient):
    """Client for local Ollama models."""
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 model: str = "llama3",
                 temperature: float = 0.7):
        config = ModelConfig(
            provider=ModelProvider.OLLAMA,
            model_name=model,
            temperature=temperature,
            cost_per_1k_input=0.0,  # Local = free
            cost_per_1k_output=0.0
        )
        super().__init__(config)
        self.base_url = base_url.rstrip("/")
    
    async def generate(self, prompt: str, system: Optional[str] = None) -> ModelResponse:
        """Generate using Ollama's generate endpoint."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.config.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        start_time = time.time()
        try:
            response = await self._client.post(url, json=payload, timeout=300.0)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            data = response.json()
            latency = (time.time() - start_time) * 1000
            
            return ModelResponse(
                content=data.get("response", ""),
                provider=ModelProvider.OLLAMA,
                model=self.config.model_name,
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                },
                latency_ms=latency,
                metadata={"done": data.get("done", False)}
            )
        except httpx.ConnectError:
            raise ConnectionError(f"Could not connect to Ollama at {self.base_url}")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    async def chat(self, messages: List[Dict[str, str]]) -> ModelResponse:
        """Chat using Ollama's chat endpoint."""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature
            }
        }
        
        start_time = time.time()
        try:
            response = await self._client.post(url, json=payload, timeout=300.0)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            data = response.json()
            latency = (time.time() - start_time) * 1000
            
            message = data.get("message", {})
            return ModelResponse(
                content=message.get("content", ""),
                provider=ModelProvider.OLLAMA,
                model=self.config.model_name,
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                },
                latency_ms=latency,
                metadata={"done": data.get("done", False)}
            )
        except httpx.ConnectError:
            raise ConnectionError(f"Could not connect to Ollama at {self.base_url}")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    async def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = await self._client.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            response = await self._client.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        except:
            return []


class OpenAIClient(BaseModelClient):
    """Client for OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None, 
                 model: str = "gpt-4",
                 temperature: float = 0.7):
        # Cost estimates (as of 2024)
        costs = {
            "gpt-4": (0.03, 0.06),
            "gpt-4-turbo": (0.01, 0.03),
            "gpt-3.5-turbo": (0.0005, 0.0015)
        }
        input_cost, output_cost = costs.get(model, (0.03, 0.06))
        
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name=model,
            temperature=temperature,
            cost_per_1k_input=input_cost,
            cost_per_1k_output=output_cost
        )
        super().__init__(config)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, prompt: str, system: Optional[str] = None) -> ModelResponse:
        """Generate using OpenAI's completions API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat(messages)
    
    async def chat(self, messages: List[Dict[str, str]]) -> ModelResponse:
        """Chat using OpenAI's chat completions API."""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "stream": False
        }
        
        if self.config.max_tokens:
            payload["max_tokens"] = self.config.max_tokens
        
        start_time = time.time()
        try:
            response = await self._client.post(
                url,
                headers=self._headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            latency = (time.time() - start_time) * 1000
            
            choice = data["choices"][0]
            usage = data.get("usage", {})
            
            return ModelResponse(
                content=choice["message"]["content"],
                provider=ModelProvider.OPENAI,
                model=self.config.model_name,
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                },
                latency_ms=latency,
                metadata={"finish_reason": choice.get("finish_reason")}
            )
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def is_available(self) -> bool:
        """Check if OpenAI API is accessible."""
        if not self.api_key:
            return False
        try:
            response = await self._client.get(
                f"{self.base_url}/models",
                headers=self._headers()
            )
            return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List available OpenAI models."""
        try:
            response = await self._client.get(
                f"{self.base_url}/models",
                headers=self._headers()
            )
            response.raise_for_status()
            models = response.json().get("data", [])
            return [m["id"] for m in models]
        except:
            return []


class AnthropicClient(BaseModelClient):
    """Client for Anthropic Claude API."""
    
    def __init__(self, api_key: Optional[str] = None,
                 model: str = "claude-3-opus-20240229",
                 temperature: float = 0.7):
        costs = {
            "claude-3-opus-20240229": (0.015, 0.075),
            "claude-3-sonnet-20240229": (0.003, 0.015),
            "claude-3-haiku-20240307": (0.00025, 0.00125)
        }
        input_cost, output_cost = costs.get(model, (0.015, 0.075))
        
        config = ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name=model,
            temperature=temperature,
            cost_per_1k_input=input_cost,
            cost_per_1k_output=output_cost
        )
        super().__init__(config)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"
    
    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    async def generate(self, prompt: str, system: Optional[str] = None) -> ModelResponse:
        """Generate using Anthropic's messages API."""
        messages = [{"role": "user", "content": prompt}]
        return await self._chat(messages, system)
    
    async def chat(self, messages: List[Dict[str, str]]) -> ModelResponse:
        """Chat using Anthropic's messages API."""
        return await self._chat(messages)
    
    async def _chat(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> ModelResponse:
        url = f"{self.base_url}/messages"
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "max_tokens": self.config.max_tokens or 4096,
            "temperature": self.config.temperature
        }
        if system:
            payload["system"] = system
        
        start_time = time.time()
        try:
            response = await self._client.post(
                url,
                headers=self._headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            latency = (time.time() - start_time) * 1000
            content = "".join(b["text"] for b in data["content"] if b["type"] == "text")
            usage = data.get("usage", {})
            return ModelResponse(
                content=content,
                provider=ModelProvider.ANTHROPIC,
                model=self.config.model_name,
                usage={
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                },
                latency_ms=latency,
                metadata={"stop_reason": data.get("stop_reason")}
            )
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def list_models(self) -> List[str]:
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]


class GeminiClient(BaseModelClient):
    """Client for Google Gemini API."""
    
    # Available models: gemini-1.5-flash-latest, gemini-1.5-pro-latest, gemini-pro
    DEFAULT_MODEL = "gemini-1.5-flash-latest"
    
    def __init__(self, api_key: Optional[str] = None,
                 model: Optional[str] = None,
                 temperature: float = 0.7):
        if model is None:
            model = self.DEFAULT_MODEL
        config = ModelConfig(
            provider=ModelProvider.GEMINI,
            model_name=model,
            temperature=temperature,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0
        )
        super().__init__(config)
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def generate(self, prompt: str, system: Optional[str] = None) -> ModelResponse:
        """Generate using Gemini API."""
        url = f"{self.base_url}/models/{self.config.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": self.config.temperature}
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        
        start_time = time.time()
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            latency = (time.time() - start_time) * 1000
            candidates = data.get("candidates", [{}])[0]
            content = candidates.get("content", {}).get("parts", [{}])[0].get("text", "")
            usage = data.get("usageMetadata", {})
            return ModelResponse(
                content=content,
                provider=ModelProvider.GEMINI,
                model=self.config.model_name,
                usage={
                    "prompt_tokens": usage.get("promptTokenCount", 0),
                    "completion_tokens": usage.get("candidatesTokenCount", 0),
                    "total_tokens": usage.get("totalTokenCount", 0)
                },
                latency_ms=latency,
                metadata={"finish_reason": candidates.get("finishReason")}
            )
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    async def chat(self, messages: List[Dict[str, str]]) -> ModelResponse:
        """Chat using Gemini API."""
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        url = f"{self.base_url}/models/{self.config.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": self.config.temperature}
        }
        start_time = time.time()
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            latency = (time.time() - start_time) * 1000
            candidates = data.get("candidates", [{}])[0]
            content = candidates.get("content", {}).get("parts", [{}])[0].get("text", "")
            usage = data.get("usageMetadata", {})
            return ModelResponse(
                content=content,
                provider=ModelProvider.GEMINI,
                model=self.config.model_name,
                usage={
                    "prompt_tokens": usage.get("promptTokenCount", 0),
                    "completion_tokens": usage.get("candidatesTokenCount", 0),
                    "total_tokens": usage.get("totalTokenCount", 0)
                },
                latency_ms=latency,
                metadata={"finish_reason": candidates.get("finishReason")}
            )
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    async def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def list_models(self) -> List[str]:
        return ["gemini-pro", "gemini-pro-vision"]


class DeepSeekClient(BaseModelClient):
    """Client for DeepSeek API (best cost-performance for coding)."""
    
    def __init__(self, api_key: Optional[str] = None,
                 model: str = "deepseek-chat",
                 temperature: float = 0.7):
        config = ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_name=model,
            temperature=temperature,
            cost_per_1k_input=0.00014,
            cost_per_1k_output=0.00028
        )
        super().__init__(config)
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com"
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, prompt: str, system: Optional[str] = None) -> ModelResponse:
        """Generate using DeepSeek API."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self.chat(messages)
    
    async def chat(self, messages: List[Dict[str, str]]) -> ModelResponse:
        """Chat using DeepSeek API."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "stream": False
        }
        if self.config.max_tokens:
            payload["max_tokens"] = self.config.max_tokens
        
        start_time = time.time()
        try:
            response = await self._client.post(
                url,
                headers=self._headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            latency = (time.time() - start_time) * 1000
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return ModelResponse(
                content=choice["message"]["content"],
                provider=ModelProvider.DEEPSEEK,
                model=self.config.model_name,
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                },
                latency_ms=latency,
                metadata={"finish_reason": choice.get("finish_reason")}
            )
        except Exception as e:
            raise Exception(f"DeepSeek API error: {str(e)}")
    
    async def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def list_models(self) -> List[str]:
        return ["deepseek-chat", "deepseek-coder"]
