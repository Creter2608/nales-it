import time
import logging
from typing import Callable, Dict, List
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)

# In-memory store for rate limiting: ip_address -> list of request timestamps
_rate_limits: Dict[str, List[float]] = {}

def rate_limit(requests: int = 5, window: int = 60) -> Callable:
    """
    FastAPI dependency for simple in-memory rate limiting.
    Allows `requests` per `window` seconds per client IP.
    """
    async def _rate_limit_dependency(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        if client_ip not in _rate_limits:
            _rate_limits[client_ip] = []
            
        # Clean up old timestamps outside the window
        _rate_limits[client_ip] = [t for t in _rate_limits[client_ip] if now - t < window]
        
        if len(_rate_limits[client_ip]) >= requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Quá nhiều yêu cầu. Vui lòng thử lại sau {window} giây."
            )
            
        _rate_limits[client_ip].append(now)
        return True
        
    return _rate_limit_dependency
