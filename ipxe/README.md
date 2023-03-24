# iPXE

PXE 是 Intel 提出的，用以网卡启动。通过 DHCP 获取 IP 以及 TFTP 获取启动文件。
iPXE 是 PXE 的增强扩展版，支持 HTTP 等多种获取手段，因此需要部署 DHCP，TFTP 和 HTTP 服务。

## DHCP

动态主机配置协议 DHCP（Dynamic Host Configuration Protocol） 是 RFC 1541（已被 RFC 2131 取代）定义的标准协议，
该协议允许服务器向客户端动态分配 IP 地址和配置信息。
而且 PXE 服务需要使用 DHCP 协议的 bootfile 字段告诉机器 PXE 的启动文件。
如果网吧等场所已经存在 DHCP 服务(路由器提供的 DHCP 地址分配)，推荐使用 dnsmasq 做 DHCP 代理，
如果没有 DHCP 服务，推荐直接使用 isc-dhcp-server 配置自己的子网。

### dnsmasq

本项目默认使用 dnsmasq 服务，因为很多客户环境已经存在路由器，
只需要 dnsmasq 做 DHCP 协议代理提供 bootfile 等字段，此时只需安装 dnsmasq 并能成功启动 dnsmasq.service 即可，
具体的配置将于项目的控制台自动生成。

```shell
# 安装 dnsmasq
$ sudo apt install dnsmasq
# 查看 dnsmasq 服务运行情况
$ systemctl status dnsmasq.service
```

```tips
ubuntu 系统默认的 systemd-resolved 会监听 53 端口做 DNS 解析，启动 dnsmasq.service 服务可能会失败。
解决办法有很多，这里提供一种参考：使用命令 systemd-resolve --interface=eno1 --set-dns=223.5.5.5 手动
为网卡 eno1 设置 dns 地址为 223.5.5.5，然后重启 systemd-resolved.service 服务，
此时再去启动 dnsmasq.service 服务就能成功了。
```

