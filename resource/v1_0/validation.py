from config.abstractconfig import DBGConfig, ResourceConfig, yl
from flask import Response
from flask_restful import Resource
from functools import wraps
import json
from sms import rand_code, send_code
from uuid import uuid4
from ..util import get_logger, get_rcon, hash_passwd, message, mycursor
from flask import request


class SMSResource(Resource):
    @staticmethod
    def sms_name(appid, mobile, method, base_url):
        appid = str(appid).lower()
        mobile = str(mobile)
        method = str(method).upper()
        base_url = str(base_url).lower()
        return yl(f'sms?{appid=}&{mobile=}&{method=}&{base_url=}')

    def post(self):
        data = json.loads(request.data)
        appid = data.get('appid')
        if appid not in ResourceConfig.SMS.appid_list:
            return message(exc='Invalid appid'), 400

        # 阿里云本身已有信息限制功能，可以考虑改成IP限制
        count_name = yl(f"sms/count?mobile={data['mobile']}")
        rcon = get_rcon()

        # 无法确保原子性
        count = rcon.incr(count_name)
        if rcon.ttl(count_name) == -1:
            rcon.expire(count_name, ResourceConfig.SMS.expire)

        if (not DBGConfig.on or not DBGConfig.SMS.close_times_limit) and count > ResourceConfig.SMS.times_limit:
            return message(exc='frequent request'), 400
        else:
            name = self.sms_name(**data)
            code = rand_code()
            rcon.set(name, code, ex=ResourceConfig.SMS.expire)
            send_code(data['mobile'], code)
            get_logger().debug(f'Send code:\n'
                               f'{name=}\n'
                               f'{code=}\n')
            return Response(status=201)

    @classmethod
    def validate(cls, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mobile = kwargs.get('mobile', request.args.get('mobile', ''))
            appid = request.args.get('appid', '')
            name = cls.sms_name(appid, mobile, request.method, request.base_url)
            code = request.args.get('code')
            rcon = get_rcon()
            real_code = rcon.get(name)
            if real_code == code:
                return func(*args, **kwargs)
            else:
                get_logger().debug(f'Failed to pass SMS validate:\n'
                                   f'{mobile=}\n'
                                   f'{name=}\n'
                                   f'{code=}\n'
                                   f'{real_code=}\n')
                return Response(status=401)

        return wrapper


class PasswdResource(Resource):
    @staticmethod
    def validate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mobile = kwargs.get('mobile', request.args.get('mobile', ''))
            passwd = request.args.get('passwd')
            if passwd:
                with mycursor(autocommit=False) as c:
                    c.execute('select sha256_passwd from user where mobile=%s limit 1', (mobile,))
                    res = c.fetchone()
                    if res is None:
                        return message(exc='nonexistent user'), 404
                    if res[0] == hash_passwd(passwd):
                        return func(*args, **kwargs)
            return Response(status=401)

        return wrapper


def or_(*validate_func):
    if len(validate_func) == 0:
        raise ValueError('empty func tuple')

    def _(func):
        artifact = []
        for it in validate_func:
            artifact.append(it(func))

        def wrapper(*args, **kwargs):
            for it_ in artifact:
                res = it_(*args, **kwargs)
                if not isinstance(res, Response) or res.status_code != 401:
                    return res

            return Response(status=401)

        return wrapper

    return _


class TokenResource(Resource):
    @staticmethod
    def token_name(mobile, appid):
        appid = str(appid).lower()
        return yl(f'mobile/{mobile}/token?{appid=}')

    @or_(SMSResource.validate, PasswdResource.validate)
    def post(self, mobile):
        appid = request.args.get('appid')
        if appid is None:
            return message(exc='appid is null'), 400
        uuid = uuid4().hex
        with mycursor() as c:
            get_rcon().delete(self.token_name(mobile, appid))
            c.execute(
                'replace into token(user, appid, hex, deadline) '
                'values (%s, %s, %s, current_timestamp + interval %s second)',
                (mobile, appid, uuid, ResourceConfig.Token.expire))
        return message(token=uuid), 201

    @classmethod
    def validate(cls, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mobile = kwargs.get('mobile', request.args.get('mobile', ''))
            appid = request.args.get('appid')
            name = cls.token_name(mobile, appid)
            token = request.args.get('token')
            rcon = get_rcon()
            res = rcon.get(name)
            if res is None:
                with mycursor(autocommit=False) as c:
                    c.execute(
                        'select hex from token where user=%s and appid=%s and current_timestamp < deadline limit 1',
                        (mobile, appid))
                    res = c.fetchone()
                    if res:
                        res = res[0]
                        rcon.set(name, res, ex=ResourceConfig.Token.expire, nx=True)
            if res == token:
                return func(*args, **kwargs)
            else:
                return Response(status=401)

        return wrapper


sms_validate = SMSResource.validate
passwd_validate = PasswdResource.validate
token_validate = TokenResource.validate


def test(validate_func, **kwargs):
    res = validate_func(lambda *args, **kwargs_: True)(**kwargs)
    return res is True
