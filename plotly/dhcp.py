import os
import shutil

# isc-dhcp-server

# def edit_dhcp_conf_include(old_name, new_name):
#   dhcp_conf = '/etc/dhcp/dhcpd.conf'
#   dhcp_conf_bak = '/etc/dhcp/dhcpd.conf.bak'
#   if not os.path.exists(dhcp_conf):
#     return 1, f'{dhcp_conf} not existed'
#   if not os.path.exists(dhcp_conf_bak):
#     shutil.copyfile(dhcp_conf, dhcp_conf_bak)
#   old_subnet_file = '/etc/dhcp/%s_subnet.conf' % old_name
#   new_subnet_file = '/etc/dhcp/%s_subnet.conf' % new_name
#   old_binding_file = '/etc/dhcp/%s_binding.conf' % old_name
#   new_binding_file = '/etc/dhcp/%s_binding.conf' % new_name
#   subnet_content = 'include "%s";' % new_subnet_file
#   binding_content = 'include "%s";' % new_binding_file
#   with open(dhcp_conf_bak, 'r', encoding='utf-8') as r, open(dhcp_conf, 'w', encoding='utf-8') as w:
#     for line in r:
#       # if line.find(old_subnet_file) != -1:
#       if line.find('_subnet.conf') != -1:
#         continue
#       if line.find('_binding.conf') != -1:
#         continue
#       w.write(line)
#   with open(dhcp_conf, 'a', encoding='tf-8') as w:
#     w.write('\n%s' % subnet_content)
#     w.write('\n%s' % binding_content)
#   if os.path.exists(old_subnet_file):
#     os.rename(old_subnet_file, new_subnet_file)
#   if os.path.exists(old_binding_file):
#     os.rename(old_binding_file, new_binding_file)
#   return 0, "bind successful"

# def edit_dhcp_conf_subnet(network_name, network_interface, subnet, subnet_mask,
#   range_from, range_to, routers, dns_servers, broadcast_address, filename, next_server):
#   dhcp_conf = f'/etc/dhcp/{network_name}_subnet.conf'
#   with open(dhcp_conf, 'w', encoding='utf-8') as file:
#     file.write('option client-architecture code 93 = unsigned integer 16;\n')
#     file.write(f'subnet {subnet} netmask {subnet_mask} {{\n')
#     file.write(f'\trange {range_from} {range_to};\n')
#     file.write(f'\toption subnet-mask {subnet_mask};\n')
#     file.write(f'\toption routers {routers};\n')
#     file.write(f'\toption domain-name-servers {dns_servers};\n')
#     file.write(f'\toption broadcast-address {broadcast_address};\n')
#     # file.write(f'\tfilename "{filename}";\n')
#     file.write('\tif exists user-class and option user-class = "iPXE" {\n')
#     file.write(f'\t\tfilename "{filename}";\n')
#     file.write('\t} elsif option client-architecture = 00:00 {\n')
#     file.write('\t\tfilename "undionly.kpxe";\n')
#     file.write('\t} else {\n')
#     file.write('\t\tfilename "ipxe.efi";\n')
#     file.write('\t}\n')
#     file.write(f'\tnext-server {next_server};\n')
#     file.write('}')
#   return 0, f'edit {network_name}_subnet.conf successful'

# def bind_mac_address_and_ip_address(network_name, hostname, mac_addr, ip_addr):
#   # dhcp_conf = '/etc/dhcp/dhcpd.conf'
#   dhcp_conf = f'/etc/dhcp/{network_name}_binding.conf'
#   lines = []
#   if os.path.exists(dhcp_conf):
#     with open(dhcp_conf, 'r', encoding='utf-8') as file:
#       lines = file.readlines()
#   existed = False
#   content = f'host {hostname} {{hardware ethernet {mac_addr}; fixed-address {ip_addr};}}'
#   with open(dhcp_conf, 'w', encoding='utf-8') as file:
#     for line in lines:
#       if line.find(mac_addr) != -1:
#         line = content
#         existed = True
#       file.write(line)
#   if not existed:
#     with open(dhcp_conf, 'a', encoding='utf-8') as w:
#       w.write('%s\n' % content)
#   return 0, f'bind {network_name}_binding.conf successful'

