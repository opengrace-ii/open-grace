import pytest
from unittest.mock import MagicMock

# Assuming standard initialization for agents
from open_grace.agents.base_agent import BaseAgent
from open_grace.agents.coder_agent import CoderAgent
from open_grace.agents.sysadmin_agent import SysAdminAgent

class DumbMockRouter:
    async def generate(self, prompt, system=None, strategy=None, response_model=None):
        from open_grace.model_router.clients import ModelResponse, ModelProvider
        content = "Mocked response"
        if response_model:
            if response_model.__name__ == 'ExecutionPlan':
                content = response_model(
                    reasoning="Mock reasoning",
                    estimated_total_minutes=30,
                    steps=[],
                    task_id="mock",
                    original_task="mock"
                )
            else:
                try:
                    content = response_model()
                except:
                    pass
        return ModelResponse(
            content=content,
            provider=ModelProvider.OLLAMA,
            model="mock-model",
            usage={"prompt_tokens": 10, "completion_tokens": 10},
            latency_ms=10.0,
            metadata={}
        )

    async def chat(self, messages, strategy=None, response_model=None):
        from open_grace.model_router.clients import ModelResponse, ModelProvider
        return ModelResponse(
            content="Mocked chat response",
            provider=ModelProvider.OLLAMA,
            model="mock-model",
            usage={"prompt_tokens": 10, "completion_tokens": 10},
            latency_ms=10.0,
            metadata={}
        )

class MockAgent(BaseAgent):
    async def process_task(self, task):
        return "Mocked task result"

@pytest.fixture
def mock_dependencies():
    return {
        "model_router": DumbMockRouter(),
        "memory": MagicMock(),
        "vault": MagicMock()
    }

def test_base_agent_initialization(mock_dependencies):
    agent = MockAgent(
        name="TestBase",
        model_router=mock_dependencies["model_router"],
        vector_store=mock_dependencies["memory"]
    )
    assert agent.name == "TestBase"
    # In the refactored BaseAgent, tools is likely _tools
    assert len(getattr(agent, "_tools", {})) == 0

def test_coder_agent_initialization(mock_dependencies):
    agent = CoderAgent(
        model_router=mock_dependencies["model_router"],
        vector_store=mock_dependencies["memory"]
    )
    assert agent.name == "Coder"
    
    # Check if tools are registered
    assert hasattr(agent, "_tools")
    assert isinstance(agent._tools, dict)

@pytest.mark.asyncio
async def test_agent_think(mock_dependencies):
    agent = MockAgent(
        name="TestThink",
        model_router=mock_dependencies["model_router"]
    )
    response = await agent.think("Hello")
    assert response == "Mocked response"

@pytest.mark.asyncio
async def test_agent_execute(mock_dependencies):
    from open_grace.agents.planner_agent import PlannerAgent
    agent = PlannerAgent(
        model_router=mock_dependencies["model_router"]
    )
    # This will call create_plan which calls think
    plan = await agent.execute("Test task")
    assert hasattr(plan, "steps")
