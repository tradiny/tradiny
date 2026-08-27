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

"""Async WebSocket client for the Tradiny backend.

The Tradiny backend has no REST API: every operation (search, historical data,
indicators, the scanner) is a JSON message over a single WebSocket endpoint,
``ws(s)://<backend>/websocket/`` (see ``backend/app/router.py``). Responses are
correlated by their ``type`` field. The backend always delivers a *single* JSON
object per frame, and clients send a JSON *array* of message objects.

This module provides:

* :meth:`TradinyClient.request` -- send one message on a pooled connection and
  return the first response whose ``type`` is one of ``expect``.
* :meth:`TradinyClient.scan_session` -- a dedicated WebSocket for the lifetime
  of a scanner run (the backend identifies the scan session by ``id(websocket)``
  and streams ``scan_progress`` / ``scan_result`` back on the same socket).
* :meth:`TradinyClient.stop_scan` -- request a cooperative stop on an active
  scan session (``{"type": "scan_stop"}``).
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import websockets

logger = logging.getLogger("tradiny.mcp.ws")


class NoDataError(Exception):
    """Raised when the backend reports that it has no data for an entity."""

    def __init__(self, entity: str | None = None, message: str | None = None):
        self.entity = entity
        super().__init__(message or f"No data available for entity: {entity}")


class RequestTimeout(Exception):
    """Raised when a request/response round-trip does not complete in time."""

    def __init__(self, last_seen: str | None = None):
        self.last_seen = last_seen
        hint = f" (last message seen: {last_seen})" if last_seen else ""
        super().__init__(f"Timed out waiting for a response{hint}")


class TradinyServerError(Exception):
    """Raised for explicit error ``notification`` frames from the backend."""

    def __init__(self, message: str):
        super().__init__(message)


class TradinyClient:
    """A thin async client over the Tradiny WebSocket protocol.

    A single pooled connection is used for the quick request/response tools
    (search, candles) and re-established at most once if it drops. Scanner
    runs get their own dedicated socket via :meth:`scan_session`.
    """

    def __init__(self, backend_url: str, timeout: float = 30.0):
        self.ws_url = self._canonical_ws_url(backend_url)
        self._timeout = timeout
        self._ws: Any = None
        self._lock = asyncio.Lock()

    @staticmethod
    def _canonical_ws_url(backend_url: str) -> str | None:
        """Return a ``ws(s)://.../websocket/`` URL, or ``None`` if not one.

        The backend route is registered as ``/websocket/`` (with the trailing
        slash); a bare ``/websocket`` falls through to the static-file
        catch-all and errors. So we guarantee exactly ``/websocket/``.
        """
        if not backend_url.startswith("ws"):
            return None
        if backend_url.endswith("/websocket/"):
            return backend_url
        if backend_url.endswith("/websocket"):
            return backend_url + "/"
        return backend_url.rstrip("/") + "/websocket/"

    # ------------------------------------------------------------------ #
    # Connection management
    # ------------------------------------------------------------------ #
    def _backend_is_open(self) -> bool:
        return self._ws is not None and getattr(self._ws, "state", None) == "OPEN"

    async def _connect(self) -> Any:
        ws = await websockets.connect(
            self.ws_url,
            max_size=None,  # data_init payloads can be large
            max_queue=64,
            close_timeout=10,
        )
        return ws

    async def close(self) -> None:
        """Close the pooled connection (if any). Idempotent."""
        async with self._lock:
            if self._ws is not None:
                try:
                    await self._ws.close()
                except Exception:  # pragma: no cover - best effort
                    pass
                self._ws = None

    # ------------------------------------------------------------------ #
    # Request/response
    # ------------------------------------------------------------------ #
    @staticmethod
    def _normalize(raw: Any) -> dict | None:
        """Backend frames are single objects; be tolerant of lists/bytes."""
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", "replace")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return None
        if isinstance(raw, list):
            return raw[0] if raw and isinstance(raw[0], dict) else None
        if isinstance(raw, dict):
            return raw
        return None

    async def _recv_matching(
        self, ws: Any, expect: list[str], timeout: float, deadline: float
    ) -> dict:
        last_seen: str | None = None
        loop = asyncio.get_running_loop()
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise RequestTimeout(last_seen)
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
            except asyncio.TimeoutError:
                raise RequestTimeout(last_seen) from None
            msg = self._normalize(raw)
            if msg is None:
                continue
            mtype = msg.get("type")
            if mtype == "notification":
                detail = str(msg.get("message", ""))
                logger.warning("Backend notification: %s", detail)
                if detail.lower().startswith("error"):
                    raise TradinyServerError(detail)
                last_seen = f"notification: {detail}"
                continue
            last_seen = f"type={mtype}"
            if mtype in expect:
                return msg
            # Unrelated frame (e.g. an unexpected update); keep waiting.

    async def request(
        self,
        msg: dict,
        expect: list[str],
        timeout: float | None = None,
    ) -> dict:
        """Send ``msg`` and return the first response whose ``type`` is in ``expect``.

        Unrelated frames are skipped. A ``no_data`` frame in ``expect`` raises
        :class:`NoDataError`. Exceeding ``timeout`` raises :class:`RequestTimeout`
        carrying the last message seen. A dropped connection is retried exactly
        once.
        """
        timeout = timeout if timeout is not None else self._timeout
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        payload = json.dumps([msg])

        async with self._lock:
            last_exc: Exception | None = None
            for attempt in range(2):  # initial + single reconnect
                if not self._backend_is_open():
                    try:
                        self._ws = await self._connect()
                    except Exception as exc:
                        self._ws = None
                        raise TradinyServerError(
                            f"Could not connect to backend at {self.ws_url}: {exc}"
                        ) from exc
                try:
                    await self._ws.send(payload)
                    return await self._recv_matching(
                        self._ws, expect, timeout, deadline
                    )
                except (
                    websockets.exceptions.ConnectionClosed,
                    websockets.exceptions.InvalidState,
                    websockets.exceptions.InvalidMessage,
                ) as exc:
                    last_exc = exc
                    logger.warning(
                        "Connection dropped (attempt %d): %s", attempt + 1, exc
                    )
                    # Abandon the pooled connection; next iteration reconnects.
                    prev = self._ws
                    self._ws = None
                    if prev is not None:
                        try:
                            await prev.close()
                        except Exception:  # pragma: no cover - best effort
                            pass
            raise TradinyServerError(
                f"WebSocket connection to backend failed: {last_exc}"
            ) from last_exc

    # ------------------------------------------------------------------ #
    # Scanner session
    # ------------------------------------------------------------------ #
    @asynccontextmanager
    async def scan_session(self) -> AsyncIterator[Any]:
        """Yield a dedicated WebSocket for a scanner run.

        The caller sends the ``scan`` message on it and then reads
        ``scan_progress`` / ``scan_result`` frames until the run completes.
        No final "done" frame exists; completion is detected heuristically by
        the caller (last progress + quiescence) or via :meth:`stop_scan`.
        On exit the socket is closed (the backend notices the disconnect).
        """
        ws = await websockets.connect(
            self.ws_url,
            max_size=None,
            max_queue=1024,
            close_timeout=10,
        )
        try:
            yield ws
        finally:
            try:
                await ws.close()
            except Exception:  # pragma: no cover - best effort
                pass

    async def stop_scan(self, ws: Any) -> None:
        """Request a cooperative stop for the scan running on ``ws``.

        This must be the *same* socket the ``scan`` message was sent on,
        because the backend associates the scan with ``id(websocket)``.
        """
        await ws.send(json.dumps([{"type": "scan_stop"}]))


def new_scan_reader():
    """Return a helper to parse ``Scanning i/N`` progress messages.

    Exposed for clarity/testing. Returns a function mapping a message string to
    ``("progress", i, n)``, ``("result",)`` or ``None``.
    """
    import re

    pattern = re.compile(r"Scanning\s+(\d+)/(\d+)")

    def parse(message: str):
        m = pattern.search(message)
        if m:
            return ("progress", int(m.group(1)), int(m.group(2)))
        return None

    return parse
