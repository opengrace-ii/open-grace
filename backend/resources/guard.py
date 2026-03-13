from typing import Dict
from .logs import get_diagnostics_logger

logger = get_diagnostics_logger()

class CreditGuard:
    def __init__(self):
        self.rules = {
            "max_tool_calls": 10,
            "max_retries": 2,
            "max_tokens": 8000
        }
        self.sessions: Dict[str, Dict] = {}

    def start_session(self, session_id: str):
        self.sessions[session_id] = {
            "tool_calls": 0,
            "retries": 0,
            "tokens": 0
        }

    def record_tool_call(self, session_id: str) -> bool:
        if session_id not in self.sessions:
            self.start_session(session_id)
        
        self.sessions[session_id]["tool_calls"] += 1
        if self.sessions[session_id]["tool_calls"] > self.rules["max_tool_calls"]:
            logger.warning(f"CreditGuard limit reached: Tool calls exceeded for {session_id}")
            return False
        return True

    def record_retry(self, session_id: str) -> bool:
        if session_id not in self.sessions:
            self.start_session(session_id)
            
        self.sessions[session_id]["retries"] += 1
        if self.sessions[session_id]["retries"] > self.rules["max_retries"]:
            logger.warning(f"CreditGuard limit reached: Retries exceeded for {session_id}")
            return False
        return True

    def record_tokens(self, session_id: str, tokens: int) -> bool:
        if session_id not in self.sessions:
            self.start_session(session_id)
            
        self.sessions[session_id]["tokens"] += tokens
        if self.sessions[session_id]["tokens"] > self.rules["max_tokens"]:
            logger.warning(f"CreditGuard limit reached: Tokens exceeded for {session_id}")
            return False
        return True

credit_guard = CreditGuard()
