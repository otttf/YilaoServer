from config.abstractconfig import Environment, ResourceConfig
from flask import request, send_from_directory, Response
from flask_restful import Resource
import os
from schema import resource_schema
from ..util import mycursor
from uuid import uuid4
from .validation import test, token_validate


def get_path(mobile, visibility='public'):
    return f'{Environment.root_dir}/data/{mobile}/{visibility}'


class ResourceListResource(Resource):
    def post(self, mobile):
        if mobile != 0 and not test(token_validate, mobile=mobile):
            return Response(status=401)
        uuid = str(uuid4())
        path = get_path(mobile)
        if not os.path.exists(path):
            os.makedirs(path)
        with open(f'{path}/{uuid}', 'wb') as f:
            f.write(request.stream.read(ResourceConfig.Resource.chuck_size))
        if mobile != 0:
            with mycursor() as c:
                c.execute('insert into resource(uuid, from_user, create_at) values (%s, %s, current_timestamp)',
                          (uuid, mobile))
        return resource_schema.dump({'uuid': uuid}), 201


def get_public_resource(mobile, uuid):
    return send_from_directory(get_path(mobile), uuid)
