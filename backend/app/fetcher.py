# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

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
