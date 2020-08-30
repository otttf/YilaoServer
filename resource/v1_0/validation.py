from base import Environment, mycursor, rcon, ResourceConfig
from flask import Response
from flask_restful import Resource
from hashlib import sha256
from schema import UserSchema, ValidationSchema
from sms import rand_code, send_code
from uuid import uuid4
from ..util import ArgsUtil, BodyUtil


class ValidationResource(Resource):
    @staticmethod
    def token_name(mobile, platform):
        return f'{Environment.root_dir}/users/{mobile}/tokens/{platform}'

    @staticmethod
    def validation_name(mobile, platform):
        return f'{Environment.root_dir}/users/{mobile}/validations/{platform}'

    @classmethod
    def set_token(cls, mobile, platform, c):
        token = uuid4().hex
        c.execute('replace into token values(%s, %s, %s)', (mobile, platform, token))
        if ResourceConfig.Token.cache:
            rcon.set(cls.token_name(mobile, platform), token, ex=ResourceConfig.Token.expire)
        return token

    @classmethod
    def validate(cls, mobile, platform, token):
        name = cls.token_name(mobile, platform)
        value = rcon.get(name)
        if not value:
            with mycursor(autocommit=False) as c:
                c.execute('select hex from token where user=%s and platform=%s limit 1', (mobile, platform))
                res = c.fetchone()
                if res:
                    if ResourceConfig.Token.cache:
                        rcon.set(name, token, ex=ResourceConfig.Token.expire)
                    value = res[0]
        else:
            rcon.expire(name, ex=ResourceConfig.Token.expire)
        return value and value == token

    @classmethod
    def login_required(cls, func, user_schema=UserSchema(), validation_schema=ValidationSchema()):
        def wrapper(**kwargs):
            mobile = kwargs['mobile']
            platform = ArgsUtil.one('platform', schema=validation_schema)
            token = ArgsUtil.one('token', schema=user_schema)
            with mycursor(autocommit=False) as c:
                res = cls.validate(mobile, platform, token)
            if res:
                return func(**kwargs)
            else:
                return Response(status=401)

        return wrapper

    def get(self, mobile, user_schema=UserSchema(), validation_schema=ValidationSchema()):
        passwd = ArgsUtil.one('passwd', schema=user_schema)
        platform = ArgsUtil.one('platform', schema=validation_schema)
        with mycursor() as c:
            c.execute('select count(*) from user where mobile=%s and sha256_passwd=%s limit 1',
                      (mobile, sha256(passwd.encode()).hexdigest()))
            if c.fetchone()[0] == 1:
                token = self.set_token(mobile, platform, c)
                return user_schema.dump({'token': token}), 200
            else:
                return Response(status=401)

    def post(self, mobile, validation_schema=ValidationSchema(only=('platform',))):
        platform, = BodyUtil.require(BodyUtil.parse(validation_schema), 'platform')
        code = rand_code()
        rcon.set(self.validation_name(mobile, platform), code, ex=ResourceConfig.Validation.expire)
        send_code(mobile, code)
        return Response(status=201)

    def delete(self, mobile, user_schema=UserSchema(), validation_schema=ValidationSchema()):
        platform = ArgsUtil.one('platform', schema=validation_schema)
        code = ArgsUtil.one('code', schema=validation_schema)
        validation_name = self.validation_name(mobile, platform)
        if rcon.get(validation_name) == code:
            with mycursor() as c:
                c.execute('update user set verify_at=current_timestamp where mobile=%s and verify_at is null limit 1',
                          (mobile,))
                token = self.set_token(mobile, platform, c)
            rcon.delete(validation_name)
            return user_schema.dump({'token': token}), 200
        else:
            return Response(status=401)
