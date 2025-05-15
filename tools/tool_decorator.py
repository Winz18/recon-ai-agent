import functools
import logging
import time
import os
import json
import hashlib
from typing import Any, Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)

def recon_tool(_func: Optional[Callable] = None, *, cache_ttl_seconds: Optional[int] = None, max_retries: int = 0, retry_delay_seconds: int = 1, retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None) -> Callable:
    """
    Decorator for recon tools: adds logging, timing, error handling, optional file-based caching, and retry logic.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            tool_name = func.__name__
            start_time = time.time()
            arg_str = ", ".join([str(a) for a in args] + [f"{k}={v}" for k, v in kwargs.items()])
            logger.info(f"Executing {tool_name}({arg_str})")

            # File-based caching
            cache_path = None
            if cache_ttl_seconds:
                cache_dir = os.path.join(os.getcwd(), 'cache')
                os.makedirs(cache_dir, exist_ok=True)
                key_source = tool_name + repr(args) + repr(sorted(kwargs.items()))
                filename = f"{tool_name}_{hashlib.md5(key_source.encode()).hexdigest()}.json"
                cache_path = os.path.join(cache_dir, filename)
                if os.path.exists(cache_path):
                    try:
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        ts = data.get('_cache_timestamp', 0)
                        if time.time() - ts < cache_ttl_seconds:
                            logger.info(f"{tool_name}: cache hit ({filename})")
                            return data.get('result')
                    except Exception as e:
                        logger.warning(f"{tool_name}: failed to read cache {filename}: {e}")

            # Execution with retry logic
            attempt = 0
            while True:
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    logger.info(f"{tool_name} completed in {duration:.2f}s")
                    break
                except Exception as e:
                    if attempt < max_retries and retryable_exceptions and isinstance(e, retryable_exceptions):
                        attempt += 1
                        logger.warning(f"{tool_name}: attempt {attempt} failed with {type(e).__name__}, retrying in {retry_delay_seconds}s")
                        time.sleep(retry_delay_seconds)
                        continue
                    duration = time.time() - start_time
                    logger.error(f"{tool_name} failed after {duration:.2f}s: {e}")
                    return {"error": True, "tool": tool_name, "error_type": type(e).__name__, "message": str(e)}

            # Write cache
            if cache_ttl_seconds and cache_path and not (isinstance(result, dict) and result.get('error')):
                try:
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump({'_cache_timestamp': time.time(), 'result': result}, f)
                    logger.info(f"{tool_name}: result cached ({filename})")
                except Exception as e:
                    logger.warning(f"{tool_name}: failed to write cache {filename}: {e}")
            return result

        return wrapper

    # Support both @recon_tool and @recon_tool(...)
    if _func:
        return decorator(_func)
    return decorator