# Start batch processing serially

from logzero import logger, loglevel
import pandas as pd
import os


debug_on = os.getenv('DEBUG') in ['true', '1', 't', 'y']
ll_str = '10' if debug_on else os.getenv('LOG_LEVEL', '20')
loglevel(int(ll_str))


PROGRESS_FILE = './outputs/progress.csv'


def main():
    df = pd.read_csv(PROGRESS_FILE)

    # DB setup
    setup()

    try:
        for index, row in df.iterrows():
            lat = row['lat']
            lng = row['lng']
            for p in PROVIDERS:
                logger.info(f'running {p}')
                fetch_all(p, lat, lng)
            df.loc[(df['lat'] == lat) & (df['lng'] == lng), 'progress'] = 1

        logger.info('Saving progress file...')
        df.to_csv(PROGRESS_FILE, index=False)

    except (KeyboardInterrupt, Exception) as e:
        logger.info('Saving progress file...')
        df.to_csv(PROGRESS_FILE, index=False)
        raise e



if __name__ == '__main__':
    if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
        from crawler import CrawlWorker, fetch_all
        from config import PROVIDERS
        from database import setup
    else:
        from ..crawler import CrawlWorker
        from ..config import PROVIDERS
        from ..database import setup

    main()
