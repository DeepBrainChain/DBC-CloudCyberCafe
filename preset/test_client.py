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

# def thriftToString(ts, key = 0):
#     return encrypt(serialize(ts), key)

def thriftToString(ts):
    return serialize(ts).decode('utf-8')

# def stringToThrift(str, ts, key = 0):
#     dec = decrypt(str.encode('utf-8'), key);
#     return deserialize(ts, dec.encode('utf-8'))

def stringToThrift(str, ts):
    return deserialize(ts, str.encode('utf-8'))

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
    print(f'pingMsg return ResultStruct{{{rs.code}, {rs.message}}}')

    getHostInfoMsg = Message(
        version=0x01000001,
        type=MessageType.GET_HOST_INFO,
        body='')
    rs = client.handleMessage(getHostInfoMsg)
    if rs.code == 0:
        info = HostInfo()
        info = stringToThrift(rs.message, info)
        print(f'getHostInfo return -> {info}')
    else:
        print(f'getHostInfo return ResultStruct{{{rs.code}, {rs.message}}}')

    setInfo = HostInfo('jerry','192.168.1.111')
    setHostInfoMsg = Message(
        version=0x01000001,
        type=MessageType.SET_HOST_INFO,
        body=thriftToString(setInfo))
    rs = client.handleMessage(setHostInfoMsg)
    print(f'setHostInfo return ResultStruct{{{rs.code}, {rs.message}}}')

    rs = client.handleMessage(getHostInfoMsg)
    if rs.code == 0:
        info = HostInfo()
        info = stringToThrift(rs.message, info)
        print(f'getHostInfo return -> {info}')
    else:
        print(f'getHostInfo return ResultStruct{{{rs.code}, {rs.message}}}')

    getUserListMsg = Message(
        version=0x01000001,
        type=MessageType.GET_USER_LIST,
        body='')
    rs = client.handleMessage(getUserListMsg)
    if rs.code == 0:
        ul = UserList()
        ul = stringToThrift(rs.message, ul)
        print(f'getUserList return -> {ul}')
    else:
        print(f'getUserList return ResultStruct{{{rs.code}, {rs.message}}}')

    up = UserPassword('dbc', 'dbtu2017')
    setUserPasswordMsg = Message(
        version=0x01000001,
        type=MessageType.SET_USER_PASSWORD,
        body=thriftToString(up))
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
