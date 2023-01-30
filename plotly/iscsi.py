import os
import rtslib

def list_rts_fb():
  root = rtslib.RTSRoot()
  print(root.path)
  # print(root.dump())
  for target in root.targets:
    print("--", target.wwn)
    for tpg in target.tpgs:
      print("---- tpg", tpg.tag, " ---- ", tpg.enable)
      if target.wwn == 'iqn.2003-01.org.linux-iscsi.jerry.x8664:sn.2ee000d2a7d1':
        tpg.enable = True
      for acl in tpg.node_acls:
        print("------ acl:",acl.node_wwn)
        # print("------ mapped_luns:", type(acl.mapped_luns))
        for mapped_lun in acl.mapped_luns:
          print("-------- mapped lun:", mapped_lun.mapped_lun, mapped_lun.tpg_lun)
      for acl in tpg.node_acl_groups:
        print("------ acl group:",acl.node_wwn)
      for lun in tpg.luns:
        print("------ luns:")
        print("-------- mapped lun:", lun.lun, lun, lun.storage_object)
      for portal in tpg.network_portals:
        print("------ portals:")
        print("-------- %s:%i" % (portal.ip_address, portal.port))
  # print(list(root.storage_objects))
  for fio in list(root.storage_objects):
    # print("-- ", type(fio))
    print("-- ", fio.plugin)
    print('-------- name: %s, udev_path: %s, state: %s' % (fio.name, fio.udev_path, fio.status))
    print('-------- version: %s, wwn %s' % (fio.version,  fio.wwn))
  #   print(fio.dump())
  # print(list(root.node_acls))

# create fileio backstores
def test_create_rts_fb(name, filepath, target_wwn):
  f = rtslib.FileIOStorageObject(name, filepath, 100000000)
  # f.status
  iscsi = rtslib.FabricModule("iscsi")
  target = rtslib.Target(iscsi, target_wwn)
  tpg = rtslib.TPG(target, 1)
  portal = rtslib.NetworkPortal(tpg, "0.0.0.0", 3260)
  lun = rtslib.LUN(tpg, 0, f)
  nodeacl = rtslib.NodeACL(tpg, "iqn.2004-03.com.example.foo:0987")
  mlun = rtslib.MappedLUN(nodeacl, 0, lun)
  tpg.set_attribute("authentication", "0")
  tpg.enable = True

def test_delete_rts_fb(name, filepath, target_wwn):
  # lookup iscsi target
  try:
    iscsi = rtslib.FabricModule("iscsi")
    target = rtslib.Target(iscsi, target_wwn, 'lookup')
    # target = rtslib.Target(iscsi, "abc", 'lookup')
    target.delete()
  except:
    print(target_wwn, ' not existed')
  # lookup fileio storage
  try:
    f = rtslib.FileIOStorageObject(name)
    # f = rtslib.FileIOStorageObject('aaa')
    f.delete()
  except:
    print(name, ' not existed')
  os.remove(filepath)

def unittest():
  list_rts_fb()
  test_create_rts_fb('win10', "/data/win10.img",
    'iqn.2003-01.org.linux-iscsi.localhost.x8664:sn.win10')
  list_rts_fb()
  test_delete_rts_fb('win10', "/data/win10.img",
    'iqn.2003-01.org.linux-iscsi.localhost.x8664:sn.win10')
  list_rts_fb()

# list_rts_fb()
# fz = os.path.getsize('/mnt/ubuntu1804/disk.img')
# fis = rtslib.FileIOStorageObject('ubuntu1804', '/mnt/ubuntu1804/disk.img', fz, write_back=True)
# for so in rtslib.RTSRoot().storage_objects:
#   if so.udev_path:
#     print(so.udev_path.split('/'))

def get_iscsi_target_list():
  target_list = []
  root = rtslib.RTSRoot()
  for target in root.targets:
    target_list.append(target.wwn)
  return target_list

def get_fileio_storage_object(name):
  try:
    f = rtslib.FileIOStorageObject(name)
    return f
  except:
    return None

