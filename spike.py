from crawler import crawl
from config import PROVIDERS

from contextlib import closing
from database import dbopen
from logzero import logger, loglevel
from time import time
import os
import pandas as pd

debug_on = os.getenv('DEBUG') in ['true', '1', 't', 'y']
ll_str = '10' if debug_on else os.getenv('LOG_LEVEL', '20')
loglevel(int(ll_str))


def clean():
    """Clean the DB."""
    with dbopen() as cur:
        for p in PROVIDERS:
            cur.execute("DROP TABLE IF EXISTS %s;" % p)


def setup():
    try:
        with dbopen(return_conn=True) as conn:
            empty_row = [None for p in PROVIDERS]
            pd.DataFrame.from_dict({
                'provider': PROVIDERS,
                'token1': empty_row,
                'token2': empty_row,
            }).to_sql('tokens', conn, if_exists='fail', index=False)
    except ValueError as e:
        logger.debug('tokens table already exists.')


def main():
    ts = time()
    lat = 40.68828329999999
    lng = -73.98899849999998
    logger.info('started...')
    crawl(lat, lng)
    logger.info('stopped.')
    logger.info(f'took {time() - ts}s')

if __name__ == '__main__':
    # clean()
    setup()
    main()
