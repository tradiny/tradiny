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

"""Render a Tradiny chart to a PNG image using the real frontend (Playwright).

Approach: open the served frontend at a **deep-link URL that the frontend itself
understands** (``frontend/chart/index.js`` ``parseArgs``):

    {FRONTEND_URL}/?s=<symbol>&i=<interval>&c=<count>
        [&indicator1=<name>&indicator1-<param>=<value>
         &indicator2=<name>&indicator2-<param>=<value> ...]

This is the *same load path the web UI and a bookmark use*, so candlesticks and
every indicator overlay render through the chart's own complete setup before we
snapshot (this is what fixes the previous "data drawn over the chart" half-frame
problem — earlier we drove the chart half-way with its promise API and captured
a partially-composited frame). We wait for the instance, then for parseArgs()
to finish (``_rendered`` flag), let the paint settle, and capture with the
built-in ``imageHandler.getImage(elementId, {scale: 1, format: "png", quality: 1})``.

With ``device_scale_factor=1`` the ``#chart`` element fills the viewport, so the
decoded PNG is exactly ``width_px x height_px`` (verified from the PNG header; a
mismatch is rejected rather than returned).

If ``FRONTEND_URL`` and ``BACKEND_URL`` live on different hosts, an init script
rewrites ``window.WebSocket`` so the chart (and its auto-reconnect in
``frontend/ws.js``) talks to the backend's ``websocket`` endpoint instead of the
frontend host's (which does not proxy it).
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import re
import struct
import time
from urllib.parse import urlencode, urlparse

from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

from .config import Config, frontend_url_required, require_backend_url

logger = logging.getLogger("tradiny.mcp.chart")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class ChartRenderError(Exception):
    """Raised when the chart cannot be rendered or captured into a valid PNG."""


def _netloc(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"http://{url}")
    netloc = parsed.netloc or parsed.path
    if ":" not in netloc:
        netloc += ":443" if parsed.scheme == "https" else ":80"
    return netloc


def _needs_ws_rewrite(frontend_url: str, backend_url: str) -> bool:
    return _netloc(frontend_url) != _netloc(backend_url)


# Injected into the page before any script runs. Rewrites any WebSocket whose
# URL path ends in /websocket/ to the backend endpoint (the frontend computes
# its own host and would otherwise point at a host with no WS route).
_WS_REWRITE_TEMPLATE = """
(() => {
  const TARGET = %s;
  const Native = window.WebSocket;
  if (!Native) return;
  function PatchedWebSocket(url, protocols) {
    let target = url;
    try {
      const u = new URL(String(url), window.location.href);
      if (u.pathname.endsWith("/websocket/") || u.pathname.endsWith("/websocket")) {
        target = TARGET;
      }
    } catch (e) { /* leave as-is */ }
    if (protocols === undefined) return new Native(target);
    return new Native(target, protocols);
  }
  PatchedWebSocket.prototype = Native.prototype;
  for (const k of Object.getOwnPropertyNames(Native)) {
    try { PatchedWebSocket[k] = Native[k]; } catch (e) { /* readonly */ }
  }
  window.WebSocket = PatchedWebSocket;
})();
""".strip()


# The served page must expose the live chart instance before we can capture it.
_INSTANCE_READY_JS = (
    "!!(window.Tradiny1 && window.Tradiny1.dataProvider"
    " && window.Tradiny1.imageHandler)"
)
# True once parseArgs() (symbol -> interval -> candlestick -> every indicator)
# has completed and the first render has been scheduled (set by renderHandler
# on the animationframe after initialize() resolves).
_LOADED_JS = "!!window.Tradiny1 && window.Tradiny1._rendered === true"

# Snapshot the finished chart through the same path the UI's download button
# uses. imageHandler.getImage renders the element (WebGL + SVG + labels) and
# returns a data URL; elementId already points at the #chart element.
_CAPTURE_JS = """
async () => {
  const chart = window.Tradiny1;
  if (!chart || !chart.imageHandler) {
    throw new Error("Tradiny chart instance is not ready for capture");
  }
  // Two frames so the last indicator overlay / axes paint before we snapshot.
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  const url = await chart.imageHandler.getImage(chart.elementId, {
    scale: 1,
    format: "png",
    quality: 1,
  });
  if (typeof url !== "string" || url.indexOf("data:image/png") !== 0) {
    throw new Error("imageHandler.getImage did not return a PNG data URL");
  }
  return url;
}
""".strip()


def _chart_inputs(ind: dict) -> dict:
    """Return the indicator's input params, tolerating both the MCP shape
    ``{"name":.., "params": {...}}`` and a flat ``{"name":.., <param>:..}``."""
    inputs = ind.get("params")
    if isinstance(inputs, dict):
        return inputs
    if inputs is None:
        return {k: v for k, v in ind.items() if k != "name"}
    return {}


def _build_chart_url(
    frontend_url: str, *, name: str, interval: str, count: int, indicators: list[dict]
) -> str:
    """Deep-link URL the frontend loads via parseArgs() (``?s= &i= &c= &indicatorN=``).

    Parameter names come straight from ``frontend/chart/index.js``
    ``parseArgs``/``extractIndicators``: ``s``=symbol, ``i``=interval,
    ``c``=candle count, and per indicator ``indicatorN=<name>`` with inputs as
    ``indicatorN-<param>=<value>``.
    """
    params: list[tuple[str, str]] = [("s", str(name)), ("i", str(interval))]
    if count:
        params.append(("c", str(int(count))))
    for n, ind in enumerate(indicators or [], start=1):
        if not isinstance(ind, dict) or not ind.get("name"):
            continue
        params.append((f"indicator{n}", str(ind["name"])))
        for key, value in _chart_inputs(ind).items():
            params.append((f"indicator{n}-{key}", str(value)))
    return f"{frontend_url.rstrip('/')}/?{urlencode(params)}"


def _check_png(data: bytes, expected_width: int, expected_height: int) -> None:
    if not data.startswith(PNG_MAGIC):
        raise ChartRenderError("Captured image is not a valid PNG.")
    if len(data) < 24:
        raise ChartRenderError("Captured PNG is truncated.")
    width, height = struct.unpack_from(">II", data, 16)
    if (width, height) != (expected_width, expected_height):
        raise ChartRenderError(
            f"Captured PNG dimensions are {width}x{height}, "
            f"expected {expected_width}x{expected_height}."
        )


def _sanitize_filename_part(part: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", part).strip("._")
    return cleaned[:64] or "x"


def _save_png(
    png_bytes: bytes, source: str, name: str, interval: str, output_dir: str | None = None
) -> str:
    out_dir = output_dir or Config.OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    fname = f"{stamp}_{_sanitize_filename_part(source)}_{_sanitize_filename_part(name)}_{_sanitize_filename_part(interval)}.png"
    path = os.path.join(out_dir, fname)
    with open(path, "wb") as fh:
        fh.write(png_bytes)
    return path


class _BrowserSession:
    """One shared, long-lived Playwright browser reused across chart renders.

    Launching Chromium is the expensive fixed cost of a single chart (tens of
    ms to a full second per launch, plus allocator churn). A batch of charts
    should pay that once. The browser is created lazily on first use and torn
    down via :meth:`close` (wire it to server shutdown). It is bound to the
    event loop that first creates it, so it must be used from the server's
    single loop -- which is the case for every MCP tool in this process.
    """

    _pw = None
    _browser = None
    _lock = None

    @classmethod
    async def ensure(cls):
        """Return the shared browser, launching the Playwright runtime +
        Chromium on first use and reusing them afterwards."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        async with cls._lock:
            if (
                cls._pw is None
                or cls._browser is None
                or not cls._browser.is_connected()
            ):
                if cls._pw is None:
                    cls._pw = await async_playwright().start()
                cls._browser = await cls._pw.chromium.launch(headless=True)
            return cls._browser

    @classmethod
    async def close(cls):
        """Tear down the shared browser and Playwright runtime (best-effort)."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        async with cls._lock:
            if cls._browser is not None:
                try:
                    await cls._browser.close()
                except Exception:  # noqa: BLE001 - best-effort teardown
                    logger.exception("Failed to close the shared browser")
                finally:
                    cls._browser = None
            if cls._pw is not None:
                try:
                    await cls._pw.stop()
                except Exception:  # noqa: BLE001 - best-effort teardown
                    logger.exception("Failed to stop the Playwright runtime")
                finally:
                    cls._pw = None


async def _ws_rewrite_target() -> str | None:
    """WebSocket-rewrite target when the frontend and backend are on different
    hosts, else ``None`` (no rewrite needed)."""
    frontend_url = frontend_url_required()
    backend_url = require_backend_url()
    if not _needs_ws_rewrite(frontend_url, backend_url):
        return None
    from .config import backend_ws_url

    target = backend_ws_url()
    logger.info(
        "Frontend (%s) and backend (%s) differ; rewriting WS host to %s",
        _netloc(frontend_url),
        _netloc(backend_url),
        target,
    )
    return target


async def _render_into(
    output_dir: str,
    *,
    source: str,
    name: str,
    interval: str,
    count: int,
    indicators: list[dict],
    width_px: int,
    height_px: int,
) -> tuple[bytes, str]:
    """Render one chart and save the PNG into ``output_dir``.

    Navigates the *shared* browser (see :class:`_BrowserSession`) to the
    frontend deep-link URL, waits for the render to complete
    (``window.Tradiny1._rendered === true``), and snapshots with the built-in
    image handler. Raises :class:`ChartRenderError` on any failure.
    """
    frontend_url = frontend_url_required()
    target_url = _build_chart_url(
        frontend_url, name=name, interval=interval, count=count, indicators=indicators
    )
    logger.info("Loading chart via %s", target_url)

    timeout_ms = int(Config.CHART_TIMEOUT_SECONDS * 1000)
    ws_target = await _ws_rewrite_target()

    browser = await _BrowserSession.ensure()
    page_errors: list[str] = []
    context = await browser.new_context(
        viewport={"width": width_px, "height": height_px},
        device_scale_factor=1,
    )
    if ws_target is not None:
        await context.add_init_script(
            _WS_REWRITE_TEMPLATE % ('"' + ws_target.replace('"', '\\"') + '"')
        )
    page = await context.new_page()
    try:
        page.on("pageerror", lambda exc: page_errors.append(f"pageerror: {exc}"))
        page.on(
            "console",
            lambda msg: (
                msg.type == "error" and page_errors.append(f"console: {msg.text}")
            ),
        )

        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_ms)
            await page.wait_for_function(_INSTANCE_READY_JS, timeout=timeout_ms)
            await page.wait_for_function(_LOADED_JS, timeout=timeout_ms)
            data_url = await asyncio.wait_for(
                page.evaluate(_CAPTURE_JS), timeout=timeout_ms / 1000
            )
        except (PlaywrightTimeoutError, asyncio.TimeoutError):
            detail = (
                f" Last frontend errors: {' | '.join(page_errors[-3:])}"
                if page_errors
                else ""
            )
            raise ChartRenderError(
                f"Chart rendering timed out after {Config.CHART_TIMEOUT_SECONDS}s."
                f"{detail} (The symbol or an indicator may be unknown; verify "
                f"them with search_assets / list_indicators.)"
            ) from None

        if not isinstance(data_url, str) or not data_url.startswith("data:image/png"):
            raise ChartRenderError("imageHandler.getImage did not return a PNG data URL")

        png_bytes = base64.b64decode(data_url.split(",", 1)[1])
        _check_png(png_bytes, width_px, height_px)
        path = _save_png(png_bytes, source, name, interval, output_dir)
        logger.info("Saved chart image to %s", path)
        return png_bytes, path
    finally:
        await context.close()


async def render_chart(
    *,
    source: str,
    name: str,
    interval: str,
    count: int,
    indicators: list[dict],
    width_px: int,
    height_px: int,
) -> tuple[bytes, str]:
    """Render the requested chart into the default output dir and return
    ``(png_bytes, saved_path)``.

    Backward-compatible single-chart entry point (used by ``get_chart_image``).
    It reuses the shared browser session, so it no longer launches Chromium per
    call. See :func:`render_charts_batch` for parallel rendering into a
    caller-chosen directory.
    """
    return await _render_into(
        Config.OUTPUT_DIR,
        source=source,
        name=name,
        interval=interval,
        count=count,
        indicators=indicators or [],
        width_px=width_px,
        height_px=height_px,
    )


def _resolve_output_dir(requested: str | None) -> tuple[str, str | None]:
    """Pick the directory charts are saved into.

    Uses ``requested`` if it exists or can be created and is writable, else
    falls back to the configured default. Returns ``(dir, warning)`` where
    ``warning`` is set only when a fallback was forced (e.g. the MCP server runs
    in a container and the requested host dir is not bind-mounted at that path).
    """
    candidate = requested or Config.OUTPUT_DIR
    if candidate and candidate != Config.OUTPUT_DIR:
        try:
            os.makedirs(candidate, exist_ok=True)
            if os.access(candidate, os.W_OK):
                return candidate, None
        except OSError:
            pass
        warning = (
            f"Requested output_dir {requested!r} is not writable by the MCP "
            f"server; saving into the default {Config.OUTPUT_DIR!r} instead. If the "
            "MCP server is containerized, bind-mount the requested dir into the "
            "server container at that same path."
        )
        return Config.OUTPUT_DIR, warning
    return candidate, None


async def render_charts_batch(
    items: list[dict],
    output_dir: str | None = None,
    concurrency: int | None = None,
) -> tuple[str, list[dict]]:
    """Render many charts in parallel, saving PNGs into ``output_dir``.

    Each item supplies ``source`` and ``symbol``; optional per-item overrides
    are ``interval``, ``count``, ``indicators``, ``width_px`` and ``height_px``.
    All renders share one headless browser (launched once, see
    :class:`_BrowserSession`) and run with at most ``concurrency`` in flight
    (default :data:`Config.RENDER_CONCURRENCY`).

    Returns ``(resolved_output_dir, results)``. Each result is a dict with
    ``source``/``symbol``/``ok`` and either ``path`` + ``image_b64``
    (success — ``image_b64`` is the rendered PNG as base64, the canonical
    artifact for the caller to persist into its own folder) or ``error``
    (failure); an individual chart's failure never aborts the batch.
    """
    if not items:
        raise ValueError("render_charts_batch requires at least one chart item")

    resolved_dir, dir_warning = _resolve_output_dir(output_dir)
    if dir_warning:
        logger.warning(dir_warning)

    limit = max(1, min(int(concurrency or Config.RENDER_CONCURRENCY), 32))
    semaphore = asyncio.Semaphore(limit)

    async def _one(item: dict) -> dict:
        symbol = item.get("symbol") or item.get("name") or ""
        source = item.get("source")
        base = {"source": source, "symbol": symbol}
        async with semaphore:
            try:
                png_bytes, path = await _render_into(
                    resolved_dir,
                    source=source,
                    name=symbol,
                    interval=item.get("interval") or "1d",
                    count=int(item.get("count") or 500),
                    indicators=item.get("indicators") or [],
                    width_px=int(item.get("width_px") or 1280),
                    height_px=int(item.get("height_px") or 720),
                )
            except Exception as exc:  # noqa: BLE001 - keep the whole batch going
                return {**base, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
        return {**base, "ok": True, "path": path,
                "image_b64": base64.b64encode(png_bytes).decode("ascii")}

    results = await asyncio.gather(*(_one(it) for it in items))
    return resolved_dir, list(results)
