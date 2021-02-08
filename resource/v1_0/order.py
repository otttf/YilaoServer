from datetime import datetime, timedelta
from flask import request, Response
from flask_restful import Resource
from schema import order_schema, task_schema
from wrap import _use
from ..util import dump_locations, curd_params, exc, mycursor, null_point
from .validation import token_validate


class PublicOrderListResource(Resource):
    def get(self):
        """获取所有可以接取的任务"""
        _use(self)
        with mycursor(dictionary=True) as c:
            # TODO 加入时间筛选
            c.execute("select * from `order` where executor is null and close_state is null")
            order_list = c.fetchall()
            for order in order_list:
                OrderListResource.handle(order)
            return order_schema.dump(order_list, many=True)

        # from_time = request.args.get('from_time')
        # to_time = request.args.get('to_time')
        # region_left = request.args.get('region_left')
        # region_right = request.args.get('region_right')
        # region_top = request.args.get('region_top')
        # region_bottom = request.args.get('region_bottom')
        # region = MySQLUtil.rect(region_left, region_top, region_right, region_bottom)
        # with mycursor() as c:
        #     c.execute("select st_polyfromtext('POLYGON((%s %s, %s %s, %s %s, %s %s, ))')")
        #     c.execute("select * from `order` join task t on `order`.id = t.`order` "
        #               "where mbrcontains(%s, point(%s, %s))")


class OrderListResource(Resource):
    @staticmethod
    def handle(order: dict):
        dump_locations(order, order_schema)
        with mycursor(autocommit=False, dictionary=True) as c:
            c.execute('select * from task where `order`=%s', (order['id'],))
            order['tasks'] = c.fetchall()
            for task in order['tasks']:
                dump_locations(task, task_schema)

    @token_validate
    def get(self, mobile):
        """获取和自己相关的订单，自己是发布者或者自己是执行者"""
        with mycursor(dictionary=True) as c:
            # TODO 加入时间筛选
            c.execute('select * from `order` where from_user=%s or executor=%s', (mobile, mobile))
            order_list = c.fetchall()
            for order in order_list:
                OrderListResource.handle(order)
            return order_schema.dump(order_list, many=True)

    @token_validate
    def post(self, mobile):
        """新建一个订单"""
        order = order_schema.loads(request.data.decode())
        order['from_user'] = mobile
        if 'destination' not in order:
            order['destination'] = null_point

        tasks = order.pop('tasks')
        for task in tasks:
            if 'destination' not in task:
                task['destination'] = null_point

        with mycursor() as c:
            to_insert = curd_params(order, order_schema)
            c.execute(f'insert into `order` set {to_insert[0]}', to_insert[1])
            order_id = c.lastrowid
            for task in tasks:
                task['order'] = order_id
                to_insert = curd_params(task, task_schema)
                c.execute(f"insert into `task` set {to_insert[0]}", to_insert[1])

        return Response(status=201)


class OrderResource(Resource):
    @token_validate
    def patch(self, mobile, order_id):
        """更新订单状态，注意patch只做订单被接受和订单被关闭的处理
        如果要修改订单信息，请使用delete+post"""
        with mycursor() as c:
            c.execute('select * from `order` where id=%s limit 1', (order_id,))
            order = c.fetchone()
            from_user = order['from_user']
            if mobile != from_user:
                # 不是发布者，只能更新是否接受任务状态
                if order['executor'] is None:
                    executor = request.args.get('executor')
                    c.execute('update `order` set receive_at=current_timestamp, executor=%s where id=%s',
                              (executor, order_id))
                elif order['executor'] == mobile:
                    # 如果接受者是自己，那么三分钟内可以取消
                    if datetime.utcnow() - order['receive_at'] < timedelta(minutes=3):
                        c.execute('update `order` set receive_at=null, executor=null where id=%s', (order_id,))
                    else:
                        return exc('超过三分钟，无法取消接单'), 400
                else:
                    # 如果任务已被接受
                    return exc('任务已被其他人接受'), 400
            else:
                # 否则是更新关闭订单的信息
                # 如果有接受者，这个订单就是完成了，否则就是取消了
                state = 'cancel' if order['receive_at'] is None else 'finish'
                c.execute('update `order` set close_at=current_timestamp, close_state=%s where id=%s',
                          (state, order_id))
