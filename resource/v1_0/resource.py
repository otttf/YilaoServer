from config.abstractconfig import Environment, ResourceConfig
from flask import request, send_from_directory
from flask_restful import Resource
import os
from schema import resource_schema
from ..util import mycursor
from uuid import uuid4
from .validation import token_validate


def get_path(mobile, visibility='public'):
    return f'{Environment.root_dir}/data/{mobile}/{visibility}'


class ResourceListResource(Resource):
    @token_validate
    def post(self, mobile):
        uuid = str(uuid4())
        path = get_path(mobile)
        if not os.path.exists(path):
            os.makedirs(path)
        with open(f'{path}/{uuid}', 'wb') as f:
            f.write(request.stream.read(ResourceConfig.Resource.chuck_size))
        with mycursor() as c:
            c.execute('insert into resource values (%s, %s, current_timestamp)', (uuid, mobile))
        return resource_schema.dump({'uuid': uuid})


def get_public_resource(mobile, uuid):
    return send_from_directory(get_path(mobile), uuid)
