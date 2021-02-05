from config.abstractconfig import DBGConfig
from flask import request, Response
from flask_restful import Api
from functools import lru_cache
from hashlib import sha256
import json
import logging
from marshmallow import Schema
from marshmallow.exceptions import ValidationError
import mysql.connector
from mysql.connector.errorcode import *
import re
import sys
import traceback
from werkzeug.exceptions import HTTPException
from wrap import connect_mysql, connect_redis, SmartCursor

logger = logging
get_mcon = connect_mysql
real_get_rcon = connect_redis


def mycursor(conn=None, autocommit=True, close_conn=False, buffered=None, raw=None, prepared=None,
             cursor_class=None, dictionary=None, named_tuple=None):
    if conn is None:
        conn = get_mcon()
    return SmartCursor(conn, autocommit, close_conn, buffered=buffered, raw=raw, prepared=prepared,
                       cursor_class=cursor_class, dictionary=dictionary, named_tuple=named_tuple)


def get_rcon():
    return real_get_rcon()


def get_logger():
    return logger


def print_tb():
    traceback.print_tb(sys.exc_info()[3], file=sys.stdout)


class ArgsUtil:
    class Error(Exception):
        pass

    @staticmethod
    def set_used(*args):
        if not hasattr(request, 'args_used'):
            request.args_used = set()
        request.args_used.update(args)

    @classmethod
    def check_all_used(cls):
        res = request.args.keys() - request.args_used
        if res:
            raise cls.Error(f'unknown argument <{res}>')

    @classmethod
    def get(cls, name: str, *, schema: Schema = None, one=True, raise_if_none=True):
        res = request.args.getlist(name)
        if len(res) == 0:
            if raise_if_none:
                raise cls.Error(f'param <{name}>: required')
            return None
        cls.set_used(name)
        if one and len(res) != 1:
            raise cls.Error(f'param <{name}>: only one is required')
        if schema:
            res = [schema.load({name: it})[name] for it in res]
        if one:
            res = res[0]
        return res

    @classmethod
    def gets(cls, *args, schema: Schema = None, one=True, raise_if_partial=True):
        res = []
        for it in args:
            res.append(cls.get(it, schema=schema, one=one, raise_if_none=raise_if_partial))
        return res


class BodyUtil:
    class Error(Exception):
        pass

    @classmethod
    def parse(cls, schema=None):
        try:
            res = json.loads(request.data)
            if schema:
                res = schema.load(res)
            return res
        except json.decoder.JSONDecodeError:
            raise cls.Error('the HTTP body should be json to pass some necessary arguments')

    @classmethod
    def require(cls, di, *args):
        for it in args:
            if it not in di:
                raise cls.Error(f'body param <{it}>: required')
        return tuple(di[it] for it in args)


class CursorUtil:
    class Error(Exception):
        pass

    @staticmethod
    def column_name(c):
        return (it[0] for it in c.description)

    @classmethod
    def one(cls, c, raise_if_none=True):
        row = c.fetchone()
        if raise_if_none and not row:
            raise cls.Error('not exist')
        column_name = cls.column_name(c)
        return dict(zip(column_name, row))

    @classmethod
    def get(cls, c, raise_if_none=True):
        rows = c.fetchall()
        if raise_if_none and not rows:
            raise cls.Error('not exist')
        column_name = cls.column_name(c)
        return [dict(zip(column_name, it)) for it in rows]


class GeoTypeUtil:
    pass


