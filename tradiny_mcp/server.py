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

"""The Tradiny MCP server.

Exposes the Tradiny backend (which is WebSocket-only, with no REST API) as
MCP tools:

* ``search_assets``   -- find tradeable entities (source/symbol pairs)
* ``list_indicators`` -- indicator catalog with inputs (defaults) and outputs
* ``get_candles``     -- historical OHLCV candles for one entity
* ``run_scanner``     -- execute a full scanner run (backend-side) and collect
                         its streamed ``scan_result`` matches
* ``stop_scanner``    -- cooperatively stop the active scanner run
* ``get_chart_image`` -- render a chart (candles + indicator overlays) using
                         the real frontend in headless Chromium, return the PNG

Everything is async; configuration comes from the environment (see
``tradiny_mcp/config.py`` and ``tradiny_mcp/.env.example``).
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import websockets
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.utilities.types import Image
from mcp.types import TextContent

from . import chart as chart_renderer
from .config import (
    Config,
    backend_host_port,
    backend_ws_url,
    require_backend_url,
)
from .ws_client import (
    NoDataError,
    RequestTimeout,
    TradinyClient,
    TradinyServerError,
)

logger = logging.getLogger("tradiny.mcp")

_CLIENT_ERRORS = (NoDataError, RequestTimeout, TradinyServerError)


def _client_error_to_tool_error(exc: BaseException) -> ToolError:
    """Map a backend-client exception into a clean MCP tool error."""
    if isinstance(exc, (NoDataError, RequestTimeout, TradinyServerError)):
        return ToolError(str(exc))
    if isinstance(exc, ToolError):
        return exc
    raise ToolError(str(exc))


# The backend's per-candidate internal fetch timeout (scanner.py: `timeout = 15`),
# so the quiet window after the last progress line must clear it or the last
# candidate's result could be lost.
_BACKEND_PER_CANDIDATE_TIMEOUT = 16.0


mcp = FastMCP("tradiny")


async def active_scans() -> list[dict]:
    """Live snapshots of the scanner runs active on this server.

    Each entry: ``{"scanned": last_i, "total": total, "matched": n,
    "stopped": bool, "note": str | None}`` -- so a client can poll progress
    without waiting for the ``run_scanner`` call to return.
    """
    async with _scans_lock:
        states = list(_active_scans.values())
    return [
        {
            "scanned": state.last_i,
            "total": state.total,
            "matched": len(state.results),
            "stopped": state.stop_requested.is_set(),
            "note": state.note,
        }
        for state in states
    ]


_client: TradinyClient | None = None


def get_client() -> TradinyClient:
    """Return the shared WS client, creating it on first use.

    Lazy so that the server starts and lists tools even when the backend is
    unconfigured or unreachable (errors surface per-call with a clear message).
    """
    global _client
    if _client is None:
        _client = TradinyClient(
            backend_url=backend_ws_url(require_backend_url()),
            timeout=Config.WS_TIMEOUT_SECONDS,
        )
    return _client


class _ScanState:
    """Per-run state shared with ``stop_scanner`` (and observable live)."""

    def __init__(self) -> None:
        self.ws: Any = None
        self.stop_requested = asyncio.Event()
        self.note: str | None = None
        self.results: list[dict] = []
        self.progress: list[str] = []
        self.last_i = 0
        self.total = 0


_active_scans: dict[int, _ScanState] = {}
_scans_lock = asyncio.Lock()


# --------------------------------------------------------------------------- #
# Lookup & data tools
# --------------------------------------------------------------------------- #
async def _search(query: str, kind: str, expect_type: str) -> list[dict]:
    res = await get_client().request(
        {"type": kind, "search": query},
        expect=[f"{kind}_done", "no_data"],
    )
    return res.get("results") or []


@mcp.tool
async def search_assets(query: str = "", limit: int = 100) -> list[dict]:
    """Find tradeable entities (data-provider source + asset name pairs).

    Use this first: the returned ``details.source`` / ``details.name`` pair is
    exactly what ``get_candles``, ``get_chart_image`` and the scanner's anchor
    (``dataProviderConfig.data`` + ``rules``) need.

    Args:
        query: Substring matched against entity names/sources (case-insensitive
            server-side; the backend caps the result set at 100 rows). ``""``
            returns up to the first 100 entities.
        limit: Max rows to return (<= 100).

    Returns:
        A list of entities, e.g. ``[{"id", "name", "type": "data",
        "details": {"source": "Binance", "name": "BTCUSDT", ...}}, ...]``.
    """
    try:
        results = await _search(query, "search_data", "search_data_done")
        return results[:limit] if limit > 0 else results
    except _CLIENT_ERRORS as exc:
        raise _client_error_to_tool_error(exc) from exc


@mcp.tool
async def list_indicators(query: str = "", limit: int = 100) -> list[dict]:
    """List indicators with their exact inputs (names + defaults) and outputs.

    Required when building a ``run_scanner`` config with indicator rules, or
    the ``indicators`` overlay list for ``get_chart_image``. Per indicator:
    ``details.inputs[].name`` are the input param keys,
    ``details.inputs[].default[0]`` the fallback value, and
    ``details.outputs[].name`` the allowed ``output1``/``output2`` values in
    scanner rules (looked up as ``"<indicator item id>-<output>"`` in the
    candidate's last data point).

    Args:
        query: Substring matched against indicator names; ``""`` lists the
            catalog (backend caps at 100 rows).
        limit: Max rows to return (<= 100).
    """
    try:
        results = await _search(query, "search_indicators", "search_indicators_done")
        return results[:limit] if limit > 0 else results
    except _CLIENT_ERRORS as exc:
        raise _client_error_to_tool_error(exc) from exc


async def _fetch_candles(source: str, symbol: str, interval: str, count: int) -> dict:
    """One-shot historical fetch; raises :class:`NoDataError` when empty."""
    if count <= 0:
        raise NoDataError(entity="n/a", message="count must be a positive integer")
    res = await get_client().request(
        {
            "type": "data",
            "source": source,
            "name": symbol,
            "interval": interval,
            "count": count,
            "stream": False,
        },
        expect=["data_init", "no_data"],
    )
    if res.get("type") == "no_data" or not (res.get("data") or []):
        raise NoDataError(entity=f"{source}/{symbol}/{interval}")
    return res


@mcp.tool
async def get_candles(
    source: str, symbol: str, interval: str, count: int = 600
) -> dict:
    """Fetch historical OHLCV candles for one entity (one-shot, no streaming).

    Args:
        source: Data-provider source, e.g. ``"Binance"`` -- must match
            ``details.source`` from ``search_assets``.
        symbol: Asset name/ticker, e.g. ``"BTCUSDT"`` -- must match
            ``details.name``.
        interval: Candle interval, e.g. ``"1m"``, ``"5m"``, ``"1h"``, ``"1d"``.
        count: Number of candles (positive; default 600).

    Returns:
        ``{"source", "name", "interval", "metadata", "data": [...]}`` where
        each row is ``{"date": "YYYY-MM-DD HH:MM:SS", ...}`` plus one keyed
        column per OHLCV field: ``"<source>-<symbol>-<interval>-<col>"``
        (e.g. ``"Binance-BTCUSDT-5m-close"``) with the value as a string
        (``"78995.30"``).

    Raises:
        A tool error (``NoDataError``) when the backend has no data -- check
        source/symbol/interval with ``search_assets``.
    """
    try:
        return await _fetch_candles(source, symbol, interval, count)
    except _CLIENT_ERRORS as exc:
        raise _client_error_to_tool_error(exc) from exc


# --------------------------------------------------------------------------- #
# Scanner
# --------------------------------------------------------------------------- #
def _prepare_scan_config(config: dict) -> dict:
    """Validate the UI-shape config and fill backend URLs when omitted."""
    if not isinstance(config, dict):
        raise ToolError("config must be a JSON object")
    for field in ("search", "rules", "operators", "dataProviderConfig"):
        if field not in config:
            raise ToolError(f"config is missing required field: {field!r}")

    rules = config["rules"]
    operators = config["operators"]
    if not isinstance(rules, list) or not rules:
        raise ToolError("config.rules must be a non-empty list of rule objects")
    if not isinstance(operators, list):
        raise ToolError("config.operators must be a list (may be empty)")
    if len(operators) != len(rules) - 1:
        raise ToolError(
            f"config.operators must have length len(rules)-1 "
            f"(= {len(rules) - 1}); got {len(operators)}"
        )

    if any(
        r.get("type1") == "indicator" or r.get("type2") == "indicator"
        for r in rules
    ):
        indicators = config.get("indicators", {})
        if not isinstance(indicators, dict) or not indicators:
            raise ToolError(
                'config.indicators (key -> {"indicator": <item>, "outputs": [...]}) '
                "is required because a rule side references an indicator"
            )

    dcc = config["dataProviderConfig"]
    if not isinstance(dcc, dict):
        raise ToolError("config.dataProviderConfig must be an object")
    data_rows = dcc.get("data")
    if not isinstance(data_rows, list) or not data_rows:
        raise ToolError(
            "config.dataProviderConfig.data must be a non-empty list of rows"
        )
    if not any(row.get("type") == "data" for row in data_rows):
        raise ToolError(
            'config.dataProviderConfig.data must contain at least one '
            'type:"data" row (the anchor series the scanner substitutes per '
            "candidate)"
        )
    # The scanner opens its own per-candidate WS to `full_url`; `url` is UI
    # bookkeeping. Fill both from BACKEND_URL when the caller omits them.
    if not dcc.get("full_url"):
        dcc["full_url"] = backend_ws_url()
    if not dcc.get("url"):
        dcc["url"] = backend_host_port()
    return config


_PROGRESS_RE = re.compile(r"Scanning\s+(\d+)/(\d+)")


async def _consume_scan(
    ws: Any, scan_timeout: float, quiesce: float, state: _ScanState
) -> dict:
    """Read frames from a scan session until the run is complete.

    The backend streams ``scan_progress`` (``"Scanning i/N"``) before each
    candidate and ``scan_result`` on match; it sends **no** final "done"
    frame. Completion is therefore detected heuristically:

    * last progress reached (``i == N``) and silence for
      ``max(quiesce, 16)s`` -- the 16s clears the backend's per-candidate
      15s data-fetch timeout, which may follow the final progress line;
    * ``stop_scanner`` was requested and that same silence held;
    * no progress ever arrived and silence held for ``max(30, 2*quiesce)s``
      (scan rejected server-side, e.g. bad config, or zero candidates);
    * hard deadline ``scan_timeout`` elapsed -> ``RequestTimeout``.
    """
    normalize = TradinyClient._normalize
    loop = asyncio.get_running_loop()
    deadline = loop.time() + scan_timeout
    last_activity = loop.time()
    results: list[dict] = state.results
    progress: list[str] = state.progress

    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            raise RequestTimeout(
                last_seen=(progress[-1] if progress else "no progress received")
            )
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, 1.0))
        except asyncio.TimeoutError:
            quiet = loop.time() - last_activity
            silence_grace = max(quiesce, _BACKEND_PER_CANDIDATE_TIMEOUT)
            if state.total > 0:
                if state.last_i >= state.total or state.stop_requested.is_set():
                    if quiet >= silence_grace:
                        if state.stop_requested.is_set():
                            state.note = "stopped by stop_scanner"
                        break
            elif quiet >= max(30.0, 2 * quiesce):
                state.note = (
                    "backend sent no progress; the scan was rejected "
                    "(check the config / backend log) or matched zero candidates"
                )
                break
            continue
        except (
            websockets.exceptions.ConnectionClosed,
            websockets.exceptions.InvalidState,
        ) as exc:
            if not results and not progress:
                raise TradinyServerError(
                    f"Backend closed the scan connection: {exc}"
                ) from exc
            if state.note is None:
                state.note = "connection to backend closed during scan"
            break

        msg = normalize(raw)
        if msg is None:
            last_activity = loop.time()
            continue
        mtype = msg.get("type")
        if mtype == "scan_progress":
            line = str(msg.get("message", ""))
            progress.append(line)
            m = _PROGRESS_RE.search(line)
            if m:
                state.last_i = int(m.group(1))
                state.total = int(m.group(2))
        elif mtype == "scan_result":
            results.append(msg)
        elif mtype == "notification":
            logger.warning("Scan notification: %s", msg.get("message"))
            if state.note is None:
                state.note = f"backend notification: {msg.get('message')}"
        else:
            logger.debug("Unexpected scan frame type: %s", mtype)
        last_activity = loop.time()

    out = {
        "total_scanned": state.total,
        "matched": len(results),
        "results": results,
        "progress": progress,
    }
    if state.note:
        out["note"] = state.note
    return out


@mcp.tool
async def run_scanner(config: dict) -> dict:
    """Execute a Tradiny scanner run and return the matched entities.

    ``config`` is the **same object the Tradiny UI sends** in a ``scan``
    message. Top-level fields (all required unless noted):

    * ``search`` (str): substring selecting the *candidate* entities, e.g.
      ``"BTC"``. The scan iterates all matching entities and substitutes each
      one's source/name into the config.
    * ``rules`` (list): ordered conditions. Each rule compares side 1 vs side
      2. Side kinds (``type1``/``type2``):
        - ``"data"``: needs ``sourceN``, ``nameN``, ``intervalN`` (must be the
          anchor strings, see discipline note) and ``keyN`` in
          ``open | high | low | close | volume``.
        - ``"indicator"``: needs ``indicatorN`` (a key of ``indicators``) and
          ``outputN`` (that indicator's ``details.outputs[].name`` from
          ``list_indicators``; the value is looked up as
          ``"<indicator item id>-<outputN>"``).
        - ``"value"``: needs ``valueN`` (a JSON number).
      Every rule also has ``comparator`` in ``"<" | ">" | "near"`` and, for
      ``near`` only, ``near`` (percent tolerance; passes when
      ``abs(v1-v2)/v2*100 < near``).
    * ``operators`` (list of ``"and" | "or"``): boolean operators *between*
      rules; length must be ``len(rules) - 1`` (``[]`` for a single rule).
    * ``indicators`` (dict, only if a rule side is ``"indicator"``):
      ``key -> {"indicator": <item>, "outputs": <outputs array>}``. Keys are
      arbitrary stable strings (UI convention: ``"EMA length=20"``); rules
      reference the same key. The item has: ``type:"indicator"``, ``id``
      (load-bearing: values land under ``"<id>-<output>"``), ``indicator``
      (the entity object from ``list_indicators``, copied verbatim, including
      ``details``), ``inputs`` (``{inputName: "value-string"}`` keyed by
      ``details.inputs[].name``; omitted inputs fall back to their defaults),
      ``dataMap`` (``{column: {"source","name","interval",
      "value": "<source>-<name>-<interval>-<column>", "dataKey": column}}``)
      and ``render`` (at least ``{"indicatorId": id}``; the scanner ignores it).
      The **identical** item object must also appear as a row of
      ``dataProviderConfig.data``. ``outputs`` is the indicator's
      ``details.outputs`` array.
    * ``dataProviderConfig`` (dict): ``data`` (list) must hold the anchor row
      ``{"type":"data", "source", "name", "interval", "count"}`` plus one row
      per indicator item. ``url`` / ``full_url`` are filled from
      ``BACKEND_URL`` by this server when omitted.

    **Anchor-string discipline (critical):** the backend substitutes the
    anchor's ``source`` and ``name`` into the *entire* config per candidate
    via string replacement. The anchor row, the rules' data sides, and every
    ``dataMap`` value must all use the *same literal strings*; any mismatch
    silently skips entities (no error). Pick the anchor from ``search_assets``
    (``details.source`` / ``details.name``).

    How to build one: (1) ``search_assets(query)`` -> anchor source/name;
    (2) ``list_indicators(query)`` -> copy the matched entity verbatim and
    read input names/defaults and output names; (3) write ``rules`` +
    ``operators``; (4) build the shared indicator item and place it in BOTH
    ``indicators.<key>.indicator`` and ``dataProviderConfig.data``;
    (5) call this tool. There is no final "done" message; completion is
    detected from the last ``Scanning N/N`` plus a silence window, and
    ``stop_scanner`` aborts early. Hard budget: ``SCAN_TIMEOUT_SECONDS``.

    Returns:
        ``{"total_scanned": N, "matched": M,
        "results": [{"data": <entity>, "data_values": {...}}, ...],
        "progress": ["Scanning 001/012", ...], "note"?}`` where
        ``data_values`` labels come from the rule sides (e.g. the indicator
        name + output, ``"close"``).
    """
    cfg = _prepare_scan_config(config)
    state = _ScanState()
    async with _scans_lock:
        _active_scans[id(state)] = state
    try:
        async with get_client().scan_session() as ws:
            state.ws = ws
            await ws.send(json.dumps([{"type": "scan", **cfg}]))
            return await _consume_scan(
                ws,
                Config.SCAN_TIMEOUT_SECONDS,
                Config.SCAN_QUIESCE_SECONDS,
                state,
            )
    except _CLIENT_ERRORS as exc:
        raise _client_error_to_tool_error(exc) from exc
    finally:
        async with _scans_lock:
            _active_scans.pop(id(state), None)


@mcp.tool
async def stop_scanner() -> dict:
    """Cooperatively stop the active scanner run (if any).

    The candidate currently being processed finishes (up to ~15s), the run
    ends, and the ``run_scanner`` call returns whatever matched so far with
    ``"note": "stopped by stop_scanner"``.

    Returns:
        ``{"requested": true, "runs": <count>, "scanned": <i/N per run>,
        "matched": <count per run>}``. Errors when no scan is running on
        this server.
    """
    try:
        client = get_client()
        async with _scans_lock:
            states = list(_active_scans.values())
        if not states:
            raise ToolError("No scanner run is active on this MCP server.")
        for state in states:
            state.stop_requested.set()
            if state.ws is not None:
                try:
                    await client.stop_scan(state.ws)
                except Exception as exc:  # best effort; the run also self-detects
                    logger.warning("scan_stop send failed: %s", exc)
        return {
            "requested": True,
            "runs": len(states),
            "scanned": [f"{state.last_i}/{state.total}" for state in states],
            "matched": [len(state.results) for state in states],
        }
    except _CLIENT_ERRORS as exc:
        raise _client_error_to_tool_error(exc) from exc


# --------------------------------------------------------------------------- #
# Chart image
# --------------------------------------------------------------------------- #
@mcp.tool
async def get_chart_image(
    source: str,
    symbol: str,
    interval: str,
    count: int = 200,
    indicators: list[dict] | None = None,
    width_px: int = 1280,
    height_px: int = 720,
) -> list:
    """Render a chart (candles + optional indicator overlays) in the real
    Tradiny frontend and return it as a PNG image.

    The image is also saved under ``OUTPUT_DIR``; the saved file path is
    included as text content.

    Args:
        source: Data-provider source, e.g. ``"Binance"`` (from
            ``search_assets`` ``details.source``); used in the data pre-check
            and the saved filename.
        symbol: Asset name/ticker, e.g. ``"BTCUSDT"`` (``details.name``).
            Must be an exact catalog name -- verify with ``search_assets``.
        interval: Candle interval, e.g. ``"1m"``, ``"5m"``, ``"1h"``.
        count: Number of candles to load (positive; default 200).
        indicators: Optional overlays, applied in order. Each entry:
            ``{"name": "<indicator display name from list_indicators>",
            "params": {"<inputName>": "<value>", ...}}`` where param keys come
            from ``details.inputs[].name`` and values are strings (omitted
            inputs take ``details.inputs[].default[0]``). Example:
            ``[{"name": "Exponential Moving Average", "params": {"length": "20"}}]``.
        width_px: Image width in pixels (default 1280). Sets the browser
            viewport; the output PNG is exactly ``width_px x height_px``.
        height_px: Image height in pixels (default 720).

    Returns:
        PNG image content plus a text note with the saved path.
    """
    try:
        if count <= 0 or width_px < 64 or height_px < 64:
            raise NoDataError(
                entity="n/a",
                message="count must be positive; width_px/height_px must be "
                "at least 64",
            )
        cleaned_indicators = []
        for ind in indicators or []:
            if not isinstance(ind, dict) or not ind.get("name"):
                raise ToolError(
                    "each indicators entry must be an object with a 'name' "
                    "(and an optional 'params' object)"
                )
            params = ind.get("params") or {}
            if not isinstance(params, dict):
                raise ToolError("indicators[].params must be an object")
            cleaned_indicators.append(
                {
                    "name": str(ind["name"]),
                    "params": {str(k): str(v) for k, v in params.items()},
                }
            )

        # Fail fast when the entity has no data at all -- otherwise the
        # browser hangs in the frontend's search/addData flow until the render
        # budget is exhausted. (A bounded count keeps this check cheap.)
        await _fetch_candles(source, symbol, interval, min(count, 600))

        try:
            png_bytes, path = await chart_renderer.render_chart(
                source=source,
                name=symbol,
                interval=interval,
                count=count,
                indicators=cleaned_indicators,
                width_px=width_px,
                height_px=height_px,
            )
        except chart_renderer.ChartRenderError as exc:
            raise ToolError(str(exc)) from exc

        return [
            Image(data=png_bytes, format="png"),
            TextContent(type="text", text=f"Chart saved to {path}"),
        ]
    except _CLIENT_ERRORS as exc:
        raise _client_error_to_tool_error(exc) from exc


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
def run_server() -> None:
    """Run the MCP server using ``MCP_TRANSPORT`` / ``MCP_HOST`` / ``MCP_PORT``."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if (Config.MCP_TRANSPORT or "http").lower() in ("stdio", "stdin"):
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="http", host=Config.MCP_HOST, port=Config.MCP_PORT)
