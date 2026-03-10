"""
Git Tool for TaskForge.
Handles Git operations like status, commit, push, pull, branch, log.
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool, ToolOutput
from tools.shell_tool import ShellTool


class GitToolInput(BaseModel):
    """Input schema for GitTool."""
    action: str = Field(..., description="Git action: status, log, branch, commit, push, pull, clone, init, add, diff")
    path: str = Field(default=".", description="Path to the git repository")
    message: Optional[str] = Field(default=None, description="Commit message")
    branch: Optional[str] = Field(default=None, description="Branch name")
    remote: Optional[str] = Field(default="origin", description="Remote name")
    url: Optional[str] = Field(default=None, description="Repository URL for clone")
    files: Optional[List[str]] = Field(default=None, description="Files to add/stage")


class GitTool(BaseTool):
    """
    Tool for Git operations.
    
    Supported actions:
    - status: Show working tree status
    - log: Show commit logs
    - branch: List, create, or switch branches
    - commit: Record changes to repository
    - push: Push changes to remote
    - pull: Fetch and merge from remote
    - clone: Clone a repository
    - init: Initialize a new repository
    - add: Add files to staging area
    - diff: Show changes between commits
    """
    
    name = "git"
    description = "Execute Git commands (status, commit, push, pull, branch, log, etc.)"
    input_schema = GitToolInput
    
    VALID_ACTIONS = [
        "status", "log", "branch", "commit", "push", "pull", 
        "clone", "init", "add", "diff", "fetch", "checkout", "remote"
    ]
    
    def __init__(self):
        super().__init__()
        self.shell = ShellTool()
    
    def _is_git_repo(self, path: str) -> bool:
        """Check if path is a git repository."""
        git_dir = Path(path) / ".git"
        return git_dir.exists() and git_dir.is_dir()
    
    def run(self, action: str, path: str = ".", message: Optional[str] = None,
            branch: Optional[str] = None, remote: str = "origin", 
            url: Optional[str] = None, files: Optional[List[str]] = None,
            **kwargs) -> ToolOutput:
        """
        Execute a Git operation.
        
        Args:
            action: The Git action to perform
            path: Path to the repository
            message: Commit message
            branch: Branch name
            remote: Remote name
            url: Repository URL for clone
            files: Files to stage
            
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
                message=message,
                branch=branch,
                remote=remote,
                url=url,
                files=files
            )
            
            repo_path = Path(path).resolve()
            
            # Check if it's a git repo (except for init and clone)
            if action not in ["init", "clone"] and not self._is_git_repo(repo_path):
                return ToolOutput(
                    success=False,
                    error=f"Not a git repository: {repo_path}"
                )
            
            # Execute the action
            method = getattr(self, f"_action_{action}")
            result = method(repo_path, message, branch, remote, url, files)
            
            return ToolOutput(success=True, result=result)
            
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"Git operation error: {str(e)}"
            )
    
    def _run_git(self, repo_path: Path, args: List[str]) -> dict:
        """Run a git command."""
        cmd = ["git"] + args
        result = self.shell.run_safe(cmd, cwd=str(repo_path))
        
        if not result.success:
            raise Exception(result.error or "Git command failed")
        
        return result.result
    
    def _action_status(self, repo_path: Path, *args) -> dict:
        """Get repository status."""
        result = self._run_git(repo_path, ["status", "--porcelain", "-b"])
        lines = result["stdout"].strip().split("\n") if result["stdout"] else []
        
        branch_line = lines[0] if lines else "## HEAD (no branch)"
        file_lines = lines[1:] if len(lines) > 1 else []
        
        staged = []
        unstaged = []
        untracked = []
        
        for line in file_lines:
            if not line:
                continue
            status = line[:2]
            filename = line[3:]
            
            if status[0] != " " and status[0] != "?":
                staged.append({"file": filename, "status": status[0]})
            if status[1] != " " and status[1] != "?":
                unstaged.append({"file": filename, "status": status[1]})
            if status == "??":
                untracked.append(filename)
        
        return {
            "branch": branch_line.replace("## ", ""),
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
            "clean": len(file_lines) == 0
        }
    
    def _action_log(self, repo_path: Path, *args) -> dict:
        """Get commit log."""
        result = self._run_git(repo_path, [
            "log", "--oneline", "--decorate", 
            "--format=%h|%an|%ae|%ad|%s", "-20"
        ])
        
        commits = []
        for line in result["stdout"].strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 4)
            if len(parts) == 5:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "email": parts[2],
                    "date": parts[3],
                    "message": parts[4]
                })
        
        return {
            "commits": commits,
            "count": len(commits)
        }
    
    def _action_branch(self, repo_path: Path, message: Optional[str], 
                       branch: Optional[str], *args) -> dict:
        """List or switch branches."""
        if branch:
            # Switch to or create branch
            result = self._run_git(repo_path, ["checkout", "-b", branch])
            return {
                "action": "create_and_switch",
                "branch": branch,
                "output": result["stdout"]
            }
        else:
            # List branches
            result = self._run_git(repo_path, ["branch", "-a"])
            branches = []
            current = None
            
            for line in result["stdout"].strip().split("\n"):
                if not line:
                    continue
                line = line.strip()
                if line.startswith("*"):
                    current = line[2:]
                    branches.append({"name": current, "current": True})
                else:
                    branches.append({"name": line, "current": False})
            
            return {
                "branches": branches,
                "current": current
            }
    
    def _action_commit(self, repo_path: Path, message: Optional[str], *args) -> dict:
        """Create a commit."""
        if not message:
            raise ValueError("Commit message is required")
        
        result = self._run_git(repo_path, ["commit", "-m", message])
        
        return {
            "message": message,
            "output": result["stdout"]
        }
    
    def _action_push(self, repo_path: Path, message: Optional[str], 
                     branch: Optional[str], remote: str, *args) -> dict:
        """Push to remote."""
        cmd = ["push", remote]
        if branch:
            cmd.append(branch)
        
        result = self._run_git(repo_path, cmd)
        
        return {
            "remote": remote,
            "branch": branch,
            "output": result["stdout"]
        }
    
    def _action_pull(self, repo_path: Path, message: Optional[str], 
                     branch: Optional[str], remote: str, *args) -> dict:
        """Pull from remote."""
        cmd = ["pull", remote]
        if branch:
            cmd.append(branch)
        
        result = self._run_git(repo_path, cmd)
        
        return {
            "remote": remote,
            "branch": branch,
            "output": result["stdout"]
        }
    
    def _action_clone(self, repo_path: Path, message: Optional[str], 
                      branch: Optional[str], remote: str, url: Optional[str], *args) -> dict:
        """Clone a repository."""
        if not url:
            raise ValueError("Repository URL is required for clone")
        
        result = self._run_git(repo_path.parent, ["clone", url, repo_path.name])
        
        return {
            "url": url,
            "destination": str(repo_path),
            "output": result["stdout"]
        }
    
    def _action_init(self, repo_path: Path, *args) -> dict:
        """Initialize a new repository."""
        result = self._run_git(repo_path, ["init"])
        
        return {
            "path": str(repo_path),
            "output": result["stdout"]
        }
    
    def _action_add(self, repo_path: Path, message: Optional[str], 
                    branch: Optional[str], remote: str, url: Optional[str], 
                    files: Optional[List[str]], *args) -> dict:
        """Add files to staging area."""
        if not files:
            # Add all changes
            result = self._run_git(repo_path, ["add", "."])
            return {
                "files": ["all"],
                "output": result["stdout"]
            }
        else:
            for file in files:
                self._run_git(repo_path, ["add", file])
            return {
                "files": files,
                "count": len(files)
            }
    
    def _action_diff(self, repo_path: Path, *args) -> dict:
        """Show diff."""
        result = self._run_git(repo_path, ["diff"])
        
        return {
            "diff": result["stdout"],
            "has_changes": bool(result["stdout"].strip())
        }
    
    def _action_fetch(self, repo_path: Path, message: Optional[str], 
                      branch: Optional[str], remote: str, *args) -> dict:
        """Fetch from remote."""
        result = self._run_git(repo_path, ["fetch", remote])
        
        return {
            "remote": remote,
            "output": result["stdout"]
        }
    
    def _action_checkout(self, repo_path: Path, message: Optional[str], 
                         branch: Optional[str], *args) -> dict:
        """Checkout a branch."""
        if not branch:
            raise ValueError("Branch name is required for checkout")
        
        result = self._run_git(repo_path, ["checkout", branch])
        
        return {
            "branch": branch,
            "output": result["stdout"]
        }
    
    def _action_remote(self, repo_path: Path, *args) -> dict:
        """List remotes."""
        result = self._run_git(repo_path, ["remote", "-v"])
        
        remotes = []
        for line in result["stdout"].strip().split("\n"):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                remotes.append({
                    "name": parts[0],
                    "url": parts[1],
                    "type": parts[2].strip("()") if len(parts) > 2 else "fetch"
                })
        
        return {
            "remotes": remotes
        }
