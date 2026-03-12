import asyncio
import sys
from pydantic import BaseModel

# Add project root to path
sys.path.append("/home/opengrace/open_grace")

from open_grace.model_router.router import ModelRouter

class TestSchema(BaseModel):
    name: str
    age: int
    is_robot: bool

async def main():
    router = ModelRouter()
    # Clear out all real clients so they don't block
    router._clients.clear()
    
    print("Testing generate with Pydantic guardrails...")
    
    # We don't have API keys, but let's see if the fallback/prompt injection works
    # Mocking client response for testing
    class MockClient:
        async def generate(self, prompt, system):
            from open_grace.model_router.clients import ModelResponse, ModelProvider
            # Return some garbage the first time to simulate failure, 
            # then return valid json the second time
            if getattr(self, 'failed', False):
                return ModelResponse(
                    content='{"name": "OG Test", "age": 1, "is_robot": true}',
                    provider=ModelProvider.OPENAI,
                    model="test",
                    usage={}, latency_ms=1, metadata={}
                )
            else:
                self.failed = True
                return ModelResponse(
                    content='I am not outputting JSON right now.',
                    provider=ModelProvider.OPENAI,
                    model="test",
                    usage={}, latency_ms=1, metadata={}
                )
        def estimate_cost(self, a, b): return 0.0
        async def is_available(self): return True
        def __init__(self):
            self.config = type("Config", (), {"model_name": "test", "cost_per_1k_input": 0.0, "cost_per_1k_output": 0.0})()

    from open_grace.model_router.clients import ModelProvider
    router._clients[ModelProvider.OPENAI] = MockClient()
    
    try:
        response = await router.generate("Tell me about yourself", response_model=TestSchema)
        print(f"Success! Parsed object: {response.content}")
        print(f"Type: {type(response.content)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
