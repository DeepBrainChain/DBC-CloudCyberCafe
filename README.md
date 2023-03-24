# CloudCyberCafe

Cloud CyberCafe -- iPXE + iSCSI 无盘启动方案

项目使用 iPXE 引导启动，使用 iSCSI 做无盘服务，使用 lvm2 做存储管理，使用 thrift 做 API 接口，使用 plotly 提供控制台界面，共同组合为客户提供无盘启动服务。

## 无盘服务器的部署

1. [部署 iPXE 服务器](ipxe/README.md)
2. [部署存储服务](plotly/storage.md)
3. [运行并设置无盘控制台](plotly/README.md)

参考 [DBC Wiki](https://deepbrainchain.github.io/DBC-Wiki/dbc-cloud-cybercafe/diskless-netboot-server.html)

## 镜像制作上传流程

1. 给无盘客户端的自带硬盘安装上Windows系统和必要的驱动，解决设备管理器的感叹号，或者禁用感叹号的设备。
2. 将注册表`HKEY_LOCAL_MACHINE\SYSTEM\ControlSet001\Control\Session Manager\Memory Management`的`PagingFiles`项的值清空。此操作跟虚拟内存有关。需要手动重启生效。
3. 启动iSCSI发起程序，修改配置中发起程序名称，输入无盘服务器的IP地址，连接远程磁盘。
4. 重启以使某些修改生效。
5. 使用磁盘精灵[DiskGenius](https://www.diskgenius.cn/)克隆磁盘，热迁移系统。将此时的系统所在整个磁盘上传到无盘存储磁盘。

备注:
1. 测试阶段请先使用纯系统和必要的驱动来测试，启动成功后再安装其他软件游戏进一步测试。
2. 镜像的上传方式以后会优化，升级成热迁移或者进入WinPE使用磁盘精灵操作。

参考 [DBC Wiki](https://deepbrainchain.github.io/DBC-Wiki/dbc-cloud-cybercafe/diskless-netboot-image.html)

视频教程:

- windows：https://www.youtube.com/watch?v=wRbOvZcp17I
- ubuntu：https://www.youtube.com/watch?v=C50i5ZS3KwY
