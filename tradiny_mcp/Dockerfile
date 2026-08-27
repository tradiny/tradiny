# Tradiny MCP server image (see tradiny_mcp/README.md and ../mcp_plan.md).
#
# Build from the repo root:
#     docker build -f tradiny_mcp/Dockerfile -t tradiny-mcp .
#
# Runs the async MCP server (6 tools). It drives the Tradiny backend over its
# WebSocket endpoint (BACKEND_URL) and renders charts with the real frontend
# in headless Chromium (FRONTEND_URL), so `get_chart_image` works out of the
# box. Chromium + its system libraries are installed at build time.
FROM python:3.14-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install the Python deps first (layer cache), then the browser.
# `playwright install --with-deps chromium` pulls Chromium and every system
# library headless Chromium needs, so chart rendering works in the container.
COPY tradiny_mcp/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY tradiny_mcp/ ./tradiny_mcp/

# Defaults (all overridable via env / docker compose):
#   - HTTP (streamable) transport bound to 0.0.0.0:9010
#   - chart PNGs written to /app/output
ENV MCP_TRANSPORT=http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=9010 \
    OUTPUT_DIR=/app/output

EXPOSE 9010

CMD ["python", "-m", "tradiny_mcp"]
