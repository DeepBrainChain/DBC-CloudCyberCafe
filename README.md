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

官方文档: https://ipxe.org/

## iSCSI

- https://github.com/open-iscsi/targetcli-fb
- https://github.com/open-iscsi/rtslib-fb

## 安装准备

因为对 iSCSI 和存储池(lvm2) 的操作很多都需要 `sudo` 权限，所以建议用户使用 `sudo` 时免密码验证。

在 `/etc/sudoers` 中添加内容 `dbc	ALL=(root) NOPASSWD:ALL`。

```shell
sudo apt install targetcli-fb open-iscsi python3-pip
sudo pip3 install dash pandas
```

## HTTP

```shell
# netboot 也可以使用阿里云或者清华源的下载
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

https://www.isc.org/kea/

https://kea.readthedocs.io/en/latest/arm/ctrl-channel.html

https://github.com/search?q=python+dhcp

https://github.com/pypxe/PyPXE

## WinPE

- ADK 制作工具: https://learn.microsoft.com/zh-cn/windows-hardware/get-started/adk-install
- 微软官方文档: https://learn.microsoft.com/zh-cn/windows-hardware/manufacture/desktop/winpe-intro?view=windows-10

## Thrift

https://thrift.apache.org/

https://github.com/apache/thrift
