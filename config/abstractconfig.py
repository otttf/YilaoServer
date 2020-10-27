from getpass import getpass
import json
import os
from typing import List, Optional


class DBGConfig:
    class SMS:
        close: bool = True
        fixed: Optional[str] = '1234'
        close_times_limit = True

    class MySQL:
        drop_before_run: bool = True
        close_foreign_key: bool = False

    on = True


class Environment:
    class Name:
        sms_aid: str = 'SMSConfig/accessKeyId'
        sms_as: str = 'SMSConfig/accessSecret'
        sms_rid = 'SMSConfig/RegionId'
        sms_sn = 'SMSConfig/SignName'
        sms_tc = 'SMSConfig/TemplateCode'
        worker_list: str = 'worker_list'

    root_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    family: List[int]

    @classmethod
    def rank(cls):
        return cls.family.index(os.getpid())


class GunicornConfig:
    bind: str = '0.0.0.0:5000'
    backlog: int = 512
    timeout: int = 30
    worker_class: str = 'gevent'
    workers: int = 4  # multiprocessing.cpu_count() * 2 + 1
    threads: int = 2
    loglevel: str = 'info'
    access_log_format: str = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'


class LogConfig:
    format_patterns: List[str] = [
        '%(message)s',
        '%(asctime)s ptid=%(process)d-%(thread)s %(levelname)s at(%(pathname)s, %(lineno)d): %(message)s']
    level: int = 0
    pattern_n: int = 0


class MySQLConfig:
    host: str = 'localhost'
    port: int = 3306
    user: str = 'admin'
    db: str = 'Yilao'
    passwd: Optional[str] = 'admin'
    scripts: List[str] = ['', '1.0']
    init_database: bool = True


class ServerConfig:
    host: str = '0.0.0.0'
    port: int = 8080


class SMSConfig:
    accessKeyId: Optional[str]
    accessSecret: Optional[str]
    RegionId: Optional[str]
    SignName: Optional[str]
    TemplateCode: Optional[str]


class RedisConfig:
    host = 'localhost'
    port = 6379
    db = 0
    passwd = None


class ResourceConfig:
    class User:
        active_duration: float = 300

    class Token:
        expire = 300
        cache = True

    class SMS:
        expire = 300
        times_limit = 5
        appid_list = [
            'df3b72a07a0a4fa1854a48b543690eab'
        ]


def get_secret():
    try:
        with open(f'{os.path.dirname(os.path.abspath(__file__))}{os.sep}secret.json') as f:
            secret = json.load(f)
        # 重要密码
        if Environment.Name.sms_as not in secret:
            secret[Environment.Name.sms_as] = getpass('请输入阿里云RAM用户的accessSecret')
        return secret
    except FileNotFoundError as e:
        print('required file "secret.json" template:')
        print(json.dumps({
            Environment.Name.sms_aid: "str",
            Environment.Name.sms_as: "Optional[str]",
            Environment.Name.sms_rid: "str",
            Environment.Name.sms_sn: "str",
            Environment.Name.sms_tc: "str"
        }, indent=4))
        exit(0)
    except KeyboardInterrupt:
        print()
        exit(0)
