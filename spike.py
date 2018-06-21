from contextlib import closing
from database import dbopen
from logzero import logger, loglevel
from pandas.io.json import json_normalize
from providers import doordash, postmates, seamless, ubereats
import pandas as pd

loglevel(20)

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

df = json_normalize(stores)

# import pdb; pdb.set_trace()

logger.info('columns: %s' % (df.columns,))

df.to_csv('doordash.csv')

with dbopen(return_conn=True) as conn:
    df[['id',
        'name',
        'address.lat',
        'address.lng',
    ]].to_sql('doordash', conn, if_exists='replace')

with dbopen() as cur:
    cur.execute("SELECT * FROM doordash")
    rows = cur.fetchall()
    logger.info('rows: %s' % (rows,))
