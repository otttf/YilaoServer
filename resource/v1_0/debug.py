from config.abstractconfig import DBGConfig
from wrap import _use
from flask import request, Response
from flask_restful import Resource
import json
from ..util import get_rcon, message, mycursor

_use(DBGConfig)


class CMDResource(Resource):
    class Error(Exception):
        pass

    class UnknownCmdTypeError(Exception):
        pass

    def post(self):
        data = json.loads(request.data)
        type_ = data['type']
        cmd = data['cmd']
        try:
            if type_ == 'python':
                return eval(cmd), 201
            elif type_ == 'mysql':
                with mycursor(dictionary=True) as c:
                    c.execute(cmd)
                    res = c.fetchall()
                    return message(msg=str(res)), 201
            elif type_ == 'redis':
                get_rcon().execute_command(cmd)
                return Response(status=201)
            else:
                raise self.UnknownCmdTypeError
        except self.UnknownCmdTypeError:
            return message(exc='unknown cmd type'), 400
        except Exception as e:
            return message(exc=str(e)), 500
