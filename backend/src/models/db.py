import os
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor


@contextmanager
def transaction():
    connection = pymysql.connect(
        host=os.environ['MYSQL_HOST'], user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'], database=os.environ['MYSQL_DATABASE'],
        charset='utf8mb4', cursorclass=DictCursor, connect_timeout=5,
    )
    try:
        with connection.cursor() as cursor:
            yield cursor
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def rows(cursor, query, values=()):
    cursor.execute(query, values)
    return cursor.fetchall()


def one(cursor, query, values=()):
    cursor.execute(query, values)
    return cursor.fetchone()
