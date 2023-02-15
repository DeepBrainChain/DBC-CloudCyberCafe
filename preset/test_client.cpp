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

template <typename ThriftStruct>
std::string ThriftToString(const ThriftStruct& ts) {
  using namespace apache::thrift::transport;  // NOLINT
  using namespace apache::thrift::protocol;   // NOLINT

  std::shared_ptr<TMemoryBuffer> buffer = std::make_shared<TMemoryBuffer>();
  std::shared_ptr<TTransport> trans(buffer);

  TBinaryProtocol protocol(trans);
  ts.write(&protocol);

  uint8_t* buf;
  uint32_t size;
  buffer->getBuffer(&buf, &size);
  // return encrypt(std::string((char*)buf, (unsigned int)size), key);
  return std::string((char*)buf, (unsigned int)size);  // NOLINT
}

template <typename ThriftStruct>
bool StringToThrift(const std::string& buff, ThriftStruct& ts) {
  // std::string dec = decrypt(buff, key);
  using namespace apache::thrift::transport;  // NOLINT
  using namespace apache::thrift::protocol;   // NOLINT
  try {
    std::shared_ptr<TMemoryBuffer> buffer = std::make_shared<TMemoryBuffer>();
    buffer->write((const uint8_t*)buff.data(), buff.size());
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
    if (rs.code == 0) {
      StringToThrift(rs.message, info);
      printf("getHostInfo return -> HostInfo{hostName='%s', ipAddress='%s'}\n",
        info.hostName.c_str(), info.ipAddress.c_str());
    } else {
      cout << "getHostInfo return ResultStruct{" << rs.code << ", " << rs.message << "}" << endl;
    }

    info.__set_hostName("jerry");
    info.__set_ipAddress("192.168.1.222");
    Message setHostInfoMsg;
    setHostInfoMsg.__set_version(0x01000001);
    setHostInfoMsg.__set_type(MessageType::SET_HOST_INFO);
    setHostInfoMsg.__set_body(ThriftToString(info));
    client.handleMessage(rs, setHostInfoMsg);
    cout << "setHostInfo return ResultStruct{" << rs.code << ", " << rs.message << "}" << endl;

    client.handleMessage(rs, getHostInfoMsg);
    if (rs.code == 0) {
      StringToThrift(rs.message, info);
      printf("getHostInfo return -> HostInfo{hostName='%s', ipAddress='%s'}\n",
        info.hostName.c_str(), info.ipAddress.c_str());
    } else {
      cout << "getHostInfo return ResultStruct{" << rs.code << ", " << rs.message << "}" << endl;
    }

    Message getUserList;
    getUserList.__set_version(0x01000001);
    getUserList.__set_type(MessageType::GET_USER_LIST);
    getHostInfoMsg.__set_body("");
    client.handleMessage(rs, getUserList);
    if (rs.code == 0) {
      UserList ul;
      StringToThrift(rs.message, ul);
      cout << "getUserList return -> UserList{users=[";
      int count = 0;
      for (const auto& item : ul.users) {
        if (count++ != 0) cout << ",";
        cout << "'" << item << "'";
      }
      cout << "]}" << endl;
    } else {
      cout << "getUserList return ResultStruct{" << rs.code << ", " << rs.message << "}" << endl;
    }

    UserPassword up;
    up.__set_userName("dbc");
    up.__set_password("dbtu2017");
    Message setUserPassword;
    setUserPassword.__set_version(0x01000001);
    setUserPassword.__set_type(MessageType::SET_USER_PASSWORD);
    setUserPassword.__set_body(ThriftToString(up));
    client.handleMessage(rs, setUserPassword);
    // rs.message 若包含中文字符，在 Windows 上输出可能会乱码，因为 thrift 采用 UTF-8 编码。
    // 修改方式: 将 rs.message 从 UTF-8 转成 Unicode 输出宽字符，或者转成 GBK 输出。
    // wstring2String(string2Wstring(rs.message, CP_UTF8), CP_ACP)
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
