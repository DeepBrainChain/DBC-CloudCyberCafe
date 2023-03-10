/**
 * The first thing to know about are types. The available types in Thrift are:
 *
 *  bool        Boolean, one byte
 *  i8 (byte)   Signed 8-bit integer
 *  i16         Signed 16-bit integer
 *  i32         Signed 32-bit integer
 *  i64         Signed 64-bit integer
 *  double      64-bit floating point value
 *  string      String
 *  binary      Blob (byte array)
 *  map<t1,t2>  Map from one type to another
 *  list<t1>    Ordered list of one type
 *  set<t1>     Set of unique elements of one type
 *
 * Did you also notice that Thrift supports C style comments?
 */

namespace cpp occ

struct ResultStruct {
  1: required i32 code,
  2: required string message
}

enum MessageType {
  PING = 1,
  GET_HOST_INFO = 2,
  SET_HOST_INFO = 3,
  GET_USER_LIST = 4,
  SET_USER_PASSWORD = 5,
  GET_BOOT_MENU = 32,
  SET_BOOT_MENU = 33,
  GET_SMYOO_DEVICE_INFO = 34,
  SET_SMYOO_DEVICE_POWER = 35
}

struct Message {
  1: required i32 version,
  2: required i32 type,
  3: required string body,
  4: optional string host
}

struct HostInfo {
  1: required string hostName,
  2: required string ipAddress
}

struct UserList {
  1: required list<string> users
}

struct UserPassword {
  1: required string userName,
  2: required string password
}

struct BootMenuList {
  1: required list<string> menus
}

struct BootMenu {
  1: required string menu,
  2: required bool superTube
}

struct SmyooDeviceInfo {
  1: required string mcuname,
  2: required string note,
  3: required i32 isonline,
  4: required i32 power,
  5: required string mcuid
}

struct SmyooDevicePowerData {
  1: required i32 status,
  2: optional string mcuid,
  3: optional string mcuname
}

/**
 * Structs can also be exceptions, if they are nasty.
 */
exception InvalidMessageType {
  1: i32 whatType,
  2: string why
}

service Preset {
  string ping(),
  ResultStruct handleMessage(1:Message msg) throws (1:InvalidMessageType ouch)
}
