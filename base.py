from config.yilaoconfig import *
from flask import Flask
import logging
from mysqlscript import iter_table, UserVersion
from resource import *
import resource.util
from wrap import connect_mysql, connect_redis, SmartCursor, Sync

logging.basicConfig(level=LogConfig.level, format=LogConfig.format_patterns[LogConfig.pattern_n])
logger = logging


def init_database():
    with SmartCursor(connect_mysql(db=None)) as c:
        if Environment.rank() == 0:
            if DBGConfig.on and DBGConfig.MySQL.drop_before_run:
                c.execute(f'drop database if exists {MySQLConfig.db}')
            c.execute(f'create database if not exists {MySQLConfig.db}')
            c.execute(f'use {MySQLConfig.db}')
            for it in iter_table:
                if UserVersion.get(c) == it.require_version:
                    for _ in c.execute(it.script, multi=True):
                        pass
                    UserVersion.update_to(it.version, c)


def sync():
    return Sync(rcon)


rcon = connect_redis()
impl(rcon)
if MySQLConfig.init_database:
    with sync():
        init_database()
mcon = connect_mysql()
app = Flask(__name__)

resource.util.get_mcon = lambda: mcon
resource.util.get_rcon = lambda: rcon

register_api_1_0(app)
