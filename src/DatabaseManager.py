# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens
"""TODO"""
import json
from typing import Any
import platform
import sqlite3
import redis

class DatabaseManager:
    """TODO"""

    def __init__(self, dbPath: str):
        self.DB_CONNECTION = sqlite3.connect(dbPath)
        self.TEMP_DB_CONNECTION = sqlite3.connect(':memory:')

        if (platform.system() == 'Linux'):
            self.CACHE = redis.StrictRedis(host='localhost', port=6379, db=0)
        else:
            self.CACHE = None # redis will not be established on Windows, which may be used for debugging, therefore skip caching

    def __del__(self):
        self.DB_CONNECTION.close()
        self.CACHE.close()

    def storeInCache(self, cog: str, store: str, key: str, value: Any,
                     overwriteIfExists: bool = False, expandIfExists: bool = False, timeUntilExpire: int | None = None):
        """TODO"""

        if (self.CACHE is not None): # redis may not be connected
            index = f'{cog}::{store}:{key}'
            temp = self.CACHE.get(index)

            if (temp is not None):
                if (overwriteIfExists):
                    self.CACHE.delete(index)
                elif (expandIfExists):
                    value = temp.append(value)
                else:
                    return

            if (not isinstance(value, list)):
                value = [value]
            value = json.dumps(value)

            if (timeUntilExpire is not None):
                self.CACHE.set(index, value, ex=timeUntilExpire)
            else:
                self.CACHE.set(index, value)

    def getFromCache(self, cog: str, store: str, key: str) -> Any:
        """TODO"""
        if (self.CACHE is not None): # redis may not be connected
            return json.loads(self.CACHE.get(f'{cog}::{store}:{key}'))
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
