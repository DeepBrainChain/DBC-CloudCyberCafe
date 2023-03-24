import json
import os
import pandas as pd

import dhcp
import global_config
import ipxe
import iscsi
import lvm2
import util

from smyoo import Smyoo
from error_code import ErrorCode

global_config._init()
smyoo = Smyoo()

def update_ipxe_cfg(mac_addr, default_boot, super_tube):
  root_path = global_config.get_cache('http_root_path')
  format_mac = ''.join(mac_addr.split(':')).lower()
  iscsi_initiator_iqn = global_config.get_cache('iscsi_initiator_iqn')
  iscsi_target_prefix = global_config.get_cache('iscsi_target_prefix')
  df_boot_menu = global_config.get_boot_menu_dataframe()
  boot_menu_list = df_boot_menu['name'].tolist()
  ipxe.edit_ipxe_cfg(os.path.join(root_path, 'ipxe', 'cfg'), format_mac,
    iscsi_initiator_iqn, iscsi_target_prefix,
    boot_menu_list, default_boot, super_tube)

def remove_snapshot_storage_item_of_host(mac_addr, boot_item):
  iscsi.delete_snap_iscsi_objects_by_host(
    global_config.get_cache('iscsi_target_prefix'), boot_item, mac_addr)

  df_boot_menu = global_config.get_boot_menu_dataframe()
  menu_index = df_boot_menu['name'].tolist().index(boot_item)
  disks = []
  disks.append(df_boot_menu.iloc[menu_index]['operation_system'])
  disks.extend(df_boot_menu.iloc[menu_index]['data_disk'].split(','))
  disks = util.deduplication(disks)

  volume_group = global_config.get_cache('volume_group_name')

  for index, disk in enumerate(disks):
    snap_disk = f'{disk}_{mac_addr}'
    lvm2.remove_logical_volume(volume_group, snap_disk)

def remove_snapshot_storage_of_host(mac_addr):
  df_boot_menu = global_config.get_boot_menu_dataframe()
  boot_menu_list = df_boot_menu['name'].tolist()
  for boot_item in boot_menu_list:
    remove_snapshot_storage_item_of_host(mac_addr, boot_item)

def reset_host_boot_menu(mac_addr, boot_item, snap_lv_size):
  iscsi_target_prefix = global_config.get_cache('iscsi_target_prefix')
  iscsi.delete_snap_iscsi_objects_by_host(iscsi_target_prefix,
    boot_item, mac_addr)

  df_boot_menu = global_config.get_boot_menu_dataframe()
  boot_menu_list = df_boot_menu['name'].tolist()
  if boot_item not in boot_menu_list:
    return 1, 'boot item not existed'

  menu_index = boot_menu_list.index(boot_item)
  disks = []
  disks.append(df_boot_menu.iloc[menu_index]['operation_system'])
  disks.extend(df_boot_menu.iloc[menu_index]['data_disk'].split(','))
  disks = util.deduplication(disks)

  volume_group = global_config.get_cache('volume_group_name')
  lv_list = lvm2.get_logical_volume_list(volume_group)

  for index, disk in enumerate(disks):
    snap_disk = f'{disk}_{mac_addr}'
    # if snap_disk in lv_list:
    lvm2.remove_logical_volume(volume_group, snap_disk)
    result_code, result_message = lvm2.create_snapshot_logical_volume(
      volume_group, disk, mac_addr, snap_lv_size)
    if result_code != 0:
      return result_code, result_message
    disks[index] = snap_disk

  initiator_iqn = '%s:sn.%s.%s' % (iscsi_target_prefix, boot_item, mac_addr)
  result_code, result_message = iscsi.create_iscsi_target(boot_item, disks,
    iscsi_target_prefix, initiator_iqn)
  if result_code != 0:
    for disk in disks:
      lvm2.remove_logical_volume(volume_group, disk)
    return result_code, result_message
  return 0, 'reset successful'

