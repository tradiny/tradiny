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

import threading

import db
from config import Config

from .fetcher import BlockingFetcher

dbconn = db.create_connection(Config.DB)

historical_data_cache = {}
last_update = {}

providers = {}
clients = {}

lock = threading.Lock()

startup_actions = []
periodic_tasks = []

indicator_fetcher = BlockingFetcher(int(Config.INDICATOR_WORKERS))
