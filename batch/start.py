# Start batch processing, storing progress in outputs/progress.csv

from logzero import logger
from queue import Queue
from threading import Thread
import pandas as pd


def main():
    df = pd.read_csv('./outputs/progress.csv')
    df = df.head(2) # DEBUG ONLY!!!

    # DB setup
    setup()

    # Create a queue to communicate with the worker threads
    queue = Queue()
    # Create 8 worker threads
    for x in range(8):
        worker = CrawlWorker(queue)
        # Setting daemon to True will let the main thread exit even though the workers are blocking
        worker.daemon = True
        worker.start()
    # Put the tasks into the queue as a tuple
    for index, row in df.iterrows():
        lat = row['lat']
        lng = row['lng']
        for p in PROVIDERS:
            logger.info(f'queueing {p}')
            queue.put((p, lat, lng))
    # Causes the main thread to wait for the queue to finish processing all the tasks
    queue.join()


if __name__ == '__main__':
    if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
        from crawler import CrawlWorker
        from config import PROVIDERS
        from database import setup
    else:
        from ..crawler import CrawlWorker
        from ..config import PROVIDERS
        from ..database import setup

    main()