def host_add_item(macaddr, hostname, ipaddr, default_menu, super_tube):
  df_boot_menu = global_config.get_boot_menu_dataframe()
  boot_menu_list = df_boot_menu['name'].tolist()
  if default_menu not in boot_menu_list:
    return 1, 'invalid boot menu item', None

  df_hosts = global_config.get_hosts_dataframe()
  mac_list = df_hosts['mac'].tolist()
  index = None
  if macaddr in mac_list:
    index = mac_list.index(macaddr)
  if util.isin(hostname, df_hosts['host_name'].tolist(), index):
    return 1, 'host name duplicated', None
  if util.isin(ipaddr, df_hosts['ip'].tolist(), index):
    return 1, 'ip address duplicated', None

  result_code, result_message = dhcp.bind_mac_address_and_ip_address(
    global_config.get_cache('dhcp_network_name'), hostname, macaddr, ipaddr)
  if result_code != 0:
    return result_code, 'bind mac and ip failed', None

  if index is None:
    series = pd.Series([hostname, ipaddr, macaddr, default_menu, super_tube],
      index=['host_name', 'ip', 'mac', 'default_menu', 'super_tube'])
    # df_hosts = pd.concat([df_hosts, series.to_frame().T], ignore_index=True)
    global_config.add_row_to_hosts(series)
  else:
    # df_hosts.iloc[index]['host_name'] = hostname
    # df_hosts.iloc[index]['ip'] = ipaddr
    # df_hosts.iloc[index]['default_menu'] = default_menu
    # df_hosts.iloc[index]['super_tube'] = super_tube
    df_hosts.loc[df_hosts['mac'] == macaddr, 'host_name'] = hostname
    df_hosts.loc[df_hosts['mac'] == macaddr, 'ip'] = ipaddr
    df_hosts.loc[df_hosts['mac'] == macaddr, 'default_menu'] = default_menu
    df_hosts.loc[df_hosts['mac'] == macaddr, 'super_tube'] = super_tube
  update_ipxe_cfg(macaddr, default_menu, super_tube)
  global_config.save_hosts_to_csv()
  return 0, 'success', index

def host_del_item(hostname=None, macaddr=None):
  if hostname is None and macaddr is None:
    return 1, 'unspecified machine'
  df_hosts = global_config.get_hosts_dataframe()
  if hostname:
    if hostname not in df_hosts['host_name'].tolist():
      return 1, 'hostname not existed'
    if macaddr is None:
      macaddr = df_hosts.loc[df_hosts['host_name'] == hostname, 'mac']
  if macaddr:
    if macaddr not in df_hosts['mac'].tolist():
      return 1, 'mac address not existed'
    if hostname is None:
      hostname = df_hosts.loc[df_hosts['mac'] == macaddr, 'host_name']

  if hostname is None or macaddr is None:
    return 1, 'invalid host data'

  result_code, result_message = dhcp.unbind_mac_address_and_ip_address(
    global_config.get_cache('dhcp_network_name'), hostname, macaddr)
  if result_code != 0:
    return 1, result_message
  root_path = global_config.get_cache('http_root_path')
  format_mac = ''.join(macaddr.split(':')).lower()
  ipxe.delete_ipxe_cfg(os.path.join(root_path, 'ipxe', 'cfg', \
    f'mac-{format_mac}.ipxe.cfg'))
  # remove all snapshot iscsi storage and logical storage of host
  remove_snapshot_storage_of_host(format_mac)
  df_hosts.drop(df_hosts[df_hosts['mac'] == macaddr].index, inplace=True)
  global_config.save_hosts_to_csv()
  return 0, 'success'

def host_power_on_item(hostname=None, macaddr=None):
  if hostname:
    return smyoo_host_power_control(1, hostname, updatedevices = True)
  elif macaddr:
    df_hosts = global_config.get_hosts_dataframe()
    mac_list = df_hosts['mac'].tolist()
    if macaddr in mac_list:
      hostname = df_hosts.loc[df_hosts['mac'] == macaddr, 'host_name']
      return smyoo_host_power_control(1, hostname, updatedevices = True)
    else:
      return 1, 'Cannot find host'
  else:
    return 1, 'Please specify the specific machine'

def host_power_off_item(hostname=None, macaddr=None):
  if hostname:
    return smyoo_host_power_control(0, hostname, updatedevices = True)
  elif macaddr:
    df_hosts = global_config.get_hosts_dataframe()
    mac_list = df_hosts['mac'].tolist()
    if macaddr in mac_list:
      hostname = df_hosts.loc[df_hosts['mac'] == macaddr, 'host_name']
      return smyoo_host_power_control(0, hostname, updatedevices = True)
    else:
      return 1, 'Cannot find host'
  else:
    return 1, 'Please specify the specific machine'

def host_reset_item(hostname=None, macaddr=None):
  return 0, 'success'

def restore_after_restart():
  volume_group = global_config.get_cache('volume_group_name')
  result_code, result_message = lvm2.restore_after_restart(volume_group)
  if result_code != 0:
    return result_code, result_message
  result_code, result_message = iscsi.restore_after_restart()
  if result_code != 0:
    return result_code, result_message
  return 0, 'success'

