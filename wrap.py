from config.abstractconfig import Environment, GunicornConfig, MySQLConfig, RedisConfig
import mysql.connector.abstracts
import mysql.connector.cursor
import mysql.connector.cursor_cext
import mysql.connector.errorcode
import os
import redis
import threading
from time import sleep
from typing import Optional


class UnhandledSignalError(mysql.connector.DatabaseError):
    def __init__(self, msg=None, errno=None, values=None, sqlstate=None):
        super(UnhandledSignalError, self).__init__(msg, errno, values, sqlstate)


mysql.connector.custom_error_exception(mysql.connector.errorcode.ER_SIGNAL_EXCEPTION, UnhandledSignalError)


def connect_mysql(host=MySQLConfig.host, port=MySQLConfig.port, db: Optional[str] = MySQLConfig.db,
                  user=MySQLConfig.user, passwd=MySQLConfig.passwd, **kwargs):
    return mysql.connector.connect(host=host, port=port, user=user, passwd=passwd, db=db, **kwargs)


class SmartCursor:
    def __init__(self, conn=None, autocommit=True, close_conn=True):
        if conn is None:
            conn = connect_mysql()
        self.conn = conn
        self.autocommit = autocommit
        self.close_conn = close_conn

    def __enter__(self) -> mysql.connector.cursor.MySQLCursor:
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        if self.autocommit:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
        if self.close_conn:
            self.conn.close()


def connect_redis(host=RedisConfig.host, port=RedisConfig.port, db=RedisConfig.db, passwd=RedisConfig.passwd,
                  decode_responses=True, **kwargs):
    return redis.Redis(host, port, db, passwd, decode_responses=decode_responses, **kwargs)


rcon = connect_redis()


class Sync:
    class Error(Exception):
        pass

    class NoMainThreadError(Error):
        pass

    class CompanionError(Error):
        pass

    def __init__(self, conn=rcon, exclude_error: Optional[set] = None):
        self.conn = conn
        self.prefix = f'{Environment.root_dir}/{os.getppid()}/{Sync.__name__}'
        self.finish = f'{self.prefix}/finish'
        self.members = f'{self.prefix}/members'
        self.error = f'{self.prefix}/error'
        self.exclude_error = set() if exclude_error is None else exclude_error
        self.li: list

    def __enter__(self):
        if threading.current_thread() != threading.main_thread():
            raise self.NoMainThreadError
        self.conn.delete(self.members)
        self.conn.delete(self.finish)
        self.conn.delete(self.error)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # get companion error
        self.conn.setnx(self.error, 0)
        if exc_type and exc_type not in self.exclude_error:
            self.conn.incr(self.error)

        # wait all companion join
        while self.conn.scard(self.members) != GunicornConfig.workers:
            self.conn.sadd(self.members, os.getpid())
            sleep(0.1)

        # get info
        error_count = int(self.conn.get(self.error))
        self.li = sorted([int(it) for it in self.conn.smembers(self.members)])

        # tell finish
        self.conn.setnx(self.finish, 0)
        self.conn.incr(self.finish)

        # wait for all companion finish
        if self.li.index(os.getpid()) == 0:
            while int(self.conn.get(self.finish)) != GunicornConfig.workers:
                sleep(0.1)
            self.conn.delete(self.error)
            self.conn.delete(self.members)
            self.conn.delete(self.finish)
        else:
            while self.conn.get(self.finish):
                sleep(0.1)

        # raise self error or companion error
        if not exc_type and error_count != 0:
            raise self.CompanionError
