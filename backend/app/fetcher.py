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

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Queue as MPQueue
import queue


class BlockingFetcher:
    def __init__(self, max_workers):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def fetch(self, fn, args):
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            self.executor, fn, *args  # The blocking function
        )
        return result