def operation_system_add_item(name, description, capacity):
  df_os = global_config.get_os_dataframe()
  os_names = df_os['name'].tolist()
  df_data_disk = global_config.get_data_disk_dataframe()
  data_disk_list = df_data_disk['name'].tolist()
  if name in os_names or name in data_disk_list:
    return 1, 'already existed, unsupport modify'
  volume_group = global_config.get_cache('volume_group_name')
  result_code, result_message = lvm2.create_logical_volume(
    volume_group, name, capacity)
  if result_code != 0:
    return result_code, result_message
  series = pd.Series([name, description, capacity],
    index=['name', 'description', 'capacity'])
  # df_os = pd.concat([df_os, series.to_frame().T], ignore_index=True)
  global_config.add_row_to_os(series)
  global_config.save_os_to_csv()
  return 0, 'success'

def operation_system_del_item(name):
  df_os = global_config.get_os_dataframe()
  os_names = df_os['name'].tolist()
  if name not in os_names:
    return 1, 'operation system not existed'
  df_boot_menu = global_config.get_boot_menu_dataframe()
  operation_system_list = df_boot_menu['operation_system'].tolist()
  if name in operation_system_list:
    return 1, 'The selected operation system is in use'
  volume_group = global_config.get_cache('volume_group_name')
  result_code, result_message = lvm2.remove_logical_volume(volume_group, name)
  if result_code != 0:
    return result_code, result_message
  df_os.drop(df_os[df_os['name'] == name].index, inplace=True)
  global_config.save_os_to_csv()
  return 0, 'success'

def data_disk_add_item(name, description, capacity):
  df_os = global_config.get_os_dataframe()
  os_names = df_os['name'].tolist()
  df_data_disk = global_config.get_data_disk_dataframe()
  data_disk_list = df_data_disk['name'].tolist()
  if name in os_names or name in data_disk_list:
    return 1, 'already existed, unsupport modify'
  volume_group = global_config.get_cache('volume_group_name')
  result_code, result_message = lvm2.create_logical_volume(
    volume_group, name, capacity)
  if result_code != 0:
    return result_code, result_message
  series = pd.Series([name, description, capacity],
    index=['name', 'description', 'capacity'])
  # df_data_disk = pd.concat([df_data_disk, series.to_frame().T], ignore_index=True)
  global_config.add_row_to_data_disk(series)
  global_config.save_data_disk_to_csv()
  return 0, 'success'

def data_disk_del_item(name):
  df_data_disk = global_config.get_data_disk_dataframe()
  data_disk_list = df_data_disk['name'].tolist()
  if name not in data_disk_list:
    return 1, 'data disk not existed'
  df_boot_menu = global_config.get_boot_menu_dataframe()
  for index, row in df_boot_menu.iterrows():
    data_disk_list_used = row['data_disk'].split(",")
    if name in data_disk_list_used:
      return 1, 'The selected data disk is in use'
  volume_group = global_config.get_cache('volume_group_name')
  result_code, result_message = lvm2.remove_logical_volume(volume_group, name)
  if result_code != 0:
    return result_code, result_message
  df_data_disk.drop(df_data_disk[df_data_disk['name'] == name].index, inplace=True)
  global_config.save_data_disk_to_csv()
  return 0, 'success'

def boot_menu_add_item(name, operation_system, data_disk):
  df_boot_menu = global_config.get_boot_menu_dataframe()
  boot_menu_list = df_boot_menu['name'].tolist()
  if name in boot_menu_list:
    return 1, 'already existed, unsupport modify'
  iscsi_target_prefix = global_config.get_cache('iscsi_target_prefix')
  disks = []
  disks.append(operation_system)
  disks.extend(data_disk)
  disks = util.deduplication(disks)
  initiator_iqn = '%s:sn.%s' % (iscsi_target_prefix, name)
  result_code, result_message = iscsi.create_iscsi_target(name, disks,
    iscsi_target_prefix, initiator_iqn)
  if result_code != 0:
    return result_code, result_message
  series = pd.Series([name, operation_system, ','.join(data_disk)],
    index=['name', 'operation_system', 'data_disk'])
  # df_boot_menu = pd.concat([df_boot_menu, series.to_frame().T], ignore_index=True)
  global_config.add_row_to_boot_menu(series)
  global_config.save_boot_menu_to_csv()
  return 0, 'success'

