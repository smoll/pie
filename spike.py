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

coords = dict(lat=40.68828329999999, lng=-73.98899849999998)

def searchall(coords):
    """Search all sequentially."""
    doordash.search(**coords)
    postmates.search(**coords)
    seamless.search(**coords)
    ubereats.search(**coords)

# searchall(coords)

response = doordash.search(**coords)
data = response.json()
stores = data['stores']

# df = pd.DataFrame(stores)

columns_to_drop = [
    'menus',
]

df = json_normalize(stores)
df.drop(columns=columns_to_drop, inplace=True)
df.rename(columns=lambda x: x.replace('.', '_'), inplace=True)

# import pdb; pdb.set_trace()

logger.info('columns: %s' % (df.columns,))

df.to_csv('doordash.csv')

# persist to tmp table
with dbopen(return_conn=True) as conn:
    try:
        for col in df.columns:
            logger.debug('checking %s...' % (col,))
            df[[col]].to_sql('tmp', conn, if_exists='replace')
    except sqlite3.InterfaceError as e:
        raise RuntimeError('SQL error with column: %s' % col) # probably some nested JSON, discard for now...
    df.to_sql('tmp', conn, if_exists='replace')

# upsert to master table
with dbopen() as cur:
    cur.execute("DROP TABLE doordash;")
    cur.execute("CREATE TABLE IF NOT EXISTS doordash AS SELECT * FROM tmp WHERE 1=2;")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_id ON doordash(id);")
    cur.execute("""
    INSERT OR REPLACE INTO doordash
    SELECT * FROM tmp;
    """)
    cur.execute("SELECT * FROM doordash;")
    rows = cur.fetchall()
    cols = [description[0] for description in cur.description]
    logger.info('rows: %s' % (rows[:3],))
    logger.info('count: %s' % (len(rows),))
    logger.info('cols: %s' % (cols,))
