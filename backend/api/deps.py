from fastapi.security import HTTPBearer
from backend.core.orchestrator import get_orchestrator
from backend.security.auth import get_auth_manager
from backend.api.routes_mobile import get_mobile_manager
from backend.tracing import get_backend_logger

security = HTTPBearer(auto_error=False)
backend_logger = get_backend_logger()
