from datetime import datetime, timedelta
from typing import List

from flask import request, Response
from flask_restful import Resource
from schema import dialog_schema
from ..util import curd_params, mycursor
from .validation import token_validate
from marshmallow import Schema, fields


class DialogUserSchema(Schema):
    mobile = fields.Str()
    id_name = fields.Str()
    id_photo = fields.Str()
    last_send_at = fields.DateTime()
    last_content = fields.Str()


dialog_user_schema = DialogUserSchema()


class DialogUsersResource(Resource):
    @token_validate
    def get(self, mobile):
        with mycursor(dictionary=True) as c:
            sql = """select mobile, id_name, id_photo, send_at last_send_at, content last_content
                from dialog
                         left join user u on u.mobile = dialog.from_user
                where to_user = %s
                  and id = (select d.id
                            from dialog d
                            where d.from_user = dialog.from_user
                              and d.to_user = dialog.to_user
                            order by send_at
                limit 1)"""
            c.execute(sql, (mobile,))
            return dialog_user_schema.dump(c.fetchall(), many=True)


class DialogListResource(Resource):
    @staticmethod
    def filter_(dialogs: List[dict]):
        now = datetime.utcnow()
        try:
            begin = now + timedelta(seconds=int(request.args.get('begin')))
        except TypeError:
            begin = None
        try:
            end = now + timedelta(seconds=int(request.args.get('end')))
        except TypeError:
            end = None
        res = []
        for dialog in dialogs:
            create_at = dialog['send_at']
            if begin is not None and create_at < begin:
                continue
            if end is not None and create_at > end:
                continue
            res.append(dialog)
        return res

    @token_validate
    def get(self, mobile, other):
        with mycursor(dictionary=True) as c:
            c.execute('select * from dialog where (from_user=%s and to_user=%s) or (from_user=%s and to_user=%s)',
                      (mobile, other, other, mobile))
            return dialog_schema.dump(self.filter_(c.fetchall()), many=True)


class DialogResource(Resource):
    @token_validate
    def post(self, mobile):
        with mycursor() as c:
            data = dialog_schema.loads(request.data.decode())
            data['from_user'] = mobile
            to_insert = curd_params(data, dialog_schema)
            c.execute(f'insert into dialog set {to_insert[0]}', to_insert[1])
            return Response(status=201)
