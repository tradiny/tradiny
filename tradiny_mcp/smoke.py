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

"""End-to-end smoke test for the Tradiny MCP server (mcp_plan.md, section 8).

Prerequisites:
- Tradiny backend running and serving the frontend (so ``BACKEND_URL`` /
  ``FRONTEND_URL`` both point at it, or use the webpack dev server).
- ``playwright install chromium`` completed (for the chart test).

Run from the repository root (so ``tradiny_mcp`` is importable):

    BACKEND_URL=http://localhost:8000 FRONTEND_URL=http://localhost:8000 \
        python -m tradiny_mcp.smoke

Every check prints PASS/FAIL; the exit code is 0 only when all pass. The
broad scanner run is stopped cooperatively once it has produced a match with
a few candidates scanned, which doubles as the ``stop_scanner`` mid-run test
and keeps the backend's per-IP data-request budget under control.
"""

from __future__ import annotations

import asyncio
import os
import re
import struct
import sys

os.environ.setdefault("BACKEND_URL", "http://localhost:8000")
os.environ.setdefault("FRONTEND_URL", "http://localhost:8000")

from fastmcp.exceptions import ToolError  # noqa: E402
from fastmcp.utilities.types import Image as McpImage  # noqa: E402

from tradiny_mcp import server  # noqa: E402

PASS = "PASS"
FAIL = "FAIL"
_RESULTS: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    _RESULTS.append((name, ok, detail))
    line = f"[{PASS if ok else FAIL}] {name}"
    if detail:
        line += f" -- {detail}"
    print(line, flush=True)


async def _expect_error(coro, name: str, needle: str | None = None) -> None:
    """Assert that awaiting ``coro`` raises a clean MCP tool error."""
    detail = ""
    try:
        await coro
    except ToolError as exc:
        detail = str(exc)
        if needle and needle.lower() not in detail.lower():
            record(name, False, f"error raised but does not mention {needle!r}: {detail[:200]}")
            return
        record(name, True, detail[:200])
    except Exception as exc:  # noqa: BLE001 - report as failure
        record(name, False, f"unexpected {type(exc).__name__}: {exc}"[:200])
    else:
        record(name, False, "expected a tool error, call succeeded")


# --------------------------------------------------------------------------- #
# Worked example (mcp_plan.md section 5.4.6, verbatim): scan every entity
# matching "BTC" on 5m where EMA(length=20) of close is above close.
# --------------------------------------------------------------------------- #
_ANCHOR = {
    "type": "data",
    "source": "Binance",
    "name": "BTCUSDT",
    "interval": "5m",
    "count": 300,
}
_EMA_ENTITY = {
    "id": "indicators.pandas_ta.overlap.ema.EMA",
    "name": "Exponential Moving Average",
    "type": "indicator",
    "details": {
        "categories": ["overlap"],
        "library": "pandas_ta",
        "columns": ["close"],
        "inputs": [{"name": "length", "default": [10]}],
        "outputs": [{"name": "EMA", "y_axis": "price"}],
    },
}
_EMA_ITEM = {
    "type": "indicator",
    "id": "indicators-pandas_ta-overlap-ema-EMA_length-20_close-Binance-BTCUSDT-5m-close",
    "indicator": _EMA_ENTITY,
    "inputs": {"length": "20"},
    "dataMap": {
        "close": {
            "source": "Binance",
            "name": "BTCUSDT",
            "interval": "5m",
            "value": "Binance-BTCUSDT-5m-close",
            "dataKey": "close",
        }
    },
    "render": {
        "indicatorId": "indicators-pandas_ta-overlap-ema-EMA_length-20_close-Binance-BTCUSDT-5m-close",
        "paneIdx": 0,
    },
}

WORKED_EXAMPLE = {
    "search": "BTC",
    "rules": [
        {
            "type1": "indicator",
            "indicator1": "EMA length=20",
            "output1": "EMA",
            "comparator": ">",
            "type2": "data",
            "source2": "Binance",
            "name2": "BTCUSDT",
            "interval2": "5m",
            "key2": "close",
        }
    ],
    "operators": [],
    "indicators": {
        "EMA length=20": {"indicator": _EMA_ITEM, "outputs": [{"name": "EMA", "y_axis": "price"}]}
    },
    "dataProviderConfig": {
        "url": "localhost:8000",
        "full_url": "ws://localhost:8000/websocket/",
        "data": [_ANCHOR, _EMA_ITEM],
    },
}

# "BTCUSDT" matches a couple of live, data-bearing pairs: cheap, and every
# rule variant (near / and / or) can actually match something. (Dead pairs
# such as 1INCHBTC have no data, so the scanner silently skips them.)
_NARROW_SEARCH = "BTCUSDT"


def _ema_scan_cfg(search: str, rules: list[dict], operators: list[str]) -> dict:
    has_indicator = any(
        r.get("type1") == "indicator" or r.get("type2") == "indicator" for r in rules
    )
    cfg = {
        "search": search,
        "rules": rules,
        "operators": operators,
        "indicators": (
            {"EMA length=20": {"indicator": _EMA_ITEM, "outputs": [{"name": "EMA", "y_axis": "price"}]}}
            if has_indicator
            else {}
        ),
        "dataProviderConfig": {"data": [_ANCHOR, _EMA_ITEM] if has_indicator else [_ANCHOR]},
    }
    # url/full_url left out on purpose: also tests the server-side fill.
    return cfg


