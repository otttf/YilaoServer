from base import mycursor, rcon, _use
from flask import request, Response
from flask_restful import Resource
from schema import UserSchema
from ..util import ArgsUtil, CursorUtil, MySQLUtil, hash_passwd
from .validation import ValidationResource


class UserResource(Resource):
    @ValidationResource.login_required
    def get(self, mobile, user_schema=UserSchema()):
        _use(self)
        with mycursor() as c:
            c.execute('select * from user where mobile=%s limit 1', (mobile,))
            res = CursorUtil.one(c)
            MySQLUtil.div_point(res, 'default_location')
            return user_schema.dump(res)

    def put(self, mobile, user_schema=UserSchema()):
        _use(self)
        mobile = user_schema.load({'mobile': mobile})['mobile']
        with mycursor() as c:
            c.execute('insert into user(mobile, default_location) values (%s, point(0, 90))', (mobile,))
            return Response(status=201)

    @ValidationResource.login_required
    def patch(self, mobile, user_schema=UserSchema(exclude=('mobile', 'token'))):
        _use(self)
        new_data = user_schema.loads(request.data.decode())
        MySQLUtil.to_point(new_data, 'default_location')

        with mycursor() as c:
            discard_tokens = False
            if 'passwd' in new_data:
                discard_tokens = True
                arg_passwd = ArgsUtil.one('passwd', schema=user_schema, raise_if_none=False)
                c.execute('select sha256_passwd from user where mobile=%s', (mobile,))
                sha256_passwd = c.fetchone()[0]
                sha256_arg_passwd = arg_passwd and hash_passwd(arg_passwd)
                if sha256_passwd != sha256_arg_passwd:
                    return {'msg': 'wrong passwd'}, 400
                new_data['sha256_passwd'] = hash_passwd(new_data.pop('passwd'))
                c.execute('delete from token where user=%s', (mobile,))

            to_update = ', '.join(map(lambda it: f'{it}=%s', new_data.keys()))
            c.execute(f"update user set {to_update} where mobile=%s", (*tuple(new_data.values()), mobile))

            if discard_tokens:
                keys = rcon.keys(ValidationResource.token_name(mobile, '*'))
                for it in keys:
                    rcon.delete(it)

            return Response(status=204)


class VerifiedUserResource(Resource):
    def get(self, mobile):
        _use(self)
        with mycursor() as c:
            c.execute('select count(*) from user where mobile=%s and verify_at is not null limit 1', (mobile,))
            if c.fetchone()[0] == 1:
                return Response(status=200)
            else:
                return Response(status=404)
