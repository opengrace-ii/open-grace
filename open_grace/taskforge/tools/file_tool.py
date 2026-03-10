"""
File Tool for TaskForge.
Handles file system operations like read, write, move, copy, delete, list.
"""

import os
import shutil
import glob
from pathlib import Path
from typing import List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool, ToolOutput


class FileToolInput(BaseModel):
    """Input schema for FileTool."""
    action: str = Field(..., description="Action to perform: read, write, list, move, copy, delete, mkdir, exists, info")
    path: str = Field(..., description="Path to the file or directory")
    content: Optional[str] = Field(default=None, description="Content for write operations")
    destination: Optional[str] = Field(default=None, description="Destination path for move/copy")
    recursive: bool = Field(default=False, description="Whether to operate recursively")


class FileTool(BaseTool):
    """
    Tool for file system operations.
    
    Supported actions:
    - read: Read file contents
    - write: Write content to file
    - list: List directory contents
    - move: Move/rename files
    - copy: Copy files
    - delete: Delete files or directories
    - mkdir: Create directories
    - exists: Check if path exists
    - info: Get file/directory info
    - glob: Find files matching pattern
    """
    
    name = "file"
    description = "Perform file system operations (read, write, list, move, copy, delete)"
    input_schema = FileToolInput
    
    # Maximum file size for reading (10MB)
    MAX_READ_SIZE = 10 * 1024 * 1024
    
    VALID_ACTIONS = [
        "read", "write", "list", "move", "copy", "delete", 
        "mkdir", "exists", "info", "glob"
    ]
    
    def run(self, action: str, path: str, content: Optional[str] = None,
            destination: Optional[str] = None, recursive: bool = False,
            **kwargs) -> ToolOutput:
        """
        Execute a file operation.
        
        Args:
            action: The operation to perform
            path: Source path
            content: Content for write operations
            destination: Destination path for move/copy
            recursive: Whether to operate recursively
            
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
                path=path,
                content=content,
                destination=destination,
                recursive=recursive
            )
            
            # Execute the action
            method = getattr(self, f"_action_{action}")
            result = method(path, content, destination, recursive)
            
            return ToolOutput(success=True, result=result)
            
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"File operation error: {str(e)}"
            )
    
    def _action_read(self, path: str, *args) -> dict:
        """Read file contents."""
        file_path = Path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        size = file_path.stat().st_size
        if size > self.MAX_READ_SIZE:
            raise ValueError(f"File too large ({size} bytes). Max: {self.MAX_READ_SIZE} bytes")
        
        content = file_path.read_text(encoding='utf-8', errors='replace')
        return {
            "path": str(file_path.absolute()),
            "content": content,
            "size": size,
            "lines": len(content.splitlines())
        }
    
    def _action_write(self, path: str, content: Optional[str], *args) -> dict:
        """Write content to file."""
        file_path = Path(path)
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if content is None:
            content = ""
        
        file_path.write_text(content, encoding='utf-8')
        
        return {
            "path": str(file_path.absolute()),
            "bytes_written": len(content.encode('utf-8')),
            "action": "write"
        }
    
    def _action_list(self, path: str, *args) -> dict:
        """List directory contents."""
        dir_path = Path(path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        entries = []
        for entry in dir_path.iterdir():
            stat = entry.stat()
            entries.append({
                "name": entry.name,
                "path": str(entry.absolute()),
                "type": "directory" if entry.is_dir() else "file",
                "size": stat.st_size if entry.is_file() else None,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return {
            "path": str(dir_path.absolute()),
            "entries": sorted(entries, key=lambda x: (x["type"] != "directory", x["name"].lower())),
            "count": len(entries)
        }
    
    def _action_move(self, path: str, content: Optional[str], destination: Optional[str], *args) -> dict:
        """Move/rename file or directory."""
        if not destination:
            raise ValueError("Destination required for move operation")
        
        src = Path(path)
        dst = Path(destination)
        
        if not src.exists():
            raise FileNotFoundError(f"Source not found: {path}")
        
        shutil.move(str(src), str(dst))
        
        return {
            "source": str(src.absolute()),
            "destination": str(dst.absolute()),
            "action": "move"
        }
    
    def _action_copy(self, path: str, content: Optional[str], destination: Optional[str], 
                     recursive: bool = False) -> dict:
        """Copy file or directory."""
        if not destination:
            raise ValueError("Destination required for copy operation")
        
        src = Path(path)
        dst = Path(destination)
        
        if not src.exists():
            raise FileNotFoundError(f"Source not found: {path}")
        
        if src.is_dir():
            if recursive:
                shutil.copytree(str(src), str(dst))
            else:
                raise ValueError("Use recursive=True to copy directories")
        else:
            shutil.copy2(str(src), str(dst))
        
        return {
            "source": str(src.absolute()),
            "destination": str(dst.absolute()),
            "action": "copy"
        }
    
    def _action_delete(self, path: str, content: Optional[str], destination: Optional[str], 
                       recursive: bool = False) -> dict:
        """Delete file or directory."""
        target = Path(path)
        
        if not target.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        if target.is_dir():
            if recursive:
                shutil.rmtree(str(target))
            else:
                target.rmdir()
        else:
            target.unlink()
        
        return {
            "path": str(target.absolute()),
            "action": "delete"
        }
    
    def _action_mkdir(self, path: str, *args) -> dict:
        """Create directory."""
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        return {
            "path": str(dir_path.absolute()),
            "action": "mkdir"
        }
    
    def _action_exists(self, path: str, *args) -> dict:
        """Check if path exists."""
        file_path = Path(path)
        
        return {
            "path": str(file_path.absolute()),
            "exists": file_path.exists(),
            "is_file": file_path.is_file() if file_path.exists() else False,
            "is_directory": file_path.is_dir() if file_path.exists() else False
        }
    
    def _action_info(self, path: str, *args) -> dict:
        """Get file/directory information."""
        file_path = Path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        stat = file_path.stat()
        
        return {
            "path": str(file_path.absolute()),
            "name": file_path.name,
            "exists": True,
            "is_file": file_path.is_file(),
            "is_directory": file_path.is_dir(),
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:]
        }
    
    def _action_glob(self, path: str, *args) -> dict:
        """Find files matching pattern."""
        matches = glob.glob(path, recursive=True)
        
        return {
            "pattern": path,
            "matches": matches,
            "count": len(matches)
        }
