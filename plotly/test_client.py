import argparse
import sys
sys.path.append('../preset/gen-py')

from preset import Preset
from preset.ttypes import *
from preset.constants import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
# from thrift.transport.TTransport import TMemoryBuffer
from thrift.TSerialization import serialize, deserialize

parser = argparse.ArgumentParser(description='script to test Cloud Cybercafe')
parser.add_argument('-s','--server',default='127.0.0.1',help='host ip of thrift server, default 127.0.0.1')
parser.add_argument('-p','--port',default=9090,help='port of thrift server, default 9090',type=int)
args = parser.parse_args()

def thriftToString(ts):
    return serialize(ts).decode('utf-8')

def stringToThrift(str, ts):
    return deserialize(ts, str.encode('utf-8'))

def main(host, port):
    # Make socket
    transport = TSocket.TSocket(host, port)
    # transport = TSocket.TSocket('192.168.118.1', 9090)

    # Buffering is critical. Raw sockets are very slow
    transport = TTransport.TBufferedTransport(transport)

    # Wrap in a protocol
    protocol = TBinaryProtocol.TBinaryProtocol(transport)

    # Create a client to use the protocol encoder
    client = Preset.Client(protocol)

    # Connect!
    transport.open()

    pingRes = client.ping()
    print(f'ping:{pingRes}')

    pingMsg = Message(version=0x01000001,type=MessageType.PING,body='')
    rs = client.handleMessage(pingMsg)
    print(f'sendPingMsg return ResultStruct{{{rs.code}, {rs.message}}}')

    getUserListMsg = Message(
        version=0x01000001,
        type=MessageType.GET_USER_LIST,
        body='',
        host='asus')
    rs = client.handleMessage(getUserListMsg)
    if rs.code == 0:
        ul = UserList()
        ul = stringToThrift(rs.message, ul)
        print(f'getUserList return -> {ul.users}')
    else:
        print(f'getUserList return ResultStruct{{{rs.code}, {rs.message}}}')

    up = UserPassword('dbc', 'dbtu2017')
    setUserPasswordMsg = Message(
        version=0x01000001,
        type=MessageType.SET_USER_PASSWORD,
        body=thriftToString(up),
        host='asus')
    rs = client.handleMessage(setUserPasswordMsg)
    print(f'setUserPassword return ResultStruct{{{rs.code}, {rs.message}}}')

    getBootMenuMsg = Message(
        version=0x01000001,
        type=MessageType.GET_BOOT_MENU,
        body='')
    rs = client.handleMessage(getBootMenuMsg)
    if rs.code == 0:
        bml = BootMenuList()
        bml = stringToThrift(rs.message, bml)
        print(f'getBootMenuMsg return -> {bml.menus}')
    else:
        print(f'getBootMenuMsg return ResultStruct{{{rs.code}, {rs.message}}}')

    # bm = BootMenu(menu='wintest',superTube=True)
    bm = BootMenu(menu='ubuntu1804',superTube=False)
    setBootMenuMsg = Message(
        version=0x01000001,
        type=MessageType.SET_BOOT_MENU,
        body=thriftToString(bm),
        host='192.168.1.101')
    rs = client.handleMessage(setBootMenuMsg)
    print(f'setBootMenuMsg return ResultStruct{{{rs.code}, {rs.message}}}')

    getSmyooDeviceInfoMsg = Message(
        version=0x01000001,
        type=MessageType.GET_SMYOO_DEVICE_INFO,
        body='',
        host='asus')
    rs = client.handleMessage(getSmyooDeviceInfoMsg)
    if rs.code == 0:
        info = SmyooDeviceInfo()
        info = stringToThrift(rs.message, info)
        print(f'getSmyooDeviceInfo return -> {info}')
    else:
        print(f'getSmyooDeviceInfo return ResultStruct{{{rs.code}, {rs.message}}}')

    sdp = SmyooDevicePowerData(status=1,mcuname='asus')
    setSmyooDevicePowerMsg = Message(
        version=0x01000001,
        type=MessageType.SET_SMYOO_DEVICE_POWER,
        body=thriftToString(sdp),
        host='asus')
    rs = client.handleMessage(setSmyooDevicePowerMsg)
    print(f'setSmyooDevicePower return ResultStruct{{{rs.code}, {rs.message}}}')

    try:
        validMsg = Message(version=0x01000001,type=99,body='')
        rs = client.handleMessage(validMsg)
        print(f'handleValidMsg return ResultStruct{{{rs.code}, {rs.message}}}')
    except InvalidMessageType as e:
        print(f'InvalidMessageType: {e}')
    # Close!
    transport.close()

if __name__ == '__main__':
    try:
        main(args.server, args.port)
    except Thrift.TException as tx:
        print(f'exception: {tx.message}')
