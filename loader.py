from database import dbopen
from logzero import logger
import sqlite3

class Loader:
    def __init__(self, table, unique_on='id', debug=False):
        self.tmp = 'tmp_%s' % table
        self.master = table
        self.unique_on = unique_on
        self.debug = debug


    def load_data(self, df):
        if df is None or df.empty:
            logger.info('empty DataFrame. doing nothing.')
            return
        self.df = df
        self._insert_to_temp_table()
        self._upsert_to_master_table()


    def _insert_to_temp_table(self):
        with dbopen(return_conn=True) as conn:
            if self.debug:
                self._test_columns_seq(conn)
            self.df.to_sql(self.tmp, conn, if_exists='replace', index=False)


    def _upsert_to_master_table(self):
        with dbopen() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS %s AS SELECT * FROM %s WHERE 1=2;" % (self.master, self.tmp))
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_id ON %s(%s);" % (self.master, self.unique_on))
            cur.execute("""
            INSERT OR REPLACE INTO %s
            SELECT * FROM %s;
            """ % (self.master, self.tmp))
            cur.execute("SELECT * FROM %s;" % self.master)
            rows = cur.fetchall()
            cols = [description[0] for description in cur.description]
            logger.debug('first 3 rows: %s' % (rows[:3],))
            logger.debug('cols: %s' % (cols,))
            logger.info('row count: %s' % (len(rows),))
            logger.info('col count: %s' % (len(cols),))


    def _test_columns_seq(self, conn):
        try:
            for col in self.df.columns:
                logger.debug('checking %s...' % (col,))
                self.df[[col]].to_sql('tmp', conn, if_exists='replace')
        except sqlite3.InterfaceError as e:
            raise RuntimeError('SQL error with column: %s' % col) # probably some nested JSON, discard for now...
