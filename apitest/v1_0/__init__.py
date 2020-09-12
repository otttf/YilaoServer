from resource.v1_0.user import UserResource
from resource.v1_0.order import OrderListResource, OrderResource
import requests

_prefix: str


def set_prefix(prefix):
    global _prefix
    _prefix = prefix


def _use(_): pass


def link(*args):
    _use(args)

    def wrapper(func):
        return func

    return wrapper


class Error(Exception):
    pass


class CheckError(Error):
    def __init__(self, url, code, content):
        super(CheckError, self).__init__(url, code, content)
        self.url = url
        self.code = code
        self.content = content


def check(resp):
    if resp.status_code // 100 != 2:
        raise CheckError(resp.url, resp.status_code, resp.content.decode())


class Null:
    pass


def set_field(di, name, value):
    di[name] = None if value == Null else value


# class UserTest:
#     @staticmethod
#     @link(UserResource.get)
#     def get(mobile, platform, token):
#         url = f'{_prefix}/v1.0/users/{mobile}'
#         params = {
#             'platform': platform,
#             'token': token
#         }
#         resp = requests.get(url, params)
#         check(resp)
#         return resp.json()
#
#     @staticmethod
#     @link(UserResource.put)
#     def put(mobile, platform, code, passwd):
#         url = f'{_prefix}/v1.0/users/{mobile}'
#         params = {
#             'platform': platform,
#             'event': 'signup',
#             'code': code,
#             'passwd': passwd
#         }
#         check(requests.put(url, params=params))
#
#     @staticmethod
#     @link(UserResource.patch)
#     def patch(mobile, platform, *, token=None, passwd=None, code=None, event=None, new_passwd=None):
#         url = f'{_prefix}/v1.0/users/{mobile}'
#         params = {
#             'platform': platform
#         }
#         body = {}
#         if token is not None:
#             set_field(params, 'token', token)
#         if passwd is not None:
#             set_field(params, 'passwd', passwd)
#         if code is not None:
#             set_field(params, 'code', code)
#         if event is not None:
#             set_field(params, 'event', event)
#         if new_passwd is not None:
#             set_field(body, 'passwd', new_passwd)
#         check(requests.patch(url, params=params, json=body))
#
#
# class VerifiedUserTest:
#     @staticmethod
#     def get(mobile):
#         url = f'{_prefix}/v1.0/verifiedUsers/{mobile}'
#         return requests.get(url).status_code == 200
#
#
# class ValidationTest:
#     @staticmethod
#     def get(mobile, platform, passwd):
#         url = f'{_prefix}/v1.0/users/{mobile}/validations'
#         params = {
#             'platform': platform,
#             'passwd': passwd
#         }
#         resp = requests.get(url, params)
#         check(resp)
#         return resp.json()['token']
#
#     @staticmethod
#     def post(mobile, platform, event):
#         url = f'{_prefix}/v1.0/users/{mobile}/validations'
#         body = {
#             'platform': platform,
#             'event': event
#         }
#         check(requests.post(url, json=body))
#
#     @staticmethod
#     def delete(mobile, platform, code, event):
#         url = f'{_prefix}/v1.0/users/{mobile}/validations'
#         params = {
#             'platform': platform,
#             'code': code,
#             'event': event
#         }
#         resp = requests.delete(url, params=params)
#         check(resp)
#         return resp.json()['token']
#
#
# class OrderTest:
#     @staticmethod
#     @link(OrderListResource.post)
#     def post(mobile, platform, token, emergency_level, destination=None, address=None, tasks=None):
#         url = f'{_prefix}/v1.0/users/{mobile}/orders'
#         params = {
#             'platform': platform,
#             'token': token
#         }
#         body = {}
#         if emergency_level is not None:
#             set_field(body, 'emergency_level', emergency_level)
#         if destination is not None:
#             set_field(body, 'destination_longitude', destination[0])
#             set_field(body, 'destination_latitude', destination[1])
#         if address is not None:
#             set_field(body, 'address', address)
#         if tasks is not None:
#             set_field(body, 'tasks', tasks)
#         resp = requests.post(url, params=params, json=body)
#         check(resp)
#
#
# def signup(mobile, platform, get_code, get_passwd):
#     if VerifiedUserTest.get(mobile):
#         raise Error(f'user {mobile} has been signup')
#     ValidationTest.post(mobile, platform, 'signup')
#     UserTest.put(mobile, platform, get_code(), get_passwd())
#
#
# def login_by_passwd(mobile, platform, passwd):
#     return ValidationTest.get(mobile, platform, passwd)
#
#
# def login_by_code(mobile, platform, get_code):
#     ValidationTest.post(mobile, platform, 'login')
#     return ValidationTest.delete(mobile, platform, get_code(), 'login')
#
#
# def reset_passwd_by_old(mobile, platform, get_old_passwd, get_new_passwd):
#     UserTest.patch(mobile, platform, passwd=get_old_passwd(), new_passwd=get_new_passwd())
#
#
# def reset_passwd_by_code(mobile, platform, get_code, get_new_passwd):
#     ValidationTest.post(mobile, platform, 'reset_secret')
#     UserTest.patch(mobile, platform, code=get_code(), event='reset_secret', new_passwd=get_new_passwd())
