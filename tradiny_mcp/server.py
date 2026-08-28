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
* ``scan``            -- high-level scanner: conditions over candle columns,
                         indicator outputs, and literal values; assembles the
                         raw scanner config so callers never deal with anchors,
                         indicator items, or dataMaps
* ``run_scanner``     -- raw scanner (exact UI config shape); advanced use
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
    ``details.inputs[].default[0]`` the fallback value,
    ``details.outputs[].name`` the allowed ``output1``/``output2`` values in
    scanner rules (looked up as ``"<indicator item id>-<output>"`` in the
    candidate's last data point), and
    ``details.columns`` the exact dataframe columns the indicator consumes in
    that order (e.g. Donchian ``["high","low"]``) — ``run_scanner`` indicator
    ``dataMap`` must contain exactly these columns.

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

    **Advanced tool: if you do not already have a UI config object, use the
    high-level ``scan`` tool instead** — same capabilities, and it assembles
    the anchor strings, indicator items, ``dataMap`` and ``outputs`` for you.

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

    **Format & lifetime pitfalls (each has bitten real callers):**

    * The ``config`` argument must be a JSON *object* (a dict literal), never
      a serialized JSON *string* -- MCP input validation rejects stringified
      configs with ``"params/config must be object"``.
    * ``dataProviderConfig`` is **always required**, even when no rule side is
      ``"indicator"`` -- it holds the anchor row the scanner iterates over.
      Omitting it fails with ``"config is missing required field:
      'dataProviderConfig'"``.
    * The anchor row's ``count`` is how many candles the backend fetches per
      candidate; it must cover every indicator's warmup window (e.g. Donchian
      length 100 needs ``count`` at least ``length + 1 = 101``, use a buffer
      like 110). Too few candles and the indicator output is missing/NaN, so
      an indicator rule simply never matches -- no error is raised.
    * An indicator's ``dataMap`` keys must be **exactly that indicator's
      ``details.columns``, in that order** (from ``list_indicators``; e.g.
      Donchian ``["high", "low"]`` -- not ``close``; ATR ``[high, low,
      close]``; RMA ``[close]``). The backend renames dataframe columns
      positionally (``["Date"] + columns``), so a wrong column set or order
      raises a "Length mismatch" inside the indicator, each candidate then
      hits the 15 s fetch timeout and is skipped -- the scan returns **0
      matches with no error**. This is the single most common silent
      failure; the high-level ``scan`` tool builds it correctly.
    * ``inputs`` values are *strings* even for numbers: e.g.
      ``{"lower_length": "100", "upper_length": "100"}``.
    * A ``"value"``-side rule's ``valueN`` must be a JSON *number*, not a
      string; the ``near`` key only exists for rules whose comparator is
      ``"near"``.
    * The run lives for exactly the lifetime of this call: if the client
      connection drops or the tool call times out, the backend run is
      abandoned and a later ``stop_scanner`` reports no active run (the
      results are gone). Budget total time: each candidate costs ~1--16s,
      so keep ``candidates_per_run * per-candidate < min(client tool
      timeout, SCAN_TIMEOUT_SECONDS)`` -- narrow the ``search`` substring
      to small candidate sets when unsure.

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
    return await _execute_scan(config)


async def _execute_scan(config: dict) -> dict:
    """Validate ``config`` and run one scanner session to completion."""
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
# High-level scanner (agent-friendly front end to run_scanner)
# --------------------------------------------------------------------------- #
_OHLCV_COLS = ("open", "high", "low", "close", "volume")


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def _find_entity(query: str, kind: str, what: str) -> dict:
    """Resolve one catalog entity by name (exact first, then unique substring)."""
    results = await _search(query, kind, f"{kind}_done")
    name = str(query).casefold()

    def _matches(pool: list[dict], predicate) -> list[dict]:
        return [e for e in pool if predicate(str(e.get("name", "")))]

    exact = _matches(results, lambda n: n.casefold() == name)
    if len(exact) == 1:
        return exact[0]
    subs = _matches(results, lambda n: name in n.casefold())
    if not exact and len(subs) == 1:
        return subs[0]
    options = exact or subs
    if options:
        raise ToolError(
            f"Ambiguous {what} name {query!r}; matches: "
            + ", ".join(f"{e.get('name')!r}" for e in options[:10])
            + " — pass one of those exactly."
        )
    raise ToolError(
        f"No {what} name matches {query!r}; call list_indicators or "
        "search_assets to see the available names."
    )