class MySQLUtil:
    class Error(Exception):
        pass

    @staticmethod
    @lru_cache(1)
    def null_point():
        with mycursor(autocommit=False) as c:
            c.execute('select point(0, 90)')
            return c.fetchone()[0]

    @classmethod
    def set_default_point(cls, di, key, default=None):
        default = default or cls.null_point()
        if key not in di:
            di[key] = default

    @classmethod
    def to_point(cls, di, name):
        longitude_name = f'{name}_longitude'
        latitude_name = f'{name}_latitude'
        if longitude_name in di or latitude_name in di:
            if longitude_name not in di or latitude_name not in di:
                raise cls.Error(
                    f'invalid point, {longitude_name} and {latitude_name} must be given or not together')
            longitude = di.pop(longitude_name)
            latitude = di.pop(latitude_name)
            if longitude == 0 and latitude == 90:
                raise cls.Error('this is not a possible point')
            if longitude is None or latitude is None:
                if longitude is not None or latitude is not None:
                    raise cls.Error(
                        f'invalid point, the {longitude_name} and {latitude_name} must be both null or not')
                longitude = 0
                latitude = 90
            with mycursor(autocommit=False) as c:
                c.execute('select point(%s, %s)', (longitude, latitude))
                di[name] = c.fetchone()[0]

    @staticmethod
    def div_point(di, name, point_pattern=re.compile(r'POINT\(([0-9.]+) ([0-9.]+)\)')):
        di.pop(name)
        point = di.pop(f'st_astext({name})')
        res = point_pattern.match(point)
        longitude, latitude = res[1], res[2]
        if longitude == '0' and latitude == '90':
            longitude = None
            latitude = None
        di[f'{name}_longitude'] = longitude
        di[f'{name}_latitude'] = latitude

    @staticmethod
    def rect(left, top, right, bottom):
        try:
            left = float(left)
            top = float(top)
            right = float(right)
            bottom = float(bottom)
            if left < right or top < bottom:
                return
        except ValueError:
            return

        with mycursor(autocommit=False) as c:
            c.execute("select st_polyfromtext('POLYGON((%s %s, %s %s, %s %s, %s %s, %s %s))')",
                      (left, top, right, top, right, bottom, left, bottom, left, top))
            return c.fetchone()


class BaseApi(Api):
    dup_entry = re.compile(r"Check constraint '(\w+)' is violated.")
    field_specified_twice = re.compile(r"Column '(\w+)' specified twice")
    no_referenced_row = re.compile(r'Cannot add or update a child row: '
                                   r'a foreign key constraint fails \(`[^`]+`\.`[^`]+`, '
                                   r'CONSTRAINT `[^`]+` FOREIGN KEY \((`[^`]+`)\) REFERENCES `[^`]+` \(`[^`]+`\)\)')

    def handle_error(self, e):
        if isinstance(e, ArgsUtil.Error):
            return message(exc=str(e)), 400
        elif isinstance(e, BodyUtil.Error):
            return message(exc=str(e)), 400
        elif isinstance(e, CursorUtil.Error):
            return message(exc=str(e)), 404
        elif isinstance(e, HTTPException):
            return Response(status=e.code)
        elif isinstance(e, mysql.connector.Error):
            if e.errno == ER_DUP_ENTRY:
                return message(exc=e.msg), 409
            elif e.errno == ER_FIELD_SPECIFIED_TWICE:
                key = self.field_specified_twice.match(e.msg)[1]
                return message(exc=f'"{key}" specified twice'), 400
            elif e.errno == ER_NO_REFERENCED_ROW_2:
                key = self.no_referenced_row.match(e.msg)[1]
                return message(f'{key}不存在'), 400
            else:
                print_tb()
                logger.debug(str(e))
                return Response(status=500)
        elif isinstance(e, MySQLUtil.Error):
            return message(exc=str(e)), 400
        elif isinstance(e, ValidationError):
            return message(exc=e.args[0]), 400
        else:
            print_tb()
            logger.debug(str(e))
            return Response(status=500)


def message(msg=None, exc=None, **kwargs):
    kwargs['msg'] = msg
    kwargs['exc'] = exc
    if DBGConfig.on:
        kwargs['echo'] = f'{request.method} {request.url}\n{request.headers}{request.data.decode()}'
    return kwargs


def hash_passwd(s: str):
    if DBGConfig.on and not DBGConfig.hash_passwd:
        return s
    else:
        return sha256(s.encode()).hexdigest()
