# plotly

本项目使用 plotly 实现管理控制台，无盘的存储方案请参考 [storage](storage.md)

## 准备

要编译和运行管理控制台，需要做些准备工作。

### 权限设置

因为对 iSCSI 和存储池(lvm2) 的操作很多都需要 `sudo` 权限，所以建议用户使用 `sudo` 时免密码验证。

在 `/etc/sudoers` 中添加内容 `dbc	ALL=(ALL) NOPASSWD:ALL`，给 `dbc` 用户添加免密权限。

```
#
# This file MUST be edited with the 'visudo' command as root.
#
# Please consider adding local content in /etc/sudoers.d/ instead of
# directly modifying this file.
#
# See the man page for details on how to write a sudoers file.
#
Defaults        env_reset
Defaults        mail_badpass
Defaults        secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin"

# Host alias specification

# User alias specification

# Cmnd alias specification

# User privilege specification
root    ALL=(ALL:ALL) ALL

# Members of the admin group may gain root privileges
%admin ALL=(ALL) ALL

# Allow members of group sudo to execute any command
%sudo   ALL=(ALL:ALL) ALL
dbc  ALL=(ALL) NOPASSWD:ALL

# See sudoers(5) for more information on "#include" directives:

#includedir /etc/sudoers.d
```

### API

本项目使用 thrift rpc 框架对外提供 API 接口，以方便第三方程序(主要是指 dbc 程序)设置机器进入 Windows 还是 Ubuntu 系统，
修改系统的登录密码和关闭无盘的客户机等操作。因此无盘网起服务器需要安装必要的 thrift 工具。

```shell
$ sudo apt install thrift-compiler python3-pip
$ pip3 install thrift
```

- https://thrift.apache.org/
- https://github.com/apache/thrift

## 运行管理控制台

```shell
$ pip3 install dash pandas thrift diskcache requests Deprecated
# 下载项目代码
$ git clone https://github.com/DeepBrainChain/DBC-CloudCyberCafe.git
$ cd DBC-CloudCyberCafe/preset/
$ thrift --gen py preset.thrift
$ cd ../plotly/
$ sudo python3 home.py
```

然后浏览器中输入 http://localhost:8050/ 即可访问控制台。切忌不要忘了将 localhost 换成无盘网起服务器的 IP 地址。

## 打包管理控制台

```shell
# 1. 需要安装 PyInstaller;
$ pip3 install pyinstaller
# 2. 请提前生成 thrift 协议文件;
$ cd <代码目录>/preset/
$ thrift --gen py preset.thrift
# 3. 使用 PyInstaller 打包命令。
$ cd <代码目录>/plotly/
$ python3 -m PyInstaller -F -n occ home.py -p ../preset/gen-py/
```

或者使用 `pyinstaller -F -n occ home.py -p ../preset/gen-py/` 命令来打包，其中 `-n occ` 指定生成的程序名为 `occ`。

