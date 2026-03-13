"""
Knowledge Store - Permanent storage for distilled insights and facts.

Uses SQLite for structured metadata and FAISS/persistent VectorStore for 
semantic retrieval of knowledge items.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from open_grace.memory.sqlite_store import get_memory_store, SQLiteMemoryStore
from open_grace.memory.vector_store import get_vector_store, VectorStore

class KnowledgeItem:
    """A single piece of distilled knowledge."""
    def __init__(self, key: str, content: str, category: str, 
                 metadata: Optional[Dict[str, Any]] = None, 
                 quality_score: Optional[float] = None,
                 critique: Optional[str] = None,
                 item_id: Optional[int] = None):
        self.item_id = item_id
        self.key = key
        self.content = content
        self.category = category
        self.metadata = metadata or {}
        self.quality_score = quality_score
        self.critique = critique
        self.timestamp = datetime.now().isoformat()

class KnowledgeStore:
    """
    Manages the lifecycle of distilled knowledge.
    
    Responsibilities:
    - Storing insights from agents
    - Retrieving relevant knowledge for new tasks
    - Deduplicating and updating existing knowledge
    """
    
    def __init__(self, 
                 sqlite_store: Optional[SQLiteMemoryStore] = None, 
                 vector_store: Optional[VectorStore] = None):
        self.sqlite = sqlite_store or get_memory_store()
        self.vector = vector_store or get_vector_store()
        self._init_tables()

    def _init_tables(self):
        """Ensure the knowledge table exists in SQLite."""
        with self.sqlite._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    quality_score REAL,
                    critique TEXT,
                    metadata TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL
                )
            """)
            # Migration to add new columns if they don't exist
            try:
                conn.execute("ALTER TABLE knowledge_items ADD COLUMN quality_score REAL")
            except: pass
            try:
                conn.execute("ALTER TABLE knowledge_items ADD COLUMN critique TEXT")
            except: pass
            conn.commit()

    def store_insight(self, key: str, content: str, category: str, 
                      quality_score: Optional[float] = None,
                      critique: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Store a new piece of distilled knowledge.
        
        Args:
            key: A short descriptor (e.g., "React Performance Pattern")
            content: The detailed insight/finding
            category: Type of knowledge (e.g., "coding", "research", "system")
            quality_score: Numeric score (0-10) of the original result quality
            critique: Qualitative feedback or "lessons learned"
            metadata: Additional context (e.g., source task_id)
        """
        metadata = metadata or {}
        timestamp = datetime.now().isoformat()
        
        with self.sqlite._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO knowledge_items (key, category, content, quality_score, critique, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (key, category, content, quality_score, critique, json.dumps(metadata), timestamp)
            )
            conn.commit()
            item_id = cursor.lastrowid
        
        # Also index in vector store for semantic search
        self.vector.add_document(
            doc_id=f"kb_{item_id}",
            content=f"{key}: {content}",
            metadata={
                "type": "knowledge", 
                "category": category, 
                "kb_id": item_id, 
                "quality_score": quality_score,
                "critique": critique,
                **metadata
            }
        )
        
        return item_id

    def query_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant knowledge across categories.
        """
        results = self.vector.search(query, top_k=limit)
        knowledge_results = []
        
        for res in results:
            if res.document.metadata.get("type") == "knowledge":
                knowledge_results.append({
                    "id": res.document.metadata.get("kb_id"),
                    "key": res.document.content.split(":")[0],
                    "content": res.document.content,
                    "score": res.score,
                    "metadata": res.document.metadata
                })
                
        return knowledge_results

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve all items in a specific category."""
        with self.sqlite._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM knowledge_items WHERE category = ? ORDER BY timestamp DESC",
                (category,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

_knowledge_store: Optional[KnowledgeStore] = None

def get_knowledge_store() -> KnowledgeStore:
    global _knowledge_store
    if _knowledge_store is None:
        _knowledge_store = KnowledgeStore()
    return _knowledge_store
