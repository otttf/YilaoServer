from config.abstractconfig import Environment, GunicornConfig, MySQLConfig, RedisConfig
import mysql.connector.abstracts
import mysql.connector.cursor
import mysql.connector.cursor_cext
import mysql.connector.errorcode
import os
import re
import redis
import threading
from time import sleep
from typing import Optional


def _use(_): pass


def echo(obj): return obj


class UnhandledSignalError(mysql.connector.DatabaseError):
    dup_entry = re.compile(r"Check constraint '(\w+)' is violated.")
    field_specified_twice = re.compile(r"Column '(\w+)' specified twice")
    pattern = [dup_entry, field_specified_twice]

    def __init__(self, msg=None, errno=None, values=None, sqlstate=None):
        super(UnhandledSignalError, self).__init__(msg, errno, values, sqlstate)
        self.info = ()
        for it in self.pattern:
            res = it.match(msg)
            if res:
                self.info = tuple(res[1:])
                break


mysql.connector.custom_error_exception(mysql.connector.errorcode.ER_SIGNAL_EXCEPTION, UnhandledSignalError)


def connect_mysql(host=MySQLConfig.host, port=MySQLConfig.port, db: Optional[str] = MySQLConfig.db,
                  user=MySQLConfig.user, passwd=MySQLConfig.passwd, **kwargs):
    return mysql.connector.connect(host=host, port=port, user=user, passwd=passwd, db=db, **kwargs)


class SmartCursor:
    def __init__(self, mysql_conn=None, autocommit=True, close_conn=True, **kwargs):
        if mysql_conn is None:
            mysql_conn = connect_mysql()
        self.mysql_conn = mysql_conn
        self.autocommit = autocommit
        self.close_conn = close_conn
        self.kwargs = kwargs

    def __enter__(self):
        self.cursor = self.mysql_conn.cursor(**self.kwargs)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        if self.autocommit:
            if exc_type:
                self.mysql_conn.rollback()
            else:
                self.mysql_conn.commit()
        if self.close_conn:
            self.mysql_conn.close()


def connect_redis(host=RedisConfig.host, port=RedisConfig.port, db=RedisConfig.db, passwd=RedisConfig.passwd,
                  decode_responses=True, **kwargs):
    return redis.Redis(host, port, db, passwd, decode_responses=decode_responses, **kwargs)


class Sync:
    class Error(Exception):
        pass

    class NoMainThreadError(Error):
        pass

    class CompanionError(Error):
        pass

    def __init__(self, redis_conn, exclude_error: Optional[set] = None):
        self.redis_conn = redis_conn
        self.prefix = f'{Environment.root_dir}/{os.getppid()}/{Sync.__name__}'
        self.finish = f'{self.prefix}/finish'
        self.members = f'{self.prefix}/members'
        self.error = f'{self.prefix}/error'
        self.exclude_error = set() if exclude_error is None else exclude_error
        self.li: list

    def __enter__(self):
        if threading.current_thread() != threading.main_thread():
            raise self.NoMainThreadError
        self.redis_conn.delete(self.members)
        self.redis_conn.delete(self.finish)
        self.redis_conn.delete(self.error)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # get companion error
        self.redis_conn.setnx(self.error, 0)
        if exc_type and exc_type not in self.exclude_error:
            self.redis_conn.incr(self.error)

        # wait all companion join
        while self.redis_conn.scard(self.members) != GunicornConfig.workers:
            self.redis_conn.sadd(self.members, os.getpid())
            sleep(0.1)

        # get info
        error_count = int(self.redis_conn.get(self.error))
        self.li = sorted([int(it) for it in self.redis_conn.smembers(self.members)])

        # tell finish
        self.redis_conn.setnx(self.finish, 0)
        self.redis_conn.incr(self.finish)

        # wait for all companion finish
        if self.li.index(os.getpid()) == 0:
            while int(self.redis_conn.get(self.finish)) != GunicornConfig.workers:
                sleep(0.1)
            self.redis_conn.delete(self.error)
            self.redis_conn.delete(self.members)
            self.redis_conn.delete(self.finish)
        else:
            while self.redis_conn.get(self.finish):
                sleep(0.1)

        # raise self error or companion error
        if not exc_type and error_count != 0:
            raise self.CompanionError


def send(rcon, name, s):
    with Sync(rcon):
        rcon.set(name, s)
    rcon.delete(name)


def recv(rcon, name):
    res = None
    while res is None:
        sleep(0.1)
        res = rcon.get(name)
    return res