def create_iscsi_target(target_name, disks, target_prefix, initiator_iqn):
  for disk in disks:
    if not os.path.exists(f'/mnt/{disk}/disk.img'):
      return 1, f'{disk} image file not existed'
  for so in rtslib.RTSRoot().storage_objects:
    if so.udev_path:
      paths = so.udev_path.split('/')
      if len(paths) >= 3 and paths[2] in disks:
        print(f'{paths[2]} already existed in storage')
        # return 1, f'{paths[2]} already existed in storage'
  fss = []
  try:
    for disk in disks:
      fiso = get_fileio_storage_object(disk)
      if fiso is not None:
        fss.append(fiso)
        continue
      size = os.path.getsize(f'/mnt/{disk}/disk.img')
      if not size:
        for fis in fss:
          fis.delete()
        return 1, 'attempting to get file size failed'
      fss.append(rtslib.FileIOStorageObject(disk, f'/mnt/{disk}/disk.img',
        size, write_back=True, wwn=None))
  except:
    for fis in fss:
      fis.delete()
    return 1, 'create fileio backstorage failed'

  iscsi = rtslib.FabricModule("iscsi")
  try:
    target = rtslib.Target(iscsi, '%s:sn.%s' % (target_prefix, target_name))
  except:
    for fis in fss:
      fis.delete()
    return 1, 'create iscsi target failed'
  tpg = rtslib.TPG(target, 1)
  nodeacl = rtslib.NodeACL(tpg, initiator_iqn)
  portal = rtslib.NetworkPortal(tpg, "0.0.0.0", 3260)
  cur_index = len(list(tpg.luns))
  for index, fis in enumerate(fss):
    lun = rtslib.LUN(tpg, cur_index, fis)
    cur_index += 1
    mlun = rtslib.MappedLUN(nodeacl, index, lun)
  tpg.set_attribute("authentication", "0")
  tpg.enable = True
  return 0, 'create file io successful'

def delete_iscsi_target_by_wwn(target_wwn, with_backstores = True):
  # lookup iscsi target
  try:
    iscsi = rtslib.FabricModule("iscsi")
    target = rtslib.Target(iscsi, target_wwn, 'lookup')
    if with_backstores:
      for tpg in target.tpgs:
        for lun in tpg.luns:
          lun.storage_object.delete()
    target.delete()
  except:
    return 1, f'target {target_wwn} not existed'
  return 0, f'delete iscsi target {target_wwn} successful'

def delete_iscsi_target(target_prefix, boot_item):
  # lookup iscsi target
  try:
    iscsi = rtslib.FabricModule("iscsi")
    target = rtslib.Target(iscsi, '%s:sn.%s' % (target_prefix, boot_item), 'lookup')
    if with_backstores:
      for tpg in target.tpgs:
        for lun in tpg.luns:
          lun.storage_object.delete()
    target.delete()
  except:
    return 1, f'target {boot_item} not existed'
  return 0, f'delete iscsi target {boot_item} successful'

def delete_snap_iscsi_objects_by_host(target_prefix, boot_item, mac_addr):
  # lookup iscsi target
  try:
    iscsi = rtslib.FabricModule("iscsi")
    target = rtslib.Target(iscsi, '%s:sn.%s' % (target_prefix, boot_item), 'lookup')
    for tpg in target.tpgs:
      for acl in tpg.node_acls:
        if acl.node_wwn == f'{target_prefix}:sn.{boot_item}.{mac_addr}':
          acl.delete()
          break
      for lun in tpg.luns:
        if lun.storage_object.name.endswith(mac_addr):
          lun.storage_object.delete()
  except:
    return 1, f'delete snap iscsi objects {boot_item} of {mac_addr} failed'
  return 0, f'delete snap iscsi objects {boot_item} of {mac_addr} successful'

def delete_snap_iscsi_objects(target_prefix, boot_item, disks):
  # lookup iscsi target
  try:
    iscsi = rtslib.FabricModule("iscsi")
    target = rtslib.Target(iscsi, '%s:sn.%s' % (target_prefix, boot_item), 'lookup')
    for tpg in target.tpgs:
      for acl in tpg.node_acls:
        if acl.node_wwn.startswith(f'{target_prefix}:sn.{boot_item}.'):
          acl.delete()
          break
      for lun in tpg.luns:
        if lun.storage_object.name not in disks:
          lun.storage_object.delete()
  except:
    return 1, f'delete snap iscsi objects {boot_item} failed'
  return 0, f'delete snap iscsi objects {boot_item} successful'

def restore_after_restart():
  try:
    root = rtslib.RTSRoot()
    # root.restore_from_file()
    root.restore_from_file(restore_file='/etc/rtslib-fb-targets/saveconfig.json')
    # root.restore_from_file(restore_file='/etc/target/saveconfig.json')
  except:
    return 1, 'Error occurred, please contact the developer'
  return 0, 'restore iscsi target successful'
