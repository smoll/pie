from config import PROVIDERS

from logzero import logger
from queue import Queue
from threading import Thread
import importlib

def fetch_all(provider_name, lat, lng):
    logger.info('Searching via provider %s...' % provider_name)
    class_name = ''.join(x.capitalize() for x in provider_name.split('_'))
    Provider = getattr(importlib.import_module("providers.%s" % provider_name), class_name)
    provider = Provider()

    more = {}
    while more is not None:
        provider.search(lat, lng, more)
        provider.save_data()
        more = provider.more

class CrawlWorker(Thread):
    """Gets all the results for a given provider + lat + lng."""

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        provider_name, lat, lng = self.queue.get()
        # import pdb; pdb.set_trace()

        fetch_all(provider_name, lat, lng)

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


def debug():
    """Single provider crawl. Useful for debugging."""
    # fetch_all('postmates', 34.424366, -117.161295)
    # fetch_all('uber_eats', 34.424366, -117.161295)
    # fetch_all('seamless', 34.02452, -117.28925500000001)
    # fetch_all('door_dash', 34.650628999999995, -117.321326)
    # fetch_all('uber_eats', 34.172754, -117.521243)
    fetch_all('door_dash', 33.547613, -117.34403999999999)

if __name__ == '__main__':
    from database import setup
    setup()
    debug()
