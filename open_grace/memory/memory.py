"""
Memory System for TaskForge.
Stores conversation history, task results, and user preferences.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: Optional[int] = None
    timestamp: str = ""
    session_id: str = ""
    entry_type: str = ""  # 'task', 'conversation', 'preference', 'action'
    content: str = ""
    metadata: str = "{}"  # JSON string
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class TaskMemory:
    """Memory of a completed task."""
    task: str
    plan: List[str]
    results: List[Dict[str, Any]]
    success: bool
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class MemoryStore:
    """
    SQLite-based memory store for TaskForge.
    
    Features:
    - Persistent storage of conversations and tasks
    - Session management
    - Preference storage
    - Search capabilities
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to ~/.taskforge/memory.db
            home = Path.home()
            db_dir = home / ".taskforge"
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
        """Initialize the database schema."""
        with self._get_connection() as conn:
            # Main memory table
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
            
            # Tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    plan TEXT,  -- JSON array
                    results TEXT,  -- JSON array
                    success BOOLEAN NOT NULL,
                    execution_time_ms INTEGER
                )
            """)
            
            # Preferences table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_active TEXT NOT NULL,
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
            return cursor.lastrowid
    
    def get_entries(self, entry_type: Optional[str] = None, 
                    session_id: Optional[str] = None,
                    limit: int = 100) -> List[MemoryEntry]:
        """Get memory entries with optional filtering."""
        with self._get_connection() as conn:
            query = "SELECT * FROM memory WHERE 1=1"
            params = []
            
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
    
    def save_task(self, task_memory: TaskMemory, session_id: str = "default") -> int:
        """Save a task execution memory."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (timestamp, session_id, task_description, plan, results, success)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    task_memory.timestamp,
                    session_id,
                    task_memory.task,
                    json.dumps(task_memory.plan),
                    json.dumps(task_memory.results),
                    task_memory.success
                )
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_tasks(self, session_id: Optional[str] = None, 
                  limit: int = 50) -> List[Dict[str, Any]]:
        """Get task history."""
        with self._get_connection() as conn:
            query = "SELECT * FROM tasks"
            params = []
            
            if session_id:
                query += " WHERE session_id = ?"
                params.append(session_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "session_id": row["session_id"],
                    "task": row["task_description"],
                    "plan": json.loads(row["plan"] or "[]"),
                    "results": json.loads(row["results"] or "[]"),
                    "success": row["success"]
                }
                for row in rows
            ]
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO preferences (key, value, updated_at)
                VALUES (?, ?, ?)
                """,
                (key, json.dumps(value), datetime.now().isoformat())
            )
            conn.commit()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM preferences WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            
            if row:
                return json.loads(row["value"])
            return default
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all user preferences."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT key, value FROM preferences")
            rows = cursor.fetchall()
            
            return {row["key"]: json.loads(row["value"]) for row in rows}
    
    def create_session(self, session_id: str, metadata: Optional[Dict] = None):
        """Create a new session."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions (id, created_at, last_active, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, now, now, json.dumps(metadata or {}))
            )
            conn.commit()
    
    def update_session(self, session_id: str):
        """Update session last active time."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET last_active = ? WHERE id = ?",
                (datetime.now().isoformat(), session_id)
            )
            conn.commit()
    
    def get_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent sessions."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM sessions 
                ORDER BY last_active DESC 
                LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "created_at": row["created_at"],
                    "last_active": row["last_active"],
                    "metadata": json.loads(row["metadata"] or "{}")
                }
                for row in rows
            ]
    
    def search(self, query: str, entry_type: Optional[str] = None) -> List[MemoryEntry]:
        """Search memory entries."""
        with self._get_connection() as conn:
            sql = "SELECT * FROM memory WHERE content LIKE ?"
            params = [f"%{query}%"]
            
            if entry_type:
                sql += " AND entry_type = ?"
                params.append(entry_type)
            
            sql += " ORDER BY timestamp DESC"
            
            cursor = conn.execute(sql, params)
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
    
    def clear(self, entry_type: Optional[str] = None, 
              session_id: Optional[str] = None):
        """Clear memory entries."""
        with self._get_connection() as conn:
            query = "DELETE FROM memory WHERE 1=1"
            params = []
            
            if entry_type:
                query += " AND entry_type = ?"
                params.append(entry_type)
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            conn.execute(query, params)
            conn.commit()
    
    def get_stats(self) -> Dict[str, int]:
        """Get memory statistics."""
        with self._get_connection() as conn:
            stats = {}
            
            cursor = conn.execute("SELECT COUNT(*) FROM memory")
            stats["total_entries"] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM tasks")
            stats["total_tasks"] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM sessions")
            stats["total_sessions"] = cursor.fetchone()[0]
            
            cursor = conn.execute(
                "SELECT entry_type, COUNT(*) FROM memory GROUP BY entry_type"
            )
            stats["by_type"] = {row[0]: row[1] for row in cursor.fetchall()}
            
            return stats


# Global memory store instance
_memory_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    """Get the global memory store instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store


def set_memory_store(store: MemoryStore):
    """Set the global memory store instance."""
    global _memory_store
    _memory_store = store