项目默认自动生成的 `/etc/dnsmasq.d/dbc.conf` 如下:

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
dhcp-range=192.168.1.50,192.168.1.80,255.255.255.0,45m
# dhcp-range=192.168.1.50,proxy,255.255.255.0,45m
```

### isc-dhcp-server

若需要安装 isc-dhcp-server 可参考下面的步骤:

```shell
# 安装 isc-dhcp-server
$ sudo apt install isc-dhcp-server
# 查看 isc-dhcp-server 服务运行情况
$ systemctl status isc-dhcp-server.service
```

```tips
使用 isc-dhcp-server 服务需要在 /etc/default/isc-dhcp-server 文件中设置具体的网卡，指定为哪个网卡启用 DHCP 服务。
```

isc-dhcp-server 在 `/etc/dhcp/dhcpd.conf` 中的设置如下:

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

- https://www.isc.org/kea/
- https://kea.readthedocs.io/en/latest/arm/ctrl-channel.html
- https://github.com/search?q=python+dhcp
- https://github.com/pypxe/PyPXE

## TFTP

PXE 服务器常常使用 TFTP 服务来传输 DHCP 设置的 bootfile。

TFTP（Trivial File Transfer Protocol,简单文件传输协议）是 TCP/IP 协议族中的一个用来在客户机与服务器之间进行简单文件传输的协议，提供不复杂、开销不大的文件传输服务，端口号为69。

TFTP 通常基于UDP协议而实现，但是也不能确定有些 TFTP 协议是基于其它传输协议完成的。TFTP 协议的设计目的主要是为了进行小文件传输，因此它不具备通常的 FTP 的许多功能，例如，它只能从文件服务器上获得或写入文件，不能列出目录，不进行认证。

TFTP 代码所占的内存较小，这对于较小的计算机或者某些特殊用途的设备来说是很重要的，这些设备不需要硬盘，只需要固化了 TFTP、UDP 和 IP 的小容量只读存储器即可。因此，随着嵌入式设备在网络设备中所占的比例的不断提升，TFTP 协议被越来越广泛的使用。

```shell
# 安装 TFTP 服务
$ sudo apt install tftpd-hpa
# 查看 tftpd-hpa 服务运行情况
$ systemctl status tftpd-hpa.service
```

tftpd-hpa 默认使用 `/srv/tftp` 文件夹作为存储目录，需要在此目录中放入 `undionly.kpxe` 和 `ipxe.efi`，这两个文件可以使用 ipxe 官网提供的文件，我们推荐使用自定义脚本自行编译文件，后面将介绍如何编译 iPXE。

iPXE 官网提供的启动文件下载地址如下：

- undionly.kpxe: https://boot.ipxe.org/undionly.kpxe
- ipxe.efi: https://boot.ipxe.org/ipxe.efi

## HTTP

iPXE 可以使用更加稳定可靠的 HTTP 协议下载需要的文件，可以使用 apache 或者 nginx 搭建 HTTP 服务器，下面以 nginx 为例：

```shell
# 安装 nginx，参考 http://nginx.org/en/linux_packages.html#Ubuntu
$ sudo apt install nginx
```

在 `/etc/nginx/nginx.conf` 文件中 http 块添加以下 server 块：

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

最后重启 nginx 就能把 `/var/www/file` 目录搭建成文件服务器，使用 8080 端口的 url 在浏览器中访问。

```shell
dbtu@dbtu:/var/www/file$ tree
.
├── ipxe
│   ├── boot.ipxe
│   ├── boot.ipxe.cfg
│   ├── cfg
│   │   ├── 404.html
│   │   ├── mac-0050562ca04b.ipxe.cfg
│   │   ├── mac-40b0767ee231.ipxe.cfg
│   │   └── mac-88aedd0508fa.ipxe.cfg
│   └── wimboot
├── netboot
│   ├── ldlinux.c32 -> ubuntu-installer/amd64/boot-screens/ldlinux.c32
│   ├── netboot.tar.gz
│   ├── pxelinux.0 -> ubuntu-installer/amd64/pxelinux.0
│   ├── pxelinux.cfg -> ubuntu-installer/amd64/pxelinux.cfg
│   ├── ubuntu-installer
│   │   └── amd64
│   │       ├── boot-screens
│   │       │   ├── adtxt.cfg
│   │       │   ├── exithelp.cfg
│   │       │   ├── f10.txt
│   │       │   ├── f1.txt
│   │       │   ├── f2.txt
│   │       │   ├── f3.txt
│   │       │   ├── f4.txt
│   │       │   ├── f5.txt
│   │       │   ├── f6.txt
│   │       │   ├── f7.txt
│   │       │   ├── f8.txt
│   │       │   ├── f9.txt
│   │       │   ├── ldlinux.c32
│   │       │   ├── libcom32.c32
│   │       │   ├── libutil.c32
│   │       │   ├── menu.cfg
│   │       │   ├── prompt.cfg
│   │       │   ├── rqtxt.cfg
│   │       │   ├── splash.png
│   │       │   ├── stdmenu.cfg
│   │       │   ├── syslinux.cfg
│   │       │   ├── txt.cfg
│   │       │   └── vesamenu.c32
│   │       ├── initrd.gz
│   │       ├── linux
│   │       ├── pxelinux.0
│   │       └── pxelinux.cfg
│   │           └── default -> ../boot-screens/syslinux.cfg
│   └── version.info
├── ubuntu
│   └── preseed.cfg
└── winpe
    ├── amd64
    │   ├── fwfiles
    │   │   ├── efisys.bin
    │   │   └── etfsboot.com
    │   ├── media
    │   │   ├── bg-bg
    │   │   │   └── bootmgr.efi.mui
    │   │   ├── Boot
    │   │   │   ├── BCD
    │   │   │   ├── bg-bg
    │   │   │   │   └── bootmgr.exe.mui
    │   │   │   ├── bootfix.bin
    │   │   │   ├── boot.sdi
    │   │   │   ├── en-us
    │   │   │   │   ├── bootmgr.exe.mui
    │   │   │   │   └── memtest.exe.mui
    │   │   │   ├── Fonts
    │   │   │   │   ├── chs_boot.ttf
    │   │   │   │   ├── cht_boot.ttf
    │   │   │   │   ├── jpn_boot.ttf
    │   │   │   │   ├── kor_boot.ttf
    │   │   │   │   ├── malgun_boot.ttf
    │   │   │   │   ├── malgunn_boot.ttf
    │   │   │   │   ├── meiryo_boot.ttf
    │   │   │   │   ├── meiryon_boot.ttf
    │   │   │   │   ├── msjh_boot.ttf
    │   │   │   │   ├── msjhn_boot.ttf
    │   │   │   │   ├── msyh_boot.ttf
    │   │   │   │   ├── msyhn_boot.ttf
    │   │   │   │   ├── segmono_boot.ttf
    │   │   │   │   ├── segoen_slboot.ttf
    │   │   │   │   ├── segoe_slboot.ttf
    │   │   │   │   └── wgl4_boot.ttf
    │   │   │   ├── memtest.exe
    │   │   │   ├── Resources
    │   │   │   │   └── bootres.dll
    │   │   │   ├── zh-cn
    │   │   │   │   ├── bootmgr.exe.mui
    │   │   │   │   └── memtest.exe.mui
    │   │   │   └── zh-tw
    │   │   │       ├── bootmgr.exe.mui
    │   │   │       └── memtest.exe.mui
    │   │   ├── bootmgr
    │   │   ├── bootmgr.efi
    │   │   ├── EFI
    │   │   │   ├── Boot
    │   │   │   │   ├── bootx64.efi
    │   │   │   │   └── en-us
    │   │   │   │       └── bootx64.efi.mui
    │   │   │   └── Microsoft
    │   │   │       └── Boot
    │   │   │           ├── BCD
    │   │   │           ├── en-us
    │   │   │           │   └── memtest.efi.mui
    │   │   │           ├── Fonts
    │   │   │           │   ├── chs_boot.ttf
    │   │   │           │   ├── cht_boot.ttf
    │   │   │           │   ├── jpn_boot.ttf
    │   │   │           │   ├── kor_boot.ttf
    │   │   │           │   ├── malgun_boot.ttf
    │   │   │           │   ├── meiryo_boot.ttf
    │   │   │           │   ├── msjh_boot.ttf
    │   │   │           │   ├── msyh_boot.ttf
    │   │   │           │   ├── segmono_boot.ttf
    │   │   │           │   ├── segoe_slboot.ttf
    │   │   │           │   └── wgl4_boot.ttf
    │   │   │           ├── memtest.efi
    │   │   │           ├── Resources
    │   │   │           │   └── bootres.dll
    │   │   │           ├── zh-cn
    │   │   │           │   └── memtest.efi.mui
    │   │   │           └── zh-tw
    │   │   │               └── memtest.efi.mui
    │   │   ├── en-us
    │   │   │   └── bootmgr.efi.mui
    │   │   ├── sources
    │   │   │   └── boot.wim
    │   └── mount
    ├── lightningWinPE
    │   ├── boot
    │   │   ├── bcd
    │   │   └── boot.sdi
    │   ├── bootmgr
    │   ├── bootmgr.efi
    │   ├── efi
    │   │   ├── boot
    │   │   │   └── bootx64.efi
    │   │   └── microsoft
    │   │       └── boot
    │   │           └── bcd
    │   └── sources
    │       └── BOOT.WIM
    ├── wepe
    │   ├── EFI
    │   │   ├── BOOT
    │   │   │   └── bootx64.efi
    │   │   └── MICROSOFT
    │   │       └── BOOT
    │   │           ├── BCD
    │   │           └── FONTS
    │   │               └── wgl4_boot.ttf
    │   ├── WEIPE
    │   └── WEPE
    │       ├── B64
    │       ├── FONTS
    │       │   └── wgl4_boot.ttf
    │       ├── MESSAGE
    │       ├── PELOAD
    │       ├── WEIPE
    │       ├── WEPE64
    │       ├── WEPE64.WIM
    │       ├── WEPE.INI
    │       ├── WEPE.SDI
    │       └── WEPE.TXT
    └── WePE64_V2.2.iso
