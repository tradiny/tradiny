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

"""Environment-based configuration for the Tradiny MCP server.

Every value can be overridden with an environment variable (or a local
``tradiny_mcp/.env`` file). ``FRONTEND_URL`` and ``BACKEND_URL`` are required in use
but default to empty strings so that the module always imports cleanly and the
MCP server can report a clear, actionable error at request time instead of
crashing on import.
"""

import os
from urllib.parse import urlparse

from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))

# Load `tradiny_mcp/.env` without overriding variables that are already present in the
# environment (so an external .env / container env always wins).
load_dotenv(os.path.join(_HERE, ".env"), override=False)


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def _env_float(name: str, default: float) -> float:
    return float(_env(name, str(default)))


class Config:
    # --- Required -------------------------------------------------------------
    # Base URL of the served frontend page (e.g. `http://localhost:8000`).
    FRONTEND_URL: str = _env("FRONTEND_URL", "")
    # Base URL of the backend (e.g. `http://localhost:8000`). The WS client
    # connects to `ws(s)://<host>/websocket/`; it also fills the scanner's
    # `dataProviderConfig.url` / `full_url` when they are omitted.
    BACKEND_URL: str = _env("BACKEND_URL", "")

    # --- MCP server -----------------------------------------------------------
    MCP_HOST: str = _env("MCP_HOST", "0.0.0.0")
    MCP_PORT: int = int(_env("MCP_PORT", "9010"))
    # "http" (streamable HTTP) or "stdio".
    MCP_TRANSPORT: str = _env("MCP_TRANSPORT", "http")

    # --- Output / timeouts ----------------------------------------------------
    OUTPUT_DIR: str = os.path.abspath(_env("OUTPUT_DIR", "./output"))
    WS_TIMEOUT_SECONDS: float = _env_float("WS_TIMEOUT_SECONDS", 30)
    CHART_TIMEOUT_SECONDS: float = _env_float("CHART_TIMEOUT_SECONDS", 60)
    # A full-book scan is many sequential provider fetches, so give it enough
    # headroom to finish: default 180 s (raise via SCAN_TIMEOUT_SECONDS if the
    # book is very large or you run multiple scans at once).
    SCAN_TIMEOUT_SECONDS: float = _env_float("SCAN_TIMEOUT_SECONDS", 180)
    SCAN_QUIESCE_SECONDS: float = _env_float("SCAN_QUIESCE_SECONDS", 5)

    # How many charts ``render_charts`` renders at once. They all reuse one
    # shared headless browser; this cap bounds parallel context/page churn.
    RENDER_CONCURRENCY: int = int(_env("RENDER_CONCURRENCY", "3"))


def require_backend_url() -> str:
    """Return ``Config.BACKEND_URL`` after validating it is set."""
    if not Config.BACKEND_URL:
        raise ValueError(
            "BACKEND_URL is not configured. Set the BACKEND_URL environment "
            "variable (e.g. http://localhost:8000) or add it to tradiny_mcp/.env."
        )
    return Config.BACKEND_URL.rstrip("/")


def backend_ws_url(backend_url: str | None = None) -> str:
    """Convert a backend base URL into its WebSocket endpoint.

    ``http://localhost:8000``   -> ``ws://localhost:8000/websocket/``
    ``https://example.com``     -> ``wss://example.com/websocket/``
    ``ws://example.com``        -> ``ws://example.com/websocket/``
    """
    base = (backend_url or require_backend_url()).rstrip("/")
    parsed = urlparse(base if "://" in base else f"http://{base}")
    scheme = parsed.scheme or "http"
    if scheme in ("https", "wss", "ws"):
        ws_scheme = "wss" if scheme in ("https", "wss") else "ws"
    else:
        ws_scheme = "ws"
    host = parsed.netloc or parsed.path  # allow `localhost:8000` without a scheme
    return f"{ws_scheme}://{host}/websocket/"


def backend_host_port(backend_url: str | None = None) -> str:
    """Return ``<host>:<port>`` for a backend base URL (for dataProviderConfig.url)."""
    base = (backend_url or require_backend_url()).rstrip("/")
    if "://" not in base:
        if base.count(":") == 1:
            return base
        return f"{base}:8000"
    parsed = urlparse(base)
    netloc = parsed.netloc or parsed.path
    if ":" not in netloc:
        port = 443 if parsed.scheme == "https" else 80
        return f"{netloc}:{port}"
    return netloc


def frontend_url_required() -> str:
    """Return ``Config.FRONTEND_URL`` after validating it is set."""
    if not Config.FRONTEND_URL:
        raise ValueError(
            "FRONTEND_URL is not configured. Set the FRONTEND_URL environment "
            "variable (e.g. http://localhost:8000) or add it to tradiny_mcp/.env."
        )
    return Config.FRONTEND_URL.rstrip("/")