def boot_menu_del_item(name):
  df_boot_menu = global_config.get_boot_menu_dataframe()
  boot_menu_list = df_boot_menu['name'].tolist()
  if name not in boot_menu_list:
    return 1, 'boot menu item not existed'
  df_hosts = global_config.get_hosts_dataframe()
  if name in df_hosts['default_menu'].tolist():
    return 1, 'boot menu item is still in use'
  target_list = iscsi.get_iscsi_target_list()
  iscsi_target_prefix = global_config.get_cache('iscsi_target_prefix')
  for target in target_list:
    if target.startswith(f'{iscsi_target_prefix}:sn.{name}.'):
      iscsi.delete_iscsi_target_by_wwn(target)
  for target in target_list:
    if target == f'{iscsi_target_prefix}:sn.{name}':
      iscsi.delete_iscsi_target_by_wwn(target)
  df_boot_menu.drop(df_boot_menu[df_boot_menu['name'] == name].index, inplace=True)
  global_config.save_boot_menu_to_csv()
  return 0, 'success'

def boot_menu_del_item_snap(name):
  df_boot_menu = global_config.get_boot_menu_dataframe()
  boot_menu_list = df_boot_menu['name'].tolist()
  if name not in boot_menu_list:
    return 1, 'boot menu item not existed'
  index_num = boot_menu_list.index(name)
  iscsi_target_prefix = global_config.get_cache('iscsi_target_prefix')
  disks = []
  disks.append(df_boot_menu.iloc[index_num]['operation_system'])
  disks.extend(df_boot_menu.iloc[index_num]['data_disk'].split(','))
  disks = util.deduplication(disks)
  iscsi.delete_snap_iscsi_objects(iscsi_target_prefix, name, disks)
  return 0, 'success'

def set_volume_group_name(volume_group):
  if not lvm2.is_volume_group_existed(volume_group):
    return 1, 'not existed'
  global_config.set_cache('volume_group_name', volume_group)
  return 0, 'volume group normal'

def set_cow_lv_size(size):
  if size > 0 and size < 1024:
    if size != global_config.get_cache('storage_lv_cow_size', default=10):
      global_config.set_cache('storage_lv_cow_size', size)
    return 0, 'success'
  else:
    return 1, 'invalid size'

def set_dhcp_network_name(network_name):
  old_value = global_config.get_cache('dhcp_network_name')
  if old_value == network_name:
    return 0, 'success'
  result_code, result_message = dhcp.edit_dhcp_conf_include(
    old_value, network_name)
  if result_code != 0:
    return result_code, result_message
  global_config.set_cache('dhcp_network_name', network_name)
  return 0, 'success'

def set_dhcp_server_subnet(network_interface, subnet, subnet_mask, range_from,
  range_to, routers, dns_servers, broadcast_address, filename, next_server):
  result_code, result_message = dhcp.edit_dhcp_conf_subnet(
    global_config.get_cache('dhcp_network_name'), network_interface, subnet,
    subnet_mask, range_from, range_to, routers, dns_servers, broadcast_address,
    filename, next_server);
  if result_code != 0:
    return result_code, result_message
  global_config.set_cache('dhcp_interface', network_interface)
  global_config.set_cache('dhcp_subnet', subnet)
  global_config.set_cache('dhcp_subnet_mask', subnet_mask)
  global_config.set_cache('dhcp_range_from', range_from)
  global_config.set_cache('dhcp_range_to', range_to)
  global_config.set_cache('dhcp_routers', routers)
  global_config.set_cache('dhcp_dns_servers', dns_servers)
  global_config.set_cache('dhcp_broadcast_address', broadcast_address)
  global_config.set_cache('dhcp_filename', filename)
  global_config.set_cache('dhcp_next_server', next_server)
  return 0, 'success'

def set_http_server_setting(root_path, base_url, iscsi_server):
  result_code = ipxe.edit_global_ipxe_cfg(os.path.join(root_path, 'ipxe'),
    iscsi_server, base_url)
  if result_code != 0:
    return result_code, 'write ipxe cfg failed'
  global_config.set_cache('http_root_path', root_path)
  global_config.set_cache('http_base_url', base_url)
  global_config.set_cache('iscsi_server', iscsi_server)
  return 0, 'success'

def set_iscsi_setting(initiator_iqn, iscsi_target_prefix):
  global_config.set_cache('iscsi_target_prefix', iscsi_target_prefix)
  global_config.set_cache('iscsi_initiator_iqn', initiator_iqn)
  return 0, 'success'

