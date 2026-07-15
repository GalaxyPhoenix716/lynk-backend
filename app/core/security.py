import time
from fastapi import Request
from app.core.exceptions import RateLimitExceededException
from app.services.redis_service import redis_service

class RateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        key = f"lynk:rate:{endpoint}:{client_ip}"
        
        client = await redis_service.get_client()
        count = await client.incr(key)
        
        if count == 1:
            await client.expire(key, self.window_seconds)
            
        if count > self.limit:
            raise RateLimitExceededException(f"Rate limit exceeded. Maximum {self.limit} requests per {self.window_seconds}s.")
