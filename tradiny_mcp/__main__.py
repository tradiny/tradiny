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

"""Entry point: ``python -m tradiny_mcp`` (from the repo root).

HTTP/sse/stdio selection and host/port come from ``tradiny_mcp/config.py``
(``MCP_TRANSPORT``, ``MCP_HOST``, ``MCP_PORT``).
"""

from .server import run_server

if __name__ == "__main__":
    run_server()
