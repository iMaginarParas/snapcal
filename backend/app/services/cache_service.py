import redis
import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    redis_client = None

def get_cache(key: str) -> Optional[Any]:
    """
    Retrieves data from Redis cache.
    """
    if not redis_client:
        return None
    
    try:
        value = redis_client.get(key)
        if value:
            from .metrics_service import record_metric
            record_metric("cache_hit", tags={"key_prefix": key.split(':')[0]})
            return json.loads(value)
        
        from .metrics_service import record_metric
        record_metric("cache_miss", tags={"key_prefix": key.split(':')[0]})
        return None
    except Exception as e:
        logger.error(f"Cache get error for key {key}: {str(e)}")
        return None

def set_cache(key: str, data: Any, ttl: int = 300):
    """
    Stores data in Redis cache with an expiration time (TTL).
    Default TTL is 5 minutes.
    """
    if not redis_client:
        return
    
    try:
        redis_client.setex(
            key,
            ttl,
            json.dumps(data)
        )
    except Exception as e:
        logger.error(f"Cache set error for key {key}: {str(e)}")

def invalidate_cache(key: str):
    """
    Removes a specific key from the cache.
    """
    if not redis_client:
        return
    
    try:
        redis_client.delete(key)
    except Exception as e:
        logger.error(f"Cache invalidation error for key {key}: {str(e)}")
