from .abstractconfig import *
from wrap import rcon, Sync

Name = Environment.Name
prefix = f'{Environment.root_dir}/{os.getppid()}'

sms_aid = f'{prefix}/{Name.sms_aid}'
sms_as = f'{prefix}/{Name.sms_as}'
sms_rid = f'{prefix}/{Name.sms_rid}'
sms_sn = f'{prefix}/{Name.sms_sn}'
sms_tc = f'{prefix}/{Name.sms_tc}'

gunicorn = rcon.get(sms_aid) is not None

if gunicorn:
    with Sync() as s:
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
    SMSConfig.accessKeyId = secret[Name.sms_aid]
    SMSConfig.accessSecret = secret[Name.sms_as]
    SMSConfig.RegionId = secret[Name.sms_rid]
    SMSConfig.SignName = secret[Name.sms_sn]
    SMSConfig.TemplateCode = secret[Name.sms_tc]
    GunicornConfig.workers = 1
    Environment.family = [os.getpid()]
