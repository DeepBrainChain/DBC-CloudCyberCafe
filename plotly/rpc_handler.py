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

import global_config
from error_code import ErrorCode
import occ

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
      df_boot_menu = global_config.get_boot_menu_dataframe()
      bml = BootMenuList(menus=df_boot_menu['name'].tolist())
      ret.code = 0
      ret.message = thriftToString(bml)
      # ret.message = 'success'
      print('handle get boot menu message')
    elif msg.type == MessageType.SET_BOOT_MENU:
      bm = BootMenu()
      bm = stringToThrift(msg.body, bm)
      print(f'setBootmenu: {bm}')
      if msg.host is None:
        ret.code = ErrorCode.UNKNOWN_HOST.value
        ret.message = 'unknown host'
      else:
        result_code, result_message = occ.rpc_set_boot_menu(
          msg.host, bm.menu, bm.superTube)
        ret.code = result_code
        ret.message = result_message
      print('handle set boot menu message')
    elif msg.type == MessageType.GET_SMYOO_DEVICE_INFO:
      if msg.host is None:
        ret.code = ErrorCode.UNKNOWN_HOST.value
        ret.message = 'unknown host'
      else:
        device = occ.get_smyoo_device_info(msg.host, updatedevices=True)
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
      print('handle get smyoo device info message')
    elif msg.type == MessageType.SET_SMYOO_DEVICE_POWER:
      sdp = SmyooDevicePowerData()
      sdp = stringToThrift(msg.body, sdp)
      print(f'setSmyooDevicePower: {sdp}')
      if msg.host is None:
        ret.code = ErrorCode.UNKNOWN_HOST.value
        ret.message = 'unknown host'
      else:
        if sdp.status == 1:
          result_code, result_message = occ.host_power_on_item(hostname=msg.host)
          ret.code = result_code
          ret.message = result_message
        elif sdp.status == 0:
          result_code, result_message = occ.host_power_off_item(hostname=msg.host)
          ret.code = result_code
          ret.message = result_message
        else:
          ret.code = ErrorCode.PLOTLY_INVALID_SMYOO_POWER_STATUS.value
          ret.message = 'invalid power status'
      print('handle set smyoo device power message')
    else:
      if msg.host is None:
        ret.code = ErrorCode.UNKNOWN_HOST.value
        ret.message = 'unknown host'
      else:
        df_hosts = global_config.get_hosts_dataframe()
        host_name_list = df_hosts['host_name'].tolist()
        if msg.host in host_name_list:
          index_num = host_name_list.index(msg.host)
          ret = self.sendMsg(msg, df_hosts.iloc[index_num]['ip'])
        else:
          ret.code = ErrorCode.UNKNOWN_HOST.value
          ret.message= 'can not find host in dashboard'
      print(f'handle message type {msg.type}')
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
