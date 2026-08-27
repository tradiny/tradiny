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
from log import setup_logging


def main(on_startup=None):
    # Python >= 3.14 changed the default POSIX multiprocessing start method from
    # "fork" to "forkserver". app/globals.py builds shared managers at import
    # time, which only works under "fork", so pin it before importing the app.
    import multiprocessing

    multiprocessing.set_start_method("fork", force=True)

    from app import app
    from app.startup import register_startup_actions
    from app.periodic import register_periodic_task, periodic_task

    setup_logging()
    register_startup_actions(on_startup)
    register_periodic_task(periodic_task)

    uvicorn.run(app, host=Config.HOST, port=int(Config.PORT), workers=1)


if __name__ == "__main__":
    main()