```

- ipxe 文件夹下存放的是 iPXE 的启动脚本，其中 mac-000c29c63944.ipxe.cfg 以 MAC 地址去除冒号全小写格式命名，每个被引导的机器都需要有一个对应的配置文件，由控制台程序自动生成。
- wimboot 文件从 https://github.com/ipxe/wimboot/releases 下载。
- winpe 下面存放安装 Windows 系统所用的 PE 文件，暂时不需要，开发测试使用。
- netboot 是网络安装 ubuntu 所用的文件，可以从阿里云或者清华源下面，如果客户需要 ubuntu 系统镜像就需要下载此文件。
- ubuntu/preseed.cfg 是网络安装 ubuntu 使用的无人值守配置文件。

[ubuntu 18.04 netboot](http://www.archive.ubuntu.com/ubuntu/dists/bionic-updates/main/installer-amd64/current/images/netboot/netboot.tar.gz)

其中 `ipxe/boot.ipxe` 文件内容如下：

```
#!ipxe
chain --autofree boot.ipxe.cfg
chain --replace cfg/mac-${mac:hexraw}.ipxe.cfg
```

其中 ipxe/boot.ipxe.cfg 文件内容如下：

```
#!ipxe
set iscsi-server 192.168.1.159
set base-url http://192.168.1.159:8080
set menu-timeout 5000
```

其中 iscsi-server 的 IP 地址即无盘网起服务器的 IP 地址，base-url 即 HTTP 服务的 url，这些内容请根据实际情况自行设置。

## WinPE

可以使用 WinPE 给无盘安装系统，但系统的兼容性方面还有很多问题待解决。

- ADK 制作工具: https://learn.microsoft.com/zh-cn/windows-hardware/get-started/adk-install
- 微软官方文档: https://learn.microsoft.com/zh-cn/windows-hardware/manufacture/desktop/winpe-intro?view=windows-10

## iPXE

编译 iPXE 的过程可以参考: https://ipxe.org/download

```shell
$ git clone https://github.com/ipxe/ipxe.git
$ cd ipxe/src
```

在 ipxe/src 文件夹中创建 `script.ipxe`,文件内容为：

```
#!ipxe
dhcp
chain --autofree http://192.168.1.2:8080/ipxe/boot.ipxe
```

此处 192.168.1.2 为无盘网起服务器的 IP 地址，8080 端口为 nginx 配置的 HTTP 服务的端口，请根据各自的实际配置填写。

然后使用 `script.ipxe` 编译 iPXE 启动文件，就能在启动 PXE 引导后自动加载 HTTP 服务提供的 `boot.ipxe` 配置，使用以下命令编译：

```shell
$ make bin-x86_64-pcbios/undionly.kpxe EMBED=script.ipxe
$ make bin-x86_64-efi/ipxe.efi EMBED=script.ipxe
```

将编译好的 `undionly.kpxe` 和 `ipxe.efi` 文件拷贝到 TFTP 服务目录。

```shell
$ sudo cp bin-x86_64-pcbios/undionly.kpxe /srv/tftp/
$ sudo cp bin-x86_64-efi/ipxe.efi /srv/tftp/
```

iPXE 官网: https://ipxe.org/