def _resolve_output(entity: dict, ref: Any) -> str:
    """Resolve an output reference to the exact ``details.outputs[].name``."""
    outs = [
        str(o.get("name"))
        for o in ((entity.get("details") or {}).get("outputs") or [])
        if o.get("name")
    ]
    if not outs:
        raise ToolError(
            f"{entity.get('name')!r} has no known outputs in the catalog; "
            "use list_indicators to inspect it"
        )
    q = str(ref).casefold()
    for n in outs:
        if n.casefold() == q:
            return n
    subs = [n for n in outs if q in n.casefold()]
    if len(subs) == 1:
        return subs[0]
    if subs:
        raise ToolError(
            f"Output {ref!r} is ambiguous for {entity.get('name')!r}; "
            f"options: {outs}"
        )
    raise ToolError(
        f"Output {ref!r} not found for {entity.get('name')!r}; options: {outs}"
    )


def _default_inputs(entity: dict) -> dict[str, str]:
    """Catalog defaults ({inputName: value-string}); unknown inputs are kept
    out of the returned dict so callers can detect typos."""
    out: dict[str, str] = {}
    for inp in (entity.get("details") or {}).get("inputs") or []:
        key = inp.get("name")
        if not key:
            continue
        d = inp.get("default")
        if isinstance(d, (list, tuple)) and d:
            out[str(key)] = str(d[0])
    return out


def _build_scanner_item(
    entity: dict, idx: int, anchor: tuple[str, str], interval: str
) -> dict:
    """One scanner indicator item: item id, defaults, dataMap from
    ``details.columns`` (order matters — the backend renames positionally)."""
    details = entity.get("details") or {}
    name = str(entity.get("name", "?"))
    cols = [str(c) for c in details.get("columns") or []]
    if not cols:
        raise ToolError(
            f"{name}: the catalog has no details.columns — cannot build a "
            "scanner item automatically; use run_scanner with an explicit "
            "dataMap"
        )
    source, symbol = anchor
    return {
        "type": "indicator",
        "id": f"ind{idx}",
        "indicator": entity,
        "inputs": _default_inputs(entity),
        "dataMap": {
            col: {
                "source": source,
                "name": symbol,
                "interval": interval,
                "value": f"{source}-{symbol}-{interval}-{col}",
                "dataKey": col,
            }
            for col in cols
        },
        "render": {"indicatorId": f"ind{idx}"},
    }


def _side_to_fields(
    side: Any,
    n: int,
    anchor: tuple[str, str],
    interval: str,
    entities: list[dict],
) -> dict:
    """Resolve one condition side into flat rule fields (typeN/keyN/...)."""
    if isinstance(side, bool):
        raise ToolError(
            "a condition side cannot be a boolean; use an OHLCV column name, "
            "a JSON number, or an indicator reference"
        )
    if isinstance(side, (int, float)):
        return {f"type{n}": "value", f"value{n}": float(side)}
    if isinstance(side, str):
        col = side.lower()
        if col not in _OHLCV_COLS:
            raise ToolError(
                f'Side {side!r}: must be an OHLCV column ({"|".join(_OHLCV_COLS)}), '
                'a JSON number, or {"indicator": <index>, "output": <name>}'
            )
        source, symbol = anchor
        return {
            f"type{n}": "data",
            f"source{n}": source,
            f"name{n}": symbol,
            f"interval{n}": interval,
            f"key{n}": col,
        }
    if isinstance(side, dict):
        if "indicator" not in side or not "output" in side:
            raise ToolError(
                'an indicator side needs {"indicator": <index into indicators>, '
                '"output": <output name or unique substring>}'
            )
        idx = side["indicator"]
        if not isinstance(idx, int) or not 0 <= idx < len(entities):
            raise ToolError(
                f'indicator index {idx!r} out of range — the condition references '
                f"indicators[{idx}], but only {len(entities)} indicator(s) were given"
            )
        return {
            f"type{n}": "indicator",
            f"indicator{n}": f"ind{idx}",
            f"output{n}": _resolve_output(entities[idx], side["output"]),
        }
    raise ToolError(
        f"unsupported condition side: {side!r}; use an OHLCV column name, a "
        "JSON number, or an indicator reference"
    )


