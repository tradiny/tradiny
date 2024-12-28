# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

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
