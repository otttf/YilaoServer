from flask import request, Response
from flask_restful import Resource
from schema import UserSchema, user_schema
from wrap import _use
from ..util import hash_passwd, message, mycursor, MySQLUtil
from .validation import or_, passwd_validate, sms_validate, test, token_validate


class UserResource(Resource):
    def get(self, mobile):
        _use(self)
        with mycursor(dictionary=True) as c:
            c.execute('select *, st_astext(default_location) from user where mobile=%s limit 1', (mobile,))
            res = c.fetchone()
            if res is None:
                return Response(status=404)
            if not test(token_validate, mobile=mobile):
                return Response(status=401)
            MySQLUtil.div_point(res, 'default_location')
            return user_schema.dump(res)

    @sms_validate
    def put(self, mobile, partial_user_schema=UserSchema(only=('passwd',))):
        mobile = user_schema.load({'mobile': mobile}, partial=True)['mobile']
        passwd = partial_user_schema.loads(request.data.decode())['passwd']

        with mycursor() as c:
            c.execute('insert into user(mobile, sha256_passwd, default_location) '
                      'values (%s, %s, point(0, 90))',
                      (mobile, hash_passwd(passwd)))
            return Response(status=201)

    def patch(self, mobile, partial_user_schema=UserSchema(exclude=('mobile',), partial=True)):
        _use(self)
        new_data = partial_user_schema.loads(request.data.decode())
        secret_field = {'passwd'}
        field = set(new_data.keys())
        intersection = secret_field & field
        if len(intersection) > 0:
            if field != secret_field:
                return message(exc='common field and secret filed could not be given together'), 400
            if not test(or_(passwd_validate, sms_validate), mobile=mobile):
                return Response(status=401)
        else:
            if not test(token_validate, mobile=mobile):
                return Response(status=401)

        if 'passwd' in new_data:
            new_data['sha256_passwd'] = hash_passwd(new_data.pop('passwd'))
        MySQLUtil.to_point(new_data, 'default_location')

        with mycursor() as c:
            to_update = ', '.join(map(lambda _it: f'{_it}=%s', new_data.keys()))
            c.execute(f"update user set {to_update} where mobile=%s", (*tuple(new_data.values()), mobile))
            return Response(status=204)
