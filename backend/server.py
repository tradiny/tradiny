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
