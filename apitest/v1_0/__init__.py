from functools import lru_cache, partial
import inspect
import json
import logging
import re
from resource.v1_0.order import OrderListResource, OrderResource
from resource.v1_0.user import UserResource
from resource.v1_0.validation import PasswdResource, SMSResource, TokenResource
import requests
import sys
from typing import Optional

_prefix: str
default_appid = 'df3b72a07a0a4fa1854a48b543690eab'
args_pattern = re.compile(rf'^[^()]+\((.*)\)$')
loglevel = 11
header_width = 50


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
    logmsg = (f"{' REQUEST '.center(header_width, '=')}\n"
              f'{resp.request.method} {resp.request.url}\n')
    if resp.request.body:
        logmsg += f'\n{json.dumps(json.loads(resp.request.body.decode()), indent=4)}\n'
    logmsg += f"{' RESPONSE '.center(header_width, '=')}\n"
    logmsg += f'{resp.status_code} {resp.reason}\n'
    if resp.content:
        logmsg += f'\n{json.dumps(json.loads(resp.content.decode()), indent=4)}\n'
    logmsg += f"{' END '.center(header_width, '=')}"
    logging.log(loglevel, logmsg)
    if resp.status_code // 100 != 2:
        raise CheckError(resp.url, resp.status_code, resp.content.decode())


class Null:
    pass


def get_args_name():
    s = inspect.stack()[2].code_context[0]
    res = args_pattern.match(s)
    return [it.strip() for it in res[1].split(',')]


def set_field(di, value, name=None):
    if value is not None:
        if name is None:
            name = get_args_name()[1]
        di[name] = None if value == Null else value


def set_point_field(di, value, name=None):
    if value is not None:
        if name is None:
            name = get_args_name()[1]
        longitude = f'{name}_longitude'
        latitude = f'{name}_latitude'
        set_field(di, value[0], longitude)
        set_field(di, value[1], latitude)


class SMSTest:
    @staticmethod
    def url():
        return f'{_prefix}/v1.0/sms'

    @classmethod
    @link(SMSResource.post)
    def post(cls, mobile, method, base_url, appid=default_appid):
        url = cls.url()
        json = {
            'appid': appid,
            'mobile': mobile,
            'method': method,
            'base_url': base_url
        }
        resp = requests.post(url, json=json)
        check(resp)


class TokenTest:
    @staticmethod
    def url(mobile):
        return f'{_prefix}/v1.0/users/{mobile}/tokens'

    @classmethod
    @link(TokenResource.post)
    def post(cls, mobile, passwd=None, code=None, appid=default_appid):
        url = cls.url(mobile)
        params = {}
        set_field(params, passwd)
        set_field(params, code)
        set_field(params, appid)
        resp = requests.post(url, params=params)
        check(resp)
        return resp.json()['token']


class UserTest:
    @staticmethod
    def url(mobile):
        return f'{_prefix}/v1.0/users/{mobile}'

    @classmethod
    @link(UserResource.get)
    def get(cls, mobile, token=None, appid: Optional[str] = default_appid):
        url = cls.url(mobile)
        params = {}
        set_field(params, token)
        set_field(params, appid)
        resp = requests.get(url, params)
        check(resp)
        return resp.json()

    @classmethod
    @link(UserResource.put)
    def put(cls, mobile, code, passwd, appid=default_appid):
        url = cls.url(mobile)
        params = {
            'appid': appid,
            'code': code
        }
        json = {
            'passwd': passwd
        }
        resp = requests.put(url, params=params, json=json)
        check(resp)

    @classmethod
    @link(UserResource.patch)
    def patch(cls, mobile, token=None, passwd=None, code=None, appid=None, new_passwd=None, nickname=None, sex=None,
              portrait=None, default_location=None, address=None):
        url = cls.url(mobile)
        params = {}
        set_field(params, token)
        set_field(params, passwd)
        set_field(params, code)
        set_field(params, appid)
        json = {}
        set_field(json, new_passwd, 'passwd')
        set_field(json, nickname)
        set_field(json, sex)
        set_field(json, portrait)
        set_point_field(json, default_location)
        set_field(json, address)
        resp = requests.patch(url, params=params, json=json)
        check(resp)


