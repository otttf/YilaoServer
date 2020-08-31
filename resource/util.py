from base import logger, mycursor, scon
from flask import request, Response
from flask_restful import Api
from hashlib import sha256
import json
from marshmallow import Schema
from marshmallow.exceptions import ValidationError
import mysql.connector
from mysql.connector.errorcode import *
import re
from werkzeug.exceptions import HTTPException


def _use(_): pass


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
    def one(cls, name: str, *, schema: Schema = None, raise_if_none=True):
        res: list = request.args.getlist(name)
        if len(res) == 0:
            if raise_if_none:
                raise cls.Error(f'param <{name}>: required')
            else:
                return None
        elif len(res) == 1:
            cls.set_used(name)
            res = res[0]
            if schema:
                res = schema.load({name: res})[name]
            return res
        else:
            cls.set_used(name)
            raise cls.Error(f'param <{name}>: more than one')

    @classmethod
    def get(cls, name: str, *, schema: Schema = None, raise_if_none=True):
        res = request.args.getlist(name)
        if len(res) == 0:
            if raise_if_none:
                raise cls.Error(f'param <{name}>: required')
            res = None
        cls.set_used(name)
        if schema:
            res = [schema.load({name: it})[name] for it in res]
        return res


class BodyUtil:
    class Error(Exception):
        pass

    @classmethod
    def parse(cls, schema=None):
        try:
            res = json.loads(request.data.decode())
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
    def one(cls, c, *, raise_if_none=True):
        row = c.fetchone()
        if raise_if_none and not row:
            raise cls.Error('not exist')
        column_name = cls.column_name(c)
        return dict(zip(column_name, row))

    @classmethod
    def get(cls, c, *, raise_if_none=True):
        rows = c.fetchall()
        if raise_if_none and not rows:
            raise cls.Error('not exist')
        column_name = cls.column_name(c)
        return [dict(zip(column_name, it)) for it in rows]


class MySQLUtil:
    class Error(Exception):
        pass

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

    @classmethod
    def div_point(cls, di, name, point_pattern=re.compile(r'POINT\(([0-9.]+) ([0-9.]+)\)')):
        point = di.pop(name)
        with mycursor(autocommit=False) as c:
            c.execute('select st_astext(%s)', (point,))
            res = point_pattern.match(c.fetchone()[0])
            longitude, latitude = res[1], res[2]
        if longitude == '0' and latitude == '90':
            longitude = None
            latitude = None
        di[f'{name}_longitude'] = longitude
        di[f'{name}_latitude'] = latitude


class BaseApi(Api):
    mysql_constraint_pattern = re.compile(r"Check constraint '(\w+)' is violated.")

    def handle_error(self, e):
        if isinstance(e, ArgsUtil.Error):
            return {'msg': str(e)}, 400
        elif isinstance(e, BodyUtil.Error):
            return {'msg': str(e)}, 400
        elif isinstance(e, CursorUtil.Error):
            return {'msg': str(e)}, 404
        elif isinstance(e, HTTPException):
            return Response(status=e.code)
        elif isinstance(e, mysql.connector.Error):
            if e.errno == ER_DUP_ENTRY:
                return Response(status=409)
            else:
                logger.debug(type(e), str(e))
                return Response(status=500)
        elif isinstance(e, MySQLUtil.Error):
            return {'msg': str(e)}, 400
        elif isinstance(e, ValidationError):
            return {'msg': e.args[0]}, 400
        else:
            logger.debug(type(e), str(e))
            return Response(status=500)


def hash_passwd(s: str):
    return sha256(s.encode()).hexdigest()
