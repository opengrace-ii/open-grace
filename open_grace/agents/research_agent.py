"""
Research Agent - Searches and analyzes information.

Specialized agent for:
- Information retrieval
- Document analysis
- Web research (when enabled)
- Data synthesis
- Fact checking
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from open_grace.agents.base_agent import BaseAgent, AgentTask
from open_grace.memory.rag_engine import RAGEngine, get_rag_engine


@dataclass
class ResearchResult:
    """Result of research."""
    query: str
    findings: List[Dict[str, Any]]
    summary: str
    sources: List[str]
    confidence: str  # "high", "medium", "low"


@dataclass
class AnalysisResult:
    """Result of analysis."""
    topic: str
    key_points: List[str]
    insights: List[str]
    recommendations: List[str]


class ResearchAgent(BaseAgent):
    """
    Agent specialized in research and information analysis.
    
    Capabilities:
    - Search indexed documents
    - Analyze and summarize information
    - Compare and contrast data
    - Generate research reports
    - Fact checking
    
    Usage:
        researcher = ResearchAgent()
        result = await researcher.process_task(AgentTask(
            description="Research Python async patterns",
            context={}
        ))
    """
    
    def __init__(self, rag_engine: Optional[RAGEngine] = None, **kwargs):
        """
        Initialize the research agent.
        
        Args:
            rag_engine: RAG engine for document retrieval
        """
        super().__init__(name="Research", **kwargs)
        self.rag_engine = rag_engine or get_rag_engine()
        
        # Register tools
        self.register_tool("search_documents", self._search_documents)
        self.register_tool("summarize", self._summarize)
        self.register_tool("analyze", self._analyze)
    
    async def process_task(self, task: AgentTask) -> Any:
        """
        Process a research task.
        
        Args:
            task: The research task
            
        Returns:
            Research results
        """
        description = task.description.lower()
        
        # Route to appropriate handler
        if any(word in description for word in ["search", "find", "lookup", "retrieve"]):
            return await self.search(task.description, task.context.get("query"))
        
        elif any(word in description for word in ["summarize", "summary", "tldr"]):
            return await self.summarize(task.context.get("text"), task.context.get("max_length"))
        
        elif any(word in description for word in ["analyze", "analysis", "compare", "contrast"]):
            return await self.analyze(task.description, task.context)
        
        elif any(word in description for word in ["report", "research", "investigate", "study"]):
            return await self.research(task.description, task.context)
        
        else:
            # Default: general research
            return await self.research(task.description, task.context)
    
    async def search(self, description: str, query: Optional[str] = None) -> ResearchResult:
        """
        Search for information in indexed documents.
        
        Args:
            description: Description of what to search for
            query: Specific search query
            
        Returns:
            ResearchResult with findings
        """
        if query is None:
            query = description
        
        # Use RAG to search
        response = self.rag_engine.query(query)
        
        # Parse findings
        findings = []
        for source in response.sources:
            findings.append({
                "source": source['id'],
                "relevance": source['score'],
                "content": "Retrieved from document"
            })
        
        return ResearchResult(
            query=query,
            findings=findings,
            summary=response.answer,
            sources=[s['id'] for s in response.sources],
            confidence="high" if response.sources and response.sources[0]['score'] > 0.8 else "medium"
        )
    
    async def summarize(self, text: Optional[str],
                       max_length: str = "3 paragraphs") -> str:
        """
        Summarize text.
        
        Args:
            text: Text to summarize
            max_length: Desired length
            
        Returns:
            Summary
        """
        if not text:
            return "No text provided to summarize"
        
        system_prompt = f"""You are a summarization expert. Create a clear, concise summary.

