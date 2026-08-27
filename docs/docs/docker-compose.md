# Run Everything with Docker Compose

Start **backend + frontend + the MCP server** together with a single command,
no separate steps:

```bash
cd tradiny
docker compose up --build
```

This composes the two pieces that already exist in the repo:

- **`tradiny`** — the standard image (root `Dockerfile`), which builds the
  frontend and the backend, and serves both on **`:8000`** (`/websocket/`
  included). This is the usual chart UI.
- **`tradiny-mcp`** — the MCP server image (`tradiny_mcp/Dockerfile`). It bundles
  Python + the `tradiny_mcp` package + **headless Chromium** (Playwright), so
  the `get_chart_image` tool works out of the box. It listens on **`:9010`**.

Once running:

| Endpoint | URL |
|---|---|
| Chart UI (frontend) | <http://localhost:8000> |
| MCP (streamable HTTP) | <http://localhost:9010/mcp> |

MCP clients use the endpoint above, or point at the container over the compose
network. The MCP service is configured automatically (`BACKEND_URL` /
`FRONTEND_URL` → `http://tradiny:8000`), so no per-tool setup is needed.

## Seeding the data catalog

The image bakes in `backend/db.sqlite3` when it is present in the working tree
(the default). On a **fresh clone** without the database, build with the
`POPULATE` flag to seed the asset/indicator catalog:

```yaml
services:
  tradiny:
    build:
      args:
        POPULATE: "true"     # seed the DB on first build
```

or override per run: `docker compose --build-arg POPULATE=true build tradiny`.
Provider keys (Binance, Polygon, OpenAI, …) come from `backend/.env`, which is
copied in at build time; override any of them via `tradiny.environment` in the
compose file.

## Everyday commands

```bash
docker compose up --build   # build (first time) + start both, in the foreground
docker compose up -d        # start in the background (daemon)
docker compose logs -f tradiny-mcp tradiny
docker compose down         # stop and remove the stack
```

## MCP client example

Any MCP client that supports streamable HTTP:

```json
{ "mcpServers": { "tradiny": { "url": "http://localhost:9010/mcp" } } }
```

> The MCP image is large (headless Chromium + system libraries are required for
> `get_chart_image`). If you will **not** use chart rendering, that is still the
> same image — the other five tools work without a browser. See the MCP tool
> reference in [`tradiny_mcp/README.md`](../../tradiny_mcp/README.md).
