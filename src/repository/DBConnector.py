import pymysql
from pymysql.cursors import DictCursor

from repository import CONFIG


class DBConnector:
    def __init__(self):
        self.config = CONFIG

    def get_connection(self):
        return pymysql.connect(**self.config, cursorclass=DictCursor)
