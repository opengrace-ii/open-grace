import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from open_grace.kernel.orchestrator import (
    GraceOrchestrator,
    TaskStatus,
    AgentStatus,
    Task
)

@pytest.fixture
def orchestrator():
    """Provides a fresh orchestrator instance with mocks."""
    o = GraceOrchestrator()
    o.logger = MagicMock()
    o.vault = MagicMock()
    
    # Mock the router
    o.router = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "mocked response"
    mock_response.provider.value = "mock_provider"
    mock_response.model = "mock_model"
    o.router.generate = MagicMock(return_value=mock_response)
    
    # Needs to be "initialized" without running the real DB setups
    o._initialized = True
    o._task_queue = asyncio.Queue()
    return o

@pytest.mark.asyncio
async def test_agent_registration(orchestrator):
    """Test that an agent can be registered and unregistered."""
    mock_agent = AsyncMock()
    
    agent_id = await orchestrator.register_agent(
        agent_type="coder",
        name="TestCoder",
        capabilities=["python", "git"],
        agent_instance=mock_agent
    )
    
    assert agent_id.startswith("coder_")
    assert agent_id in orchestrator._agents
    assert agent_id in orchestrator._agent_instances
    
    info = orchestrator._agents[agent_id]
    assert info.name == "TestCoder"
    assert info.status == AgentStatus.IDLE
    
    # Unregister
    success = await orchestrator.unregister_agent(agent_id)
    assert success is True
    assert agent_id not in orchestrator._agents
    assert agent_id not in orchestrator._agent_instances

@pytest.mark.asyncio
async def test_agent_selection(orchestrator):
    """Test the upgraded agent selection logic."""
    # Register a coder and a sysadmin
    coder_id = await orchestrator.register_agent(
        "coder", "Coder1", ["python"], AsyncMock()
    )
    sysadmin_id = await orchestrator.register_agent(
        "sysadmin", "Sys1", ["docker"], AsyncMock()
    )
    
    # Explicit type request
    selected = await orchestrator._select_agent(agent_type="coder")
    assert selected == coder_id
    
    # Capability matching via description
    selected_desc = await orchestrator._select_agent(
        agent_type=None, task_description="deploy this docker container"
    )
    assert selected_desc == sysadmin_id
    
    selected_desc2 = await orchestrator._select_agent(
        agent_type=None, task_description="refactor this python bug"
    )
    assert selected_desc2 == coder_id

@pytest.mark.asyncio
async def test_task_execution_fallback(orchestrator):
    """Test that task execution falls back to router async call without blocking."""
    # Create task
    task = Task(
        id="test_task",
        description="Write a haiku",
        status=TaskStatus.PENDING,
        agent_type=None,
        created_at=datetime.now()
    )
    orchestrator._tasks[task.id] = task
    
    # Execute (should hit the router fallback since no agents registered)
    await orchestrator._execute_task(task)
    
    # Verifications
    assert task.status == TaskStatus.COMPLETED
    assert task.result["content"] == "mocked response"
    
    # Ensure it used the synchronous generate, but we can't easily assert to_thread here in a simple unit test
    # without a more complex mock on asyncio.to_thread, but we verify it triggered router.generate
    orchestrator.router.generate.assert_called_once()
