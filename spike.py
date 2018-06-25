from contextlib import closing
from database import dbopen
from logzero import logger, loglevel
from pandas.io.json import json_normalize
from providers import doordash, postmates, seamless, ubereats
import os
import pandas as pd
import sqlite3

debug_on = os.getenv('DEBUG') in ['true', '1', 't', 'y']
ll_str = '10' if debug_on else os.getenv('LOG_LEVEL', '20')
loglevel(int(ll_str))

def _all(coords):
    """Search all sequentially."""
    doordash.search(**coords)
    postmates.search(**coords)
    seamless.search(**coords)
    ubereats.search(**coords)

# _all(coords)

def test_columns_seq(df, conn):
    try:
        for col in df.columns:
            logger.debug('checking %s...' % (col,))
            df[[col]].to_sql('tmp', conn, if_exists='replace')
    except sqlite3.InterfaceError as e:
        raise RuntimeError('SQL error with column: %s' % col) # probably some nested JSON, discard for now...


def clean():
    """Clean the DB."""
    with dbopen() as cur:
        cur.execute("DROP TABLE doordash;")


def massage_data(data):
    stores = data['stores']
    columns_to_drop = [
        'menus',
        'merchant_promotions',
        'status_asap_minutes_range',
    ]
    df = json_normalize(stores)
    df.rename(columns=lambda x: x.replace('.', '_'), inplace=True)
    df.drop(columns=columns_to_drop, inplace=True)
    logger.debug('columns: %s' % (df.columns,))
    return df


def insert_to_temp_table(df, name, debug):
    tmp = 'tmp_%s' % name
    with dbopen(return_conn=True) as conn:
        if debug:
            test_columns_seq(df, conn)
        df.to_sql(tmp, conn, if_exists='replace', index=False)


def upsert_to_master_table(df, name):
    master = name
    tmp = 'tmp_%s' % name
    with dbopen() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS %s AS SELECT * FROM %s WHERE 1=2;" % (master, tmp))
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_id ON %s(id);" % master)
        cur.execute("""
        INSERT OR REPLACE INTO %s
        SELECT * FROM %s;
        """ % (master, tmp))
        cur.execute("SELECT * FROM %s;" % master)
        rows = cur.fetchall()
        cols = [description[0] for description in cur.description]
        logger.debug('first 3 rows: %s' % (rows[:3],))
        logger.debug('cols: %s' % (cols,))
        logger.info('row count: %s' % (len(rows),))
        logger.info('col count: %s' % (len(cols),))


def fetch_page(lat, lng, page_info=None, debug_columns=False):
    response = doordash.search(lat, lng, page_info)
    if not response:
        return # stop condition
    data = response.json()

    df = massage_data(data)
    insert_to_temp_table(df, 'doordash', debug_columns)
    upsert_to_master_table(df, 'doordash')

    return data

def setup():
    try:
        with dbopen(return_conn=True) as conn:
            pd.DataFrame.from_dict({
                'provider': ['doordash', 'postmates', 'seamless', 'ubereats'],
                'token1': [None,None,None,None,],
                'token2': [None,None,None,None,],
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
