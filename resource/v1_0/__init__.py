from config.abstractconfig import DBGConfig, Environment, yl
from flask import send_from_directory, redirect
from mkdocs import config
from mkdocs.__main__ import build
import os
# import tempfile
from wrap import send, recv
from .order import OrderListResource, OrderResource
from .user import UserResource
from .validation import PasswdResource, SMSResource, TokenResource
from ..util import BaseApi, get_rcon


class Api1o0(BaseApi):
    pass


def register_api_1_0(app):
    api = Api1o0(app)
    name = yl('v1.0/docs_path', False)
    if Environment.rank() == 0:
        # td = tempfile.TemporaryDirectory()
        site_dir = yl('outcome/site', False)  # td.name
        build.build(config.load_config(f'{__path__[0]}/docs/mkdocs.yml', site_dir=site_dir), dirty=True)
        send(get_rcon(), name, site_dir)
    else:
        site_dir = recv(get_rcon(), name)

    @app.route('/v1.0/docs/', methods=['GET'])
    def docs_index():
        return redirect('./index.html')

    @app.route('/v1.0/docs/<path:filename>', methods=['GET'])
    def get_doc(filename):
        return send_from_directory(site_dir, filename)

    api.add_resource(OrderListResource, '/v1.0/users/<int:mobile>/orders')
    api.add_resource(OrderResource, '/v1.0/users/<int:mobile>/orders/<int:order_id>')
    api.add_resource(SMSResource, '/v1.0/sms')
    api.add_resource(TokenResource, '/v1.0/users/<int:mobile>/tokens')
    api.add_resource(UserResource, '/v1.0/users/<int:mobile>')
    if DBGConfig.on:
        pass

    return api
