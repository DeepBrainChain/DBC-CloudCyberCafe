import os

def edit_global_ipxe_cfg(root_path, iscsi_server, base_url):
  if os.path.exists(f'{root_path}/boot.ipxe'):
    with open(f'{root_path}/boot.ipxe.cfg', 'w', encoding='utf-8') as file:
      file.write('#!ipxe\n')
      file.write(f'set iscsi-server {iscsi_server}\n')
      file.write(f'set base-url {base_url}\n')
      file.write('set menu-timeout 5000\n')
    return 0
  return 1

def edit_ipxe_cfg(config_folder, mac_addr, initiator_iqn, iscsi_target_prefix, boot_menu,
  default_menu, manager = False, menu_timeout = 5000):
  if not os.path.exists(config_folder):
    os.mkdir(config_folder)
  with open(f'{config_folder}/mac-{mac_addr}.ipxe.cfg', 'w', encoding='utf-8') as file:
    file.write('#!ipxe\n')
    file.write(f'\nset menu-timeout {menu_timeout}\n')
    file.write(f'set menu-default {default_menu}\n')
    file.write(f'set initiator-iqn {initiator_iqn}\n')
    for item in boot_menu:
      file.write(f'set {item}-iscsi-iqn {iscsi_target_prefix}:sn.{item}')
      if manager:
        file.write('\n')
      else:
        file.write(f'.{mac_addr}\n')
    if manager:
      file.write(f'set install-iscsi-iqn {iscsi_target_prefix}:sn.{default_menu}\n')
    file.write('\n')
    file.write(':start\n')
    file.write('menu iPXE boot menu build 20220717\n')
    file.write('%s %s\n' % ('item --gap --'.ljust(36), ' Operating systems '.center(72,'-')))
    for item in boot_menu:
      file.write(f'item --key w {item.ljust(24)}Boot {item} from iSCSI\n')
    if manager:
      file.write('%s %s\n' % ('item --gap --'.ljust(36), ' Tools and utilities '.center(72,'-')))
      file.write('item --key d %sBoot basic WindowsPE 32 bit\n' % 'winpe32'.ljust(24))
      file.write('item --key d %sBoot basic WindowsPE 64 bit\n' % 'winpe64'.ljust(24))
      file.write('item --key d %sBoot basic WindowsPE 32 bit UEFI\n' % 'winpe32uefi'.ljust(24))
      file.write('item --key d %sBoot basic WindowsPE 64 bit UEFI\n' % 'winpe64uefi'.ljust(24))
      file.write('item --key d %sInstalling Ubuntu to iSCSI target\n' % 'install_ubuntu_iscsi'.ljust(24))
    file.write('%s %s\n' % ('item --gap --'.ljust(36), ' Advanced options '.center(72,'-')))
    file.write('item --key c %sConfigure settings\n' % 'config'.ljust(24))
    file.write('item %sDrop to iPXE shell\n' % 'shell'.ljust(32))
    file.write('item %sReboot computer\n' % 'reboot'.ljust(32))
    file.write('item\n')
    file.write('item --key x %sExit iPXE and continue BIOS boot\n' % 'exit'.ljust(24))
    file.write('choose --timeout ${menu-timeout} --default ${menu-default} selected || goto cancel\n')
    file.write('set menu-timeout 0\n')
    file.write('goto ${selected}\n')
    file.write('\n')
    file.write(':cancel\n')
    file.write('echo You cancelled the menu, dropping you to a shell\n')
    file.write('\n')
    file.write(':shell\n')
    file.write('echo Type \'exit\' to get the back to the menu\n')
    file.write('shell\n')
    file.write('goto start\n')
    file.write('\n')
    file.write(':failed\n')
    file.write('echo Failed to start, will return to main menu within 5 seconds\n')
    file.write('sleep 5\n')
    file.write('goto start\n')
    file.write('\n')
    file.write(':reboot\n')
    file.write('reboot\n')
    file.write('\n')
    file.write(':exit\n')
    file.write('exit\n')
    file.write('\n')
    file.write(':config\n')
    file.write('config\n')
    file.write('goto start\n')
    for item in boot_menu:
      file.write('\n')
      file.write(f':{item}\n')
      file.write('cpuid --ext 29 && set arch amd64\n')
      file.write('ifopen net0\n')
      file.write('dhcp\n')
      file.write('echo Booting from SAN device\n')
      file.write(f'sanhook --drive 0x80 iscsi:${{iscsi-server}}:::0:${{{item}-iscsi-iqn}} || goto failed\n')
      file.write('sanboot --drive 0x80\n')
      file.write('goto start\n')
    if manager:
      file.write('\n')
      file.write(':winpe32\n')
      file.write('cpuid --ext 29 && set arch x86\n')
      file.write('goto winpe\n')
      file.write('\n')
      file.write(':winpe64\n')
      file.write('cpuid --ext 29 && set arch amd64\n')
      file.write('goto winpe\n')
      file.write('\n')
      file.write(':winpe32uefi\n')
      file.write('cpuid --ext 29 && set arch x86\n')
      file.write('goto winpeuefi\n')
      file.write('\n')
      file.write(':winpe64uefi\n')
      file.write('cpuid --ext 29 && set arch amd64\n')
      file.write('goto winpeuefi\n')
      file.write('\n')
      file.write(':winpe\n')
      file.write('ifopen net0\n')
      file.write('dhcp\n')
      file.write('set netX/gateway 0.0.0.0\n')
      file.write('echo Attach SAN device...\n')
      file.write('sanhook --drive 0x80 iscsi:${iscsi-server}:::0:${install-iscsi-iqn} || goto failed\n')
      file.write('echo Load Windows PE file...\n')
      file.write('kernel ${base-url}/ipxe/wimboot\n')
      file.write('initrd ${base-url}/winpe/${arch}/media/Boot/BCD            BCD\n')
      file.write('initrd ${base-url}/winpe/${arch}/media/Boot/boot.sdi       boot.sdi\n')
      file.write('initrd ${base-url}/winpe/${arch}/media/sources/boot.wim    boot.wim\n')
      file.write('echo Starting the system....\n')
      file.write('boot || goto failed\n')
      file.write('goto start\n')
      file.write('\n')
      file.write(':winpeuefi\n')
      file.write('ifopen net0\n')
      file.write('dhcp\n')
      file.write('set netX/gateway 0.0.0.0\n')
      file.write('echo Attach SAN device...\n')
      file.write('sanhook --drive 0x80 iscsi:${iscsi-server}:::0:${install-iscsi-iqn} || goto failed\n')
      file.write('echo Load Windows PE file...\n')
      file.write('kernel ${base-url}/ipxe/wimboot\n')
      file.write('initrd ${base-url}/winpe/${arch}/media/EFI/Boot/bootx64.efi\n')
      file.write('initrd ${base-url}/winpe/${arch}/media/EFI/Microsoft/Boot/BCD\n')
      file.write('initrd ${base-url}/winpe/${arch}/media/Boot/boot.sdi\n')
      file.write('initrd ${base-url}/winpe/${arch}/media/sources/boot.wim\n')
      file.write('echo Starting the system....\n')
      file.write('boot || goto failed\n')
      file.write('goto start\n')
      file.write('\n')
      file.write(':install_ubuntu_iscsi\n')
      file.write('ifopen net0\n')
      file.write('dhcp\n')
      file.write('cpuid --ext 29 && set arch x86_64\n')
      file.write('echo Attach SAN device...\n')
      file.write('sanhook --drive 0x80 iscsi:${iscsi-server}:::0:${install-iscsi-iqn} || goto failed\n')
      file.write('echo Load Ubuntu ISO file...\n')
      file.write('kernel ${base-url}/netboot/ubuntu-installer/amd64/linux\n')
      file.write('initrd ${base-url}/netboot/ubuntu-installer/amd64/initrd.gz\n')
      file.write('imgargs linux auto=true fb=false url=${base-url}/ubuntu/preseed.cfg\n')
      file.write('boot || goto failed\n')
      file.write('goto start\n')

def delete_ipxe_cfg(config_file):
  if os.path.exists(config_file):
    os.remove(config_file)

# edit_ipxe_cfg('mac.ipxe', ['windows', 'ubuntu'], 'windows', True)