def set_smyoo_account(phone, password):
  if phone is None or password is None or \
    len(phone) == 0 or len(password) == 0:
    return 1, 'invalid phone or password'

  changed = False
  if phone != global_config.get_cache('smyoo_phone',default=''):
    global_config.set_cache('smyoo_phone', phone)
    changed = True
  if password != global_config.get_cache('smyoo_password',default=''):
    global_config.set_cache('smyoo_password', password)
    changed = True
  if changed:
    bpeSessionId, resultMsg = smyoo.login(phone, password)
    if bpeSessionId is None:
      global_config.delete_cache('smyoo_session')
      return 1, resultMsg
    global_config.set_cache('smyoo_session', bpeSessionId, expire=3600*24)
  else:
    if global_config.get_cache('smyoo_session', default=None) is None:
      return 1, 'wrong phone or password'
  return 0, 'success'

def update_smyoo_session():
  bpeSessionId = global_config.get_cache('smyoo_session', default=None)
  if bpeSessionId:
    return 0, bpeSessionId
  bpeSessionId, resultMsg = smyoo.login(
    global_config.get_cache('smyoo_phone',default=''),
    global_config.get_cache('smyoo_password',default=''))
  if bpeSessionId is None:
    return 1, resultMsg
  global_config.set_cache('smyoo_session', bpeSessionId, expire=3600*24)
  return 0, bpeSessionId

def update_smyoo_devices_info(bpeSessionId=None):
  if bpeSessionId is None:
    result_code, result_message = update_smyoo_session()
    if result_code != 0:
      return result_code, result_message
    bpeSessionId = result_message
  if bpeSessionId is None or len(bpeSessionId) == 0:
    return 1, 'Smyoo session of cookie is None'
  updateTime, resultMsg = smyoo.statusChanged(bpeSessionId)
  if updateTime is None:
    return 1, resultMsg
  updateTimeCache = global_config.get_cache('smyoo_updatetime', default='')
  if updateTime != updateTimeCache:
    devices, resultMsg = smyoo.queryDevices(bpeSessionId)
    if devices is None:
      return 1, resultMsg
    global_config.set_cache('smyoo_updatetime', updateTime)
    global_config.set_cache('smyoo_devices', json.dumps(devices))
  return 0, 'success'

def get_smyoo_device_info(hostname, updatedevices=False):
  if updatedevices:
    update_smyoo_devices_info()
  devicesContent = global_config.get_cache('smyoo_devices',default='')
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

def smyoo_host_power_control(op, hostname, updatedevices=False):
  bpeSessionId = None
  result_code, result_message = update_smyoo_session()
  if result_code != 0:
    return ErrorCode.PLOTLY_SMYOO_SESSION_ERROR.value, result_message
  bpeSessionId = result_message

  if updatedevices:
    result_code, result_message = update_smyoo_devices_info(bpeSessionId=bpeSessionId)
    if result_code != 0:
      return result_code, result_message

  sdi = get_smyoo_device_info(hostname)
  if sdi is None or sdi['mcuid'] is None:
    return ErrorCode.SMYOO_HOST_NOT_EXISTED.value, 'Can not get smyoo mcuid of host'
  result_code, result_message = smyoo.powerControl(bpeSessionId, sdi['mcuid'], op)
  return result_code if result_code != 1 else \
    ErrorCode.PLOTLY_SET_SMYOO_HOST_POWER_FAILED.value, result_message

def rpc_set_boot_menu(hostname, boot_item, super_tube):
  df_hosts = global_config.get_hosts_dataframe()
  host_name_list = df_hosts['host_name'].tolist()
  if hostname in host_name_list:
    df_boot_menu = global_config.get_boot_menu_dataframe()
    boot_menu_list = df_boot_menu['name'].tolist()
    if boot_item in boot_menu_list:
      index_num = host_name_list.index(hostname)
      # df_hosts.iloc[index_num]['default_menu'] = boot_item
      # df_hosts.iloc[index_num]['super_tube'] = super_tube
      df_hosts.loc[df_hosts['host_name'] == hostname, 'default_menu'] = boot_item
      df_hosts.loc[df_hosts['host_name'] == hostname, 'super_tube'] = super_tube
      update_ipxe_cfg(df_hosts.iloc[index_num]['mac'], boot_item, super_tube)
      global_config.save_hosts_to_csv()
      return 0, 'success'
    else:
      return ErrorCode.PLOTLY_BOOT_MENU_NOT_EXISTED.value, 'boot menu not existed'
  else:
    return ErrorCode.SMYOO_HOST_NOT_EXISTED.value, 'request host not existed'
