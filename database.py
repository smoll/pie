from config import PROVIDERS
from logzero import logger
import pandas as pd
import sqlite3

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

class dbopen(object):
    """
    Simple CM for sqlite3 databases. Commits everything at exit.
    """
    def __init__(self, path=None, return_conn=False):
        self.path = path or './restaurants.db'
        self.conn = None
        self.cursor = None
        self.return_conn = return_conn

    def __enter__(self):
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        return self.conn if self.return_conn else self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.conn.commit()
        self.conn.close()
