from config import PROVIDERS

from logzero import logger
from queue import Queue
from threading import Thread
import importlib

class CrawlWorker(Thread):
    """Gets all the results for a given provider + lat + lng."""

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        provider_name, lat, lng = self.queue.get()
        # import pdb; pdb.set_trace()

        logger.info('Searching via provider %s...' % provider_name)
        class_name = ''.join(x.capitalize() for x in provider_name.split('_'))
        Provider = getattr(importlib.import_module("providers.%s" % provider_name), class_name)
        provider = Provider()

        more = {}
        while more is not None:
            provider.search(lat, lng, more)
            provider.save_data()
            more = provider.more

        self.queue.task_done()


def crawl(lat, lng):
    """Multi-threaded crawl."""
    # Create a queue to communicate with the worker threads
    queue = Queue()
    # Create 8 worker threads
    for x in range(8):
        worker = CrawlWorker(queue)
        # Setting daemon to True will let the main thread exit even though the workers are blocking
        worker.daemon = True
        worker.start()
    # Put the tasks into the queue as a tuple
    for p in PROVIDERS:
        logger.info(f'queueing {p}')
        queue.put((p, lat, lng))
    # Causes the main thread to wait for the queue to finish processing all the tasks
    queue.join()
