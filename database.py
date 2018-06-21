import sqlite3

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
