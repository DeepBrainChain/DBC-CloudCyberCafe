#!/usr/bin/python3
'''
测试开机卡的脚本:
1. 如果只传 phone 和 password 参数，则会登录获取 session 并列出所有设备的简略信息；
2. 如果传了 session 参数，则无需登录，直接使用 session 查询所有设备的简略信息；
3. 如果还传了 host 和 power 参数，则会根据 power 的值(on/off)来控制开关机。
测试命令：
python3 test.py --phone 17********3 --password 12345678
python3 test.py --session HJY_67FC1EBDC2D9411B969830DFDE8D5266
python3 test.py --phone 17********3 --password 12345678 --host asus --power on
'''

import requests
import json
import argparse

parser = argparse.ArgumentParser(description='script to test smyoo product')
parser.add_argument('--phone',dest='phone',action='store',
  help='phone number as user name to login in')
parser.add_argument('--password',dest='password',action='store',
  help='user password of phone to login in')
parser.add_argument('--session',dest='session',action='store',
  help='BpeSessionId when login in using phone number and password')
parser.add_argument('--host',dest='host',action='store',
  help='the host you want to control')
parser.add_argument('--power',dest='op',action='store',
  help='power operation like on/off',choices=['on','off'])
args = parser.parse_args()

class Smyoo:
  def __init__(self):
    self.log = {}
    self.appId = 1314
    self.endpointOS = 1
    self.deviceId = 'D6AB6C159B1FE1F8EF33109CDEE0D9AD'
    self.client_id = '86921651'
    self.client_secret = 'C0A53D2EFF2E4B418BB6B66A0F575EC5'
    self.context = 'A3C64845E49049BF8EA4027B6828CEF1'
    # self.bpeSessionId = ''
    self.urlList = {
      'loginopen':'https://auth.smyoo.com/v1/account/synloginopen',
      'loginticket':'https://auth.smyoo.com/api/gfriend/synloginticket',
      'statuschanged': 'https://auth.smyoo.com/api/gfriend/statuschanged',
      'querydevices':'https://auth.smyoo.com/api/gfriend/querydevices',
      'setdevicedata':'https://auth.smyoo.com/api/gfriend/setdevicedata'
    }

  def login(self, phone, password):
    injson = {
      "appId":self.appId,
      "endpointOS":self.endpointOS,
      "areaId":0,
      "clientVersion":"",
      "phone":phone,
      "password":password,
      "deviceId":self.deviceId,
      "autologin":"true",
      "client_id":self.client_id,
      "client_secret":self.client_secret
    }
    response = requests.post(self.urlList['loginopen'],json=injson)
    ticket = None
    resultMsg = None
    try:
      # print('json: ', response.json())
      resultMsg = response.json()['resultMsg']
      ticket = response.json()['data']['ticket']
    except:
      print('status_code: ', response.status_code)
      # print('apparent_encoding: ', response.apparent_encoding)
      # print('encoding: ', response.encoding)
      # print('cookies: ', response.cookies)
      # print(requests.utils.dict_from_cookiejar(response.cookies))
      print('headers: ', response.headers)
      print('text: ', response.text)

    if ticket is None:
      return None, resultMsg if resultMsg else 'unknown error'

    injson = {
      "appId":self.appId,
      "endpointOS":self.endpointOS,
      "clientVersion":"",
      "ticket":ticket,
      "deviceId":self.deviceId,
      "context":self.context
    }
    response = requests.post(self.urlList['loginticket'],json=injson)
    bpeSessionId = None
    resultMsg = None
    try:
      # print('json: ', response.json())
      resultMsg = response.json()['resultMsg']
      bpeSessionId = response.json()['data']['BpeSessionId']
    except:
      print('status_code: ', response.status_code)
      # print('apparent_encoding: ', response.apparent_encoding)
      # print('encoding: ', response.encoding)
      # print('cookies: ', response.cookies)
      # print(requests.utils.dict_from_cookiejar(response.cookies))
      print('headers: ', response.headers)
      print('text: ', response.text)
    return bpeSessionId, resultMsg if resultMsg else 'unknown error'

  def statusChanged(self, bpeSessionId):
    injson = {
      "appId":self.appId,
      "endpointOS":self.endpointOS,
      "clientVersion":"",
      "deviceId":self.deviceId,
      "context":self.context
    }
    cookies = {'BpeSessionId':bpeSessionId}
    response = requests.post(self.urlList['statuschanged'],json=injson,cookies=cookies)
    updateTime = None
    resultMsg = None
    try:
      # print('json: ', response.json())
      resjson = response.json()
      resultMsg = resjson['resultMsg']
      updateTime = resjson['data']['deviceupdatetime']
    except:
      print('An error occurred while retrieving the update time')
      print('status_code: ', response.status_code)
      print('headers: ', response.headers)
      print('text: ', response.text)
    return updateTime, resultMsg if resultMsg else 'unknown error'

  def queryDevices(self, bpeSessionId):
    injson = {
      "appId":self.appId,
      "endpointOS":self.endpointOS,
      "clientVersion":"",
      "deviceId":self.deviceId,
      "context":self.context
    }
    cookies = {'BpeSessionId':bpeSessionId}
    # cookies = requests.cookies.RequestsCookieJar()
    # cookies.set('BpeSessionId', bpeSessionId, path='/', domain='.smyoo.com')
    response = requests.post(self.urlList['querydevices'],json=injson,cookies=cookies)
    devices = None
    resultMsg = None
    try:
      # print('json: ', response.json())
      resultMsg = response.json()['resultMsg']
      mcuinfos = json.loads(response.json()['data']['mcuinfos'])
      # 还需要去除'datapoint'中的转义字符
      for index, mcuinfo in enumerate(mcuinfos):
        translate = mcuinfo['datapoint']
        mcuinfo['datapoint'] = json.loads(translate)
        mcuinfos[index] = mcuinfo
      devices = []
      device = {'mcuname':'', 'note':'', 'isonline': None, 'power': None, 'mcuid':''}
      for mcuinfo in mcuinfos:
        # print(mcuinfo)
        device['mcuname'] = mcuinfo['mcuname']
        device['note'] = mcuinfo['note']
        device['isonline'] = mcuinfo['isonline']
        device['power'] = mcuinfo['datapoint']['status']
        device['mcuid'] = mcuinfo['mcuid']
        # print(device)
        devices.append(device)
    except:
      print('status_code: ', response.status_code)
      # print('apparent_encoding: ', response.apparent_encoding)
      # print('encoding: ', response.encoding)
      # print('cookies: ', response.cookies)
      print('headers: ', response.headers)
      print('text: ', response.text)
    return devices, resultMsg if resultMsg else 'unknown error'

  def powerControl(self, bpeSessionId, mcuid, switch):
    # datapoint = {'status':switch}
    injson = {
      "appId":self.appId,
      "endpointOS":self.endpointOS,
      "clientVersion":"",
      "deviceId":self.deviceId,
      "mcuid":mcuid,
      "datatype":1,
      # "datapoint":repr(datapoint),
      "datapoint":f'{{\"status\":{switch}}}',
      "context":self.context
    }
    # print(injson)
    cookies = {'BpeSessionId':bpeSessionId}
    response = requests.post(self.urlList['setdevicedata'],json=injson,cookies=cookies)
    resultCode = -1
    resultMsg = None
    try:
      # print('json: ', response.json())
      resjson = response.json()
      resultMsg = resjson['resultMsg']
      print(f'power control request resultCode: {resjson["resultCode"]}, ',
        f'resultMsg: {resjson["resultMsg"]}.')
      resultCode = resjson['resultCode']
    except:
      print('power control except something wrong')
      print('status_code: ', response.status_code)
      # print('apparent_encoding: ', response.apparent_encoding)
      # print('encoding: ', response.encoding)
      # print('cookies: ', response.cookies)
      print('headers: ', response.headers)
      print('text: ', response.text)
    return resultCode, resultMsg if resultMsg else 'unknown error'

