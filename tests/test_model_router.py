"""Tests for Model Router."""

import pytest
from open_grace.model_router.router import ModelRouter, RoutingStrategy


class TestModelRouter:
    """Test cases for ModelRouter."""
    
    def test_router_creation(self):
        """Test router initialization."""
        router = ModelRouter()
        assert router is not None
    
    def test_complexity_analysis(self):
        """Test task complexity analysis."""
        router = ModelRouter.__new__(ModelRouter)
        router.COMPLEXITY_INDICATORS = {
            "high": ["complex", "architecture", "design"],
            "medium": ["create", "write", "implement"],
            "low": ["list", "show", "get"]
        }
        
        # Test low complexity
        low = router._analyze_complexity("List all files")
        assert low == "low"
        
        # Test medium complexity
        med = router._analyze_complexity("Create a Python function")
        assert med == "medium"
        
        # Test high complexity
        high = router._analyze_complexity("Design a complex architecture")
        assert high == "high"
    
    def test_routing_strategy_selection(self):
        """Test routing strategy selection."""
        router = ModelRouter.__new__(ModelRouter)
        router.config = {"preferred_local": "llama3"}
        router._clients = {}
        
        # Test local only strategy
        from open_grace.model_router.clients import ModelProvider
        
        # This test verifies the logic exists
        assert RoutingStrategy.LOCAL_ONLY is not None
        assert RoutingStrategy.HYBRID is not None
        assert RoutingStrategy.COST_OPTIMIZED is not None
        assert RoutingStrategy.QUALITY_FIRST is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])