import subprocess
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class BwrapRunner:
    """
    Executes commands within a Bubblewrap sandbox for secure Linux isolation.
    An excellent lightweight alternative when Docker is unavailable.
    """
    def __init__(self):
        self.bwrap_path = "/usr/bin/bwrap" # Common location

    def run_command(self, command: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs a command inside a bwrap sandbox.
        Isolates the filesystem and network.
        """
        logger.info(f"BwrapRunner: Running command '{command}' in {working_dir or 'current dir'}")
        
        # Base bubblewrap command
        # --ro-bind / / : Root is read-only
        # --dev /dev : Mount dev
        # --proc /proc : Mount proc
        # --tmpfs /tmp : Isolated tmp
        # --unshare-all : Isolate all namespaces (network, pid, etc.)
        # --new-session : New session
        
        bwrap_cmd = [
            "bwrap",
            "--ro-bind", "/", "/",
            "--dev", "/dev",
            "--proc", "/proc",
            "--tmpfs", "/tmp",
            "--tmpfs", "/home", # Isolate home
        ]

        if working_dir:
            wd = Path(working_dir).absolute()
            # Bind the working directory as writeable
            bwrap_cmd.extend(["--bind", str(wd), str(wd)])
            bwrap_cmd.extend(["--chdir", str(wd)])

        # Safety: block network unless explicitly allowed (not implemented for now)
        bwrap_cmd.append("--unshare-net")
        
        # Add the actual command
        bwrap_cmd.extend(["bash", "-c", command])

        try:
            result = subprocess.run(
                bwrap_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            logger.error(f"BwrapRunner: Command timed out: {command}")
            return {"error": "Timeout", "exit_code": -1, "success": False}
        except Exception as e:
            logger.error(f"BwrapRunner: Error running command: {str(e)}")
            return {"error": str(e), "exit_code": 1, "success": False}

def get_sandbox() -> BwrapRunner:
    return BwrapRunner()
