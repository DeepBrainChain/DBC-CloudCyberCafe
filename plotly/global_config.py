# config.py

import diskcache
import json
import os
import pandas as pd
from deprecated import deprecated

cache = diskcache.Cache("./db")
host_csv_file = './db/host.csv'
os_csv_file = './db/os.csv'
data_disk_csv_file = './db/data_disk.csv'
boot_menu_csv_file = './db/boot_menu.csv'

config_file = './config.json'

def _init():
  print('global config initionlize')
  # _global_config will be deprecated later
  global _global_config
  global _df_hosts
  global _df_os
  global _df_data_disk
  global _df_boot_menu

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
    os.rename(config_file, f'{config_file}.bak')

  # move config json to diskcache
  move_config_json_to_diskcache()
  # what if csv file not existed ?
  init_table_data_csv()
  _df_hosts = pd.read_csv(host_csv_file)
  _df_os = pd.read_csv(os_csv_file)
  _df_data_disk = pd.read_csv(data_disk_csv_file)
  _df_boot_menu = pd.read_csv(boot_menu_csv_file)

def read_config_file():
  global _global_config
  with open(config_file, 'r') as f:
    _global_config = json.load(f)
    # _global_config = json.loads(f.read())

@deprecated(version='0.0.0-alpha.2', reason='This method is deprecated')
def write_config_file():
  file_content = json.dumps(_global_config)
  with open(config_file, "w") as f:
    f.write(file_content)

@deprecated(version='0.0.0-alpha.2', reason='This method is deprecated')
def set_value(key, value):
  _global_config[key] = value

@deprecated(version='0.0.0-alpha.2', reason='This method is deprecated')
def get_value(key, defValue=None):
  try:
    return _global_config[key]
  except:
    # print('read ', key, ' error')
    return defValue

# host table
def get_hosts_dataframe():
  global _df_hosts
  return _df_hosts

def add_row_to_hosts(series):
  global _df_hosts
  _df_hosts = pd.concat([_df_hosts, series.to_frame().T], ignore_index=True)

def save_hosts_to_csv():
  global _df_hosts
  _df_hosts.to_csv(host_csv_file, index=False)

# operation system table
def get_os_dataframe():
  global _df_os
  return _df_os

def add_row_to_os(series):
  global _df_os
  _df_os = pd.concat([_df_os, series.to_frame().T], ignore_index=True)

def save_os_to_csv():
  global _df_os
  _df_os.to_csv(os_csv_file, index=False)

# data disk table
def get_data_disk_dataframe():
  global _df_data_disk
  return _df_data_disk

def add_row_to_data_disk(series):
  global _df_data_disk
  _df_data_disk = pd.concat([_df_data_disk, series.to_frame().T], ignore_index=True)

def save_data_disk_to_csv():
  global _df_data_disk
  _df_data_disk.to_csv(data_disk_csv_file, index=False)

# boot menu table
def get_boot_menu_dataframe():
  global _df_boot_menu
  return _df_boot_menu

def add_row_to_boot_menu(series):
  global _df_boot_menu
  _df_boot_menu = pd.concat([_df_boot_menu, series.to_frame().T], ignore_index=True)

def save_boot_menu_to_csv():
  global _df_boot_menu
  _df_boot_menu.to_csv(boot_menu_csv_file, index=False)

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

# move config.json to diskcache and csv
def move_config_json_to_diskcache():
  global _global_config
  global cache
  # dhcp server
  dhcp_server = _global_config['dhcp_server']
  if get_cache('dhcp_network_name') is None:
    cache['dhcp_network_name'] = dhcp_server['network_name']
  if get_cache('dhcp_interface') is None:
    cache['dhcp_interface'] = dhcp_server['interface']
  if get_cache('dhcp_subnet') is None:
    cache['dhcp_subnet'] = dhcp_server['subnet']
  if get_cache('dhcp_subnet_mask') is None:
    cache['dhcp_subnet_mask'] = dhcp_server['subnet_mask']
  if get_cache('dhcp_range_from') is None:
    cache['dhcp_range_from'] = dhcp_server['range_from']
  if get_cache('dhcp_range_to') is None:
    cache['dhcp_range_to'] = dhcp_server['range_to']
  if get_cache('dhcp_routers') is None:
    cache['dhcp_routers'] = dhcp_server['routers']
  if get_cache('dhcp_dns_servers') is None:
    cache['dhcp_dns_servers'] = dhcp_server['dns_servers']
  if get_cache('dhcp_broadcast_address') is None:
    cache['dhcp_broadcast_address'] = dhcp_server['broadcast_address']
  if get_cache('dhcp_filename') is None:
    cache['dhcp_filename'] = dhcp_server['filename']
  if get_cache('dhcp_next_server') is None:
    cache['dhcp_next_server'] = dhcp_server['next_server']
  # http server
  http_server = _global_config['http_server']
  if get_cache('http_root_path') is None:
    cache['http_root_path'] = http_server['root_path']
  if get_cache('http_base_url') is None:
    cache['http_base_url'] = http_server['base_url']
  # iscsi setting
  iscsi_setting = _global_config['iscsi_setting']
  if get_cache('iscsi_server') is None:
    cache['iscsi_server'] = iscsi_setting['server']
  if get_cache('iscsi_target_prefix') is None:
    cache['iscsi_target_prefix'] = iscsi_setting['iscsi_target_prefix']
  if get_cache('iscsi_initiator_iqn') is None:
    cache['iscsi_initiator_iqn'] = iscsi_setting['initiator_iqn']
  # storage
  if get_cache('volume_group_name') is None:
    cache['volume_group_name'] = _global_config['volume_group_name']

def init_table_data_csv():
  global _global_config
  # host table
  if not os.path.exists(host_csv_file):
    df_hosts = pd.DataFrame.from_dict(_global_config['hosts'])
    df_hosts.to_csv(host_csv_file, index=False)
  # os table
  if not os.path.exists(os_csv_file):
    df_os = pd.DataFrame.from_dict(_global_config['operation_system'])
    df_os.to_csv(os_csv_file, index=False)
  # data disk table
  if not os.path.exists(data_disk_csv_file):
    df_data_disk = pd.DataFrame.from_dict(_global_config['data_disk'])
    df_data_disk.to_csv(data_disk_csv_file, index=False)
  # boot menu table
  if not os.path.exists(boot_menu_csv_file):
    df_boot_menu = pd.DataFrame.from_dict(_global_config['boot_menu'])
    df_boot_menu.to_csv(boot_menu_csv_file, index=False)
