# Preset

预先安装的系统服务，用于提供修改密码等功能。

## building

生成服务协议的CPP文件。

```
sudo apt install thrift-compiler
thrift --gen cpp preset.thrift
```

Linux

```
mkdir build
cd build
cmake ..
make
```

Windows 打开 Developer Command Prompt for VS 2019

```
cmake -G "Visual Studio 16 2019" -A Win32 . -B "build32"
cmake -G "Visual Studio 16 2019" -A x64 . -B "build64"
cmake --build build32 --config Release
cmake --build build64 --config Release
```

## autostart service

设置开机启动系统服务

### Linux

`/etc/systemd/system/preset.service`

```
[Unit]
# 服务名称，可自定义
Description=preset
After=network.target syslog.target
Wants=network.target

[Service]
Type=simple
# 启动preset的命令，需修改为您的preset的安装路径
ExecStart=/usr/local/bin/Preset
RestartSec=3s
Restart=always

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl enable preset.service
sudo systemctl start preset.service
```

### Windows

[nssm](https://nssm.cc/download)

- 安装服务: nssm.exe install
- 修改服务: nssm.exe edit <服务名>
- 删除服务: nssm.exe remove <服务名> [confirm]
- 启动服务: nssm.exe start <服务名>
- 停止服务: nssm.exe stop <服务名>
- 重启服务: nssm.exe restart <服务名>

删除服务或者更新服务程序前先停止服务。

[NSIS打包发布WindowsService(Windows服务)](https://www.cnblogs.com/lv-jinliang/articles/15748044.html)
