# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

import uvicorn
import db
import os
import sys

from config import Config

from app import app
from app.startup import register_startup_actions
from app.periodic import register_periodic_task, periodic_task
from log import setup_logging


def main(on_startup=None):

    setup_logging()
    register_startup_actions(on_startup)
    register_periodic_task(periodic_task)

    uvicorn.run(app, host=Config.HOST, port=int(Config.PORT), workers=1)


if __name__ == "__main__":
    main()
