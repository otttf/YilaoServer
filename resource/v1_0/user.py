from base import mycursor, _use
from flask import request, Response
from flask_restful import Resource
from hashlib import sha256
from schema import UserSchema
from ..util import ArgsUtil, CursorUtil, MySQLUtil
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
        passwd = ArgsUtil.one('passwd', schema=user_schema)
        if not self.validate(mobile, passwd):
            return Response(status=401)

        new_data = user_schema.loads(request.data.decode())
        MySQLUtil.to_point(new_data, 'default_location')
        if 'passwd' in new_data:
            new_data['sha256_passwd'] = sha256(new_data.pop('passwd').encode()).hexdigest()

        with mycursor() as c:
            to_update = ', '.join(map(lambda it: f'{it}=%s', new_data.keys()))
            c.execute(f"update user set {to_update} where mobile=%s", (*tuple(new_data.values()), mobile))
            return Response(status=204)
