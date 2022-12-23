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

def encrypt(message, key):
  dec = bytearray(message)
  for index, item in enumerate(dec):
    dec[index] = item ^ key
  return dec.decode(encoding='utf-8',errors='strict')

def decrypt(message, key):
  dec = bytearray(message)
  for index, item in enumerate(dec):
    dec[index] = item ^ key
  return dec.decode(encoding='utf-8',errors='strict')

def thriftToString(ts, key = 0):
  return encrypt(serialize(ts), key)

def stringToThrift(str, ts, key = 0):
  dec = decrypt(str.encode('utf-8'), key);
  return deserialize(ts, dec.encode('utf-8'))

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
    transport.open()
    pingRes = client.ping()
    print(f'ping {host}:{port} return {pingRes}')
    try:
      rs = client.handleMessage(message)
      print(f'handleMessage return ResultStruct{{{rs.code}, {rs.message}}}')
    except InvalidMessageType as e:
      print(f'InvalidMessageType: {e}')
      rs.code = 1
      rs.message = f'InvalidMessageType: {e}'
    except Thrift.TException as tx:
      print(f'exception: {tx.message}')
      rs.code = 1
      rs.message = f'exception: {tx.message}'
    transport.close()
    return rs

  def handleMessage(self, msg):
    ret = ResultStruct()
    if msg.type == MessageType.PING:
      ret.code = 0
      ret.message = 'pong'
      print('handle ping message')
    elif msg.type == MessageType.GET_BOOT_MENU:
      boot_menu = global_config.get_value('boot_menu')
      bml = BootMenuList(menus=list(boot_menu['name']))
      ret.code = 0
      ret.message = thriftToString(bml, MessageType.GET_BOOT_MENU)
      # ret.message = 'success'
      print('handle get boot menu message')
    elif msg.type == MessageType.SET_BOOT_MENU:
      bm = BootMenu()
      bm = stringToThrift(msg.body, bm, MessageType.SET_BOOT_MENU)
      print(f'setBootmenu:{bm.menu},{bm.superTube}')
      # global_config.push_queue(f'set_boot_menu,{bm.menu}')
      # global_config.push_queue('set_boot_menu')
      # print('thread queue size: ', global_config.queue_size())
      # with open('thrift.data', 'w', encoding='utf-8') as file:
      #   file.write(f'set_boot_menu,{bm.menu}')
      global_config.set_cache('request', f'set_boot_menu,{msg.host},{bm.menu}')
      time.sleep(1)
      resultcache = global_config.get_cache('result')
      for sec in range(3):
        if resultcache != "":
          break;
        time.sleep(1)
        resultcache = global_config.get_cache('result')
      global_config.delete_cache('result')
      if resultcache == "":
        resultcache = 'error'
      ret.code = 0
      ret.message = resultcache
      print('handle set boot menu message')
    else:
      ret = sendMsg(msg, msg.host)
    return ret

def thrift_thread():
  # run thrift api server
  handler = OccHandler()
  processor = Preset.Processor(handler)
  transport = TSocket.TServerSocket(host='0.0.0.0',port=9090)
  tfactory = TTransport.TBufferedTransportFactory()
  pfactory = TBinaryProtocol.TBinaryProtocolFactory()
  # tServer = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
  tServer = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
  # tServer = TNonblockingServer.TNonblockingServer(processor, transport, pfactory)
  print('thrift server start serve')
  tServer.serve()