# def unbind_mac_address_and_ip_address(network_name, hostname, mac_addr):
#   # dhcp_conf = '/etc/dhcp/dhcpd.conf'
#   dhcp_conf = f'/etc/dhcp/{network_name}_binding.conf'
#   if not os.path.exists(dhcp_conf):
#     return 1, f'{dhcp_conf} not existed'
#   with open(dhcp_conf, 'r+', encoding='utf-8') as file:
#     lines = file.readlines()
#     file.seek(0)
#     file.truncate()
#     for line in lines:
#       if line.find(mac_addr) == -1:
#         file.write(line)
#   return 0, 'unbind successful'

# def restart_dhcp_service(service_name = 'isc-dhcp-server'):
#   ret = os.system(f"sudo systemctl restart {service_name}")
#   return ret

# dnsmasq

def edit_dhcp_conf_include(old_name, new_name):
  if not os.path.exists('/etc/dnsmasq.conf'):
    return 1, '/etc/dnsmasq.conf not existed'
  old_file = '/etc/dnsmasq.d/%s.conf' % old_name
  new_file = '/etc/dnsmasq.d/%s.conf' % new_name
  if os.path.exists(old_file):
    os.rename(old_file, new_file)
  return 0, "bind successful"

def edit_dhcp_conf_subnet(network_name, network_interface, subnet, subnet_mask,
  range_from, range_to, routers, dns_servers, broadcast_address, filename, next_server):
  dhcp_conf = f'/etc/dnsmasq.d/{network_name}.conf'
  bindings = []
  with open(dhcp_conf, 'r', encoding='utf-8') as file:
    for line in file:
      if line.startswith('dhcp-host='):
        bindings.append(line)
  # print(bindings)
  with open(dhcp_conf, 'w', encoding='utf-8') as file:
    file.write('port=0\n')
    file.write('log-dhcp\n')
    file.write('tftp-root=/srv/tftp\n\n')
    file.write(f'dhcp-option=option:router,{routers}\n')
    file.write(f'dhcp-option=option:dns-server,{dns_servers}\n')
    # file.write('dhcp-no-override\n\n')
    file.write('dhcp-match=set:iPXE,option:user-class,"iPXE"\n')
    file.write('dhcp-match=set:bios,option:client-arch,0\n\n')
    file.write(f'dhcp-boot=tag:bios,undionly.kpxe,,{next_server}\n')
    file.write(f'dhcp-boot=tag:!bios,ipxe.efi,,{next_server}\n')
    file.write(f'dhcp-boot=net:iPXE,{filename},,{next_server}\n\n')
    file.write('pxe-prompt="Booting from iPXE",1\n\n')
    file.write(f'interface={network_interface}\n')
    for line in bindings:
      file.write(f'{line}')
    file.write(f'dhcp-range={range_from},{range_to},{subnet_mask},45m\n')
  return 0, f'edit {network_name}.conf successful'

def bind_mac_address_and_ip_address(network_name, hostname, mac_addr, ip_addr):
  dhcp_conf = f'/etc/dnsmasq.d/{network_name}.conf'
  lines = []
  if os.path.exists(dhcp_conf):
    with open(dhcp_conf, 'r', encoding='utf-8') as file:
      lines = file.readlines()
  existed = False
  content = f'dhcp-host={mac_addr},{hostname},{ip_addr}\n'
  # content = f'dhcp-host={mac_addr},{ip_addr}\n'
  for index, line in enumerate(lines):
    if line.find(mac_addr) != -1:
      lines[index] = content
      existed = True
      break
  if not existed:
    lines.insert(len(lines) - 1, content)
  with open(dhcp_conf, 'w', encoding='utf-8') as file:
    file.truncate()
    for line in lines:
      file.write(line)
  return 0, f'bind {network_name}.conf successful'

def unbind_mac_address_and_ip_address(network_name, hostname, mac_addr):
  dhcp_conf = f'/etc/dnsmasq.d/{network_name}.conf'
  if not os.path.exists(dhcp_conf):
    return 1, f'{dhcp_conf} not existed'
  with open(dhcp_conf, 'r+', encoding='utf-8') as file:
    lines = file.readlines()
    file.seek(0)
    file.truncate()
    for line in lines:
      if line.find(mac_addr) == -1:
        file.write(line)
  return 0, 'unbind successful'

def restart_dhcp_service(service_name = 'dnsmasq'):
  ret = os.system(f"sudo systemctl restart {service_name}")
  return ret
