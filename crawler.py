from config import PROVIDERS

from logzero import logger
from queue import Queue, Empty
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

    logger.info('done paging %s.' % provider_name)
    return 'done'

class CrawlWorker(Thread):
    """Gets all the results for a given provider + lat + lng."""

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        try:
            provider_name, lat, lng = self.queue.get(timeout=3)
            # import pdb; pdb.set_trace()
        except Empty:
            logger.warn('queue empty!')
            return

        fetch_all(provider_name, lat, lng)
        self.queue.task_done()


def crawl(lat, lng):
    """Multi-threaded crawl."""
    # Create a queue to communicate with the worker threads
    queue = Queue()

    # Put the tasks into the queue as a tuple
    for p in PROVIDERS:
        logger.info(f'queueing {p}')
        queue.put_nowait((p, lat, lng))

    # Create 4 worker threads
    for x in range(4):
        worker = CrawlWorker(queue)
        # Setting daemon to True will let the main thread exit even though the workers are blocking
        worker.daemon = True
        worker.start()

    # Causes the main thread to wait for the queue to finish processing all the tasks
    queue.join()


def debug():
    """Single provider crawl. Useful for debugging."""
    fetch_all('seamless', 34.424366, -117.161295)

if __name__ == '__main__':
    from database import setup
    setup()
    debug()
