# lvm2.py

import os
# import pathlib
import subprocess

def is_volume_group_existed(volume_group):
  return os.system(f"sudo vgs | grep '{volume_group}'") == 0

def get_logical_volume_list(volume_group):
  cmd_output = os.popen(f'sudo lvs -a {volume_group} -o lv_name --noheadings | tr "\n" "|"').read()
  lv_list = cmd_output.split('|')
  for index, item in enumerate(lv_list):
    lv_list[index] = item.strip()
  lv_list.remove('')
  return lv_list

def create_logical_volume(volume_group, logical_volume, capacity):
  # mpath = pathlib.Path(f"/mnt/{logical_volume}")
  # if mpath.is_dir():
  if os.path.exists(f"/mnt/{logical_volume}"):
    return 1, f'mount dir /mnt/{logical_volume} already existed'
  size = (capacity + 1) * 1024
  ret = os.system(f"sudo lvcreate -L {size}M -n {logical_volume} -y {volume_group}")
  if ret != 0:
    return ret, f'create logical volume {logical_volume} failed'
  ret = os.system(f"sudo mkfs -t ext4 /dev/{volume_group}/{logical_volume}")
  if ret != 0:
    return ret, f'make filesystem ext4 /dev/{volume_group}/{logical_volume} failed'
  # os.mkdir(f"/mnt/{logical_volume}")
  # os.makedirs(f"/mnt/{logical_volume}")
  ret = os.system(f"sudo mkdir -p /mnt/{logical_volume}")
  if ret != 0:
    return ret, f'create mount dir /mnt/{logical_volume} failed'
  ret = os.system(f"sudo mount /dev/{volume_group}/{logical_volume} /mnt/{logical_volume} ")
  if ret != 0:
    return ret, f'mount logical volume {logical_volume} failed'
  size = capacity * 1024
  # ret = os.system(f"sudo dd if=/dev/zero of=/mnt/{logical_volume}/disk.img bs=1M count={size}")
  ret = os.system(f"sudo dd if=/dev/zero of=/mnt/{logical_volume}/disk.img bs=1M count=0 seek={size}")
  if ret != 0:
    return ret, f'create image file {logical_volume} failed'
  return ret, 'create successful'

def remove_logical_volume(volume_group, logical_volume):
  ret = os.system(f"sudo umount /mnt/{logical_volume}")
  if ret != 0:
    return ret, f'unmount logical volume {logical_volume} failed'
  ret = os.system(f"sudo rm -rf /mnt/{logical_volume}")
  if ret != 0:
    return ret, f'remove mount dir {logical_volume} failed'
  # ret = os.system(f"sudo lvchange -an /dev/{volume_group}/{logical_volume}")
  # if ret != 0:
  #   return ret, f'deactivate logical volume {logical_volume} failed'
  ret = os.system(f"sudo lvremove -y /dev/{volume_group}/{logical_volume}")
  if ret != 0:
    return ret, f'remove logical volume {logical_volume} failed'
  return ret, 'remove successfully'

def create_snapshot_logical_volume(volume_group, logical_volume, mac_addr, capacity):
  # lvcreate -L 1024M -s -n host01 /dev/bootpool/bootimg
  if os.path.exists(f"/mnt/{logical_volume}_{mac_addr}"):
    return 1, f'mount dir /mnt/{logical_volume}_{mac_addr} already existed'
  size = capacity * 1024
  ret = os.system(f"sudo lvcreate -L {size}M -s -n {logical_volume}_{mac_addr} /dev/{volume_group}/{logical_volume}")
  if ret != 0:
    return ret, f'create logical volume {logical_volume}_{mac_addr} failed'
  ret = os.system(f"sudo mkdir -p /mnt/{logical_volume}_{mac_addr}")
  if ret != 0:
    return ret, f'create mount dir /mnt/{logical_volume}_{mac_addr} failed'
  ret = os.system(f"sudo mount /dev/{volume_group}/{logical_volume}_{mac_addr} /mnt/{logical_volume}_{mac_addr}")
  if ret != 0:
    return ret, f'mount logical volume {logical_volume}_{mac_addr} failed'
  return ret, 'create successful'

def remove_snapshot_logical_volume(volume_group, logical_volume, macaddr):
  return 0

def list_mount_point_in_lvm():
  cmd_output=os.popen("df -h | awk '{print $6}' | grep '/mnt/' | tr '\n' '|'").read()
  mount_list = cmd_output.split('|')
  mpl=[]
  for item in mount_list:
    if len(item) > 5:
      mpl.append(item[5:])
  return mpl

def restore_after_restart(volume_group):
  mount_list = list_mount_point_in_lvm()
  lv_list = get_logical_volume_list(volume_group)
  for logical_volume in lv_list:
    if logical_volume not in mount_list:
      ret = os.system(
        f"sudo mount /dev/{volume_group}/{logical_volume} /mnt/{logical_volume}")
      if ret != 0:
        return ret, f'mount logical volume {logical_volume} failed'
  return 0, 'restore mount state successful'
