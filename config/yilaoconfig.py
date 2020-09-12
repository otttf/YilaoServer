from .abstractconfig import *
from wrap import Sync


def impl(rcon):
    name = Environment.Name
    prefix = f'{Environment.root_dir}/{os.getppid()}'

    sms_aid = f'{prefix}/{name.sms_aid}'
    sms_as = f'{prefix}/{name.sms_as}'
    sms_rid = f'{prefix}/{name.sms_rid}'
    sms_sn = f'{prefix}/{name.sms_sn}'
    sms_tc = f'{prefix}/{name.sms_tc}'

    gunicorn = rcon.get(sms_aid) is not None

    if gunicorn:
        with Sync(rcon) as s:
            # 获取重要信息
            SMSConfig.accessKeyId = rcon.get(sms_aid)
            SMSConfig.accessSecret = rcon.get(sms_as)
            SMSConfig.RegionId = rcon.get(sms_rid)
            SMSConfig.SignName = rcon.get(sms_sn)
            SMSConfig.TemplateCode = rcon.get(sms_tc)
        Environment.family = s.li
        if Environment.rank() == 0:
            rcon.delete(sms_aid)
            rcon.delete(sms_as)
            rcon.delete(sms_rid)
            rcon.delete(sms_sn)
            rcon.delete(sms_tc)
    else:
        secret = get_secret()
        SMSConfig.accessKeyId = secret[name.sms_aid]
        SMSConfig.accessSecret = secret[name.sms_as]
        SMSConfig.RegionId = secret[name.sms_rid]
        SMSConfig.SignName = secret[name.sms_sn]
        SMSConfig.TemplateCode = secret[name.sms_tc]
        GunicornConfig.workers = 1
        Environment.family = [os.getpid()]
