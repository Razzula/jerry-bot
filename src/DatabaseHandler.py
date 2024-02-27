# pylint: disable=fixme, line-too-long, invalid-name, superfluous-parens
"""TODO"""
import sqlite3

class DatabaseHandler:
    """TODO"""

    def __init__(self, dbPath: str):
        self.DB_CONNECTION = sqlite3.connect(dbPath)

    def __del__(self):
        self.DB_CONNECTION.close()

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
