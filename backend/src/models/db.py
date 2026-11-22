import os
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor


@contextmanager
def transaction(isolation=None):
    """打开一个事务。

    isolation 为 'REPEATABLE READ' 时以一致的只读快照开启，多个 SELECT 之间不会
    看到其他事务在批次中途提交的部分数据；'READ COMMITTED' 用于需要看到最新已提交
    行的写入路径（如离线补传按编号判重）。
    """
    connection = pymysql.connect(
        host=os.environ['MYSQL_HOST'], user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'], database=os.environ['MYSQL_DATABASE'],
        charset='utf8mb4', cursorclass=DictCursor, connect_timeout=5,
    )
    try:
        with connection.cursor() as cursor:
            if isolation:
                cursor.execute(f'SET TRANSACTION ISOLATION LEVEL {isolation}')
                cursor.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT'
                               if isolation == 'REPEATABLE READ' else 'START TRANSACTION')
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
