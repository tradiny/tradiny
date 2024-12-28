# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

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
