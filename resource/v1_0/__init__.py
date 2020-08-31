from base import app, DBGConfig
from markdown import markdown
import os
from .debug import DebugResource
from .user import UserResource, VerifiedUserResource
from .validation import ValidationResource
from ..util import BaseApi


class Api1o0(BaseApi):
    pass


api1_0 = Api1o0(app)


def register_api_1_0():
    with open(rf'{__path__[0]}{os.sep}doc.md') as f:
        doc = markdown(f.read())

    @app.route('/v1.0')
    def get_doc():
        return doc

    api1_0.add_resource(UserResource, '/v1.0/users/<int:mobile>')
    api1_0.add_resource(ValidationResource, '/v1.0/users/<int:mobile>/validations')
    api1_0.add_resource(VerifiedUserResource, '/v1.0/verifiedUsers/<int:mobile>')
    if DBGConfig.on:
        api1_0.add_resource(DebugResource, '/v1.0/')
