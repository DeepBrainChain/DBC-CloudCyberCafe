import sys
sys.path.append('./gen-py')

from preset import Preset
from preset.ttypes import *
from preset.constants import *
 
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
# from thrift.transport.TTransport import TMemoryBuffer
from thrift.TSerialization import serialize, deserialize

# def encrypt(message, key):
#     dec = list(message)
#     for index, item in enumerate(dec):
#         dec[index] = chr(ord(item) ^ key)
#     return ''.join(dec)

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

# deserialize need struct and bytes
def printHostInfo(body):
    info = HostInfo()
    # tmb = TMemoryBuffer(body)
    # tbp = TBinaryProtocol(tmb)
    # info.read(tbp)
    info = deserialize(info, body)
    print(f'hostName:{info.hostName},ipAddress:{info.ipAddress}')

# serialize return type <bytes>
def makeHostInfoBody(hostName, ipAddress):
    info = HostInfo(hostName,ipAddress)
    # tmb = TMemoryBuffer()
    # tbp = TBinaryProtocol(tmb)
    # info.write(tbp)
    # return tmb.getvalue()
    return serialize(info).decode('utf-8')

def thriftToString(ts, key = 0):
    return encrypt(serialize(ts), key)

def stringToThrift(str, ts, key = 0):
    dec = decrypt(str.encode('utf-8'), key);
    return deserialize(ts, dec.encode('utf-8'))

def main():
    # Make socket
    transport = TSocket.TSocket('127.0.0.1', 9090)
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
    print(f'getHostInfo return ResultStruct{{{rs.code}, {rs.message}}}')

    getHostInfoMsg = Message(
        version=0x01000001,
        type=MessageType.GET_HOST_INFO,
        body='')
    rs = client.handleMessage(getHostInfoMsg)
    print(f'getHostInfo return ResultStruct{{{rs.code}, {rs.message}}}')
    if rs.code == 0:
        info = HostInfo()
        info = stringToThrift(rs.message, info, MessageType.GET_HOST_INFO)
        print(f'hostName:{info.hostName}, ipAddress:{info.ipAddress}')

    setInfo = HostInfo('jerry','192.168.1.111')
    setHostInfoMsg = Message(
        version=0x01000001,
        type=MessageType.SET_HOST_INFO,
        body=thriftToString(setInfo, MessageType.SET_HOST_INFO))
    rs = client.handleMessage(setHostInfoMsg)
    print(f'setHostInfo return ResultStruct{{{rs.code}, {rs.message}}}')

    rs = client.handleMessage(getHostInfoMsg)
    print(f'getHostInfo return ResultStruct{{{rs.code}, {rs.message}}}')
    if rs.code == 0:
        info = HostInfo()
        info = stringToThrift(rs.message, info, MessageType.GET_HOST_INFO)
        print(f'hostName:{info.hostName}, ipAddress:{info.ipAddress}')

    getUserListMsg = Message(
        version=0x01000001,
        type=MessageType.GET_USER_LIST,
        body='')
    rs = client.handleMessage(getUserListMsg)
    print(f'getUserList return ResultStruct{{{rs.code}, {rs.message}}}')
    if rs.code == 0:
        ul = UserList()
        ul = stringToThrift(rs.message, ul, MessageType.GET_USER_LIST)
        print(f'user list: {ul.users}')

    up = UserPassword('dbc', 'dbc')
    setUserPasswordMsg = Message(
        version=0x01000001,
        type=MessageType.SET_USER_PASSWORD,
        body=thriftToString(up, MessageType.SET_USER_PASSWORD))
    rs = client.handleMessage(setUserPasswordMsg)
    print(f'setUserPassword return ResultStruct{{{rs.code}, {rs.message}}}')

    try:
        validMsg = Message(version=0x01000001,type=99,body='')
        rs = client.handleMessage(validMsg)
        print(f'handleValidMsg return ResultStruct{{{rs.code}, {rs.message}}}')
    except InvalidMessageType as e:
        print(f'InvalidMessageType: {e}')

    # Close!
    transport.close()
    print('socket close')

if __name__ == '__main__':
    try:
        main()
    except Thrift.TException as tx:
        print(f'exception: {tx.message}')
