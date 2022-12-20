# config.py

import json
import os

config_file = './config.json'

def _init():
  global _global_config
  _global_config = {
    "dhcp_server":{
      "network_name":"dbc",
      "interface":"eth0",
      "subnet":"192.168.119.0",
      "subnet_mask":"255.255.255.0",
      "range_from":"192.168.119.100",
      "range_to":"192.168.119.200",
      "routers":"192.168.119.1",
      "dns_servers":"223.5.5.5",
      "broadcast_address":"192.168.119.255",
      "filename":"http://192.168.119.2:8080/ipxe/boot.ipxe",
      "next_server":"192.168.119.2"
    },
    "http_server":{
      "root_path":"/var/www/file",
      "base_url":"http://192.168.119.2:8080"
    },
    "iscsi_setting":{
      "server":"192.168.119.2",
      "iscsi_target_prefix":"iqn.2022-10.org.dbc.iscsi",
      "initiator_iqn":"iqn.2022-10.org.dbc.iscsi:global.client",
    },
    "volume_group_name":"bootpool",
    "hosts":{
      "host_name":[],
      "ip":[],
      "mac":[],
      "default_menu":[],
      "super_tube":[]
    },
    "operation_system":{
      "name":[],
      "description":[],
      "capacity":[]
    },
    "data_disk":{
      "name":[],
      "description":[],
      "capacity":[]
    },
    "boot_menu":{
      "name":[],
      "operation_system":[],
      "data_disk":[]
    }
  }
  if os.path.isfile(config_file):
    read_config_file()

def read_config_file():
  global _global_config
  with open(config_file, 'r') as f:
    _global_config = json.load(f)
    # _global_config = json.loads(f.read())

def write_config_file():
  file_content = json.dumps(_global_config)
  with open(config_file, "w") as f:
    f.write(file_content)

def set_value(key, value):
  _global_config[key] = value

def get_value(key, defValue=None):
  try:
    return _global_config[key]
  except:
    # print('read ', key, ' error')
    return defValue
