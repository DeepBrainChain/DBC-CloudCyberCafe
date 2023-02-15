#ifndef PRESET_ERROR_CODE_H
#define PRESET_ERROR_CODE_H

enum ErrorCode {
  // success
  SUCCESS = 0,
  // start of error code
  ERROR_BEGIN = 10001,
  // unknown error
  UNKNOWN_ERROR,
  // invalid message body
  INVALID_MESSAGE_BODY,
  // get host info failed
  GET_HOST_INFO_FAILED = 10101,
  // set host info failed
  SET_HOST_INFO_FAILED = 10201,
  // get user list failed
  GET_USER_LIST_FAILED = 10301,
  // set user password failed
  SET_USER_PASSWORD_FAILED = 10401,
  // end of error code
  ERROR_END = 20000
};

#endif  // PRESET_ERROR_CODE_H
