"""
cache/service.py
----------------
Redis caching layer. Owns the Redis client lifecycle and the cached() helper.

Usage (from any tool):
    from cache.service import cached

    result = cached("tool_name", my_function, ttl_seconds=300, arg1, arg2)
"""

import hashlib
import json
from upstash_redis import Redis

# ---------------------------------------------------------------------------
# Redis Client — initialised once at import time. Falls back gracefully to
# None so the rest of the app continues working without a Redis connection.
# ---------------------------------------------------------------------------
try:
    _redis_client = Redis.from_env()
except Exception as e:
    print(f"Warning: Could not initialise Upstash Redis client: {e}")
    _redis_client = None


def cached(tool_name: str, func, ttl_seconds: int, *args, **kwargs):
    """
    Execute `func` with the given args, returning a cached result when available.

    Falls back to executing the function directly if:
    - Redis is unavailable
    - Any cache read/write error occurs
    """
    if not _redis_client:
        return func(*args, **kwargs)

    try:
        # Build a deterministic cache key from the tool name and arguments
        arg_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        key_hash = hashlib.md5(arg_str.encode()).hexdigest()
        cache_key = f"cache:{tool_name}:{key_hash}"

        # Check cache
        cached_result = _redis_client.get(cache_key)
        if cached_result:
            print(f"[CACHE HIT] Returning cached result for {tool_name}")
            if isinstance(cached_result, str):
                try:
                    return json.loads(cached_result)
                except json.JSONDecodeError:
                    return cached_result
            return cached_result

        print(f"[CACHE MISS] Executing {tool_name}...")
        result = func(*args, **kwargs)

        # Store in cache
        if isinstance(result, (dict, list)):
            _redis_client.setex(cache_key, ttl_seconds, json.dumps(result))
        else:
            _redis_client.setex(cache_key, ttl_seconds, str(result))

        return result

    except Exception as e:
        print(f"Cache Error ({tool_name}): {e}")
        return func(*args, **kwargs)
