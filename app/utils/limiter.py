import os
from slowapi import Limiter
from slowapi.util import get_remote_address

REDIS_URL = os.getenv("REDIS_URL")

# Note: Using Redis as the central storage if available, otherwise fallback to memory
storage_uri = REDIS_URL if REDIS_URL else "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri
)
