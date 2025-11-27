# This software is licensed under a dual-license model:
# 1. Under the Affero General Public License (AGPL) for open-source use.
# 2. With additional terms tailored to individual users (e.g., traders and investors):
#
#    - Individual users may use this software for personal profit (e.g., trading/investing)
#      without releasing proprietary strategies.
#
#    - Redistribution, public tools, or commercial use require compliance with AGPL
#      or a commercial license. Contact: license@tradiny.com
#
# For full details, see the LICENSE.md file in the root directory of this project.

import json
import logging
from functools import wraps
from hashlib import sha256
from typing import Callable, Any
from cachetools import TTLCache, LRUCache
import time
from typing import Any, Callable


def _serialize_params(*args, **kwargs) -> str:
    """
    Convert (args, kwargs) into a deterministic, hashable string.
    Falls back to str(obj) when json can’t handle the object.
    """

    def to_jsonable(o):
        try:
            json.dumps(o)
            return o
        except TypeError:
            return str(o)

    args_ser = [to_jsonable(a) for a in args]
    kwargs_ser = {k: to_jsonable(v) for k, v in sorted(kwargs.items())}

    payload = json.dumps({"args": args_ser, "kwargs": kwargs_ser}, sort_keys=True)
    return sha256(payload.encode()).hexdigest()


def cached(
    maxsize: int = 1024,
    ttl: int | None = 600,
    validator: Callable[[Any, tuple, dict], bool] | None = None,
    shared_dict: "dict[str, Any] | None" = None,  # ← NEW PARAM
):
    """
    Decorator factory (now multi-process aware):

    maxsize     – max #entries
    ttl         – seconds until automatic expiry (None ⇒ infinite)
    validator   – fn(result, args, kwargs) -> bool
    shared_dict – Manager().dict() (or any dict-like) that should be
                  *visible to all processes*. If omitted we fall back to
                  the original per-process cachetools cache.
    """

    # Ensure a sentinel exists for both code paths
    _MISS = object()

    # ---------- choose backend ----------
    if shared_dict is None:  # ORIGINAL PATH
        cache = (
            TTLCache(maxsize=maxsize, ttl=ttl)
            if ttl is not None
            else LRUCache(maxsize=maxsize)
        )

        def _get(k):
            return cache.get(k, _MISS)

        def _put(k, v):
            cache[k] = v

        def _size():
            return len(cache)

    else:  # SHARED PATH

        def _get(k):
            try:
                exp, val = shared_dict[k]
            except KeyError:
                return _MISS
            if exp is not None and exp < time.time():  # expired
                shared_dict.pop(k, None)
                return _MISS
            return val

        def _put(k, v):
            exp = None if ttl is None else time.time() + ttl
            shared_dict[k] = (exp, v)
            # naive size cap (no strict LRU) — avoid iterating the proxy
            if maxsize and len(shared_dict) > maxsize:
                try:
                    # Prefer server-side removal
                    shared_dict.popitem()
                except Exception:
                    # Fallback: pop first available key without using __iter__
                    try:
                        keys = list(shared_dict.keys())
                        if keys:
                            shared_dict.pop(keys[0], None)
                    except Exception:
                        # Manager may be shutting down; ignore eviction
                        pass

        def _size():
            return len(shared_dict)

    # ------------------------------------

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = _serialize_params(*args, **kwargs)
            val = _get(key)
            if val is not _MISS:
                try:
                    if validator is None or validator(val, args, kwargs):
                        return val  # cache hit & still valid
                except Exception as e:
                    logging.warning(f"Unable to validate freshness of cache: {e}")
            # miss / invalid -------------------------------------------------------------------
            val = func(*args, **kwargs)
            _put(key, val)
            return val

        return wrapper

    return decorator
