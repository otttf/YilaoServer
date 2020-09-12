from config.abstractconfig import Environment, ResourceConfig
from flask import request, Response
from flask_restful import Resource
from schema import order_schema
from ..util import ArgsUtil, BodyUtil, CursorUtil, hash_passwd,mycursor, MySQLUtil
from .validation import or_, passwd_validate, sms_validate, test, token_validate


class OrderListResource(Resource):
    @token_validate
    def post(self, mobile):
        order = order_schema.loads(request.data.decode())
        order['from_user'] = mobile
        MySQLUtil.to_point(order, 'destination')
        MySQLUtil.set_default_point(order, 'destination')

        tasks = order.pop('tasks')
        for it in tasks:
            MySQLUtil.to_point(it, 'destination')
            MySQLUtil.set_default_point(it, 'destination')
        with mycursor() as c:
            to_insert = ', '.join(map(lambda it_: f'{it_}=%s', order.keys()))
            c.execute(f'insert into `order` set {to_insert}', order.values())
            order_id = c.lastrowid
            for it in tasks:
                it['order'] = order_id
                to_insert = ', '.join(map(lambda it_: f'{it_}=%s', order.keys()))
                c.execute(f"insert into `task` set {to_insert}", it.values())


class OrderResource(Resource):
    @token_validate
    def get(self, mobile):
        pass
