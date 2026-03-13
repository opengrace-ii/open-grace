"""
File Editor Tool - Safe file manipulation for Open Grace agents.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from open_grace.plugins.sdk import Plugin, PluginMetadata, PluginType, tool

class FileEditorPlugin(Plugin):
    """Plugin providing core file editing capabilities."""
    
    def __init__(self):
        super().__init__(
            metadata=PluginMetadata(
                name="file_editor",
                version="1.0.0",
                description="Core file editing tools",
                author="Open Grace",
                plugin_type=PluginType.TOOL
            )
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._config = config
        self.register_tool("write_file", self.write_file, permission_level="normal")
        self.register_tool("read_file", self.read_file, permission_level="normal")
        self.register_tool("list_files", self.list_files, permission_level="normal")
        return True

    def _resolve_path(self, path: str) -> Path:
        """Ensure path is within the allowed workspace."""
        base_dir = Path("/home/opengrace/open_grace/workspace")
        target_path = Path(path)
        if not target_path.is_absolute():
            target_path = base_dir / target_path
        
        # Simple security check (could be more robust with real path resolution)
        if not str(target_path).startswith(str(base_dir)):
             raise PermissionError(f"Access to path {path} is restricted to workspace.")
             
        return target_path

    def write_file(self, path: str, content: str) -> str:
        """
        Write content to a file. Creates directories if needed.
        """
        try:
            target = self._resolve_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'w') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def read_file(self, path: str) -> str:
        """
        Read content from a file.
        """
        try:
            target = self._resolve_path(path)
            if not target.exists():
                return f"Error: File {path} does not exist."
            with open(target, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def list_files(self, directory: str = ".") -> List[str]:
        """
        List files in a directory.
        """
        try:
            target = self._resolve_path(directory)
            if not target.is_dir():
                 return [f"Error: {directory} is not a directory."]
            return [str(p.relative_to(target)) for p in target.iterdir()]
        except Exception as e:
            return [f"Error listing files: {e}"]
