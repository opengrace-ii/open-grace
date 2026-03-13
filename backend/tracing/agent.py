import traceback
from .logs import get_diagnostics_logger
from .self_test import run_all_diagnostics

logger = get_diagnostics_logger()

class DebuggingAgent:
    def handle_error(self, e: Exception, context: str):
        stacktrace = "".join(traceback.format_tb(e.__traceback__))
        error_msg = str(e)
        logger.error(f"DebuggingAgent triggered by {context}: {error_msg}")
        
        diagnostics = run_all_diagnostics()
        
        probable_cause = f"Exception '{e.__class__.__name__}' occurred in {context}."
        
        suggested_fix = "Please review the stacktrace and ensure dependencies and data formats are correct. (No auto-fix applied)"
        
        report = {
            "error": error_msg,
            "stacktrace": stacktrace,
            "diagnostics": diagnostics,
            "probable_cause": probable_cause,
            "suggested_fix": suggested_fix,
            "requires_human_approval": True
        }
        
        logger.info(f"Debugging Agent Report: {report}")
        return report

debugging_agent = DebuggingAgent()
