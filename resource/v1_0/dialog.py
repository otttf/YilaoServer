from flask import request, Response
from flask_restful import Resource
from schema import dialog_schema
from ..util import curd_params, mycursor
from .validation import token_validate


class DialogListResource(Resource):
    @token_validate
    def get(self, mobile, other):
        with mycursor(dictionary=True) as c:
            # TODO 加入时间筛选
            c.execute('select * from dialog where (from_user=%s and to_user=%s) or (from_user=%s and to_user=%s)',
                      (mobile, other, other, mobile))
            return dialog_schema.dump(c.fetchall(), many=True)


class DialogResource(Resource):
    @token_validate
    def post(self, mobile):
        with mycursor() as c:
            data = dialog_schema.loads(request.data.decode())
            data['from_user'] = mobile
            to_insert = curd_params(data, dialog_schema)
            c.execute(f'insert into dialog set {to_insert[0]}', to_insert[1])
            return Response(status=201)
