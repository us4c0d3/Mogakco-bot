import os

import pymysql
from pymysql.cursors import DictCursor


class DBConnector:
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_DATABASE'),
            'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
        }

    def get_connection(self):
        return pymysql.connect(**self.config, cursorclass=DictCursor)