def _summarize_match(result: dict) -> dict:
    """Flatten one raw scan_result into {source, name, label, values, cross?}."""
    data = result.get("data") or {}
    details = data.get("details") or {}
    values = result.get("data_values") or {}
    entry: dict[str, Any] = {
        "source": details.get("source"),
        "name": details.get("name"),
        "label": details.get("name_label") or details.get("name"),
        "values": dict(values),
    }
    close = _to_float(values.get("close") if "close" in values else None)
    refs = [
        (k, _to_float(v))
        for k, v in values.items()
        if k != "close" and _to_float(v) is not None
    ]
    if close is not None and refs:
        ref_label, ref_value = refs[0]
        if ref_value:
            pct = (close - ref_value) / abs(ref_value) * 100.0
            entry["cross"] = {
                "reference": ref_label,
                "close": close,
                "reference_value": ref_value,
                "direction": "up" if close > ref_value else "down",
                "pct": round(pct, 3),
            }
    return entry


@mcp.tool
async def scan(
    search: str,
    interval: str,
    condition: dict | list,
    indicators: list[dict] | None = None,
    joiners: list[str] | None = None,
    within_pct: float = 2.0,
    count: int = 300,
) -> dict:
    """Find assets whose latest candle matches condition(s) — the simple,
    general scanner. Use this instead of ``run_scanner`` unless you already
    have a UI config object: anchors, indicator items, ``dataMap``, and
    ``outputs`` are assembled here from the same ``list_indicators`` data.

    Example — assets whose daily close recently crossed the middle Donchian
    (100) band (``cross.direction`` = "up" if close ended above Mid,
    "down" if below):

    ```
    scan(
        search="BTC",
        interval="1d",
        condition={
            "left": "close",
            "op": "near",
            "right": {"indicator": 0, "output": "Mid"}
        },
        indicators=[{
            "name": "Donchian Channels (DC)",
            "params": {"lower_length": "100", "upper_length": "100"}
        }],
        within_pct=2,
    )
    ```

    Args:
        search: Substring selecting the candidate entities (e.g. ``"BTC"``
            scans every BTC pair). Must match at least one entity.
        interval: Candle interval, e.g. ``"1d"``, ``"1h"``, ``"5m"``.
        condition: One condition object, or a list for several. Each object:
            ``{"left": <side>, "op": "<" | ">" | "near", "right": <side>}``
            with an optional ``"within"`` percent for per-condition tolerance.
            A ``<side>`` is exactly one of:
            - an OHLCV column name: ``"open" | "high" | "low" | "close"
              | "volume"`` (the entity's own candle);
            - a JSON number (a literal value, e.g. ``50`` — for "close > 50");
            - an indicator reference ``{"indicator": <index into indicators>,
              "output": <output name or unique substring>}`` — output names
              come from ``list_indicators`` ``details.outputs`` (``"Mid"``,
              ``"Mid 2"``, ``"Signal"`` are unique substrings for EMA/RSI-style
              indicators; if two outputs share a substring the tool errors and
              lists the valid full names).
            ``"near"`` passes when ``abs(left-right)/right*100 < within``.
        indicators: Optional overlays, each ``{"name": <name from
            list_indicators>, "params": {<inputName>: <value>}}`` — the same
            shape as ``get_chart_image`` indicators. Omitted inputs take the
            catalog default; ``params`` values are coerced to strings.
            Conditions reference them by list index (``0`` = first).
        joiners: Boolean operators *between* conditions — ``"and" | "or"``,
            length ``len(conditions) - 1``. Defaults to all ``"and"``.
        within_pct: Default percent tolerance for ``"near"`` (2%). Keep it
            small (1–3%) for cross signals; a "recent cross" is close *near*
            a reference.
        count: Candles fetched per candidate (default 300). Must cover the
            longest indicator warm-up (Donchian 100 needs ≥ 101) — raise it
            only when the task requires long indicators. Too few candles and
            every candidate silently 0-matches.

    Returns:
        ``{"total_scanned": N, "matched": M,
        "assets": [{"source", "name", "label", "values": {...}, "cross"?}, ...],
        "results": [raw scanner frames], "progress": [...], "note"?}``
        where ``values`` are the numeric sides of each condition and
        ``cross.direction`` is ``"up"`` when the close ended above the other
        value (bullish) and ``"down"`` when below (bearish).

    Raises:
        A tool error on ambiguous names, unknown inputs/outputs, an unknown
        indicator index, or zero candidates (it lists the valid options
        where applicable). Note: an indicator rule whose side has no data for
        a candidate silently skips that candidate — zero matches is a valid
        result; ``stop_scanner`` aborts a running scan.
    """
    if not search or not search.strip():
        raise ToolError("search must be a non-empty substring (entity search)")
    if not interval or not str(interval).strip():
        raise ToolError("interval must be a non-empty string (e.g. \"1d\")")

    if isinstance(condition, dict):
        conditions = [condition]
    elif isinstance(condition, list):
        conditions = condition
    else:
        raise ToolError(
            "condition must be an object or a list of condition objects"
        )
    if not conditions:
        raise ToolError("condition must contain at least one condition")
    for c in conditions:
        if (
            not isinstance(c, dict)
            or c.get("op") not in ("<", ">", "near")
            or "left" not in c
            or "right" not in c
        ):
            raise ToolError(
                "each condition needs \"left\", \"op\" (<, >, near), \"right\""
            )

    ind_specs = [
        s
        for s in (
            indicators
            or []
        )
        if isinstance(s, dict) and s.get("name")
    ]
    if indicators and len(ind_specs) != len(indicators):
        raise ToolError("each indicators entry must be an object with a \"name\"")

    anchors = await _search(search, "search_data", "search_data_done")
    anchor = None
    for e in anchors:
        det = e.get("details") or {}
        if det.get("source") and det.get("name"):
            anchor = (det["source"], det["name"])
            break
    if anchor is None:
        raise ToolError(
            f"No tradeable entity matches {search!r}; call search_assets to "
            "see available names"
        )

    entities: list[dict] = []
    for spec in ind_specs:
        entities.append(
            await _find_entity(str(spec["name"]), "search_indicators", "indicator")
        )

    # Validate every indicator side before paying for a scan run.
    for c in conditions:
        for side in (c["left"], c["right"]):
            if isinstance(side, dict) and "indicator" in side:
                idx = side["indicator"]
                if not isinstance(idx, int) or not 0 <= idx < len(entities):
                    raise ToolError(
                        f"indicator index {idx!r} out of range — only "
                        f"{len(entities)} indicator(s) were given in indicators"
                    )
                _resolve_output(entities[idx], side["output"])
            _side_to_fields(side, 1, anchor, interval, entities)

    items: list[dict] = []
    indicators_cfg: dict[str, dict] = {}
    for idx, (spec, entity) in enumerate(zip(ind_specs, entities)):
        item = _build_scanner_item(entity, idx, anchor, interval)
        inputs = item["inputs"]
        params = spec.get("params") or {}
        if not isinstance(params, dict):
            raise ToolError("indicators[].params must be an object")
        allowed = set(inputs)
        unknown = sorted(set(str(k) for k in params) - allowed)
        if unknown:
            raise ToolError(
                f'{entity.get("name")}: unknown input(s) {unknown}; allowed: '
                f"{sorted(allowed)} (see list_indicators)"
            )
        item["inputs"].update({str(k): str(v) for k, v in params.items()})
        items.append(item)
        indicators_cfg[f"ind{idx}"] = {
            "indicator": item,
            "outputs": [
                str(o.get("name"))
                for o in ((entity.get("details") or {}).get("outputs") or [])
                if o.get("name")
            ],
        }

    rules: list[dict] = []
    for c in conditions:
        f1 = _side_to_fields(c["left"], 1, anchor, interval, entities)
        f2 = _side_to_fields(c["right"], 2, anchor, interval, entities)
        rule = {**f1, **f2, "comparator": c["op"]}
        if c["op"] == "near":
            within = c.get("within", within_pct)
            if not isinstance(within, (int, float)) or isinstance(within, bool):
                raise ToolError(
                    "\"within\" must be a positive number (percent tolerance)"
                )
            rule["near"] = float(within)
        rules.append(rule)

    expected_joiners = len(conditions) - 1
    join = (
        ["and"] * expected_joiners
        if joiners is None
        else list(joiners)
    )
    if len(join) != expected_joiners:
        raise ToolError(
            f"joiners must have length {expected_joiners} "
            f"(one per condition join), got {len(join)}"
        )
    for op in join:
        if op not in ("and", "or"):
            raise ToolError(f"joiner {op!r} must be \"and\" or \"or\"")

    if count <= 0:
        raise ToolError("count must be a positive integer")

    config = {
        "search": search,
        "rules": rules,
        "operators": join,
        "dataProviderConfig": {
            "data": [
                {
                    "type": "data",
                    "source": anchor[0],
                    "name": anchor[1],
                    "interval": interval,
                    "count": count,
                },
                *items,
            ]
        },
    }
    if indicators_cfg:
        config["indicators"] = indicators_cfg

    result = await _execute_scan(config)
    result["assets"] = [
        _summarize_match(r) for r in (result.get("results") or [])
    ]
    return result


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
) -> list[Image | TextContent]:
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
