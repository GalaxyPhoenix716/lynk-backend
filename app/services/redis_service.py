# Redis service placeholder
import json
import logging
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException, TransferNotFoundException

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self) -> None:
        self.pool: aioredis.ConnectionPool | None = None

    def init_pool(self) -> None:
        """Initializes the connection pool. Called during app startup."""
        try:
            self.pool = aioredis.ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8"
            )
            logger.info("Redis connection pool initialized.")
        except Exception as e:
            logger.error(f"Failed to create Redis pool: {e}")
            raise ServiceUnavailableException("Failed to initialize Redis connection pool")

    async def get_client(self) -> aioredis.Redis:
        """Helper to get a client instance from the pool."""
        if not self.pool:
            raise ServiceUnavailableException("Redis connection pool is not initialized")
        return aioredis.Redis(connection_pool=self.pool)

    def _get_key(self, transfer_id: str) -> str:
        return f"lynk:transfer:{transfer_id}"

    async def set_transfer(self, transfer_id: str, data: dict, ttl_seconds: int) -> None:
        """Stores transfer metadata with a specific TTL (time-to-live) in seconds."""
        client = await self.get_client()
        key = self._get_key(transfer_id)
        try:
            val = json.dumps(data)
            await client.setex(key, ttl_seconds, val)
        except Exception as e:
            logger.error(f"Redis set_transfer failed: {e}")
            raise ServiceUnavailableException("Failed to save transfer metadata")

    async def get_transfer(self, transfer_id: str) -> dict | None:
        """Retrieves transfer metadata. Returns None if expired or not found."""
        client = await self.get_client()
        key = self._get_key(transfer_id)
        try:
            val = await client.get(key)
            if not val:
                return None
            return json.loads(val)
        except Exception as e:
            logger.error(f"Redis get_transfer failed: {e}")
            raise ServiceUnavailableException("Failed to retrieve transfer metadata")

    async def update_transfer(self, transfer_id: str, data: dict) -> None:
        """
        Updates transfer metadata while preserving the remaining TTL.
        Raises TransferNotFoundException if the transfer has expired or does not exist.
        """
        client = await self.get_client()
        key = self._get_key(transfer_id)
        try:
            # 1. Read current TTL to prevent extending the lifetime
            ttl = await client.ttl(key)
            
            # Redis TTL returns -2 if key does not exist
            if ttl == -2:
                raise TransferNotFoundException()
            
            # Handle edge cases (no expiry key -1 or expired keys)
            if ttl <= 0:
                if ttl == -1:
                    ttl = settings.TRANSFER_LIFETIME_SECONDS
                else:
                    raise TransferNotFoundException()

            # 2. Write the updated data preserving the remaining seconds
            val = json.dumps(data)
            await client.setex(key, ttl, val)
        except TransferNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Redis update_transfer failed: {e}")
            raise ServiceUnavailableException("Failed to update transfer metadata")

    async def delete_transfer(self, transfer_id: str) -> None:
        """Deletes a transfer's metadata immediately."""
        client = await self.get_client()
        key = self._get_key(transfer_id)
        try:
            await client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete_transfer failed: {e}")
            raise ServiceUnavailableException("Failed to delete transfer metadata")

    async def close_pool(self) -> None:
        """Closes the connection pool. Called during app shutdown."""
        if self.pool:
            await self.pool.disconnect()
            logger.info("Redis connection pool closed.")
            self.pool = None

# Global service instance to import throughout the app
redis_service = RedisService()