from config.abstractconfig import Environment, ResourceConfig
from flask import request, Response, send_from_directory, send_file
from flask_restful import Resource
import os
from schema import resource_schema
from ..util import mycursor
from uuid import uuid4
from .validation import token_validate


class ResourceResource(Resource):
    @token_validate
    def post(self, mobile):
        uuid = str(uuid4())
        path = f'{Environment.root_dir}/data/{mobile}/public'
        if not os.path.exists(path):
            os.makedirs(path)
        with open(f'{path}/{uuid}', 'wb') as f:
            f.write(request.stream.read(ResourceConfig.Resource.chuck_size))
        with mycursor() as c:
            c.execute('insert into resource values (%s, %s, current_timestamp)', (uuid, mobile))
        return resource_schema.dump({'uuid': uuid})
