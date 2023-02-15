# CloudCyberCafe

Cloud Cyber Cafe -- iPXE + iSCSI 无盘启动方案

## iPXE

```shell
mkdir -p /var/www/file/ipxe/cfg
wget https://github.com/ipxe/wimboot/releases/latest/download/wimboot /var/www/file/ipxe/
rm -f /var/www/file/ipxe/boot.ipxe
touch /var/www/file/ipxe/boot.ipxe
echo '#!'"ipxe" >> /var/www/file/ipxe/boot.ipxe
echo "chain --autofree boot.ipxe.cfg" >> /var/www/file/ipxe/boot.ipxe
echo "chain --replace cfg/mac-"'$'"{mac:hexraw}.ipxe.cfg" >> /var/www/file/ipxe/boot.ipxe
```

以下引导启动文件放到TFTP文件夹中
- undionly.kpxe: https://boot.ipxe.org/undionly.kpxe
- ipxe.efi: https://boot.ipxe.org/ipxe.efi

建议使用自定义的脚本编译生成boot文件，例如[script.ipxe](./ipxe/script.ipxe)，这样可以避免一些dhcp option的影响。

```
make bin-x86_64-pcbios/undionly.kpxe EMBED=script.ipxe
make bin-x86_64-efi/ipxe.efi EMBED=script.ipxe
```

官方文档: https://ipxe.org/

## iSCSI

- https://github.com/open-iscsi/targetcli-fb
- https://github.com/open-iscsi/rtslib-fb

## 安装准备

因为对 iSCSI 和存储池(lvm2) 的操作很多都需要 `sudo` 权限，所以建议用户使用 `sudo` 时免密码验证。

在 `/etc/sudoers` 中添加内容 `dbc	ALL=(root) NOPASSWD:ALL`。

```shell
sudo apt install targetcli-fb open-iscsi python3-pip thrift-compiler
sudo pip3 install dash pandas thrift diskcache
```

## HTTP

需要 ubuntu 18.04 netboot 也可以使用阿里云或者清华源的下载

```shell
mkdir -p /var/www/file/netboot/
cd /var/www/file/netboot/
wget http://www.archive.ubuntu.com/ubuntu/dists/bionic-updates/main/installer-amd64/current/images/netboot/netboot.tar.gz
tar -zxvf netboot.tar.gz
```

nginx.conf
```
    server {
        listen    8080;
        root      /var/www/file;
        location / {
            autoindex on;# 显示目录
            autoindex_exact_size on;# 显示文件大小
            autoindex_localtime on;# 显示文件时间
        }
    }
```

## DHCP

支持 iPXE 的网络配置，甚至为机器绑定固定的IP地址。如果已经存在 DHCP 服务，推荐使用 dnsmasq 做 DHCP 代理，如果没有 DHCP 服务，推荐直接使用 isc-dhcp-server 配置自己的子网。

isc-dhcp-server
```
option client-architecture code 93 = unsigned integer 16;
subnet 192.168.1.0 netmask 255.255.255.0 {
    range 192.168.1.100 192.168.1.200;
    option subnet-mask 255.255.255.0;
    option routers 192.168.1.159;
    option domain-name-servers 223.5.5.5;
    option broadcast-address 192.168.1.255;
    if exists user-class and option user-class = "iPXE" {
        filename "http://192.168.1.159:8080/ipxe/boot.ipxe";
    } elsif option client-architecture = 00:00 {
        filename "undionly.kpxe";
    } else {
        filename "ipxe.efi";
    }
    next-server 192.168.1.159;
}
host host001 {hardware ethernet 88:AE:DD:05:08:FA; fixed-address 192.168.1.101;}
```

dnsmasq
```
port=0
log-dhcp
tftp-root=/srv/tftp

dhcp-option=option:router,192.168.1.1
dhcp-option=option:dns-server,223.5.5.5
# dhcp-match=set:ipxe,option:user-class,"iPXE"
dhcp-match=set:ipxe,175
dhcp-match=set:bios,option:client-arch,0

dhcp-boot=tag:!ipxe,tag:bios,undionly.kpxe,,192.168.1.159
dhcp-boot=tag:!ipxe,tag:!bios,ipxe.efi,,192.168.1.159
dhcp-boot=tag:ipxe,http://192.168.1.159:8080/ipxe/boot.ipxe,,192.168.1.159

pxe-prompt="Booting from iPXE",1

pxe-service=X86PC,"Boot to X86PC",undionly.kpxe,192.168.1.159
pxe-service=X86-64_EFI,"Boot to X86-64_EFI",ipxe.efi,192.168.1.159
pxe-service=BC_EFI,"Boot to BC_EFI",ipxe.efi,192.168.1.159

interface=eno1
dhcp-host=40:B0:76:7E:E2:31,asus,192.168.1.55
dhcp-host=88:AE:DD:05:08:FA,host001,192.168.1.56
# dhcp-range=192.168.1.50,192.168.1.80,255.255.255.0,45m
dhcp-range=192.168.1.50,proxy,255.255.255.0,45m
```

- https://www.isc.org/kea/
- https://kea.readthedocs.io/en/latest/arm/ctrl-channel.html
- https://github.com/search?q=python+dhcp
- https://github.com/pypxe/PyPXE

## WinPE

- ADK 制作工具: https://learn.microsoft.com/zh-cn/windows-hardware/get-started/adk-install
- 微软官方文档: https://learn.microsoft.com/zh-cn/windows-hardware/manufacture/desktop/winpe-intro?view=windows-10

## Thrift

使用 Thrift 提供对外的 API 接口。

- https://thrift.apache.org/
- https://github.com/apache/thrift

## 镜像制作上传流程

1. 给无盘客户端的自带硬盘安装上Windows系统和必要的驱动，解决设备管理器的感叹号，或者禁用感叹号的设备。
2. 将注册表`HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\Session Manager\Memory Management`的`PagingFiles`项的值清空。此操作跟虚拟内存有关。需要手动重启生效。
3. 启动iSCSI发起程序，修改配置中发起程序名称，输入无盘服务器的IP地址，连接远程磁盘。
4. 重启以使某些修改生效。
5. 使用磁盘精灵[DiskGenius](https://www.diskgenius.cn/)克隆磁盘，热迁移系统。将此时的系统所在整个磁盘上传到无盘存储磁盘。

备注:
1. 测试阶段请先使用纯系统和必要的驱动来测试，启动成功后再安装其他软件游戏进一步测试。
2. 镜像的上传方式以后会优化，升级成热迁移或者进入WinPE使用磁盘精灵操作。

## dashboard 打包

```shell
# 1. 需要安装 PyInstaller;
pip3 install pyinstaller
# 2. 请提前生成 thrift 协议文件;
cd <代码目录>/preset/
thrift --gen py preset.thrift
# 3. 使用 PyInstaller 打包命令。
cd <代码目录>/plotly/
python3 -m PyInstaller -F -n occ home.py -p ../preset/gen-py/
```
