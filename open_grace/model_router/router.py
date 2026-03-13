"""
Model Router - Intelligent routing between local and external AI models.

The router decides which model to use based on:
- Task complexity
- Cost constraints
- Model availability
- User preferences
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Callable, Type, TypeVar
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, ValidationError

T = TypeVar('T', bound=BaseModel)

from open_grace.model_router.clients import (
    BaseModelClient,
    OllamaClient,
    OpenAIClient,
    AnthropicClient,
    GeminiClient,
    DeepSeekClient,
    ModelProvider,
    ModelResponse,
)
from open_grace.security.vault import get_vault
from open_grace.observability.logger import get_logger


class RoutingStrategy(Enum):
    """Routing strategies."""
    LOCAL_ONLY = "local_only"           # Only use local models
    COST_OPTIMIZED = "cost_optimized"   # Prefer cheaper options
    QUALITY_FIRST = "quality_first"     # Prefer best quality
    HYBRID = "hybrid"                   # Smart routing based on task


@dataclass
class RoutingDecision:
    """Record of a routing decision."""
    task: str
    provider: ModelProvider
    model: str
    strategy: RoutingStrategy
    reasoning: str
    estimated_cost: float
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ModelRouter:
    """
    Intelligent router for AI model selection.
    
    Routes requests between local (Ollama) and external providers based on:
    - Task complexity analysis
    - Cost constraints
    - Provider availability
    - User preferences
    
    Usage:
        router = ModelRouter()
        response = router.generate("Write a Python function", strategy=RoutingStrategy.HYBRID)
    """
    
    # Task complexity indicators
    COMPLEXITY_INDICATORS = {
        "high": [
            "complex", "architecture", "design pattern", "algorithm",
            "optimize", "refactor", "debug", "analyze", "review",
            "explain in detail", "comprehensive", "thorough"
        ],
        "medium": [
            "create", "write", "implement", "build", "generate",
            "convert", "transform", "summarize", "paraphrase"
        ],
        "low": [
            "list", "show", "display", "get", "find", "check",
            "simple", "basic", "quick"
        ]
    }
    
    # Model capabilities (rough estimate)
    MODEL_CAPABILITIES = {
        "llama3": {"coding": 0.8, "reasoning": 0.8, "speed": 0.9},
        "mistral": {"coding": 0.85, "reasoning": 0.85, "speed": 0.9},
        "qwen": {"coding": 0.9, "reasoning": 0.85, "speed": 0.85},
        "deepseek": {"coding": 0.95, "reasoning": 0.9, "speed": 0.8},
        "gpt-4": {"coding": 0.95, "reasoning": 0.95, "speed": 0.9},
        "gpt-4-turbo": {"coding": 0.95, "reasoning": 0.95, "speed": 0.9},
        "gpt-3.5-turbo": {"coding": 0.85, "reasoning": 0.8, "speed": 0.95},
        "claude-3-opus-20240229": {"coding": 0.95, "reasoning": 0.95, "speed": 0.85},
        "claude-3-sonnet-20240229": {"coding": 0.9, "reasoning": 0.9, "speed": 0.9},
        "claude-3-haiku-20240307": {"coding": 0.8, "reasoning": 0.8, "speed": 0.95},
        "gemini-pro": {"coding": 0.85, "reasoning": 0.85, "speed": 0.9},
        "deepseek-chat": {"coding": 0.9, "reasoning": 0.85, "speed": 0.9},
        "deepseek-coder": {"coding": 0.95, "reasoning": 0.85, "speed": 0.9},
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the model router.
        
        Args:
            config_path: Path to router configuration
        """
        self.config_path = config_path or os.path.expanduser("~/.open_grace/router_config.json")
        self.vault = get_vault()
        self.logger = get_logger()
        
        # Initialize clients
        self._clients: Dict[ModelProvider, BaseModelClient] = {}
        self._init_clients()
        
        # Load configuration
        self.config = self._load_config()
        
        # Routing history
        self._history: List[RoutingDecision] = []

        # Concurrency control
        self.model_semaphore = asyncio.Semaphore(1)
    
    def _init_clients(self):
        """Initialize all model clients."""
        # Local Ollama (always try)
        try:
            self._clients[ModelProvider.OLLAMA] = OllamaClient()
        except:
            pass
        
        # External providers (need API keys from vault)
        vault = get_vault()
        
        # OpenAI
        openai_key = vault.get_secret("openai_api_key")
        if openai_key:
            self._clients[ModelProvider.OPENAI] = OpenAIClient(api_key=openai_key)
        
        # Anthropic
        anthropic_key = vault.get_secret("anthropic_api_key")
        if anthropic_key:
            self._clients[ModelProvider.ANTHROPIC] = AnthropicClient(api_key=anthropic_key)
        
        # Gemini
        gemini_key = vault.get_secret("gemini_api_key")
        if gemini_key:
            self._clients[ModelProvider.GEMINI] = GeminiClient(api_key=gemini_key)
        
        # DeepSeek
        deepseek_key = vault.get_secret("deepseek_api_key")
        if deepseek_key:
            self._clients[ModelProvider.DEEPSEEK] = DeepSeekClient(api_key=deepseek_key)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load router configuration."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path) as f:
                    return json.load(f)
            except:
                pass
        
        # Default configuration
        return {
            "default_strategy": "hybrid",
            "local_models": ["llama3", "mistral", "qwen"],
            "external_models": {
                "coding": "deepseek-coder",
                "reasoning": "claude-3-opus-20240229",
                "general": "gpt-4-turbo"
            },
            "cost_budget_daily": 10.0,  # USD
            "cost_budget_monthly": 100.0,  # USD
            "fallback_enabled": True,
            "preferred_local": "llama3"
        }
    
    def _save_config(self):
        """Save router configuration."""
        Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _analyze_complexity(self, task: str) -> str:
        """Analyze task complexity."""
        task_lower = task.lower()
        
        # Count complexity indicators
        high_count = sum(1 for indicator in self.COMPLEXITY_INDICATORS["high"] 
                        if indicator in task_lower)
        medium_count = sum(1 for indicator in self.COMPLEXITY_INDICATORS["medium"] 
                          if indicator in task_lower)
        low_count = sum(1 for indicator in self.COMPLEXITY_INDICATORS["low"] 
                       if indicator in task_lower)
        
        # Determine complexity
        if high_count > 0 or len(task) > 500:
            return "high"
        elif medium_count > 0 or len(task) > 200:
            return "medium"
        else:
            return "low"
    
    async def _select_model(self, task: str, strategy: RoutingStrategy, explicit_model: Optional[str] = None) -> tuple[ModelProvider, str]:
        """Select the best model for a task."""
        # Check for explicit model override first
        if explicit_model:
            # Try to find which provider has this model
            for provider, client in self._clients.items():
                if await client.is_available():
                    # For Ollama, the model name is dynamic
                    if provider == ModelProvider.OLLAMA:
                        # We trust the user knows if the model is in Ollama
                        # or we could check client.list_models()
                        return provider, explicit_model
                    
                    # For external providers, we usually check their specific model names
                    # or if the client config matches exactly
                    if client.config.model_name == explicit_model:
                        return provider, explicit_model
            
            # Fallback handling for common aliases or substring matches
            for provider, client in self._clients.items():
                if await client.is_available():
                    if explicit_model.lower() in client.config.model_name.lower():
                        return provider, client.config.model_name

        complexity = self._analyze_complexity(task)
        
        # Check which providers are available
        available = {}
        for p, c in self._clients.items():
            if await c.is_available():
                available[p] = c
        
        if not available:
            raise Exception("No model providers available")
        
        # Strategy-based selection
        if strategy == RoutingStrategy.LOCAL_ONLY:
            if ModelProvider.OLLAMA in available:
                # Intelligent local selection
                if any(word in task.lower() for word in ["code", "python", "javascript", "implement"]):
                    return ModelProvider.OLLAMA, "codellama" # Specific coding model
                if any(word in task.lower() for word in ["research", "explain", "analyze"]):
                    return ModelProvider.OLLAMA, "qwen" # Good for reasoning
                return ModelProvider.OLLAMA, self.config["preferred_local"]
            raise Exception("Local models not available")
        
        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            # Prefer local (free), then cheapest external
            if ModelProvider.OLLAMA in available:
                return ModelProvider.OLLAMA, self.config["preferred_local"]
            
            # Find cheapest available
            cheapest = None
            cheapest_cost = float('inf')
            for provider, client in available.items():
                if provider != ModelProvider.OLLAMA:
                    cost = client.config.cost_per_1k_input + client.config.cost_per_1k_output
                    if cost < cheapest_cost:
                        cheapest_cost = cost
                        cheapest = provider
            
            if cheapest:
                return cheapest, available[cheapest].config.model_name
        
        elif strategy == RoutingStrategy.QUALITY_FIRST:
            # Always use best available
            if complexity == "high":
                # Prefer Claude or GPT-4 for complex tasks
                for provider in [ModelProvider.ANTHROPIC, ModelProvider.OPENAI]:
                    if provider in available:
                        return provider, available[provider].config.model_name
            
            # For coding, prefer DeepSeek
            if any(word in task.lower() for word in ["code", "program", "function", "class"]):
                if ModelProvider.DEEPSEEK in available:
                    return ModelProvider.DEEPSEEK, "deepseek-coder"
            
            # Fallback to best available
            for provider in [ModelProvider.ANTHROPIC, ModelProvider.OPENAI, 
                           ModelProvider.DEEPSEEK, ModelProvider.OLLAMA]:
                if provider in available:
                    return provider, available[provider].config.model_name
        
        elif strategy == RoutingStrategy.HYBRID:
            # Smart routing based on complexity
            if complexity == "low":
                # Use local for simple tasks
                if ModelProvider.OLLAMA in available:
                    return ModelProvider.OLLAMA, self.config["preferred_local"]
            
            elif complexity == "medium":
                # Use local if available, otherwise cheap external
                if ModelProvider.OLLAMA in available:
                    return ModelProvider.OLLAMA, self.config["preferred_local"]
                
                # Prefer DeepSeek for cost-effective quality
                if ModelProvider.DEEPSEEK in available:
                    return ModelProvider.DEEPSEEK, "deepseek-chat"
            
            elif complexity == "high":
                # Use external for complex tasks
                if any(word in task.lower() for word in ["code", "program", "debug"]):
                    if ModelProvider.DEEPSEEK in available:
                        return ModelProvider.DEEPSEEK, "deepseek-coder"
                
                if ModelProvider.ANTHROPIC in available:
                    return ModelProvider.ANTHROPIC, "claude-3-opus-20240229"
                elif ModelProvider.OPENAI in available:
                    return ModelProvider.OPENAI, "gpt-4-turbo"
        
        # Default fallback
        if ModelProvider.OLLAMA in available:
            return ModelProvider.OLLAMA, self.config["preferred_local"]
        # Last resort: use any available
        provider = list(available.keys())[0]
        return provider, available[provider].config.model_name
    
    def _inject_schema(self, system: Optional[str], response_model: Optional[Type[BaseModel]]) -> Optional[str]:
        if not response_model:
            return system
        schema_json = json.dumps(response_model.model_json_schema())
        instruction = f"Respond ONLY with valid JSON matching the following schema:\n{schema_json}"
        return f"{system}\n\n{instruction}" if system else instruction

    def _parse_content(self, content: str, response_model: Type[BaseModel]) -> BaseModel:
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        return response_model.model_validate_json(content)

    def _record_decision(self, task_hint: str, provider: ModelProvider, model: str, strategy: RoutingStrategy, response: ModelResponse, client: BaseModelClient):
        decision = RoutingDecision(
            task=str(task_hint)[:100] + "..." if len(str(task_hint)) > 100 else str(task_hint),
            provider=provider,
            model=model,
            strategy=strategy,
            reasoning=f"Complexity: {self._analyze_complexity(task_hint)}",
            estimated_cost=client.estimate_cost(
                response.usage.get("prompt_tokens", 0),
                response.usage.get("completion_tokens", 0)
            )
        )
        self._history.append(decision)

    async def generate(
        self, 
        prompt: str, 
        system: Optional[str] = None, 
        strategy: Optional[RoutingStrategy] = None,
        model: Optional[str] = None,
        response_model: Optional[Type[BaseModel]] = None,
        max_retries: int = 3
    ) -> ModelResponse:
        """Generate a response using the best available model."""
        strategy = strategy or RoutingStrategy(self.config.get("default_strategy", "hybrid"))
        provider, actual_model = await self._select_model(prompt, strategy, explicit_model=model)
        client = self._clients.get(provider)
        if not client:
            raise Exception(f"Selected provider {provider} not available")
        
        system_with_schema = self._inject_schema(system, response_model)
        current_prompt = prompt
        
        async with self.model_semaphore:
            for attempt in range(max_retries):
                try:
                    response = await client.generate(current_prompt, system_with_schema)
                    self._record_decision(prompt, provider, actual_model, strategy, response, client)
                    
                    if response_model:
                        try:
                            parsed = self._parse_content(response.content, response_model)
                            response.content = parsed
                            return response
                        except ValidationError as e:
                            if attempt == max_retries - 1:
                                raise e
                            current_prompt += f"\n\nValidation Failed. Error:\n{e}\nPlease correct the JSON output."
                            continue
                    return response
                except Exception as e:
                    import traceback
                    self.logger.error(f"Error in ModelRouter.generate: {e}\n{traceback.format_exc()}")
                    # Simple fallback
                    if self.config.get("fallback_enabled", True) and not isinstance(e, ValidationError):
                        for fallback_provider in [ModelProvider.OLLAMA, ModelProvider.DEEPSEEK]:
                            if fallback_provider in self._clients and fallback_provider != provider:
                                try:
                                    fallback_client = self._clients[fallback_provider]
                                    if await fallback_client.is_available():
                                        response = await fallback_client.generate(current_prompt, system_with_schema)
                                        if response_model:
                                            parsed = self._parse_content(response.content, response_model)
                                            response.content = parsed
                                        return response
                                except Exception:
                                    continue
                    raise e
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        strategy: Optional[RoutingStrategy] = None,
        model: Optional[str] = None,
        response_model: Optional[Type[BaseModel]] = None,
        max_retries: int = 3
    ) -> ModelResponse:
        """Chat using the best available model."""
        last_message = messages[-1]["content"] if messages else ""
        strategy = strategy or RoutingStrategy(self.config.get("default_strategy", "hybrid"))
        provider, actual_model = await self._select_model(last_message, strategy, explicit_model=model)
        client = self._clients.get(provider)
        if not client:
            raise Exception(f"Selected provider {provider} not available")
            
        current_messages = list(messages)
        # Inject schema into the last system message or create one
        if response_model:
            schema_json = json.dumps(response_model.model_json_schema())
            instruction = f"Respond ONLY with valid JSON matching the following schema:\n{schema_json}"
            if current_messages and current_messages[0]["role"] == "system":
                current_messages[0]["content"] += f"\n\n{instruction}"
            else:
                current_messages.insert(0, {"role": "system", "content": instruction})

        async with self.model_semaphore:
            for attempt in range(max_retries):
                try:
                    response = await client.chat(current_messages)
                    self._record_decision(last_message, provider, actual_model, strategy, response, client)
                    
                    if response_model:
                        try:
                            parsed = self._parse_content(response.content, response_model)
                            response.content = parsed
                            return response
                        except ValidationError as e:
                            if attempt == max_retries - 1:
                                raise e
                            current_messages.append({"role": "assistant", "content": response.content})
                            current_messages.append({"role": "user", "content": f"Validation Failed. Error:\n{e}\nPlease correct the JSON output."})
                            continue
                    return response
                except Exception as e:
                    if self.config.get("fallback_enabled", True) and not isinstance(e, ValidationError):
                        for fallback_provider in [ModelProvider.OLLAMA, ModelProvider.DEEPSEEK]:
                            if fallback_provider in self._clients and fallback_provider != provider:
                                try:
                                    fallback_client = self._clients[fallback_provider]
                                    if await fallback_client.is_available():
                                        response = await fallback_client.chat(current_messages)
                                        if response_model:
                                            parsed = self._parse_content(response.content, response_model)
                                            response.content = parsed
                                        return response
                                except Exception:
                                    continue
                    raise e
    
    async def get_available_providers(self) -> List[ModelProvider]:
        """Get list of available providers."""
        available = []
        for p, c in self._clients.items():
            if await c.is_available():
                available.append(p)
        return available
    
    async def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        status = {}
        for provider, client in self._clients.items():
            status[provider.value] = {
                "available": await client.is_available(),
                "model": client.config.model_name,
                "cost_per_1k_input": client.config.cost_per_1k_input,
                "cost_per_1k_output": client.config.cost_per_1k_output
            }
        return status
    
    def get_routing_history(self) -> List[Dict[str, Any]]:
        """Get history of routing decisions."""
        return [asdict(d) for d in self._history]
    
    def set_strategy(self, strategy: RoutingStrategy):
        """Set the default routing strategy."""
        self.config["default_strategy"] = strategy.value
        self._save_config()
    
    async def add_api_key(self, provider: ModelProvider, api_key: str):
        """Add an API key for a provider."""
        key_name = f"{provider.value}_api_key"
        self.vault.set_secret(key_name, api_key, category="api_key", 
                             description=f"API key for {provider.value}")
        
        # Reinitialize client
        if provider == ModelProvider.OPENAI:
            self._clients[provider] = OpenAIClient(api_key=api_key)
        elif provider == ModelProvider.ANTHROPIC:
            self._clients[provider] = AnthropicClient(api_key=api_key)
        elif provider == ModelProvider.GEMINI:
            self._clients[provider] = GeminiClient(api_key=api_key)
        elif provider == ModelProvider.DEEPSEEK:
            self._clients[provider] = DeepSeekClient(api_key=api_key)


# Global router instance
_router: Optional[ModelRouter] = None


def get_router() -> ModelRouter:
    """Get the global router instance."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


def set_router(router: ModelRouter):
    """Set the global router instance."""
    global _router
    _router = router