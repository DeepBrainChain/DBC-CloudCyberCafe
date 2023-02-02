# config.py

import json
import os
import queue
import diskcache

cache = diskcache.Cache("./cache")

config_file = './config.json'
thrift_queue = queue.Queue(10)

def _init():
  global _global_config
  _global_config = {
    "dhcp_server":{
      "network_name":"dbc",
      "interface":"eth0",
      "subnet":"192.168.1.0",
      "subnet_mask":"255.255.255.0",
      "range_from":"192.168.1.100",
      "range_to":"192.168.1.200",
      "routers":"192.168.1.1",
      "dns_servers":"223.5.5.5",
      "broadcast_address":"192.168.1.255",
      "filename":"http://192.168.1.2:8080/ipxe/boot.ipxe",
      "next_server":"192.168.1.2"
    },
    "http_server":{
      "root_path":"/var/www/file",
      "base_url":"http://192.168.1.2:8080"
    },
    "iscsi_setting":{
      "server":"192.168.1.2",
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

def find_host_name(hostname=None, ip=None, mac=None):
  hosts_data = get_value('hosts')
  if hostname and hostname in hosts_data['host_name']:
    return hostname
  if ip is None and mac is None:
    return None
  if mac and mac in hosts_data['mac']:
    index_num = hosts_data['mac'].index(mac)
    return hosts_data['host_name'][index_num]
  if ip and ip in hosts_data['ip']:
    index_num = hosts_data['ip'].index(ip)
    return hosts_data['host_name'][index_num]
  return None

def find_host_ip(hostname=None, ip=None, mac=None):
  hosts_data = get_value('hosts')
  if ip and ip in hosts_data['ip']:
    return ip
  if hostname is None and mac is None:
    return None
  if mac and mac in hosts_data['mac']:
    index_num = hosts_data['mac'].index(mac)
    return hosts_data['ip'][index_num]
  if hostname and hostname in hosts_data['host_name']:
    index_num = hosts_data['host_name'].index(hostname)
    return hosts_data['ip'][index_num]
  return None

def push_queue(item):
  global thrift_queue
  thrift_queue.put(item)

def pop_queue():
  global thrift_queue
  msg = thrift_queue.get()
  return msg
  # if not thrift_queue.empty():
  #   return thrift_queue.get()
  # return None

def pop_queue_nowait():
  global thrift_queue
  return thrift_queue.get_nowait()

def queue_size():
  global thrift_queue
  return thrift_queue.qsize()

def set_cache(key, value, expire=None):
  global cache
  # cache.set(key, value, expire=3,read=True,tag='data',retry=True)
  return cache.set(key, value, expire=expire)

def get_cache(key, default=None):
  global cache
  # return cache.get(key,default="",expire_time=True,tag=True)
  return cache.get(key,default=default)

def delete_cache(key):
  global cache
  return cache.delete(key)

def pop_cache(key):
  global cache
  return cache.pop(key)

def get_smyoo_device_info(hostname):
  devicesContent = get_cache('smyoo_devices',default='')
  if len(devicesContent) == 0:
    return None
  try:
    devices = json.loads(devicesContent)
    for device in devices:
      if device['mcuname'] == hostname:
        return device
  except:
    print('get smyoo host mcuid failed')
  return None
