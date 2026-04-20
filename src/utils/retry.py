import time
from functools import wraps

import httpx

from src.utils.logger import log


def retry_http(attempts: int = 3, base_delay: float = 1.0, exp_base: float = 2.0):
    """Retry a function on transient HTTP failures.

    Retries on httpx.TimeoutException, ConnectError, and 5xx HTTPStatusError.
    Does NOT retry on 4xx -- those are auth/quota/bad-request and retrying
    wastes API budget.
    """

    def decorator(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code < 500 or attempt == attempts - 1:
                        raise
                    last_exc = e
                    delay = base_delay * (exp_base ** attempt)
                    log.warning(
                        f"{fn.__name__}: HTTP {e.response.status_code}, "
                        f"retry {attempt + 1}/{attempts} in {delay:.1f}s"
                    )
                    time.sleep(delay)
                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    if attempt == attempts - 1:
                        raise
                    last_exc = e
                    delay = base_delay * (exp_base ** attempt)
                    log.warning(
                        f"{fn.__name__}: {type(e).__name__}, "
                        f"retry {attempt + 1}/{attempts} in {delay:.1f}s"
                    )
                    time.sleep(delay)
            # Defensive: loop always either returns or raises. If we somehow
            # fall through, surface the last exception rather than silently None.
            if last_exc is not None:
                raise last_exc
            return None

        return inner

    return decorator
