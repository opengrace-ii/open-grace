"""
Model Router - Hybrid AI model routing for Open Grace.

Routes requests between local models (Ollama) and external providers
(OpenAI, Anthropic, Gemini, DeepSeek) based on task complexity,
cost constraints, and availability.
"""

from open_grace.model_router.router import ModelRouter, RoutingDecision
from open_grace.model_router.clients import (
    OllamaClient,
    OpenAIClient,
    AnthropicClient,
    GeminiClient,
    DeepSeekClient,
)

__all__ = [
    "ModelRouter",
    "RoutingDecision",
    "OllamaClient",
    "OpenAIClient",
    "AnthropicClient",
    "GeminiClient",
    "DeepSeekClient",
]