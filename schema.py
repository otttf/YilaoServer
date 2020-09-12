from functools import partial
from marshmallow import Schema, fields
import re

__all__ = ['UserSchema', 'ResourceSchema', 'DialogSchema', 'StoreSchema', 'CommoditySchema', 'OrderSchema',
           'user_schema', 'resource_schema', 'dialog_schema', 'store_schema', 'commodity_schema', 'order_schema']


def varchar(s, n):
    return len(s) <= n


varchar32 = partial(varchar, n=32)
varchar64 = partial(varchar, n=64)
text = partial(varchar, n=65535)


class UserSchema(Schema):
    mobile_pattern = re.compile(r'^1[3-9]\d{9}')
    mobile = fields.Int(validate=lambda it: UserSchema.mobile_pattern.match(str(it)))
    passwd = fields.Str(load_only=True, validate=lambda it: 8 <= len(it) <= 16)
    nickname = fields.Str(validate=varchar32)
    sex = fields.Str(allow_none=True, validate=lambda it: it in ['male', 'female'])
    portrait = fields.Int()
    default_location_longitude = fields.Decimal(allow_none=True, validate=lambda it: -180 <= it <= 180)
    default_location_latitude = fields.Decimal(allow_none=True, validate=lambda it: -90 <= it <= 90)
    address = fields.Str(allow_none=True, validate=varchar64)
    mark = fields.Str(dump_only=True, allow_none=True, validate=lambda it: it in ['test'])
    create_at = fields.DateTime(dump_only=True)


class ResourceSchema(Schema):
    id = fields.Int()
    suffix = fields.Str(allow_none=True)
    data = fields.Raw(required=True)


class DialogSchema(Schema):
    id = fields.Int()
    context = fields.Str(required=True)
    from_user = fields.Int(dump_only=True)
    to_user = fields.Int(required=True)
    send_time = fields.DateTime(dump_only=True)


class StoreSchema(Schema):
    id = fields.Int()
    name = fields.Str(required=True, validate=varchar32)
    location_longitude = fields.Decimal(allow_none=True, validate=lambda it: -180 <= it <= 180)
    location_latitude = fields.Decimal(allow_none=True, validate=lambda it: -90 <= it <= 90)
    address = fields.Str(allow_none=True, validate=varchar64)
    photo = fields.Int(allow_none=True)
    from_user = fields.Int(dump_only=True)


class CommoditySchema(Schema):
    id = fields.Int()
    name = fields.Str(required=True, validate=varchar32)
    store = fields.Str(required=True)
    on_offer = fields.Bool(required=True)
    price = fields.Decimal(required=True)
    sales_volume = fields.Float(dump_only=True)
    photo = fields.Int(allow_none=True)


class OrderSchema(Schema):
    id = fields.Int()
    from_user = fields.Int(dump_only=True)
    destination_longitude = fields.Decimal(allow_none=True, validate=lambda it: -180 <= it <= 180)
    destination_latitude = fields.Decimal(allow_none=True, validate=lambda it: -90 <= it <= 90)
    address = fields.Str(allow_none=True, validate=varchar64)
    emergency_level = fields.Str(required=True, validate=lambda it: it in ['normal', 'urgent'])
    create_at = fields.DateTime(dump_only=True)
    receive_at = fields.DateTime(dump_only=True)
    executor = fields.Int(allow_none=True)
    close_at = fields.DateTime(dump_only=True)
    close_state = fields.Str(validate=lambda it: it in ['finish', 'cancel'])
    tasks = fields.List(fields.Nested(lambda: TaskSchema()), required=True)


class TaskSchema(Schema):
    id = fields.Int()
    name = fields.Str(required=True, validate=varchar32)
    type = fields.Str(required=True, validate=varchar32)
    detail = fields.Str(allow_none=True, validate=text)
    protected_info = fields.Str(allow_none=True, validate=text)
    tangible = fields.Bool(required=True)
    destination_longitude = fields.Decimal(allow_none=True, validate=lambda it: -180 <= it <= 180)
    destination_latitude = fields.Decimal(allow_none=True, validate=lambda it: -90 <= it <= 90)
    address = fields.Str(allow_none=True, validate=varchar64)
    count = fields.Int(required=True)
    reward = fields.Decimal(required=True)
    in_at = fields.DateTime(allow_none=True)
    out_at = fields.DateTime(allow_none=True)


user_schema = UserSchema()
resource_schema = ResourceSchema()
dialog_schema = DialogSchema()
store_schema = StoreSchema()
commodity_schema = CommoditySchema()
order_schema = OrderSchema()
