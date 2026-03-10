"""
Permission System for TaskForge.
Handles permission prompts, allowlists, and security policies.
"""

import os
from enum import Enum
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


class PermissionLevel(Enum):
    """Permission levels for actions."""
    ALLOW = "allow"           # Always allow
    PROMPT = "prompt"         # Ask for confirmation
    DENY = "deny"             # Always deny


class ActionCategory(Enum):
    """Categories of actions for permission management."""
    SHELL = "shell"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    GIT_PUSH = "git_push"
    SQL_WRITE = "sql_write"
    SYSTEM = "system"


@dataclass
class PermissionRule:
    """A permission rule for a specific action pattern."""
    category: ActionCategory
    pattern: str
    level: PermissionLevel
    description: str = ""
    
    def matches(self, action: str) -> bool:
        """Check if an action matches this rule."""
        import fnmatch
        return fnmatch.fnmatch(action.lower(), self.pattern.lower())


@dataclass
class PermissionLog:
    """Log entry for permission decisions."""
    timestamp: str
    action: str
    category: str
    granted: bool
    user_response: Optional[str] = None


class PermissionManager:
    """
    Manages permissions for TaskForge actions.
    
    Features:
    - Configurable permission levels per action category
    - Pattern-based rules
    - Session-based allowlists
    - Permission logging
    """
    
    DEFAULT_RULES = [
        PermissionRule(ActionCategory.SHELL, "rm -rf /*", PermissionLevel.DENY, "Dangerous delete"),
        PermissionRule(ActionCategory.SHELL, "rm -rf /", PermissionLevel.DENY, "Dangerous delete"),
        PermissionRule(ActionCategory.SHELL, "*", PermissionLevel.PROMPT, "All shell commands"),
        PermissionRule(ActionCategory.FILE_DELETE, "*", PermissionLevel.PROMPT, "File deletion"),
        PermissionRule(ActionCategory.FILE_WRITE, "*", PermissionLevel.ALLOW, "File writes"),
        PermissionRule(ActionCategory.GIT_PUSH, "*", PermissionLevel.PROMPT, "Git push operations"),
        PermissionRule(ActionCategory.SQL_WRITE, "*", PermissionLevel.PROMPT, "Database modifications"),
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        self.rules: List[PermissionRule] = []
        self.session_allowlist: Dict[str, datetime] = {}
        self.permission_log: List[PermissionLog] = []
        self.prompt_callback: Optional[Callable[[str], bool]] = None
        
        self.config_path = config_path or os.path.expanduser("~/.taskforge/permissions.json")
        self._load_config()
        
        # Add default rules if none loaded
        if not self.rules:
            self.rules = self.DEFAULT_RULES.copy()
    
    def _load_config(self):
        """Load permission configuration from file."""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file) as f:
                    data = json.load(f)
                    for rule_data in data.get("rules", []):
                        self.rules.append(PermissionRule(
                            category=ActionCategory(rule_data["category"]),
                            pattern=rule_data["pattern"],
                            level=PermissionLevel(rule_data["level"]),
                            description=rule_data.get("description", "")
                        ))
            except Exception as e:
                print(f"Warning: Could not load permission config: {e}")
    
    def _save_config(self):
        """Save permission configuration to file."""
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "rules": [
                {
                    "category": rule.category.value,
                    "pattern": rule.pattern,
                    "level": rule.level.value,
                    "description": rule.description
                }
                for rule in self.rules
            ]
        }
        
        with open(config_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def set_prompt_callback(self, callback: Callable[[str], bool]):
        """Set a custom callback for permission prompts."""
        self.prompt_callback = callback
    
    def check_permission(self, action: str, category: ActionCategory) -> bool:
        """
        Check if an action is permitted.
        
        Args:
            action: The action to check
            category: The category of the action
            
        Returns:
            True if permitted, False otherwise
        """
        # Check session allowlist
        action_key = f"{category.value}:{action}"
        if action_key in self.session_allowlist:
            return True
        
        # Find matching rule
        for rule in self.rules:
            if rule.category == category and rule.matches(action):
                if rule.level == PermissionLevel.ALLOW:
                    self._log_permission(action, category.value, True)
                    return True
                elif rule.level == PermissionLevel.DENY:
                    self._log_permission(action, category.value, False)
                    return False
                elif rule.level == PermissionLevel.PROMPT:
                    return self._prompt_user(action, category, action_key)
        
        # Default to prompt if no rule matches
        return self._prompt_user(action, category, action_key)
    
    def _prompt_user(self, action: str, category: ActionCategory, action_key: str) -> bool:
        """Prompt the user for permission."""
        if self.prompt_callback:
            granted = self.prompt_callback(action)
        else:
            # Default CLI prompt
            print(f"\n[Permission Required]")
            print(f"Category: {category.value}")
            print(f"Action: {action}")
            print(f"\nAllow this action?")
            print("  [y] Yes    [n] No    [a] Always (session)")
            
            try:
                response = input("Choice [y/n/a]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                response = "n"
            
            if response == "a":
                self.session_allowlist[action_key] = datetime.now()
                granted = True
            else:
                granted = response in ["y", "yes"]
        
        self._log_permission(action, category.value, granted)
        return granted
    
    def _log_permission(self, action: str, category: str, granted: bool):
        """Log a permission decision."""
        log_entry = PermissionLog(
            timestamp=datetime.now().isoformat(),
            action=action,
            category=category,
            granted=granted
        )
        self.permission_log.append(log_entry)
    
    def add_rule(self, category: ActionCategory, pattern: str, 
                 level: PermissionLevel, description: str = ""):
        """Add a new permission rule."""
        self.rules.append(PermissionRule(category, pattern, level, description))
        self._save_config()
    
    def remove_rule(self, category: ActionCategory, pattern: str):
        """Remove a permission rule."""
        self.rules = [
            rule for rule in self.rules 
            if not (rule.category == category and rule.pattern == pattern)
        ]
        self._save_config()
    
    def get_rules(self) -> List[PermissionRule]:
        """Get all permission rules."""
        return self.rules.copy()
    
    def get_log(self) -> List[PermissionLog]:
        """Get permission decision log."""
        return self.permission_log.copy()
    
    def clear_session_allowlist(self):
        """Clear the session allowlist."""
        self.session_allowlist.clear()


# Global permission manager instance
_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """Get the global permission manager instance."""
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager


def set_permission_manager(manager: PermissionManager):
    """Set the global permission manager instance."""
    global _permission_manager
    _permission_manager = manager


def confirm(action: str, category: ActionCategory = ActionCategory.SHELL) -> bool:
    """
    Convenience function to check permission for an action.
    
    Args:
        action: The action to check
        category: The category of the action
        
    Returns:
        True if permitted, False otherwise
    """
    return get_permission_manager().check_permission(action, category)
