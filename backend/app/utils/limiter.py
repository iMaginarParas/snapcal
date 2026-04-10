import os
from slowapi import Limiter
from slowapi.util import get_remote_address

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Note: Using Redis as the central storage for rate limits
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=REDIS_URL
)
