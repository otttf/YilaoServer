from functools import partial
from marshmallow import Schema, fields

__all__ = ['PointSchema', 'UserSchema', 'ResourceSchema', 'DialogSchema', 'StoreSchema', 'CommoditySchema',
           'OrderSchema', 'user_schema', 'resource_schema', 'dialog_schema', 'store_schema', 'commodity_schema',
           'order_schema', 'task_schema']


def varchar(s, n):
    return len(s) <= n


varchar32 = partial(varchar, n=32)
varchar64 = partial(varchar, n=64)
text = partial(varchar, n=65535)


class PointSchema(Schema):
    longitude = fields.Float(validate=lambda it: -180 <= it <= 180)
    latitude = fields.Float(validate=lambda it: -90 <= it <= 90)
    name = fields.Str(allow_none=True, validate=varchar64)


class UserSchema(Schema):
    mobile = fields.Int()
    passwd = fields.Str(load_only=True, validate=lambda it: 8 <= len(it) <= 16)
    nickname = fields.Str(validate=varchar32)
    sex = fields.Str(allow_none=True, validate=lambda it: it in ['male', 'female'])
    portrait = fields.Int()
    default_location = fields.Nested(PointSchema, allow_none=True)
    mark = fields.Str(dump_only=True, allow_none=True, validate=lambda it: it in ['test'])
    create_at = fields.DateTime(dump_only=True)
    id_name = fields.Str(validate=varchar32)
    id_school = fields.Str(validate=varchar32)
    id_photo = fields.Str(validate=lambda it: len(it) == 36)


class ResourceSchema(Schema):
    uuid = fields.Str(dump_only=True)
    name = fields.Str(validate=varchar32)
    from_user = fields.Int(dump_only=True)
    create_at = fields.DateTime(dump_only=True)


class DialogSchema(Schema):
    id = fields.Int(dump_only=True)
    content = fields.Str(required=True)
    from_user = fields.Int(dump_only=True)
    to_user = fields.Int(required=True)
    send_at = fields.DateTime(dump_only=True)


class CommoditySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=varchar32)
    from_user = fields.Int(dump_only=True)
    location = fields.Nested(PointSchema, allow_none=True)
    on_offer = fields.Bool()
    price = fields.Float(required=True)
    sales_volume = fields.Float(dump_only=True)
    photo = fields.Int(allow_none=True)


class OrderSchema(Schema):
    id = fields.Int(dump_only=True)
    from_user = fields.Int(dump_only=True)
    phone = fields.Int()
    destination = fields.Nested(PointSchema, allow_none=True)
    emergency_level = fields.Str(validate=lambda it: it in ['normal', 'urgent'])
    create_at = fields.DateTime(dump_only=True)
    receive_at = fields.DateTime(dump_only=True)
    executor = fields.Int(dump_only=True)
    close_at = fields.DateTime(dump_only=True)
    close_state = fields.Str(validate=lambda it: it in ['finish', 'cancel'])
    tasks = fields.List(fields.Nested(lambda: task_schema), required=True)


class TaskSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=varchar32)
    type = fields.Str(required=True, validate=varchar32)
    detail = fields.Str(allow_none=True, validate=text)
    protected_info = fields.Str(allow_none=True, validate=text)
    destination = fields.Nested(PointSchema, allow_none=True)
    count = fields.Int(required=True)
    reward = fields.Float(required=True)
    in_at = fields.DateTime(allow_none=True)
    out_at = fields.DateTime(allow_none=True)


user_schema = UserSchema()
resource_schema = ResourceSchema()
dialog_schema = DialogSchema()
commodity_schema = CommoditySchema()
order_schema = OrderSchema()
task_schema = TaskSchema()
