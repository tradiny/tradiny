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

"""Tradiny MCP server.

A Model Context Protocol bridge that exposes the Tradiny backend's data,
scanner, and charting capabilities to MCP clients (e.g. Claude). The real
work is still done by the Tradiny backend this server talks to over its
WebSocket API; see ``server.py`` in this package for the tool definitions
and ``mcp_plan.md`` (repo root) for the design.

``python -m tradiny_mcp`` starts the server (HTTP by default on :9010, or
stdio with ``MCP_TRANSPORT=stdio``).

Note: this package is intentionally NOT named ``mcp``. The ``mcp`` PyPI
package is the MCP SDK that ``fastmcp`` depends on, and a top-level package
named ``mcp`` on ``sys.path`` would shadow it and break ``fastmcp``'s
imports.
"""

__all__ = ["config", "ws_client", "chart", "server"]
