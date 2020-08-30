import cryptography  # 让 pipreqs 能够识别该库
from datetime import datetime
import pymysql
import requests

del cryptography

host = 'api.yilao.tk'
db_port = 3306
port = 5000
conn = pymysql.connect(host=host, port=db_port, db='yilao', user='test', passwd='test')
c: pymysql.cursors.Cursor = conn.mycursor()


def clear():
    c.execute('set foreign_key_checks = 0')
    for it in ['user', 'token', 'validation', 'resource', 'dialog', 'dialog_resource_reference', 'store', 'commodity',
               'order', 'task']:
        it = f'`{it}`'
        c.execute(f'truncate table {it}')
    c.execute('set foreign_key_checks = 1')
    conn.commit()


def add_user(mobile, passwd):
    c.execute('insert into user(mobile, verify_at) values (%s, %s)', (mobile, datetime.now()))
    c.execute('call token_add(%s, %s, true)', (mobile, passwd))
    conn.commit()


def signup():
    mobile = input('输入手机号：')
    resp = requests.put(f'http://{host}:{port}/v1.0/users/{mobile}')
    if resp.status_code != 204:
        print(resp.text)
        exit(0)
    resp = requests.post(f'http://{host}:{port}/v1.0/users/{mobile}/validations', json={
        'event': 'signup'
    })
    if resp.status_code != 204:
        print(resp.text)
        exit(0)
    code = input('输入验证码：')
    passwd = input('输入密码：')
    resp = requests.delete(f'http://{host}:{port}/v1.0/users{mobile}/validations', params={
        'event': 'signup',
        'code': code
    }, json={
        'passwd': passwd
    })
    if resp.status_code != 204:
        print(resp.text)
        exit(0)
    resp = requests.get(f'http://{host}:{port}/v1.0/users/{mobile}')
    print(resp.text)


def login_by_sms():
    mobile = input('输入手机号：')
    requests.put(f'http://{host}:{port}/v1.0/users/{mobile}')
    requests.post(f'http://{host}:{port}/v1.0/users/{mobile}/validations', json={
        'event': 'signup'
    })
    code = input('输入验证码：')
    passwd = input('输入密码：')
    requests.delete(f'http://{host}:{port}/v1.0/users{mobile}/validations', params={
        'event': 'signup',
        'code': code
    }, json={
        'passwd': passwd
    })
    resp = requests.get(f'http://{host}:{port}/v1.0/users/{mobile}')
    print(resp.raw)


if __name__ == '__main__':
    clear()
    signup()
