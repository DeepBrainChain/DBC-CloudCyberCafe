#include "preset_handler.h"

#include <thrift/protocol/TBinaryProtocol.h>
#include <thrift/transport/TBufferTransports.h>

#include "cross_platform_func.h"

using namespace ::occ;

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

PresetHandler::PresetHandler() {
  getHostInfo(info_);
}

void PresetHandler::ping(std::string& _return) {
  // Your implementation goes here
  _return = u8"pong";
  printf("ping\n");
}

void PresetHandler::handleMessage(ResultStruct& _return, const Message& msg) {
  // Your implementation goes here
  // printf("handleMessage\n");
  switch(msg.type) {
    case MessageType::PING:
      _return.code = 0;
      _return.message = u8"pong";
      printf("handle ping message\n");
      break;
    case MessageType::GET_HOST_INFO:
      _return.code = 0;
      _return.message = ThriftToString(info_, msg.type);
      printf("handle get host info message\n");
      break;
    case MessageType::SET_HOST_INFO:
      {
        HostInfo info;
        if (StringToThrift(msg.body, info, msg.type)) {
          info_.hostName = info.hostName;
          info_.ipAddress = info.ipAddress;
          _return.code = 0;
          _return.message = u8"success";
        } else {
          _return.code = 1;
          _return.message = u8"invalid message body";
        }
      }
      printf("handle set host info message\n");
      break;
    case MessageType::GET_USER_LIST:
      {
        std::vector<std::string> users;
        _return.code = enumUserName(users);
        if (_return.code == 0) {
          UserList ul;
          ul.__set_users(users);
          _return.message = ThriftToString(ul, msg.type);
        } else {
          _return.message = u8"failed to get user list";
        }
      }
      printf("handle get user list message\n");
      break;
    case MessageType::SET_USER_PASSWORD:
      {
        UserPassword up;
        if (StringToThrift(msg.body, up, msg.type)) {
          _return.code = setUserPassword(up.userName, up.password);
          if (_return.code == 0)
            _return.message = u8"success";
          else
            _return.message = getErrorMessage(_return.code);
        } else {
          _return.code = 1;
          _return.message = u8"invalid message body";
        }
      }
      printf("handle set user password message\n");
      break;
    default:
      InvalidMessageType io;
      io.whatType = msg.type;
      io.why = u8"Invalid Operation";
      printf("handle invalid message\n");
      throw io;
  }
  // _return.code = 0;
  // _return.message = "success";
}
