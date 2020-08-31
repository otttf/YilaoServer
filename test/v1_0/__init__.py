import os
import requests

_prefix: str
_version = os.path.basename(__path__[0]).replace('_', '.')


def set_prefix(prefix):
    global _prefix
    _prefix = prefix


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


class Login:
    def __init__(self, mobile, platform, passwd=None):
        self.mobile = mobile
        self.platform = platform
        self.passwd = passwd
        self.token = None
        if not self.passwd:
            check(requests.post(f'{_prefix}/{_version}/users/{mobile}/validations', json={
                'platform': platform
            }))

    def validate(self, code=None):
        if self.passwd:
            resp = requests.get(f'{_prefix}/{_version}/users/{self.mobile}/validations', params={
                'passwd': self.passwd,
                'platform': self.platform
            })
        else:
            resp = requests.delete(f'{_prefix}/{_version}/users/{self.mobile}/validations', params={
                'code': code,
                'platform': self.platform
            })
        check(resp)
        self.token = resp.json()['token']


class Signup:
    def __init__(self, mobile, platform):
        self.mobile = mobile
        self.platform = platform
        try:
            check(requests.put(f'{_prefix}/{_version}/users/{mobile}'))
        except CheckError as e:
            if e.args[1] == 409:
                if requests.get(f'{_prefix}/{_version}/verifiedUsers/{mobile}').status_code != 404:
                    raise Error(f'{mobile} has been verified')
        self.login = Login(mobile, platform)

    def validate(self, code, new_passwd):
        self.login.validate(code)
        check(requests.patch(
            f'{_prefix}/{_version}/users/{self.mobile}', params={
                'platform': self.platform,
                'token': self.login.token
            }, json={
                'passwd': new_passwd
            }))
