from contextlib import closing
from database import dbopen
from logzero import logger, loglevel
import importlib
import os
import pandas as pd
import sqlite3

debug_on = os.getenv('DEBUG') in ['true', '1', 't', 'y']
ll_str = '10' if debug_on else os.getenv('LOG_LEVEL', '20')
loglevel(int(ll_str))


PROVIDERS = [
    'door_dash',
    'postmates',
    'seamless',
    'uber_eats',
]


def clean():
    """Clean the DB."""
    with dbopen() as cur:
        for p in PROVIDERS:
            cur.execute("DROP TABLE IF EXISTS %s;" % p)


def fetch_page(lat, lng, page_info=None):
    provider_name = PROVIDERS[0]
    class_name = ''.join(x.capitalize() for x in provider_name.split('_'))

    Provider = getattr(importlib.import_module("providers.%s" % provider_name), class_name)
    provider = Provider()
    provider.search(lat, lng, page_info)
    provider.save_data()

    return provider.data


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
    logger.info('starting...')
    lat = 40.68828329999999
    lng = -73.98899849999998
    more = True
    while more:
        data_or_none = fetch_page(lat, lng, more)
        more = data_or_none
    logger.info('stopping.')


if __name__ == '__main__':
    # clean()
    setup()
    main()
