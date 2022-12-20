#include <iostream>
#include <string>

#include <thrift/protocol/TBinaryProtocol.h>
#include <thrift/transport/TSocket.h>
#include <thrift/transport/TTransportUtils.h>

#include "Preset.h"

using namespace std;
using namespace apache::thrift;
using namespace apache::thrift::protocol;
using namespace apache::thrift::transport;

using namespace occ;

static std::string encrypt(const std::string& buff, int key) {
  std::string enc;
  enc.resize(buff.length());
  for (int i = 0; i < buff.length(); ++i)
    enc[i] = buff[i] ^ key;
  return enc;
}

static std::string decrypt(const std::string& buff, int key) {
  std::string enc;
  enc.resize(buff.length());
  for (int i = 0; i < buff.length(); ++i)
    enc[i] = buff[i] ^ key;
  return enc;
}

template<typename ThriftStruct>
std::string ThriftToString(const ThriftStruct& ts, int key = 0) {
  using namespace apache::thrift::transport;  // NOLINT
  using namespace apache::thrift::protocol;  // NOLINT

  std::shared_ptr<TMemoryBuffer> buffer = std::make_shared<TMemoryBuffer>();
  std::shared_ptr<TTransport> trans(buffer);

  TBinaryProtocol protocol(trans);
  ts.write(&protocol);

  uint8_t* buf;
  uint32_t size;
  buffer->getBuffer(&buf, &size);
  return encrypt(std::string((char*)buf, (unsigned int)size), key);  // NOLINT
}

template<typename ThriftStruct>
bool StringToThrift(const std::string& buff, ThriftStruct& ts, int key = 0) {
  std::string dec = decrypt(buff, key);
  using namespace apache::thrift::transport;  // NOLINT
  using namespace apache::thrift::protocol;  // NOLINT
  try {
    std::shared_ptr<TMemoryBuffer> buffer = std::make_shared<TMemoryBuffer>();
    buffer->write((const uint8_t*)dec.data(), dec.size());
    std::shared_ptr<TTransport> trans(buffer);
    TBinaryProtocol protocol(trans);
    ts.read(&protocol);
  } catch (TProtocolException& io) {
    printf("read invalid data\n");
    return false;
  }
  return true;
}

int main() {
  std::shared_ptr<TTransport> socket(new TSocket("localhost", 9090));
  std::shared_ptr<TTransport> transport(new TBufferedTransport(socket));
  std::shared_ptr<TProtocol> protocol(new TBinaryProtocol(transport));
  PresetClient client(protocol);

  try {
    transport->open();

    std::string pingRes;
    client.ping(pingRes);
    cout << "ping:" << pingRes << endl;

    Message getHostInfoMsg;
    HostInfo info;
    ResultStruct rs;
    getHostInfoMsg.__set_version(0x01000001);
    getHostInfoMsg.__set_type(MessageType::GET_HOST_INFO);
    getHostInfoMsg.__set_body("");
    client.handleMessage(rs, getHostInfoMsg);
    cout << "getHostInfo return ResultStruct{" << rs.code << ", " << rs.message << "}" << endl;
    if (rs.code == 0) {
      StringToThrift(rs.message, info, MessageType::GET_HOST_INFO);
      printf("hostName:%s, ipAddress:%s\n", info.hostName.c_str(), info.ipAddress.c_str());
    }

    info.__set_hostName("jerry");
    info.__set_ipAddress("192.168.1.222");
    Message setHostInfoMsg;
    setHostInfoMsg.__set_version(0x01000001);
    setHostInfoMsg.__set_type(MessageType::SET_HOST_INFO);
    setHostInfoMsg.__set_body(ThriftToString(info, MessageType::SET_HOST_INFO));
    client.handleMessage(rs, setHostInfoMsg);
    cout << "setHostInfo return ResultStruct{" << rs.code << ", " << rs.message << "}" << endl;

    client.handleMessage(rs, getHostInfoMsg);
    cout << "getHostInfo return ResultStruct{" << rs.code << ", " << rs.message << "}" << endl;
    if (rs.code == 0) {
      StringToThrift(rs.message, info, MessageType::GET_HOST_INFO);
      printf("hostName:%s, ipAddress:%s\n", info.hostName.c_str(), info.ipAddress.c_str());
    }

    Message getUserList;
    getUserList.__set_version(0x01000001);
    getUserList.__set_type(MessageType::GET_USER_LIST);
    getHostInfoMsg.__set_body("");
    client.handleMessage(rs, getUserList);
    cout << "getUserList return ResultStruct{" << rs.code << ", " << rs.message << "}" << endl;
    if (rs.code == 0) {
      UserList ul;
      StringToThrift(rs.message, ul, MessageType::GET_USER_LIST);
      cout << "userList:";
      for (const auto& item : ul.users)
        cout << "<" << item << ">";
      cout << endl;
    }

    UserPassword up;
    up.__set_userName("dbc");
    up.__set_password("dbc");
    Message setUserPassword;
    setUserPassword.__set_version(0x01000001);
    setUserPassword.__set_type(MessageType::SET_USER_PASSWORD);
    setUserPassword.__set_body(ThriftToString(up, MessageType::SET_USER_PASSWORD));
    client.handleMessage(rs, setUserPassword);
    cout << "setUserPassword return ResultStruct{" << rs.code << ", " << rs.message << "}" << endl;

    try {
      Message invalidMsg;
      invalidMsg.__set_version(0x01000001);
      invalidMsg.__set_type(99);
      invalidMsg.__set_body("");
      client.handleMessage(rs, invalidMsg);
      cout << "handle invalid message return ResultCode{" << rs.code << ", " << rs.message << "}" << endl;
    } catch (InvalidMessageType& io) {
      cout << "InvalidMessageType: whatType=" << io.whatType << ", why=" << io.why << endl;
      // or using generated operator<<: cout << io << endl;
      // or by using std::exception native method what(): cout << io.what() << endl;
    }

    transport->close();
  } catch (TException& tx) {
    cout << "ERROR: " << tx.what() << endl;
  }
  return 0;
}
