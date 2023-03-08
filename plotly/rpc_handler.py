import sys
sys.path.append('../preset/gen-py')

from preset import Preset
from preset.ttypes import *
from preset.constants import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.TSerialization import serialize, deserialize
from thrift.server import TServer, TNonblockingServer

import time

import global_config
from error_code import ErrorCode

def thriftToString(ts):
  return serialize(ts).decode('utf-8')

def stringToThrift(str, ts):
  return deserialize(ts, str.encode('utf-8'))

class OccHandler:
  def __init__(self):
    self.log = {}

  def ping(self):
    print('ping')
    return 'pong'

  def sendMsg(self, message, host, port = 9090):
    transport = TSocket.TSocket(host, port)
    transport = TTransport.TBufferedTransport(transport)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = Preset.Client(protocol)
    try:
      transport.open()
      pingRes = client.ping()
      print(f'ping {host}:{port} return {pingRes}')
    except:
      return ResultStruct(
        code=ErrorCode.CONNECT_FAILED.value,
        message='connect failed')
    try:
      rs = client.handleMessage(message)
      print(f'handleMessage return ResultStruct{{{rs.code}, {rs.message}}}')
    except InvalidMessageType as e:
      print(f'InvalidMessageType: {e}')
      rs.code = ErrorCode.UNKNOWN_MESSAGE_TYPE.value
      rs.message = f'InvalidMessageType: {e}'
    except Thrift.TException as tx:
      print(f'exception: {tx.message}')
      rs.code = ErrorCode.EXCEPTION_OCCURRED.value
      rs.message = f'exception: {tx.message}'
    transport.close()
    return rs

  def handleMessage(self, msg):
    ret = ResultStruct()
    mtl = list(MessageType._VALUES_TO_NAMES.keys())
    if msg.type not in mtl:
      ret.code = ErrorCode.UNKNOWN_MESSAGE_TYPE.value
      ret.message = 'unknown message type'
      print('handle unknown message type')
    elif msg.type == MessageType.PING:
      ret.code = 0
      ret.message = 'pong'
      print('handle ping message')
    elif msg.type == MessageType.GET_BOOT_MENU:
      boot_menu = global_config.get_value('boot_menu')
      bml = BootMenuList(menus=list(boot_menu['name']))
      ret.code = 0
      ret.message = thriftToString(bml)
      # ret.message = 'success'
      print('handle get boot menu message')
    elif msg.type == MessageType.SET_BOOT_MENU:
      bm = BootMenu()
      bm = stringToThrift(msg.body, bm)
      print(f'setBootmenu: {bm}')
      request = {
        'type':'SET_BOOT_MENU',
        'host':msg.host,
        'menu':bm.menu,
        'superTube':bm.superTube
      }
      global_config.set_cache('request',repr(request), expire=3)
      time.sleep(1)
      resultcache = global_config.get_cache('result', default="")
      for sec in range(3):
        if len(resultcache) > 0:
          break;
        time.sleep(1)
        resultcache = global_config.get_cache('result', default="")
      if len(resultcache) > 0:
        global_config.delete_cache('result')
        response = eval(resultcache)
        ret.code = response['code']
        ret.message = response['message']
      else:
        ret.code = ErrorCode.TIMEOUT.value
        ret.message = 'timeout error'
      print('handle set boot menu message')
    elif msg.type == MessageType.GET_SMYOO_DEVICE_INFO:
      hostname = global_config.find_host_name(hostname=msg.host,ip=msg.host)
      if hostname:
        device = global_config.get_smyoo_device_info(hostname)
        if device:
          # print(f'get smyoo device info: {device}')
          info = SmyooDeviceInfo(mcuname=device['mcuname'],
            note=device['note'], isonline=device['isonline'],
            power=device['power'], mcuid=device['mcuid'])
          ret.code = 0
          ret.message = thriftToString(info)
        else:
          ret.code = ErrorCode.SMYOO_HOST_NOT_EXISTED.value
          ret.message= 'smyoo device not existed'
      else:
        ret.code = ErrorCode.UNKNOWN_HOST.value
        ret.message = 'can not find smyoo mcuname of host'
      print('handle get smyoo device info message')
    elif msg.type == MessageType.SET_SMYOO_DEVICE_POWER:
      sdp = SmyooDevicePowerData()
      sdp = stringToThrift(msg.body, sdp)
      print(f'setSmyooDevicePower: {sdp}')
      request = {
        'type':'SET_SMYOO_DEVICE_POWER',
        'host':msg.host,
        'status':sdp.status,
        'mcuid':sdp.mcuid,
        'mcuname':sdp.mcuname
      }
      global_config.set_cache('request',repr(request), expire=3)
      time.sleep(1)
      resultcache = global_config.get_cache('result', default="")
      for sec in range(3):
        if len(resultcache) > 0:
          break;
        time.sleep(1)
        resultcache = global_config.get_cache('result', default="")
      if len(resultcache) > 0:
        global_config.delete_cache('result')
        response = eval(resultcache)
        ret.code = response['code']
        ret.message = response['message']
      else:
        ret.code = ErrorCode.TIMEOUT.value
        ret.message = 'timeout error'
      print('handle set smyoo device power message')
    else:
      hostip = global_config.find_host_ip(hostname=msg.host,ip=msg.host)
      if hostip:
        ret = self.sendMsg(msg, hostip)
      else:
        ret.code = ErrorCode.UNKNOWN_HOST.value
        ret.message = 'unknown host'
    return ret

def thrift_thread(tport):
  # run thrift api server
  handler = OccHandler()
  processor = Preset.Processor(handler)
  transport = TSocket.TServerSocket(host='0.0.0.0',port=tport)
  tfactory = TTransport.TBufferedTransportFactory()
  pfactory = TBinaryProtocol.TBinaryProtocolFactory()
  # tServer = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
  tServer = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
  # tServer = TNonblockingServer.TNonblockingServer(processor, transport, pfactory)
  print('thrift server start serve')
  tServer.serve()
