# Tradiny MCP Server

An async [Model Context Protocol](https://modelcontextprotocol.io) server that
exposes the Tradiny backend's capabilities as MCP tools: asset & indicator
lookup, historical candle data, a high-level scanner (progress reported
server-side; not user-stoppable — there is a hard timeout instead), and real
frontend chart rendering to PNG (Playwright + headless Chromium).

Design spec: [`mcp_plan.md`](../mcp_plan.md).

**Package name:** the importable package is `tradiny_mcp`, not `mcp`. The
`mcp` PyPI package is the MCP SDK that `fastmcp` depends on — a top-level
package named `mcp` on `sys.path` would shadow it and break `fastmcp`'s
imports, so this one is named to avoid the collision (the plan's `mcp/`
directory became `tradiny_mcp/`).

## Tools

| Tool | Purpose |
|---|---|
| `search_assets(query, limit, source?)` | Discover tradeable entities (`source`/`symbol` pairs + details). |
| `list_indicators(query, limit)` | Indicator catalog with exact IDs, inputs (names + defaults) and outputs. |
| `get_candles(source, symbol, interval, count=600)` | Historical OHLCV candles (one-shot, no streaming). |
| `scan(interval, condition, indicators?, joiners?, within_pct=2, count=300, source?, search="")` | High-level scanner: condition(s) over OHLCV columns, indicator outputs, or literal values. `source` scopes to one exchange; leaving `search=""` scans the **whole book of that exchange in one call**. Runs to completion (or `SCAN_TIMEOUT_SECONDS`). |
| `get_chart_image(source, symbol, interval, count=200, indicators, width_px=1280, height_px=720)` | Render a chart in the real frontend and return it as a PNG image (exact `width_px × height_px`), saved under `OUTPUT_DIR`. |

The low-level scanner primitives (`run_scanner`, `stop_scanner`,
`active_scans`) still exist in `tradiny_mcp/server.py` (and are exercised by
`smoke.py`) but are intentionally **not** MCP tools — `scan` is the only
scanner surface exposed to MCP clients, so clients never need to learn the
UI-shape scanner config directly.

All tools are async; the backend has **no REST API** — this server drives it
over its WebSocket at `ws(s)://<BACKEND host>/websocket/`, and `get_chart_image`
drives the actual frontend page, so charts look exactly like the UI's.

## Setup

```bash
cd tradiny_mcp
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
playwright install chromium      # one-time, needed for get_chart_image
cp .env.example .env             # then edit
```

Prerequisites:
- Tradiny backend running (`cd backend && python server.py`, or the Docker image).
- A **served frontend** for `FRONTEND_URL`:
  - Docker: the backend serves `frontend/dist` at `http://<host>:8000`.
  - Bare local checkout: build it first — `cd frontend && npm ci && npm run build`
    (the backend mounts `dist/` at `/`); alternatively point `FRONTEND_URL` at
    the webpack dev server (`http://localhost:9000`).

## Configuration

Environment variables (process env wins over `tradiny_mcp/.env`):

| Variable | Default | Description |
|---|---|---|
| `FRONTEND_URL` | (required) | Served frontend page, e.g. `http://localhost:8000`. Used by `get_chart_image`. |
| `BACKEND_URL` | (required) | Backend origin, e.g. `http://localhost:8000`. WS endpoint = `ws(s)://<host>/websocket/`; also fills `dataProviderConfig.url`/`full_url` in scanner configs. |
| `MCP_HOST` | `0.0.0.0` | Bind host for the HTTP transport. |
| `MCP_PORT` | `9010` | Port for the streamable-HTTP endpoint. |
| `MCP_TRANSPORT` | `http` | `http` (streamable HTTP) or `stdio`. |
| `OUTPUT_DIR` | `./output` | Where chart PNGs are saved (created if missing). |
| `WS_TIMEOUT_SECONDS` | `30` | Per request/response round-trip timeout (search / candles / indicator init). |
| `CHART_TIMEOUT_SECONDS` | `60` | Page-load + data + render budget for `get_chart_image`. |
| `SCAN_TIMEOUT_SECONDS` | `180` | Overall scanner run budget. Raise it if the book is very large or you run multiple scans at once. |
| `SCAN_QUIESCE_SECONDS` | `5` | Silence window after the last progress line before a scan is declared complete. |

## Running

```bash
# from the repo root
python -m tradiny_mcp                      # streamable-HTTP on $MCP_HOST:$MCP_PORT (default 0.0.0.0:9010)
MCP_TRANSPORT=stdio python -m tradiny_mcp  # stdio (for MCP clients that spawn the server)
```

Example client config (any MCP client that supports streamable HTTP):

```json
{ "mcpServers": { "tradiny": { "url": "http://localhost:9010/mcp" } } }
```

## Tool notes

### `search_assets`
`query` is a case-insensitive substring over entity names/sources (`""` = all,
capped by `limit`, backend default cap 100). Returns
`[{ id, name, details: {source, name, type, outputs, ...}, type: "data" }]`.

### `list_indicators`
Returns the indicator catalog. From `details` you get:
- `inputs[].name` — exact keys for an indicator item's `inputs` dict;
- `inputs[].default[n]` — fallback values when omitted;
- `outputs[].name` — the allowed `output1`/`output2` values in scanner rules;
- `columns` — the price column(s) the indicator consumes (drives `dataMap`).

### `get_candles`
One-shot historical fetch (`stream:false`). `no_data` from the backend raises a
`NoDataError` surfaced as a tool error naming the entity. Returns
`{source, name, interval, metadata, data: [...]}` where each row is
`{"date": "YYYY-MM-DD HH:MM:SS", ...}` plus one keyed column per OHLCV field:
`"<source>-<symbol>-<interval>-<col>"` (e.g. `"Binance-BTCUSDT-5m-close"`,
value as a string) — the backend's wire format, returned verbatim.

### `scan`
`scan(interval, condition, indicators=None, joiners=None, within_pct=2, count=300, source=None, search="")` —
the high-level scanner. `condition` is one object (or a list of them) shaped
`{"left": <side>, "op": "<" | ">" | "near", "right": <side>}` (optional
`"within"` percent overrides `within_pct`); a `<side>` is an OHLCV column name
(`open|high|low|close|volume`), a JSON number, or an indicator reference
`{"indicator": <index into indicators>, "output": <output name or unique
substring>}` (output names come from `list_indicators` `details.outputs`).
`indicators` is a list of `{"name": <indicator display name from
`list_indicators`>, "params": {<inputName>: <value>}}` (omitted inputs fall
back to the catalog default). `joiners` are `"and"`/`"or"` between
conditions (defaults to all `"and"`). **`source` scopes the candidate set to
one exchange** (case-insensitive), and **`search` is an optional name
substring** — leave it `""` (default) to scan **every asset on that exchange
in ONE call**. The anchor, indicator items, `dataMap`, and outputs are
assembled internally from a seed entity; the backend re-substitutes each
candidate's source/name, so the anchor does **not** need to come from the
target exchange. Callers never deal with the raw UI-shape scanner config.

**Example (preferred — one whole-exchange scan):** "every Hyperliquid asset
on 1d whose close recently crossed the middle Donchian (100) band. A single
call, no per-coin loop":

```python
scan(
    interval="1d",
    condition={
        "left": "close",
        "op": "near",
        "right": {"indicator": 0, "output": "Mid"},
    },
    indicators=[{
        "name": "Donchian Channels (DC)",
        "params": {"lower_length": "100", "upper_length": "100"},
    }],
    within_pct=2,
    source="Hyperliquid",   # scope to one exchange; search left empty => whole book
)
```

To narrow by ticker instead, pass `search="BTC"` alongside a `source`.

**Completion semantics.** The backend sends `scan_progress`
(`"Scanning 003/012"`) and `scan_result` frames and **no final "done"** message.
This server therefore finishes a run when, after the last progress line
(`Scanning N/N`), it sees silence for `SCAN_QUIESCE_SECONDS` — the same
heuristic the frontend uses, so it is approximate (a late `scan_result` on the
final candidate can still be missed in edge cases). `SCAN_TIMEOUT_SECONDS`
hard-caps the run; there is **no** user-facing "stop" tool — narrow `search`
to a smaller candidate set if a run is taking too long.

**Returns:**
`{ "total_scanned": N, "matched": M,
"assets": [ {source, name, label, values, cross?}, ... ],
"results": [ { data, data_values }, ... ],
"progress": [ "Scanning 001/N", ... ], "note"? }` where `values` holds the
numeric sides of each condition, and `cross.direction` is `"up"` when the
close ended above the other value (bullish) and `"down"` when below (bearish).

(The low-level `run_scanner(config)` / `stop_scanner()` functions still exist
in `server.py` for internal use and `smoke.py` testing, but are not MCP tools.)

### `run_scanner` (internal, not an MCP tool)
`config` is **the exact object the Tradiny UI sends in a `scan` message**.
Top-level required fields: `search`, `rules`, `operators`,
`dataProviderConfig`; plus `indicators` whenever any rule side is of type
`"indicator"`.

Rules: each rule compares side 1 vs side 2 with a `typeN` of `"data"`,
`"indicator"`, or `"value"`:
- `data` side → `sourceN`, `nameN`, `intervalN`, `keyN` (`open`/`high`/`low`/
  `close`/`volume`) — these must be **char-for-char identical** to the anchor in
  `dataProviderConfig.data` (see warning below).
- `indicator` side → `indicatorN` (key into the `indicators` map) and `outputN`
  (must equal the indicator's `outputs[].name`; values in the last data point
  are keyed `"<indicator item id>-<outputN>"`, so the item `id` + `outputs`
  must line up).
- `value` side → `valueN` (JSON number).
- `comparator` is `"<"` | `">"` | `"near"`; for `"near"` also set `near`
  (tolerance in **percent**: passes when `abs(v1-v2)/v2 * 100 < near`).
- `operators` holds `"and"`/`"or"` **between** rules; length must be
  `len(rules) - 1`.

The `indicators` map is `{ "<key>": { "indicator": <item>, "outputs": [...] } }`
where each **item** carries: `type: "indicator"`, a unique `id`, the indicator
**entity** under `indicator` (copy verbatim from `list_indicators`), `inputs`
(values as **strings**, e.g. `{"length": "20"}`), a `dataMap` mapping each
consumed column → `{source, name, interval, value: "<source>-<name>-<interval>-
<column>", dataKey}` (anchor strings again), and a minimal `render`
(`{indicatorId: <id>, paneIdx: 0}`).

`dataProviderConfig` needs `url` (`host:port`), `full_url`
(`ws(s)://<host>:port/websocket/`), and `data` — one `type:"data"` row for the
anchor series (its `source`/`name`/`interval` are the **anchor** the scanner
string-replaces per candidate across the whole config) plus one row per
indicator item (the same objects). The scanner fetches each candidate's data +
indicators on a fresh WS (`count` ≥ 300 recommended so long indicators have
history).

> url / full_url may be omitted — the server fills both from `BACKEND_URL`.

> ⚠ **Anchor-string discipline.** The scanner substitutes the anchor
> `source`/`name` strings via a regex over the *entire* config (`scanning`
> relies on it), and `rules_evaluate` drops any entity whose referenced key is
> missing from the last data point — i.e. a wrong `indicator1` key, a wrong
> `output1`, or a `source`/`name`/`interval`/`key` that doesn't match the
> anchor **silently skips the entity** (no error is returned). Keep the anchor
> strings char-for-char identical in `dataProviderConfig.data`, every `data`
> rule side, and every `dataMap`.

**How to build a scanner config** (recommended flow for an LLM client):
1. `search_assets(query)` → pick an entity's `details.{source, name}`, choose an
   interval → that is your anchor.
2. `list_indicators(query)` → copy the matched entity verbatim into
   `indicators.<key>.indicator.indicator`; read `inputs` (names + defaults) and
   `outputs` (valid `output1`/`output2` values).
3. Write `rules[]` + `operators[]` using the side-type field rules above; use
   `outputs[].name` for `output1`/`output2` and `open/high/low/close/volume`
   for `key1`/`key2`.
4. Build the shared indicator item (`id`, `inputs`, `dataMap`, `render`) with
   the anchor strings; put it both in `indicators.<key>.indicator` and as a row
   of `dataProviderConfig.data` alongside the anchor `type:"data"` row.
5. Call `run_scanner(config)`.

**Worked example** — "Scan every entity matching `BTC` on 5m where
EMA(length=20) of close is above close":

```json
{
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
      "key2": "close"
    }
  ],
  "operators": [],
  "indicators": {
    "EMA length=20": {
      "indicator": {
        "type": "indicator",
        "id": "indicators-pandas_ta-overlap-ema-EMA_length-20_close-Binance-BTCUSDT-5m-close",
        "indicator": {
          "id": "indicators.pandas_ta.overlap.ema.EMA",
          "name": "Exponential Moving Average",
          "type": "indicator",
          "details": {
            "categories": ["overlap"],
            "library": "pandas_ta",
            "columns": ["close"],
            "inputs": [ { "name": "length", "default": [10] } ],
            "outputs": [ { "name": "EMA", "y_axis": "price" } ]
          }
        },
        "inputs": { "length": "20" },
        "dataMap": {
          "close": {
            "source": "Binance",
            "name": "BTCUSDT",
            "interval": "5m",
            "value": "Binance-BTCUSDT-5m-close",
            "dataKey": "close"
          }
        },
        "render": {
          "indicatorId": "indicators-pandas_ta-overlap-ema-EMA_length-20_close-Binance-BTCUSDT-5m-close",
          "paneIdx": 0
        }
      },
      "outputs": [ { "name": "EMA", "y_axis": "price" } ]
    }
  },
  "dataProviderConfig": {
    "url": "localhost:8000",
    "full_url": "ws://localhost:8000/websocket/",
    "data": [
      { "type": "data", "source": "Binance", "name": "BTCUSDT", "interval": "5m", "count": 300 },
      {
        "type": "indicator",
        "id": "indicators-pandas_ta-overlap-ema-EMA_length-20_close-Binance-BTCUSDT-5m-close",
        "indicator": { "id": "indicators.pandas_ta.overlap.ema.EMA", "name": "Exponential Moving Average", "type": "indicator", "details": { "categories": ["overlap"], "library": "pandas_ta", "columns": ["close"], "inputs": [{ "name": "length", "default": [10] }], "outputs": [{ "name": "EMA", "y_axis": "price" }] } },
        "inputs": { "length": "20" },
        "dataMap": { "close": { "source": "Binance", "name": "BTCUSDT", "interval": "5m", "value": "Binance-BTCUSDT-5m-close", "dataKey": "close" } },
        "render": { "indicatorId": "indicators-pandas_ta-overlap-ema-EMA_length-20_close-Binance-BTCUSDT-5m-close", "paneIdx": 0 }
      }
    ]
  }
}
```

**Completion semantics.** The backend sends `scan_progress`
(`"Scanning 003/012"`) and `scan_result` frames and **no final "done"** message.
This server therefore finishes a run when, after the last progress line
(`Scanning N/N`), it sees silence for `SCAN_QUIESCE_SECONDS` — this is the same
heuristic the frontend uses, so it is approximate (a late `scan_result` on the
final candidate can still be missed in edge cases). `SCAN_TIMEOUT_SECONDS`
hard-caps the run. There is no user-facing stop tool for this low-level path
either — narrow the `search` substring to a smaller candidate set if a run is
slow.

**Returns:**
`{ "total_scanned": N, "matched": M, "results": [ { data, data_values }, ... ],
"progress": [ "Scanning 001/N", ... ] }` where each `data_values` maps labels
(derived from `rules_evaluate`, e.g. `"Exponential Moving Average
length=20"`, `"close"`) to the numbers compared.

### `stop_scanner` (internal, not an MCP tool)
No parameters. Sends `scan_stop` on the active scanner session; the backend
finishes the current candidate and stops. Returns `{ "requested": true,
"runs": <count>, "scanned": ["10/137", ...], "matched": [3, ...] }` — the
`i/N` progress position and match count per run at the moment of the request.
Errors if no scan is active on this server.

### `get_chart_image`
`indicators` is a list of `{ "name": <display name matching list_indicators;
first match wins>, "params": { "length": "20", ... } }` overlays applied in
order (key/value semantics as in `list_indicators` details). The page loads at
`FRONTEND_URL` with a `width_px × height_px` viewport, so the PNG is **exactly**
`width_px × height_px` (verified from the PNG header — a mismatch is an error,
never a silent blank). The PNG is returned as MCP image content and saved to
`OUTPUT_DIR/<YYYYmmdd_HHMMSS>_<source>_<symbol>_<interval>.png`, whose path is
returned as text alongside.

If `FRONTEND_URL` and `BACKEND_URL` live on different hosts, an init script
rewrites `window.WebSocket` so the chart (including its 5-second
auto-reconnect) talks to the backend's `/websocket/` endpoint.

## Risks & notes

- **fastmcp pin.** `requirements.txt` pins the exact `fastmcp` version the
  protocol surface (imports, `run()` signature) was built against — MCP library
  APIs drift between major versions.
- **Scanner completion is heuristic** (see `scan` / `run_scanner` notes above);
  there is no user-facing stop tool — narrow `search` if a run is slow.
- **Anchor-string discipline** (internal detail of `run_scanner`; `scan`
  handles this automatically) — mismatches cause *silent skips*, not errors
  (see warning in `run_scanner` above).
- **Rate limits.** The backend rate-limits per IP (`MAX_DATA_REQUESTS_PER_IP_
  PER_HOUR`); only `WHITELIST_IP` origins are exempt. Heavy scans from a remote
  host may be throttled — extend `WHITELIST_IP` or raise the cap server-side.
- **Frontend build.** `frontend/dist` (or the webpack dev server) must be
  reachable at `FRONTEND_URL` or `get_chart_image` cannot work.
