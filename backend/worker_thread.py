import asyncio
import queue
import threading

import db



def queue_to_async(async_queue, task_queue, loop):
    while True:
        task = task_queue.get()  # blocking get
        asyncio.run_coroutine_threadsafe(async_queue.put(task), loop)


class WorkerThread(threading.Thread):
    def __init__(self, task_queue: queue.Queue, i: int, process_queue):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.task_queue = task_queue
        self.i = i
        self.process_queue = process_queue

    def run(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.main())
        finally:
            self.loop.close()
            asyncio.set_event_loop(None)

    async def main(self):
        # Create asyncio queue
        async_queue = asyncio.Queue()

        # Create a new thread that will block on get() calls on the task_queue.
        threading.Thread(
            target=queue_to_async, args=(async_queue, self.task_queue, self.loop)
        ).start()

        # Process incoming tasks
        await self.process_queue(async_queue, self.i)

def spawn_workers(num, process_queue):
    task_queue = queue.Queue()

    threads = []
    for i in range(num):
        worker_thread = WorkerThread(task_queue, i, process_queue)
        threads.append(worker_thread)
        worker_thread.start()

    return task_queue, threads


class Worker:
    instances = {}

    def __init__(self, key, workers, process_queue):
        if key not in Worker.instances:
            Worker.instances[key] = self

            self.queue = spawn_workers(workers, process_queue)
