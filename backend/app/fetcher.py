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

from __future__ import annotations

import asyncio
from concurrent.futures import ProcessPoolExecutor, Future
from typing import Any, Awaitable, Callable, Tuple
from multiprocessing import Manager

_shared_cache: dict[str, Any] | None = None  # will be set in each worker


def _init_worker(shared_cache_proxy):
    """Executed once in every worker process – stores the proxy."""
    global _shared_cache
    _shared_cache = shared_cache_proxy


def get_shared_cache() -> dict[str, Any]:
    return _shared_cache


def _run_async_func(
    async_fn: Callable[..., Awaitable[Any]], args: Tuple[Any, ...]
) -> Any:
    """
    Helper executed inside a *separate process*.

    It creates a new event-loop for that process, executes the given coroutine
    and returns its result.  It must live at module scope to be *picklable* by
    multiprocessing.
    """
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    try:
        return new_loop.run_until_complete(async_fn(*args))
    finally:
        new_loop.close()


class BlockingFetcher:
    """
    Execute blocking callables in a pool of worker *processes* so the main
    asyncio loop is never blocked by the GIL.

    Usage
    -----
    fetcher = BlockingFetcher(max_workers=4)

    # Blocking function
    result = await fetcher.fetch(blocking_fn, (arg1, arg2))

    # Coroutine
    result = await fetcher.fetch_async(async_fn, (arg1, arg2))
    """

    def __init__(
        self, max_workers: int = 4, *, shared_cache: dict | None = None
    ) -> None:
        self._executor: ProcessPoolExecutor
        if shared_cache is not None:
            self._executor = ProcessPoolExecutor(
                max_workers=max_workers,
                initializer=_init_worker,  # passes cache to every worker
                initargs=(shared_cache,),
            )
        else:
            self._executor = ProcessPoolExecutor(max_workers=max_workers)

    # --------------------------------------------------------------------- #
    # Public methods                                                        #
    # --------------------------------------------------------------------- #
    async def fetch(
        self,
        fn: Callable[..., Any],
        args: Tuple[Any, ...] | list[Any],
    ) -> Any:
        """
        Run a *synchronous* function in a worker process and return its result.
        """
        loop = asyncio.get_running_loop()
        future: Future[Any] = loop.run_in_executor(self._executor, fn, *args)
        return await future

    async def fetch_async(
        self,
        async_fn: Callable[..., Awaitable[Any]],
        args: Tuple[Any, ...] | list[Any],
    ) -> Any:
        """
        Run an *asynchronous* function/coroutine in a worker process and return
        its result.
        """
        loop = asyncio.get_running_loop()
        future: Future[Any] = loop.run_in_executor(
            self._executor, _run_async_func, async_fn, args
        )
        return await future

    def close(self, wait: bool = True) -> None:
        """
        Shut down the underlying ProcessPoolExecutor. Call this once your
        application is terminating.
        """
        self._executor.shutdown(wait=wait)

    def __del__(self) -> None:
        # Ensure resources are freed if the user forgot to call `close`.
        try:
            self._executor.shutdown(wait=False)
        except Exception:  # pragma: no cover
            # Executor may already be gone during interpreter shutdown.
            pass
