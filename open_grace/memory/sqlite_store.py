"""
SQLite Memory Store - Structured data storage for Open Grace.

Extends the TaskForge memory system with additional capabilities
for the Open Grace platform.
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager


@dataclass
class MemoryEntry:
    """A memory entry."""
    id: Optional[int] = None
    timestamp: str = ""
    session_id: str = ""
    entry_type: str = ""
    content: str = ""
    metadata: str = "{}"
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class SQLiteMemoryStore:
    """
    SQLite-based memory store for Open Grace.
    
    Extends TaskForge memory with additional tables for:
    - Agent states
    - System events
    - Configuration history
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the memory store.
        
        Args:
            db_path: Path to SQLite database
        """
        if db_path is None:
            home = Path.home()
            db_dir = home / ".open_grace"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "memory.db")
        
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            # Core memory table (from TaskForge)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Tasks table (from TaskForge)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    plan TEXT,
                    results TEXT,
                    success BOOLEAN NOT NULL,
                    execution_time_ms INTEGER
                )
            """)
            
            # Sessions table (from TaskForge)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_active TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Agent states (new for Open Grace)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_states (
                    agent_id TEXT PRIMARY KEY,
                    agent_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    state_data TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # System events (new for Open Grace)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            
            # Configuration history (new for Open Grace)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    config_key TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    changed_by TEXT
                )
            """)
            
            # Episodic Memory (new for Open Grace Contextual RAG)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    context TEXT NOT NULL,
                    action TEXT NOT NULL,
                    result TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            conn.commit()
    
    def save_entry(self, entry: MemoryEntry) -> int:
        """Save a memory entry."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO memory (timestamp, session_id, entry_type, content, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (entry.timestamp, entry.session_id, entry.entry_type,
                 entry.content, entry.metadata)
            )
            conn.commit()
            return cursor.lastrowid or 0
    
    def get_entries(self, entry_type: Optional[str] = None,
                    session_id: Optional[str] = None,
                    limit: int = 100) -> List[MemoryEntry]:
        """Get memory entries."""
        with self._get_connection() as conn:
            query = "SELECT * FROM memory WHERE 1=1"
            params: List[Any] = []
            
            if entry_type:
                query += " AND entry_type = ?"
                params.append(entry_type)
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                MemoryEntry(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    session_id=row["session_id"],
                    entry_type=row["entry_type"],
                    content=row["content"],
                    metadata=row["metadata"]
                )
                for row in rows
            ]

# Global memory store instance
_memory_store: Optional[SQLiteMemoryStore] = None

def get_memory_store() -> SQLiteMemoryStore:
    """Get the global memory store instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = SQLiteMemoryStore()
    return _memory_store

def set_memory_store(store: SQLiteMemoryStore):
    """Set the global memory store instance."""
    global _memory_store
    _memory_store = store
    
    def save_agent_state(self, agent_id: str, agent_type: str,
                        status: str, state_data: Dict[str, Any]) -> None:
        """Save agent state."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO agent_states (agent_id, agent_type, status, state_data, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (agent_id, agent_type, status, json.dumps(state_data), datetime.now().isoformat())
            )
            conn.commit()
    
    def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent state."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM agent_states WHERE agent_id = ?",
                (agent_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    "agent_id": row["agent_id"],
                    "agent_type": row["agent_type"],
                    "status": row["status"],
                    "state_data": json.loads(row["state_data"]),
                    "updated_at": row["updated_at"]
                }
            return None
    
    def log_event(self, event_type: str, source: str, data: Dict[str, Any]) -> None:
        """Log a system event."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO system_events (timestamp, event_type, source, data)
                VALUES (?, ?, ?, ?)
                """,
                (datetime.now().isoformat(), event_type, source, json.dumps(data))
            )
            conn.commit()
    
    def get_events(self, event_type: Optional[str] = None,
                   source: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Get system events."""
        with self._get_connection() as conn:
            query = "SELECT * FROM system_events WHERE 1=1"
            params: List[Any] = []
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "event_type": row["event_type"],
                    "source": row["source"],
                    "data": json.loads(row["data"])
                }
                for row in rows
            ]

    def clone_session(self, source_session_id: str, target_session_id: str) -> bool:
        """
        Clone all memory entries from one session to another to support DAG branching.
        
        Args:
            source_session_id: The session ID to clone from
            target_session_id: The new session ID to create
            
        Returns:
            True if entries were cloned, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO memory (timestamp, session_id, entry_type, content, metadata)
                SELECT ?, ?, entry_type, content, metadata
                FROM memory WHERE session_id = ?
                """,
                (datetime.now().isoformat(), target_session_id, source_session_id)
            )
            count = cursor.rowcount
            
            # Clone tasks related to the session as well
            conn.execute(
                """
                INSERT INTO tasks (timestamp, session_id, task_description, plan, results, success, execution_time_ms)
                SELECT ?, ?, task_description, plan, results, success, execution_time_ms
                FROM tasks WHERE session_id = ?
                """,
                (datetime.now().isoformat(), target_session_id, source_session_id)
            )
            
            conn.commit()
            return count > 0

    def save_episode(self, session_id: str, agent_id: str, context: str, action: str, result: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """Save an episodic memory entry."""
        if metadata is None:
            metadata = {}
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO episodic_memory (timestamp, session_id, agent_id, context, action, result, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (datetime.now().isoformat(), session_id, agent_id, context, action, result, json.dumps(metadata))
            )
            conn.commit()
            return cursor.lastrowid or 0
            
    def get_episodes(self, session_id: Optional[str] = None, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve episodic memory entries."""
        with self._get_connection() as conn:
            query = "SELECT * FROM episodic_memory WHERE 1=1"
            params: List[Any] = []
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "session_id": row["session_id"],
                    "agent_id": row["agent_id"],
                    "context": row["context"],
                    "action": row["action"],
                    "result": row["result"],
                    "metadata": json.loads(row["metadata"])
                }
                for row in rows
            ]