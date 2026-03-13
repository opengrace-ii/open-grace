import os
import shutil
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

class WorkspaceManager:
    """
    Manages the physical directories and file isolation for agent projects.
    Prevents agents from writing to unauthorized parts of the system.
    """
    def __init__(self, base_path: str = "/home/opengrace/open_grace/workspace"):
        self.base_path = Path(base_path).absolute()
        self.projects_path = self.base_path / "projects"
        self._ensure_dirs()

    def _ensure_dirs(self):
        self.projects_path.mkdir(parents=True, exist_ok=True)

    def create_project_workspace(self, project_name: str) -> Path:
        """
        Creates a dedicated directory for a project.
        """
        # Sanitize project name
        safe_name = "".join(c for c in project_name if c.isalnum() or c in ("-", "_")).strip()
        project_dir = self.projects_path / safe_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"WorkspaceManager: Created workspace at {project_dir}")
        return project_dir

    def resolve_path(self, project_name: str, relative_path: str) -> Path:
        """
        Safely resolves a path within a project workspace.
        Raises ValueError if the path escapes the workspace.
        """
        project_dir = self.projects_path / project_name
        target_path = (project_dir / relative_path).resolve()
        
        if not str(target_path).startswith(str(project_dir)):
            raise ValueError(f"Path escape detected: {relative_path} is outside {project_dir}")
            
        return target_path

    def list_project_files(self, project_name: str) -> List[str]:
        project_dir = self.projects_path / project_name
        if not project_dir.exists():
            return []
            
        files = []
        for root, _, filenames in os.walk(project_dir):
            for f in filenames:
                rel_path = os.path.relpath(os.path.join(root, f), project_dir)
                files.append(rel_path)
        return files

    def cleanup_project(self, project_name: str):
        project_dir = self.projects_path / project_name
        if project_dir.exists():
            shutil.rmtree(project_dir)
            logger.info(f"WorkspaceManager: Cleaned up project {project_name}")

# Global instance
_workspace_manager: Optional[WorkspaceManager] = None

def get_workspace_manager() -> WorkspaceManager:
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager()
    return _workspace_manager