def _data_rule(key: str) -> dict:
    return {
        "type1": "data",
        "source1": "Binance",
        "name1": "BTCUSDT",
        "interval1": "5m",
        "key1": key,
        "comparator": ">",
        "type2": "value",
        "value2": 0,
    }


async def main() -> int:
    loop = asyncio.get_running_loop()

    # --- 1. search_assets ---------------------------------------------------
    try:
        assets = await server.search_assets("BTC", limit=5)
        ok = isinstance(assets, list) and assets and "details" in assets[0]
        record(
            "search_assets('BTC') returns entities",
            bool(ok),
            f"{len(assets)} rows; first: {assets[0]['details'].get('source')}/{assets[0]['details'].get('name') if assets else ''}",
        )
    except Exception as exc:  # noqa: BLE001
        record("search_assets('BTC') returns entities", False, f"{type(exc).__name__}: {exc}"[:200])

    # --- 2. list_indicators -------------------------------------------------
    try:
        inds = await server.list_indicators("EMA", limit=5)
        ok = isinstance(inds, list) and inds and "details" in inds[0]
        names = [i.get("name") for i in (inds or [])][:3]
        record("list_indicators('EMA') returns catalog", bool(ok), f"{len(inds)} rows; {names}")
    except Exception as exc:  # noqa: BLE001
        record("list_indicators('EMA') returns catalog", False, f"{type(exc).__name__}: {exc}"[:200])

    # --- 3. get_candles: exactly 100 rows, full OHLCV shape ------------------
    # The backend's wire format keys OHLCV columns as
    # "<source>-<symbol>-<interval>-<col>" alongside "date".
    try:
        candles = await server.get_candles("Binance", "BTCUSDT", "5m", 100)
        rows = candles.get("data") or []
        cols = [f"Binance-BTCUSDT-5m-{c}" for c in ("open", "high", "low", "close", "volume")]
        good_rows = all(r.get("date") is not None and all(r.get(c) is not None for c in cols)
                        for r in rows)
        record(
            "get_candles(Binance,BTCUSDT,5m,100) -> exactly 100 complete rows",
            len(rows) == 100 and good_rows,
            f"{len(rows)} rows; last close: {rows[-1].get(cols[-2]) if rows else None}",
        )
    except Exception as exc:  # noqa: BLE001
        record("get_candles(...) -> exactly 100 complete rows", False, f"{type(exc).__name__}: {exc}"[:200])

    # --- 4. run_scanner: worked example, stopped mid-run after a match ------
    scan_task = asyncio.create_task(server.run_scanner(WORKED_EXAMPLE))
    stop_resp: dict | None = None
    try:
        deadline = loop.time() + 240
        while loop.time() < deadline and not scan_task.done():
            await asyncio.sleep(2)
            snaps = await server.active_scans()
            if not snaps:
                break
            snap = snaps[0]
            if snap["matched"] >= 1 and snap["scanned"] >= 10:
                stop_resp = await server.stop_scanner()
                break
        out = await asyncio.wait_for(asyncio.shield(scan_task), timeout=180)
    except Exception as exc:  # noqa: BLE001
        record("run_scanner(worked example) matches + stop_scanner mid-run", False,
               f"{type(exc).__name__}: {exc}"[:200])
        out = None

    if out is not None:
        matched = out.get("matched", 0)
        results = out.get("results") or []
        progress = out.get("progress") or []
        res0 = results[0] if results else {}
        dv = res0.get("data_values") or {}
        dv_ok = len(dv) >= 2 and all(
            isinstance(v, (int, float)) for v in dv.values() if v is not None
        )
        note = out.get("note")
        stopped_ok = stop_resp is None or (stop_resp.get("requested") and note == "stopped by stop_scanner")
        ok = matched >= 1 and dv_ok and progress and progress[0].startswith("Scanning") and stopped_ok
        detail = (
            f"matched={matched} scanned={out.get('total_scanned')} "
            f"data_values={ {k: dv[k] for k in list(dv)[:3]} } note={note!r} "
            f"stop={stop_resp if stop_resp is None else {k: stop_resp[k] for k in ('requested','runs','scanned','matched')}}"
        )
        record("run_scanner(worked example) matches + stop_scanner mid-run", bool(ok), detail[:400])

    # --- 5. stop_scanner with nothing active --------------------------------
    await _expect_error(
        server.stop_scanner(),
        "stop_scanner with no active run -> clean error",
        "no scanner run is active",
    )

    # --- 6. scanner variant: 'near' comparator (narrow search) ---------------
    cfg_near = _ema_scan_cfg(
        _NARROW_SEARCH,
        [
            {
                "type1": "indicator",
                "indicator1": "EMA length=20",
                "output1": "EMA",
                "comparator": "near",
                "near": 10,
                "type2": "data",
                "source2": "Binance",
                "name2": "BTCUSDT",
                "interval2": "5m",
                "key2": "close",
            }
        ],
        [],
    )
    try:
        out = await server.run_scanner(cfg_near)
        # With a live pair and a 10% tolerance, at least one candidate should match.
        record(
            "run_scanner near-comparator (narrow) matches",
            bool(out.get("total_scanned", 0) > 0 and out.get("matched", 0) >= 1),
            f"matched={out.get('matched')} scanned={out.get('total_scanned')} note={out.get('note')!r}",
        )
    except Exception as exc:  # noqa: BLE001
        record("run_scanner near-comparator (narrow) matches", False, f"{type(exc).__name__}: {exc}"[:200])

    # --- 7a. scanner variant: two rules joined by 'and' ----------------------
    cfg_and = _ema_scan_cfg(_NARROW_SEARCH, [_data_rule("close"), _data_rule("open")], ["and"])
    try:
        out = await server.run_scanner(cfg_and)
        res0 = (out.get("results") or [{}])[0]
        record(
            "run_scanner two-rule 'and' (narrow) matches",
            bool(out.get("matched", 0) >= 1) and bool(res0.get("data_values")),
            f"matched={out.get('matched')} data_values={res0.get('data_values')}",
        )
    except Exception as exc:  # noqa: BLE001
        record("run_scanner two-rule 'and' (narrow) matches", False, f"{type(exc).__name__}: {exc}"[:200])

    # --- 7b. scanner variant: rules joined by 'or' (indicator + data) --------
    cfg_or = _ema_scan_cfg(
        _NARROW_SEARCH,
        [
            {
                "type1": "indicator",
                "indicator1": "EMA length=20",
                "output1": "EMA",
                "comparator": ">",
                "type2": "data",
                "source2": "Binance",
                "name2": "BTCUSDT",
                "interval2": "5m",
                "key2": "close",
            },
            _data_rule("close"),
        ],
        ["or"],
    )
    try:
        out = await server.run_scanner(cfg_or)
        record(
            "run_scanner 'or' operator (narrow) matches",
            bool(out.get("matched", 0) >= 1),
            f"matched={out.get('matched')} scanned={out.get('total_scanned')}",
        )
    except Exception as exc:  # noqa: BLE001
        record("run_scanner 'or' operator (narrow) matches", False, f"{type(exc).__name__}: {exc}"[:200])

    # --- 8. invalid scanner config -> clean client-side error ----------------
    await _expect_error(
        server.run_scanner({"search": "BTC"}),
        "run_scanner with config missing required fields -> clean error",
        "missing required field",
    )

    # --- 9. get_chart_image: 1600x900 with two overlays ----------------------
    saved_path: str | None = None
    try:
        content = await server.get_chart_image(
            "Binance",
            "BTCUSDT",
            "5m",
            count=200,
            indicators=[
                {"name": "Exponential Moving Average", "params": {"length": "20"}},
                {"name": "Simple Moving Average", "params": {"length": "50"}},
            ],
            width_px=1600,
            height_px=900,
        )
        img = next((c for c in content if isinstance(c, McpImage)), None)
        txt = next((c for c in content if getattr(c, "text", None)), None)
        m = re.search(r"Chart saved to (\S+)", txt.text if txt else "")
        saved_path = m.group(1) if m else None
        png_ok = bool(img) and img.data[:8] == b"\x89PNG\r\n\x1a\n"
        dims_ok = False
        if png_ok and saved_path and os.path.exists(saved_path):
            with open(saved_path, "rb") as fh:
                head = fh.read(26)
            w, h = struct.unpack(">II", head[16:24])
            dims_ok = (w, h) == (1600, 900)
        record(
            "get_chart_image 1600x900 (EMA20 + SMA50) -> PNG exactly 1600x900",
            bool(png_ok and dims_ok and saved_path),
            f"saved: {saved_path}",
        )
    except Exception as exc:  # noqa: BLE001
        record("get_chart_image 1600x900 (EMA20 + SMA50)", False, f"{type(exc).__name__}: {exc}"[:300])

    # --- 10. error path: unknown symbol via get_candles -----------------------
    await _expect_error(
        server.get_candles("Binance", "DEFI_NOT_A_SYMBOL_12345", "5m", 10),
        "get_candles unknown symbol -> clean error",
        None,
    )

    # --- 11. error path: unknown symbol via chart (pre-check, no browser hang)
    await _expect_error(
        server.get_chart_image("Binance", "DEFI_NOT_A_SYMBOL_12345", "5m", count=50),
        "get_chart_image unknown symbol -> clean error (fast pre-check)",
        None,
    )

    # --- summary -------------------------------------------------------------
    failed = [r for r in _RESULTS if not r[1]]
    print("\n" + "=" * 64)
    print(f"{len(_RESULTS) - len(failed)}/{len(_RESULTS)} checks passed")
    if failed:
        print("Failed:")
        for name, _, detail in failed:
            print(f"  - {name}: {detail[:200]}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
