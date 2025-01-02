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

import os
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .router import websocket_router

from utils import (
    resource_path,
)

app = FastAPI()
app.include_router(websocket_router)

dist_directory = resource_path("dist")

if os.path.exists(dist_directory):
    app.mount("/", StaticFiles(directory=dist_directory, html=True), name="static")
else:
    logging.warning(
        "Warning: 'dist' directory does not exist; static files not mounted."
    )
