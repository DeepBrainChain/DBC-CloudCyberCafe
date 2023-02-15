from enum import Enum

class ErrorCode(Enum):
  # success
  SUCCESS = 0,
  # start of error code
  ERROR_BEGIN = 1
  # unknown error
  UNKNOWN_ERROR = 2
  # an exception occurred
  EXCEPTION_OCCURRED = 3
  # timeout
  TIMEOUT = 4
  # unknown message type
  UNKNOWN_MESSAGE_TYPE = 5
  # unknown host to sending to
  UNKNOWN_HOST = 6
  # could not connect to 192.168.1.55:9090
  CONNECT_FAILED = 7
  # plotly: unknown notify message type
  PLOTLY_UNKNOWN_NOTIFY_TYPE = 1001
  # plotly: boot menu not existed in SET_BOOT_MENU request
  PLOTLY_BOOT_MENU_NOT_EXISTED = 1101
  # plotly: invalid power status in SET_SMYOO_DEVICE_POWER request
  PLOTLY_INVALID_SMYOO_POWER_STATUS = 1201
  # plotly: set smyoo device power failed
  PLOTLY_SET_SMYOO_HOST_POWER_FAILED = 1202
  # smyoo: could not find host in smyoo
  SMYOO_HOST_NOT_EXISTED = 2001
  # end of error code
  ERROR_END = 10000
