"""
SQL Tool for TaskForge.
Handles database operations for SQLite databases.
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool, ToolOutput


class SQLToolInput(BaseModel):
    """Input schema for SQLTool."""
    action: str = Field(..., description="Action: query, execute, tables, schema, backup")
    database: str = Field(..., description="Path to the SQLite database file")
    query: Optional[str] = Field(default=None, description="SQL query to execute")
    params: Optional[List[Any]] = Field(default=None, description="Query parameters")


class SQLTool(BaseTool):
    """
    Tool for SQLite database operations.
    
    Supported actions:
    - query: Execute SELECT queries
    - execute: Execute INSERT, UPDATE, DELETE, CREATE, etc.
    - tables: List all tables in the database
    - schema: Get schema for a specific table
    - backup: Create a backup of the database
    """
    
    name = "sql"
    description = "Execute SQL queries on SQLite databases"
    input_schema = SQLToolInput
    
    VALID_ACTIONS = ["query", "execute", "tables", "schema", "backup"]
    
    # Maximum rows to return for queries
    MAX_ROWS = 1000
    
    def run(self, action: str, database: str, query: Optional[str] = None,
            params: Optional[List[Any]] = None, **kwargs) -> ToolOutput:
        """
        Execute a SQL operation.
        
        Args:
            action: The SQL action to perform
            database: Path to the SQLite database
            query: SQL query to execute
            params: Query parameters for parameterized queries
            
        Returns:
            ToolOutput with operation results
        """
        try:
            # Validate action
            action = action.lower()
            if action not in self.VALID_ACTIONS:
                return ToolOutput(
                    success=False,
                    error=f"Invalid action '{action}'. Valid actions: {', '.join(self.VALID_ACTIONS)}"
                )
            
            # Validate input
            self.validate_input(
                action=action,
                database=database,
                query=query,
                params=params
            )
            
            db_path = Path(database).resolve()
            
            # Check database exists (except for certain operations)
            if action not in ["tables"] and not db_path.exists():
                # Create database directory if needed
                db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Execute the action
            method = getattr(self, f"_action_{action}")
            result = method(db_path, query, params)
            
            return ToolOutput(success=True, result=result)
            
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"SQL operation error: {str(e)}"
            )
    
    def _get_connection(self, db_path: Path) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _action_query(self, db_path: Path, query: Optional[str], 
                      params: Optional[List[Any]]) -> dict:
        """Execute a SELECT query."""
        if not query:
            raise ValueError("Query is required for query action")
        
        conn = self._get_connection(db_path)
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows = cursor.fetchmany(self.MAX_ROWS)
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            results = []
            for row in rows:
                results.append(dict(row))
            
            return {
                "columns": columns,
                "rows": results,
                "count": len(results),
                "truncated": len(results) == self.MAX_ROWS,
                "query": query
            }
        finally:
            conn.close()
    
    def _action_execute(self, db_path: Path, query: Optional[str], 
                        params: Optional[List[Any]]) -> dict:
        """Execute a non-SELECT query (INSERT, UPDATE, DELETE, etc.)."""
        if not query:
            raise ValueError("Query is required for execute action")
        
        conn = self._get_connection(db_path)
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            
            return {
                "rows_affected": cursor.rowcount,
                "last_row_id": cursor.lastrowid,
                "query": query
            }
        finally:
            conn.close()
    
    def _action_tables(self, db_path: Path, *args) -> dict:
        """List all tables in the database."""
        conn = self._get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            
            tables = [row[0] for row in cursor.fetchall()]
            
            return {
                "tables": tables,
                "count": len(tables),
                "database": str(db_path)
            }
        finally:
            conn.close()
    
    def _action_schema(self, db_path: Path, query: Optional[str], *args) -> dict:
        """Get schema for a table."""
        if not query:
            raise ValueError("Table name is required for schema action (pass as query)")
        
        table_name = query.strip()
        
        conn = self._get_connection(db_path)
        try:
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "cid": row[0],
                    "name": row[1],
                    "type": row[2],
                    "notnull": bool(row[3]),
                    "default": row[4],
                    "pk": bool(row[5])
                })
            
            # Get indexes
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = []
            for row in cursor.fetchall():
                indexes.append({
                    "name": row[1],
                    "unique": bool(row[2])
                })
            
            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = []
            for row in cursor.fetchall():
                foreign_keys.append({
                    "from": row[3],
                    "table": row[2],
                    "to": row[4]
                })
            
            return {
                "table": table_name,
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys
            }
        finally:
            conn.close()
    
    def _action_backup(self, db_path: Path, *args) -> dict:
        """Create a backup of the database."""
        import shutil
        from datetime import datetime
        
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"
        
        shutil.copy2(str(db_path), str(backup_path))
        
        return {
            "original": str(db_path),
            "backup": str(backup_path),
            "timestamp": timestamp
        }