Guidelines:
- Length: {max_length}
- Capture main points
- Maintain original meaning
- Use clear, simple language
- Include key details only"""
        
        user_prompt = f"Summarize the following:\n\n{text[:4000]}"
        
        return await self.think(user_prompt, system=system_prompt)
    
    async def analyze(self, topic: str, 
                     context: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Analyze a topic in depth.
        
        Args:
            topic: Topic to analyze
            context: Additional context
            
        Returns:
            AnalysisResult
        """
        context = context or {}
        
        # Build analysis prompt
        system_prompt = """You are an analysis expert. Provide a thorough analysis including:
1. Key points (main findings)
2. Insights (deeper understanding)
3. Recommendations (actionable advice)

Respond in JSON format:
{
  "key_points": ["point 1", "point 2"],
  "insights": ["insight 1", "insight 2"],
  "recommendations": ["recommendation 1"]
}"""
        
        user_prompt = f"Analyze: {topic}\n\n"
        if context.get("data"):
            user_prompt += f"Data: {json.dumps(context['data'], indent=2)}\n\n"
        user_prompt += "Provide a comprehensive analysis."
        
        response = await self.think(user_prompt, system=system_prompt)
        
        try:
            # Extract JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            data = json.loads(response[json_start:json_end])
            
            return AnalysisResult(
                topic=topic,
                key_points=data.get("key_points", []),
                insights=data.get("insights", []),
                recommendations=data.get("recommendations", [])
            )
        except:
            # Fallback
            return AnalysisResult(
                topic=topic,
                key_points=["Analysis completed"],
                insights=["See summary for details"],
                recommendations=[]
            )
    
    async def research(self, topic: str,
                      context: Optional[Dict[str, Any]] = None) -> ResearchResult:
        """
        Conduct comprehensive research on a topic.
        
        Args:
            topic: Research topic
            context: Additional context
            
        Returns:
            ResearchResult
        """
        context = context or {}
        
        # First, search for relevant documents
        search_result = await self.search(topic, topic)
        
        # Then, analyze the findings
        analysis = await self.analyze(topic, {"data": search_result.findings})
        
        # Generate comprehensive summary
        system_prompt = """You are a research expert. Synthesize information into a comprehensive report.

Structure:
1. Executive Summary
2. Key Findings
3. Detailed Analysis
4. Conclusions
5. Recommendations

Be thorough but concise."""
        
        user_prompt = f"""Research Topic: {topic}

Findings:
{json.dumps(search_result.findings, indent=2)}

Analysis:
- Key Points: {', '.join(analysis.key_points)}
- Insights: {', '.join(analysis.insights)}

Write a comprehensive research report."""
        
        summary = await self.think(user_prompt, system=system_prompt)
        
        return ResearchResult(
            query=topic,
            findings=search_result.findings,
            summary=summary,
            sources=search_result.sources,
            confidence=search_result.confidence
        )
    
    async def compare(self, items: List[str],
                     criteria: List[str]) -> Dict[str, Any]:
        """
        Compare multiple items based on criteria.
        
        Args:
            items: Items to compare
            criteria: Comparison criteria
            
        Returns:
            Comparison results
        """
        system_prompt = """You are a comparison expert. Compare items objectively based on the given criteria.

Provide:
1. Side-by-side comparison
2. Pros/cons for each item
3. Overall recommendation

Be objective and data-driven."""
        
        user_prompt = f"""Compare these items: {', '.join(items)}

Criteria: {', '.join(criteria)}

Provide a detailed comparison."""
        
        comparison = await self.think(user_prompt, system=system_prompt)
        
        return {
            "items": items,
            "criteria": criteria,
            "comparison": comparison
        }
    
    async def _search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Tool: Search documents."""
        response = self.rag_engine.query(query)
        return [
            {
                "id": s['id'],
                "score": s['score'],
                "content": response.answer
            }
            for s in response.sources
        ]
    
    async def _summarize(self, text: str, max_length: str = "3 paragraphs") -> str:
        """Tool: Summarize text."""
        return await self.summarize(text, max_length)
    
    async def _analyze(self, topic: str) -> Dict[str, Any]:
        """Tool: Analyze topic."""
        result = await self.analyze(topic)
        return {
            "key_points": result.key_points,
            "insights": result.insights,
            "recommendations": result.recommendations
        }