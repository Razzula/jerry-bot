# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens
"""TODO"""
from typing import Any
import platform
import sqlite3
import redis

class DatabaseHandler:
    """TODO"""

    def __init__(self, dbPath: str):
        self.DB_CONNECTION = sqlite3.connect(dbPath)

        if (platform.system() == 'Linux'):
            self.CACHE = redis.StrictRedis(host='localhost', port=6379, db=0)
        else:
            self.CACHE = None # redis will not be established on Windows, which may be used for debugging, therefore skip caching

    def __del__(self):
        self.DB_CONNECTION.close()
        self.CACHE.close()

    def storeInCache(self, store: str, key: str, value: Any):
        """TODO"""
        if (self.CACHE is not None): # redis may not be connected
            self.CACHE.set(f'{store}::{key}', value)

    def getFromCache(self, store: str, key: str) -> Any:
        """TODO"""
        if (self.CACHE is not None): # redis may not be connected
            return self.CACHE.get(f'{store}::{key}')
        return None

    def getCursor(self):
        """TODO"""
        return self.DB_CONNECTION.cursor()

    def commit(self):
        """TODO"""
        self.DB_CONNECTION.commit()

    def executeOneshot(self, sql: str):
        """TODO"""
        cursor = self.getCursor()
        cursor.execute(sql)
        self.commit()
        res = cursor.fetchall()
        cursor.close()

        return res

    def arrayToSqlInArgument(self, array: list[str]) -> str:
        """TODO"""
        sqlSafeArray = [f"'{str(item)}'" if isinstance(item, str) else str(item) for item in array]
        return f"({', '.join(sqlSafeArray)})"