def signup(mobile, get_code, get_passwd):
    try:
        UserTest.get(mobile, appid=None)
        raise Error(f'{mobile} has been signup')
    except CheckError as e:
        if e.code == 404:
            SMSTest.post(mobile, 'PUT', UserTest.url(mobile))
            UserTest.put(mobile, get_code(), get_passwd())
        else:
            raise


def login_by_passwd(mobile, passwd):
    return TokenTest.post(mobile, passwd)


def login_by_code(mobile, get_code):
    SMSTest.post(mobile, 'POST', TokenTest.url(mobile))
    return TokenTest.post(mobile, code=get_code(), appid=default_appid)


def reset_passwd_by_old(mobile, get_old_passwd, get_new_passwd):
    UserTest.patch(mobile, passwd=get_old_passwd(), new_passwd=get_new_passwd())


def reset_passwd_by_code(mobile, get_code, get_new_passwd):
    SMSTest.post(mobile, 'PATCH', UserTest.url(mobile))
    UserTest.patch(mobile, code=get_code(), appid=default_appid, new_passwd=get_new_passwd())


def get_code_template():
    return input(r'input your code(^\d{4}$): ')


@lru_cache()
def get_passwd_template(i: int):
    s = {1: '1st', 2: '2nd', 3: '3rd'}.get(i, f'{i}th')
    return input(rf"input your {s} passwd(^\w{{8, 64}}$): ")


class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


color = Color


def header(msg, i=0):
    header_color = [color.HEADER, color.OKGREEN, color.OKBLUE]
    header_str = f' {header_color[i]}{msg}{color.ENDC} '
    logging.log(loglevel, header_str.center(header_width + 9, '*'))


def test_template(mobile=13927553153, prefix='http://api.yilao.tk:5000', get_code=get_code_template,
                  get_passwd=get_passwd_template, proxies=None):
    global _prefix
    _prefix = prefix
    if proxies is not None:
        requests.api.request = partial(requests.api.request, proxies=proxies)
    logging.basicConfig(format='%(message)s', level=loglevel, stream=sys.stdout)

    try:
        header('Usertest')
        header('Test Signup', 1)
        logging.log(loglevel, '')
        try:
            signup(mobile, get_code, partial(get_passwd, 1))
            logging.log(loglevel, 'Signup successfully\n')
        except Error as e:
            logging.log(loglevel, f'{e}\n')
        logging.log(loglevel, '')

        # user login
        header('Test Login', 1)
        header('By passwd', 2)
        logging.log(loglevel, '')
        token = login_by_passwd(mobile, get_passwd(1))
        UserTest.get(mobile, token)
        logging.log(loglevel, '')
        header('By code', 2)
        logging.log(loglevel, '')
        token = login_by_code(mobile, get_code)
        UserTest.get(mobile, token)
        logging.log(loglevel, '')

        # user secret patch
        header('Test Patch passwd', 1)
        header('By old', 2)
        logging.log(loglevel, '')
        reset_passwd_by_old(mobile, partial(get_passwd, 1), partial(get_passwd, 2))
        token = login_by_passwd(mobile, get_passwd(2))
        UserTest.get(mobile, token)
        logging.log(loglevel, '')
        header('By code', 2)
        logging.log(loglevel, '')
        reset_passwd_by_code(mobile, get_code, partial(get_passwd, 1))
        token = login_by_passwd(mobile, get_passwd(1))
        UserTest.get(mobile, token)
        logging.log(loglevel, '')

        # user common patch
        header('Test patch common', 1)
        header('Patch name', 2)
        logging.log(loglevel, '')
        token = login_by_passwd(mobile, get_passwd(1))
        UserTest.patch(mobile, token, appid=default_appid, nickname='new name')
        UserTest.get(mobile, token)
        logging.log(loglevel, '')
    except CheckError:
        logging.log(loglevel, 'Failed to pass the test')
