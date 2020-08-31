from config.yilaoconfig import *
from flask import Flask
import logging
from mysqlscript import iter_table, UserVersion
from wrap import connect_mysql, rcon, SmartCursor, Sync

logging.basicConfig(level=LogConfig.level, format=LogConfig.format_patterns[LogConfig.pattern_n])
logger = logging


def _use(_): pass


def init_database():
    with SmartCursor(connect_mysql(db=None)) as c:
        if Environment.rank() == 0:
            if DBGConfig.on and DBGConfig.drop_database_before_run:
                c.execute(f'drop database if exists {MySQLConfig.db}')
            c.execute(f'create database if not exists {MySQLConfig.db}')
            c.execute(f'use {MySQLConfig.db}')
            for it in iter_table:
                if UserVersion.get(c) == it.require_version:
                    for _ in c.execute(it.script, multi=True):
                        pass
                    UserVersion.update_to(it.version, c)


if MySQLConfig.init_database:
    with Sync():
        init_database()

# 全局静态的连接，用于在非flask的地方使用
_use(rcon)
scon = connect_mysql()
app = Flask(__name__)


def mycursor(conn=scon, autocommit=True, close_conn=False):
    return SmartCursor(conn, autocommit, close_conn)
