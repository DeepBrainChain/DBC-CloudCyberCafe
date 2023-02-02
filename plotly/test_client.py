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

    getBootMenuMsg = Message(
        version=0x01000001,
        type=MessageType.GET_BOOT_MENU,
        body='')
    rs = client.handleMessage(getBootMenuMsg)
    print(f'getBootMenuMsg return ResultStruct{{{rs.code}, {rs.message}}}')
    if rs.code == 0:
        bml = BootMenuList()
        bml = stringToThrift(rs.message, bml, MessageType.GET_BOOT_MENU)
        print(f'BootMenuList:{bml.menus}')

    # bm = BootMenu(menu='wintest',superTube=True)
    bm = BootMenu(menu='ubuntu1804',superTube=False)
    setBootMenuMsg = Message(
        version=0x01000001,
        type=MessageType.SET_BOOT_MENU,
        body=thriftToString(bm, MessageType.SET_BOOT_MENU),
        host='192.168.1.101')
    rs = client.handleMessage(setBootMenuMsg)
    print(f'setBootMenuMsg return ResultStruct{{{rs.code}, {rs.message}}}')

    getSmyooDeviceInfoMsg = Message(
        version=0x01000001,
        type=MessageType.GET_SMYOO_DEVICE_INFO,
        body='',
        host='asus')
    rs = client.handleMessage(getSmyooDeviceInfoMsg)
    print(f'getSmyooDeviceInfo return ResultStruct{{{rs.code}, {rs.message}}}')
    if rs.code == 0:
        info = SmyooDeviceInfo()
        info = stringToThrift(rs.message, info, MessageType.GET_SMYOO_DEVICE_INFO)
        print(f'SmyooDeviceInfo:{info}')

    sdp = SmyooDevicePowerData(status=1,mcuname='asus')
    setSmyooDevicePowerMsg = Message(
        version=0x01000001,
        type=MessageType.SET_SMYOO_DEVICE_POWER,
        body=thriftToString(sdp, MessageType.SET_SMYOO_DEVICE_POWER),
        host='asus')
    rs = client.handleMessage(setSmyooDevicePowerMsg)
    print(f'setSmyooDevicePower return ResultStruct{{{rs.code}, {rs.message}}}')
    # Close!
    transport.close()

if __name__ == '__main__':
    try:
        main()
    except Thrift.TException as tx:
        print(f'exception: {tx.message}')