def test(phone=None,password=None,session=None,host=None,op=None):
  smyoo = Smyoo()
  bpeSessionId = None
  if session:
    bpeSessionId = session
  elif phone and password:
    bpeSessionId, resultMsg = smyoo.login(phone, password)
    if bpeSessionId is None:
      print(f'login failed: {resultMsg}')
      exit(1)
    print('login successful and bpeSessionId: ', bpeSessionId)
  else:
    print('Either provide a session, or provide a phone number and password to login in')
    exit(1)

  updateTime, resultMsg = smyoo.statusChanged(bpeSessionId)
  if updateTime is None:
    print(f'get smyoo devices update time failed: {resultMsg}')
    exit(1)
  print(f'smyoo devices update time: {updateTime}')

  devices, resultMsg = smyoo.queryDevices(bpeSessionId)
  if devices is None:
    print(f'query smyoo devices failed: {resultMsg}')
    exit(1)

  input_mcuid = None
  print(' %s %s %s %s' % ('mcuname'.ljust(12), 'note'.ljust(12),
    'isonline'.ljust(8), 'power'.ljust(5)))
  for device in devices:
    print(' %s %s %s %s' % (device['mcuname'].ljust(12), device['note'].ljust(12), \
      ('%d' % device['isonline']).ljust(8), ('%d' % device['power']).ljust(5)))
    if device['mcuname'] == host:
      input_mcuid = device['mcuid']

  if host and input_mcuid is None:
    print(f'Can not get smyoo mcuid of host: {host}')
    exit(1)

  if op and input_mcuid:
    smyoo.powerControl(bpeSessionId, input_mcuid, 1 if op == 'on' else 0)

# test(phone='17********3',password='12345678')
# test(session='HJY_67FC1EBDC2D9411B969830DFDE8D5266')
# test(phone='17********3',password='12345678',host='asus',op='on')

if __name__=='__main__':
  print(args)
  test(phone=args.phone, password=args.password, session=args.session, host=args.host, op=args.op)
