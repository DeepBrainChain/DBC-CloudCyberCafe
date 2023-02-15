from dash import Dash, dash_table, dcc, html, callback_context, no_update
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
# import dash_daq as daq
import os
import re
import json

import global_config
import lvm2
import iscsi
import dhcp
import ipxe
import util

import rpc_handler
from threading import Thread

from smyoo import Smyoo
from error_code import ErrorCode

global_config._init()
smyoo = Smyoo()

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# external_stylesheets = ['./style.css']

df_hosts = pd.DataFrame.from_dict(global_config.get_value('hosts'))
df_os = pd.DataFrame.from_dict(global_config.get_value('operation_system'))
df_data_disk = pd.DataFrame.from_dict(global_config.get_value('data_disk'))
df_boot_menu = pd.DataFrame.from_dict(global_config.get_value('boot_menu'))
# print(list(global_config.get_value('operation_system').keys()))
# print(pd.Index(list(global_config.get_value('operation_system').keys())))

hosts_precautions = '''
### 注意事项

1. 添加修改删除 host_name, ip address, mac address 需要重启 DHCP 服务才能生效。
2. host_name, ip address, mac address 均不能重复。
3. 若无盘网络启动服务器重启，会导致某些服务设置丢失，请在控制台重新运行后首先点击上面的 "Restore the environment and settings after the server restarts" 按钮来恢复运行环境和设置。
4. 修改基础无盘镜像的步骤:
    - 4.1. 修改前请先关闭所有正在使用此镜像的所有机器，只保留运行超管权限的一台机器；
    - 4.2. 点击Boot Menu表格下的"Delete boot menu snap"清理所有基础镜像的快照。
    - 4.3. 使用超管权限启动保留的机器，进入基础镜像中修改需要的设置、安装软件或者下载游戏。
    - 4.4. 修改完成后关机，取消超管权限，再次启动其他机器前依旧需要重新生成镜像快照。
    - 4.5. 使用新的镜像快照启动使用。
'''

app = Dash(__name__)
# app = Dash(__name__, external_stylesheets=external_stylesheets)

tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}

app.layout = html.Div([
    html.H1(
        children='DBC Cloud Cybercafe',
        style={
            'textAlign': 'center'
        }
    ),
    dcc.Tabs(id="tabs-styled-with-props", value='hosts', children=[
        dcc.Tab(label='Hosts', value='hosts', style=tab_style,
            selected_style=tab_selected_style, children=[
            html.Div(children=[
                dash_table.DataTable(
                    id='hosts-table',
                    columns=[{
                        "name": i,
                        "id": i,
                        "selectable": True
                        # "editable": (i not in ['mac', 'default_menu'])
                    } for i in df_hosts.columns],
                    data=df_hosts.to_dict('records'),
                    # editable=True,
                    sort_action="native",
                    sort_mode="multi",
                    # style_data_conditional=[
                    #     {
                    #         'if': {
                    #             'filter_query': '{{{col}}} = "N/A"'.format(col=col),
                    #             'column_id': col
                    #         },
                    #         'backgroundColor': 'tomato',
                    #         'color': 'white'
                    #     } for col in df_hosts.columns
                    # ],
                    row_selectable="single",
                    # row_deletable=True,
                    page_action="native",
                    page_current=0,
                    page_size=20,
                    style_data_conditional=[{
                        'if': {'column_editable': False},
                        'backgroundColor': 'AliceBlue',
                        # 'color': 'white'
                    }],
                    style_header_conditional=[{
                        'if': {'column_editable': False},
                        'backgroundColor': 'AliceBlue',
                        # 'color': 'white'
                    }],
                    # persistence=True,
                    # persisted_props=['columns.name', 'data', 'filter_query',
                    #     'hidden_columns', 'page_current', 'selected_columns',
                    #     'selected_rows', 'sort_by'],
                ),
                html.Br(),
                html.Div(children=[
                    html.Label('host name: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='host-name-input', type='text', style={'width':100}),
                    html.Label(style={'width':10}),
                    html.Label('ip address: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='host-ip-input', type='text', style={'width':120}),
                    html.Label(style={'width':10}),
                    html.Label('mac address: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='host-mac-input', type='text', style={'width':120}),
                    html.Label(style={'width':10}),
                    html.Label('default menu: '),
                    html.Label(style={'width':10}),
                    dcc.Dropdown(id='host-default-menu-dropdown',
                        options=global_config.get_value('boot_menu')['name'],
                        style={'width':200}),
                    html.Label(style={'width':10}),
                    dcc.Checklist(id='host-super-tube-checklist', options=['Super tube'])
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(children=[
                    html.Button('Add/Modify Row', id='add-host-button', n_clicks=0),
                    html.Label(style={'width':10}),
                    html.Button('Delete Row', id='delete-host-button', n_clicks=0),
                    html.Label(style={'width':10}),
                    html.Button('Power On', id='power-on-button', n_clicks=0),
                    html.Label(style={'width':10}),
                    html.Button('Power Off', id='power-off-button', n_clicks=0),
                    html.Label(style={'width':10}),
                    html.Button('Reset Host Image', id='reset-host-image', n_clicks=0),
                    # html.Label(style={'width':10}),
                    # dcc.Checklist(id='super-tube-checklist', options=['Super tube']),
                    html.Label(style={'width':10}),
                    html.Button('Restart DHCP', id='restart-dhcp-button', n_clicks=0),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(id='operate-host-state'),
                html.Div(children=[
                    html.Button('Restore the environment and settings after the \
                    server restarts', id='restore-after-restart-button', n_clicks=0),
                    html.Div(id='restore-after-restart-state')
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                dcc.Markdown(children=hosts_precautions)
            ], style={'padding': 10, 'flex': 1})
        ]),
        dcc.Tab(label='Image', value='image', style=tab_style,
            selected_style=tab_selected_style, children=[
            html.Div(children=[
                html.H2('Operation System'),
                dash_table.DataTable(
                    id='os-table',
                    columns=[{
                        "name": i,
                        "id": i,
                        "selectable": True
                        # "editable": (i not in ['mac', 'default_menu'])
                    } for i in df_os.columns],
                    data=df_os.to_dict('records'),
                    # editable=True,
                    sort_action="native",
                    sort_mode="multi",
                    row_selectable="single",
                    # row_deletable=True,
                    page_action="native",
                    page_current=0,
                    page_size=20,
                ),
                html.Br(),
                html.Div(children=[
                    html.Label('name: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='os-name-input', type='text'),
                    html.Label(style={'width':10}),
                    html.Label('description: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='os-description-input', type='text'),
                    html.Label(style={'width':10}),
                    html.Label('capacity(G): '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='os-capacity-input', type='number', min=1, max=1024,step=1),
                    # daq.NumericInput(id='os-capacity-input',value=30,min=1,max=1024,size=70),
                    # html.Label(style={'width':10}),
                    # html.Label('iscsi target: '),
                    # html.Label(style={'width':10}),
                    # dcc.Input(id='os-iscsi-target-input', type='text', style={'width':300})
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(children=[
                    html.Button('Add Operation System', id='add-os-button', n_clicks=0),
                    html.Label(style={'width':10}),
                    html.Button('Delete Operation System', id='del-os-button', n_clicks=0),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(id='operate-operation-system-state'),
                html.H2('Data Disk'),
                dash_table.DataTable(
                    id='data-disk-table',
                    columns=[{
                        "name": i,
                        "id": i,
                        "selectable": True
                    } for i in df_data_disk.columns],
                    data=df_data_disk.to_dict('records'),
                    # editable=True,
                    sort_action="native",
                    sort_mode="multi",
                    row_selectable="single",
                    # row_deletable=True,
                    page_action="native",
                    page_current=0,
                    page_size=20,
                ),
                html.Br(),
                html.Div(children=[
                    html.Label('name: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='data-disk-name-input', type='text'),
                    html.Label(style={'width':10}),
                    html.Label('description: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='data-disk-description-input', type='text'),
                    html.Label(style={'width':10}),
                    html.Label('capacity(G): '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='data-disk-capacity-input', type='number', min=1, max=1024,step=1),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(children=[
                    html.Button('Add data disk', id='add-data-disk-button', n_clicks=0),
                    html.Label(style={'width':10}),
                    html.Button('Delete data disk', id='del-data-disk-button', n_clicks=0),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(id='operate-data-disk-state'),
                html.H2('Boot Menu'),
                dash_table.DataTable(
                    id='boot-menu-table',
                    columns=[{
                        "name": i,
                        "id": i,
                        "selectable": True
                    } for i in df_boot_menu.columns],
                    data=df_boot_menu.to_dict('records'),
                    # editable=True,
                    sort_action="native",
                    sort_mode="multi",
                    row_selectable="single",
                    # row_deletable=True,
                    page_action="native",
                    page_current=0,
                    page_size=20,
                ),
                html.Br(),
                html.Div(children=[
                    html.Label('name: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='boot-menu-name-input', type='text'),
                    html.Label(style={'width':10}),
                    html.Label('operation system: '),
                    html.Label(style={'width':10}),
                    dcc.Dropdown(id='boot-menu-operation-system-dropdown',
                        options=global_config.get_value('operation_system')['name'],
                        style={'width':200}),
                    html.Label(style={'width':10}),
                    html.Label('data disk: '),
                    html.Label(style={'width':10}),
                    dcc.Dropdown(id='boot-menu-data-disk-dropdown',
                        options=global_config.get_value('data_disk')['name'],
                        multi=True, style={'width':500})
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(children=[
                    html.Button('Add boot menu', id='add-boot-menu-button', n_clicks=0),
                    html.Label(style={'width':10}),
                    html.Button('Delete boot menu', id='del-boot-menu-button', n_clicks=0),
                    html.Label(style={'width':10}),
                    html.Button('Delete boot menu snap', id='del-boot-menu-snap-button', n_clicks=0),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(id='operate-boot-menu-state')
            ], style={'padding': 10, 'flex': 1})
        ]),
        dcc.Tab(label='Setting', value='setting', style=tab_style,
            selected_style=tab_selected_style, children=[
            html.Div(children=[
                html.H2('Storage'),
                html.Div(children=[
                    html.Label('Volume Group: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='volume-group-name-input', type='text', debounce=True,
                        value=global_config.get_value('volume_group_name'),
                        persistence=True),
                    html.Label(style={'width':10}),
                    html.Div(id='operate-volume-group-name-state')
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(children=[
                    html.Label('COW LV Size(G): '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='cow-lv-size-input', type='number', value=10,
                        min=1, max=1024, step=1, persistence=True),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.H2('DHCP'),
                html.Div(children=[
                    html.Label('network name: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-network-name-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['network_name'],
                        persistence=True),
                    html.Label(style={'width':10}),
                    html.Label('interface: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-interface-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['interface'],
                        persistence=True, style={'width':100}),
                    html.Label(style={'width':10}),
                    html.Div(id='operate-dhcp-network-name-state')
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(children=[
                    html.Label('subnet: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-subnet-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['subnet'],
                        persistence=True, style={'width':100}),
                    html.Label(style={'width':10}),
                    html.Label('subnet mask: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-subnet-mask-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['subnet_mask'],
                        persistence=True, style={'width':100}),
                    html.Label(style={'width':10}),
                    html.Label('range: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-range-from-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['range_from'],
                        persistence=True, style={'width':100}),
                    html.Label(style={'width':10}),
                    html.Label(' - '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-range-to-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['range_to'],
                        persistence=True, style={'width':100}),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(children=[
                    html.Label('routers: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-routers-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['routers'],
                        persistence=True),
                    html.Label(style={'width':10}),
                    html.Label('dns servers: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-dns-servers-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['dns_servers'],
                        persistence=True),
                    html.Label(style={'width':10}),
                    html.Label('broadcast address: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-broadcast-address-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['broadcast_address'],
                        persistence=True, style={'width':100}),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(children=[
                    html.Label('filename: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-filename-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['filename'],
                        persistence=True, style={'width':300}),
                    html.Label(style={'width':10}),
                    html.Label('next server: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-next-server-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['next_server'],
                        persistence=True, style={'width':100}),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Div(id='operate-dhcp-server-state'),
                html.H2('HTTP'),
                html.Div(children=[
                    html.Label('root path: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='http-root-path-input', type='text', debounce=True,
                        value=global_config.get_value('http_server')['root_path'],
                        persistence=True),
                    html.Label(style={'width':10}),
                    html.Label('http ip:port '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='http-base-url-input', type='text', debounce=True,
                        value=global_config.get_value('http_server')['base_url'],
                        persistence=True),
                    html.Div(id='operate-http-server-state'),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.H2('iSCSI'),
                html.Div(children=[
                    html.Label('iscsi server: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='iscsi-server-input', type='text', debounce=True,
                        value=global_config.get_value('iscsi_setting')['server'],
                        persistence=True, style={'width':100}),
                    html.Label(style={'width':10}),
                    html.Label('initiator iqn: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='iscsi-initiator-iqn-input', type='text', debounce=True,
                        value=global_config.get_value('iscsi_setting')['initiator_iqn'],
                        persistence=True, style={'width':300}),
                    html.Label(style={'width':10}),
                    html.Label('target prefix: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='iscsi-target-prefix-input', type='text', debounce=True,
                        value=global_config.get_value('iscsi_setting')['iscsi_target_prefix'],
                        persistence=True, style={'width':200}),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Div(id='operate-iscsi-setting-state'),
                html.H2('Smyoo'),
                html.Div(children=[
                    html.Label('phone number: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='smyoo-phone-input', type='tel', debounce=True,
                        value=global_config.get_cache('smyoo_phone',default=''),
                        placeholder='input type telphone number',
                        persistence=True),
                    html.Label(style={'width':10}),
                    html.Label('password '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='smyoo-password-input', type='password', debounce=True,
                        value=global_config.get_cache('smyoo_password',default=''),
                        placeholder='input type password',
                        persistence=True),
                    html.Div(id='operate-smyoo-state'),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
            ], style={'padding': 10, 'flex': 1})
        ])
    ], style=tabs_styles),
    html.Div(id='tabs-content-props'),
    dcc.Interval(id='thrift-interval',interval=1*500,n_intervals=0),
    dcc.Store(id='thrift-network-notify')
])

def update_ipxe_cfg(mac_addr, default_boot, super_tube):
    root_path = global_config.get_value('http_server')['root_path']
    format_mac = ''.join(mac_addr.split(':')).lower()
    iscsi_setting = global_config.get_value('iscsi_setting')
    boot_menu = global_config.get_value('boot_menu')
    ipxe.edit_ipxe_cfg(os.path.join(root_path, 'ipxe', 'cfg'), format_mac,
        iscsi_setting['initiator_iqn'], iscsi_setting['iscsi_target_prefix'],
        boot_menu['name'], default_boot, super_tube)

def reset_host_boot_menu(mac_addr, boot_item, snap_lv_size):
    iscsi_setting = global_config.get_value('iscsi_setting')
    iscsi.delete_snap_iscsi_objects_by_host(iscsi_setting['iscsi_target_prefix'],
        boot_item, mac_addr)

    boot_menu = global_config.get_value('boot_menu')
    if boot_item not in boot_menu['name']:
        return 1, 'boot item not existed'

    menu_index = boot_menu['name'].index(boot_item)
    disks = []
    disks.append(boot_menu['operation_system'][menu_index])
    disks.extend(boot_menu['data_disk'][menu_index].split(','))
    disks = util.deduplication(disks)

    volume_group = global_config.get_value('volume_group_name')
    lv_list = lvm2.get_logical_volume_list(volume_group)

    for index, disk in enumerate(disks):
        snap_disk = f'{disk}_{mac_addr}'
        # if snap_disk in lv_list:
        lvm2.remove_logical_volume(volume_group, snap_disk)
        result_code, result_message = lvm2.create_snapshot_logical_volume(
            volume_group, disk, mac_addr, snap_lv_size)
        if result_code != 0:
            return result_code, result_message
        disks[index] = snap_disk

    initiator_iqn = '%s:sn.%s.%s' % (iscsi_setting['iscsi_target_prefix'],
        boot_item, mac_addr)
    result_code, result_message = iscsi.create_iscsi_target(boot_item, disks,
        iscsi_setting['iscsi_target_prefix'], initiator_iqn)
    if result_code != 0:
        for disk in disks:
            lvm2.remove_logical_volume(volume_group, disk)
        return result_code, result_message
    return 0, 'reset successful'

def remove_snapshot_storage_item_of_host(mac_addr, boot_item):
    iscsi_setting = global_config.get_value('iscsi_setting')
    iscsi.delete_snap_iscsi_objects_by_host(iscsi_setting['iscsi_target_prefix'],
        boot_item, mac_addr)

    boot_menu = global_config.get_value('boot_menu')
    menu_index = boot_menu['name'].index(boot_item)
    disks = []
    disks.append(boot_menu['operation_system'][menu_index])
    disks.extend(boot_menu['data_disk'][menu_index].split(','))
    disks = util.deduplication(disks)

    volume_group = global_config.get_value('volume_group_name')

    for index, disk in enumerate(disks):
        snap_disk = f'{disk}_{mac_addr}'
        lvm2.remove_logical_volume(volume_group, snap_disk)

def remove_snapshot_storage_of_host(mac_addr):
    boot_menu = global_config.get_value('boot_menu')
    for boot_item in boot_menu['name']:
        remove_snapshot_storage_item_of_host(mac_addr, boot_item)

def update_smyoo_session(phone, password):
    if len(phone) == 0 or len(password) == 0:
        return 1, 'invalid phone or password'
    bpeSessionId, resultMsg = smyoo.login(phone, password)
    if bpeSessionId is None:
        return 1, resultMsg
    global_config.set_cache('smyoo_session', bpeSessionId, expire=3600*24)
    return 0, bpeSessionId

def update_smyoo_devices_info():
    bpeSessionId = global_config.get_cache('smyoo_session', default='')
    if len(bpeSessionId) == 0:
        return 1, 'Smyoo session of cookie is None'
    updateTime, resultMsg = smyoo.statusChanged(bpeSessionId)
    if updateTime is None:
        return 1, resultMsg
    updateTimeCache = global_config.get_cache('smyoo_updatetime', default='')
    if updateTime != updateTimeCache:
        devices, resultMsg = smyoo.queryDevices(bpeSessionId)
        if devices is None:
            return 1, resultMsg
        global_config.set_cache('smyoo_updatetime', updateTime)
        global_config.set_cache('smyoo_devices', json.dumps(devices))
    return 0, 'success'

def get_smyoo_host_mcuid(hostname):
    devicesContent = global_config.get_cache('smyoo_devices',default='')
    if len(devicesContent) == 0:
        return None
    try:
        devices = json.loads(devicesContent)
        for device in devices:
            if device['mcuname'] == hostname:
                return device['mcuid']
    except:
        print('get smyoo host mcuid failed')
    return None

def smyoo_host_power_control(op,hostname=None, ipaddr=None, updatedevices=False):
    bpeSessionId = global_config.get_cache('smyoo_session', default=None)
    if bpeSessionId is None:
        result_code, result_message = update_smyoo_session(
            global_config.get_cache('smyoo_phone',default=''),
            global_config.get_cache('smyoo_password',default=''))
        if result_code != 0:
            return result_code, result_message
        bpeSessionId = result_message
    if updatedevices:
        result_code, result_message = update_smyoo_devices_info()
        if result_code != 0:
            return result_code, result_message
    if hostname is None and ipaddr:
        hosts_data = global_config.get_value('hosts')
        if ipaddr in hosts_data['ip']:
            index_num = hosts_data['ip'].index(ipaddr)
            hostname = hosts_data['host_name'][index_num]
    if hostname is None:
        return 1, 'Cannot find host name'
    mcuid = get_smyoo_host_mcuid(hostname)
    if mcuid is None:
        return 1, 'Can not get smyoo mcuid of host'
    result_code, result_message = smyoo.powerControl(bpeSessionId, mcuid, op)
    return result_code, result_message

@app.callback(
    Output('host-name-input', 'value'),
    Output('host-ip-input', 'value'),
    Output('host-mac-input', 'value'),
    Output('host-default-menu-dropdown', 'value'),
    Output('host-super-tube-checklist', 'value'),
    Input('hosts-table', "derived_virtual_data"),
    Input('hosts-table', 'selected_row_ids'),
    Input('hosts-table', 'selected_rows')
)
def load_hosts_table_item(rows, selected_row_ids, selected_rows):
    hostname=''
    ipaddr=''
    macaddr=''
    default_menu=''
    super_tube=False
    # print('select row ids {}'.format(selected_row_ids))
    # print('select rows {}'.format(selected_rows))
    selected_id_set = set(selected_rows or [])

    dff = df_hosts if rows is None else pd.DataFrame(rows)

    for index in selected_id_set:
        hostname = dff.loc[index].host_name
        ipaddr = dff.loc[index].ip
        macaddr = dff.loc[index].mac
        default_menu = dff.loc[index].default_menu
        super_tube = dff.loc[index].super_tube
    super_tube_value = ['Super tube'] if super_tube else []
    return hostname, ipaddr, macaddr, default_menu, super_tube_value

@app.callback(
    Output('hosts-table', 'data'),
    Output('operate-host-state', 'children'),
    Output('hosts-table', 'selected_rows'),
    Input('add-host-button', 'n_clicks'),
    Input('delete-host-button', 'n_clicks'),
    Input('power-on-button', 'n_clicks'),
    Input('power-off-button', 'n_clicks'),
    Input('reset-host-image', 'n_clicks'),
    Input('restart-dhcp-button', 'n_clicks'),
    Input('thrift-network-notify', 'data'),
    State('host-mac-input', 'value'),
    State('host-name-input', 'value'),
    State('host-ip-input', 'value'),
    State('host-default-menu-dropdown', 'value'),
    State('host-super-tube-checklist', 'value'),
    State('hosts-table', 'selected_rows'),
    State('cow-lv-size-input', 'value')
)
def edit_hosts_table(n_clicks1, n_clicks2, n_clicks3, n_clicks4,  n_clicks5,
    n_clicks6, thrift_request_data, macaddr, hostname, ipaddr, default_menu,
    super_tube_value, selected_rows, snap_lv_size):
    hosts_data = global_config.get_value('hosts')
    df_hosts = pd.DataFrame.from_dict(hosts_data)

    if n_clicks1 == 0 and n_clicks2 == 0 and n_clicks3 == 0 and n_clicks4 == 0 \
        and n_clicks5 == 0 and n_clicks6 == 0 and thrift_request_data is None:
        return df_hosts.to_dict('records'), '', []
        # raise PreventUpdate

    # 转换所需值
    macaddr = macaddr.upper() if macaddr else ''
    super_tube = True if super_tube_value and super_tube_value.count('Super tube') > 0 else False

    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == 'add-host-button':
        # if re.match('^[A-F0-9]{2}(:[A-F0-9]{2}){5}$', '00:0C:29:A8:81:F2'):
        if not re.match('^[A-Fa-f0-9]{2}(:[A-Fa-f0-9]{2}){5}$', f'{macaddr}'):
            return df_hosts.to_dict('records'), 'invalid mac address', no_update
        if not re.match('^\w+$', f'{hostname}'):
            return df_hosts.to_dict('records'), 'invalid host name', no_update
        if not re.match(
            '((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}',
            f'{ipaddr}'):
            return df_hosts.to_dict('records'), 'invalid ip address', no_update
        boot_menu_list = global_config.get_value('boot_menu')
        if default_menu not in boot_menu_list['name']:
            return df_hosts.to_dict('records'), 'invalid boot menu', no_update

        result_code, result_message = dhcp.bind_mac_address_and_ip_address(
            global_config.get_value('dhcp_server')['network_name'],
            hostname, macaddr, ipaddr)
        if result_code != 0:
            return df_hosts.to_dict('records'), 'bind mac and ip failed', no_update

        if macaddr in hosts_data['mac']:
            index_num = hosts_data['mac'].index(macaddr)
            hosts_data['host_name'][index_num] = hostname
            hosts_data['ip'][index_num] = ipaddr
            hosts_data['default_menu'][index_num] = default_menu
            hosts_data['super_tube'][index_num] = super_tube
            if hosts_data['host_name'].count(hostname) > 1:
                return df_hosts.to_dict('records'), 'host name duplicated', no_update
            if hosts_data['ip'].count(ipaddr) > 1:
                return df_hosts.to_dict('records'), 'ip address duplicated', no_update
        else:
            if hostname in hosts_data['host_name']:
                return df_hosts.to_dict('records'), 'host name duplicated', no_update
            if ipaddr in hosts_data['ip']:
                return df_hosts.to_dict('records'), 'ip address duplicated', no_update
            hosts_data['mac'].append(macaddr)
            hosts_data['host_name'].append(hostname)
            hosts_data['ip'].append(ipaddr)
            hosts_data['default_menu'].append(default_menu)
            hosts_data['super_tube'].append(super_tube)
        update_ipxe_cfg(macaddr, default_menu, super_tube)
    elif trigger_id == 'delete-host-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_hosts.to_dict('records'), 'selected none', selected_rows
        else:
            for index_num in selected_rows:
                result_code, result_message = dhcp.unbind_mac_address_and_ip_address(
                    global_config.get_value('dhcp_server')['network_name'],
                    hosts_data['host_name'][index_num],
                    hosts_data['mac'][index_num])
                if result_code != 0:
                    return df_hosts.to_dict('records'), 'unbind mac and ip failed', selected_rows
                root_path = global_config.get_value('http_server')['root_path']
                format_mac = ''.join(hosts_data['mac'][index_num].split(':')).lower()
                ipxe.delete_ipxe_cfg(os.path.join(root_path, 'ipxe', 'cfg', \
                    f'mac-{format_mac}.ipxe.cfg'))
                # remove all snapshot iscsi storage and logical storage of host
                remove_snapshot_storage_of_host(format_mac)
                hosts_data['host_name'].pop(index_num)
                hosts_data['ip'].pop(index_num)
                hosts_data['mac'].pop(index_num)
                hosts_data['default_menu'].pop(index_num)
                hosts_data['super_tube'].pop(index_num)
            selected_rows.clear()
    elif trigger_id == 'power-on-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_hosts.to_dict('records'), 'selected none', no_update
        else:
            for index_num in selected_rows:
                result_code, result_message = smyoo_host_power_control(
                    1, hostname = hosts_data['host_name'][index_num],
                    updatedevices = True)
                return no_update, result_message if result_code != 0 else '', no_update
    elif trigger_id == 'power-off-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_hosts.to_dict('records'), 'selected none', no_update
        else:
            for index_num in selected_rows:
                result_code, result_message = smyoo_host_power_control(
                    0, hostname = hosts_data['host_name'][index_num],
                    updatedevices = True)
                return no_update, result_message if result_code != 0 else '', no_update
    elif trigger_id == 'reset-host-image':
        if selected_rows is None or len(selected_rows) == 0:
            return df_hosts.to_dict('records'), 'selected none', no_update
        else:
            for index_num in selected_rows:
                default_menu = hosts_data['default_menu'][index_num]
                format_mac = ''.join(hosts_data['mac'][index_num].split(':')).lower()
                super_tube = hosts_data['super_tube'][index_num]
                result_code, result_message = reset_host_boot_menu(
                    format_mac, default_menu, snap_lv_size)
                if result_code != 0:
                    return df_hosts.to_dict('records'), result_message, no_update
    elif trigger_id == 'restart-dhcp-button':
        result_code = dhcp.restart_dhcp_service()
        result_message = 'restart dhcp service failed' if result_code != 0 else ''
        return df_hosts.to_dict('records'), result_message, no_update
    elif trigger_id == 'thrift-network-notify':
        if thrift_request_data and len(thrift_request_data) > 0:
            request = eval(thrift_request_data)
            response = {
                'code': ErrorCode.UNKNOWN_ERROR.value,
                'message': 'unknown error when dealing with plotly network notify'
            }
            if request['type'] == 'SET_BOOT_MENU':
                hostip = global_config.find_host_ip(
                    hostname=request['host'],ip=request['host'])
                if hostip:
                    index_num = hosts_data['ip'].index(hostip)
                    boot_menu_list = global_config.get_value('boot_menu')
                    if request['menu'] in boot_menu_list['name']:
                        hosts_data['default_menu'][index_num] = request['menu']
                        hosts_data['super_tube'][index_num] = request['superTube']
                        update_ipxe_cfg(hosts_data['mac'][index_num],
                            request['menu'], request['superTube'])
                        global_config.set_value('hosts', hosts_data)
                        df_hosts = pd.DataFrame.from_dict(hosts_data)
                        global_config.write_config_file()
                        response['code'] = 0
                        response['message'] = 'success'
                        global_config.set_cache('result', repr(response), expire=3)
                        return df_hosts.to_dict('records'), no_update, no_update
                    else:
                        response['code'] = ErrorCode.PLOTLY_BOOT_MENU_NOT_EXISTED.value
                        response['message'] = 'boot menu not existed'
                else:
                    response['code'] = ErrorCode.UNKNOWN_HOST.value
                    response['message'] = 'invalid request host'
            elif request['type'] == 'SET_SMYOO_DEVICE_POWER':
                hostname = global_config.find_host_name(
                    hostname=request['host'],ip=request['host'])
                if hostname:
                    if request['status'] in [0,1]:
                        result_code, result_message = smyoo_host_power_control(
                            request['status'], hostname=hostname)
                        response['code'] = result_code if result_code != 1 else \
                            ErrorCode.PLOTLY_SET_SMYOO_HOST_POWER_FAILED.value
                        response['message'] = result_message
                        global_config.set_cache('result', repr(response), expire=3)
                        return no_update, no_update, no_update
                    else:
                        response['code'] = ErrorCode.PLOTLY_INVALID_SMYOO_POWER_STATUS.value
                        response['message'] = 'invalid power status'
                else:
                    response['code'] = ErrorCode.UNKNOWN_HOST.value
                    response['message'] = 'invalid request host'
            else:
                response['code'] = ErrorCode.PLOTLY_UNKNOWN_NOTIFY_TYPE.value
                response['message'] = 'unsupported message type'
            global_config.set_cache('result', repr(response), expire=3)
        # return no_update, no_update, no_update
        raise PreventUpdate

    global_config.set_value('hosts', hosts_data)
    df_hosts = pd.DataFrame.from_dict(hosts_data)
    global_config.write_config_file()
    return df_hosts.to_dict('records'), '', selected_rows

@app.callback(
    Output('thrift-network-notify', 'data'),
    Input('thrift-interval', 'n_intervals')
)
def interval_update(n_intervals):
    request_cache = global_config.get_cache('request', default="")
    if len(request_cache) > 0:
        global_config.delete_cache('request')
        print('get thrift request in diskcache: ', request_cache)
        return request_cache
    return no_update

@app.callback(
    Output('restore-after-restart-state', 'children'),
    Input('restore-after-restart-button', 'n_clicks')
)
def restore_after_restart(n_clicks):
    if n_clicks == 0:
        return ''
    volume_group = global_config.get_value('volume_group_name')
    result_code, result_message = lvm2.restore_after_restart(volume_group)
    if result_code != 0:
        return result_message
    result_code, result_message = iscsi.restore_after_restart()
    if result_code != 0:
        return result_message

@app.callback(
    Output('os-name-input', 'value'),
    Output('os-description-input', 'value'),
    Output('os-capacity-input', 'value'),
    Input('os-table', "derived_virtual_data"),
    Input('os-table', 'selected_row_ids'),
    Input('os-table', 'selected_rows')
)
def load_os_table_item(rows, selected_row_ids, selected_rows):
    name=''
    description=''
    capacity=None

    selected_id_set = set(selected_rows or [])

    dff = df_os if rows is None else pd.DataFrame(rows)

    for index in selected_id_set:
        # 此处使用dff.loc[index].name可能有歧义，会返回pandas Series的行序号
        name = dff.loc[index]['name']
        description = dff.loc[index].description
        capacity = dff.iloc[index].capacity
        # print(type(dff.iloc[index].capacity))
    return name, description, capacity

@app.callback(
    Output('os-table', 'data'),
    Output('operate-operation-system-state', 'children'),
    Output('os-table', 'selected_rows'),
    Output('boot-menu-operation-system-dropdown', 'options'),
    Input('add-os-button', 'n_clicks'),
    Input('del-os-button', 'n_clicks'),
    State('os-name-input', 'value'),
    State('os-description-input', 'value'),
    State('os-capacity-input', 'value'),
    State('os-table', 'selected_rows')
)
def edit_operation_system_table(n_clicks1, n_clicks2,
    name, description, capacity, selected_rows):
    os_data = global_config.get_value('operation_system')
    df_os = pd.DataFrame.from_dict(os_data)
    if n_clicks1 == 0 and n_clicks2 == 0:
        return df_os.to_dict('records'), '', [], os_data['name']

    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == 'add-os-button':
        if not re.match('^\w+$', f'{name}'):
            return df_os.to_dict('records'), 'invalid name', no_update, no_update

        os_data2 = global_config.get_value('data_disk')
        if name in os_data['name'] or name in os_data2['name']:
            return df_os.to_dict('records'), 'already existed, unsupport modify', selected_rows, os_data['name']
            # index_num = os_data['name'].index(name)
            # os_data['description'][index_num] = description
            # os_data['capacity'][index_num] = capacity
        else:
            result_code, result_message = lvm2.create_logical_volume(
                global_config.get_value('volume_group_name'),
                name, capacity)
            if result_code != 0:
                return df_os.to_dict('records'), result_message, no_update, no_update
            os_data['name'].append(name);
            os_data['description'].append(description)
            os_data['capacity'].append(capacity)
    elif trigger_id == 'del-os-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_os.to_dict('records'), 'selected none', no_update, no_update
        else:
            boot_menu_list = global_config.get_value('boot_menu')
            for index_num in selected_rows:
                if os_data['name'][index_num] in boot_menu_list['operation_system']:
                    return df_os.to_dict('records'), 'The selected operation system is in use', no_update, no_update
                result_code, result_message = lvm2.remove_logical_volume(
                    global_config.get_value('volume_group_name'),
                    os_data['name'][index_num])
                if result_code != 0:
                    return df_os.to_dict('records'), result_message, no_update, no_update
                os_data['name'].pop(index_num)
                os_data['description'].pop(index_num)
                os_data['capacity'].pop(index_num)
            selected_rows.clear()

    global_config.set_value('operation_system', os_data)
    df_os = pd.DataFrame.from_dict(os_data)
    global_config.write_config_file()
    return df_os.to_dict('records'), '', selected_rows, os_data['name']

@app.callback(
    Output('data-disk-name-input', 'value'),
    Output('data-disk-description-input', 'value'),
    Output('data-disk-capacity-input', 'value'),
    Input('data-disk-table', "derived_virtual_data"),
    Input('data-disk-table', 'selected_row_ids'),
    Input('data-disk-table', 'selected_rows')
)
def load_data_disk_table_item(rows, selected_row_ids, selected_rows):
    name=''
    description=''
    capacity=None

    selected_id_set = set(selected_rows or [])

    dff = df_data_disk if rows is None else pd.DataFrame(rows)

    for index in selected_id_set:
        # 此处使用dff.loc[index].name可能有歧义，会返回pandas Series的行序号
        name = dff.loc[index]['name']
        description = dff.loc[index].description
        capacity = dff.iloc[index].capacity
    return name, description, capacity

@app.callback(
    Output('data-disk-table', 'data'),
    Output('operate-data-disk-state', 'children'),
    Output('data-disk-table', 'selected_rows'),
    Output('boot-menu-data-disk-dropdown', 'options'),
    Input('add-data-disk-button', 'n_clicks'),
    Input('del-data-disk-button', 'n_clicks'),
    State('data-disk-name-input', 'value'),
    State('data-disk-description-input', 'value'),
    State('data-disk-capacity-input', 'value'),
    State('data-disk-table', 'selected_rows')
)
def edit_data_disk_table(n_clicks1, n_clicks2,
    name, description, capacity, selected_rows):
    os_data = global_config.get_value('data_disk')
    df_data_disk = pd.DataFrame.from_dict(os_data)
    if n_clicks1 == 0 and n_clicks2 == 0:
        return df_data_disk.to_dict('records'), '', [], os_data['name']

    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == 'add-data-disk-button':
        if not re.match('^\w+$', f'{name}'):
            return df_data_disk.to_dict('records'), 'invalid name', no_update, no_update

        os_data2 = global_config.get_value('operation_system')
        if name in os_data['name'] or name in os_data2['name']:
            return df_data_disk.to_dict('records'), 'already existed, unsupport modify', selected_rows, os_data['name']
            # index_num = os_data['name'].index(name)
            # os_data['description'][index_num] = description
            # os_data['capacity'][index_num] = capacity
        else:
            result_code, result_message = lvm2.create_logical_volume(
                global_config.get_value('volume_group_name'),
                name, capacity)
            if result_code != 0:
                return df_data_disk.to_dict('records'), result_message, no_update, no_update
            os_data['name'].append(name);
            os_data['description'].append(description)
            os_data['capacity'].append(capacity)
    elif trigger_id == 'del-data-disk-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_data_disk.to_dict('records'), 'selected none', selected_rows, os_data['name']
        else:
            boot_menu_list = global_config.get_value('boot_menu')
            for index_num in selected_rows:
                for data_disk_string in boot_menu_list['data_disk']:
                    data_disk_list = data_disk_string.split(",")
                    if os_data['name'][index_num] in data_disk_list:
                        return df_data_disk.to_dict('records'), 'The selected data disk is in use', no_update, no_update
                result_code, result_message = lvm2.remove_logical_volume(
                    global_config.get_value('volume_group_name'),
                    os_data['name'][index_num])
                if result_code != 0:
                    return df_data_disk.to_dict('records'), result_message, selected_rows, os_data['name']
                os_data['name'].pop(index_num)
                os_data['description'].pop(index_num)
                os_data['capacity'].pop(index_num)
            selected_rows.clear()

    global_config.set_value('data_disk', os_data)
    df_data_disk = pd.DataFrame.from_dict(os_data)
    global_config.write_config_file()
    return df_data_disk.to_dict('records'), '', selected_rows, os_data['name']

@app.callback(
    Output('boot-menu-name-input', 'value'),
    Output('boot-menu-operation-system-dropdown', 'value'),
    Output('boot-menu-data-disk-dropdown', 'value'),
    Input('boot-menu-table', "derived_virtual_data"),
    Input('boot-menu-table', 'selected_row_ids'),
    Input('boot-menu-table', 'selected_rows')
)
def load_boot_menu_table_item(rows, selected_row_ids, selected_rows):
    name=''
    operation_system=''
    data_disk=[]

    selected_id_set = set(selected_rows or [])

    dff = df_boot_menu if rows is None else pd.DataFrame(rows)

    for index in selected_id_set:
        # 此处使用dff.loc[index].name可能有歧义，会返回pandas Series的行序号
        name = dff.loc[index]['name']
        operation_system = dff.loc[index].operation_system
        data_disk = dff.loc[index].data_disk.split(",")
    return name, operation_system, data_disk

@app.callback(
    Output('boot-menu-table', 'data'),
    Output('operate-boot-menu-state', 'children'),
    Output('boot-menu-table', 'selected_rows'),
    Output('host-default-menu-dropdown', 'options'),
    Input('add-boot-menu-button', 'n_clicks'),
    Input('del-boot-menu-button', 'n_clicks'),
    Input('del-boot-menu-snap-button', 'n_clicks'),
    State('boot-menu-name-input', 'value'),
    State('boot-menu-operation-system-dropdown', 'value'),
    State('boot-menu-data-disk-dropdown', 'value'),
    State('boot-menu-table', 'selected_rows')
)
def edit_boot_menu_table(n_clicks1, n_clicks2, n_clicks3,
    name, operation_system, data_disk, selected_rows):
    bm_data = global_config.get_value('boot_menu')
    df_boot_menu = pd.DataFrame.from_dict(bm_data)
    if n_clicks1 == 0 and n_clicks2 == 0 and n_clicks3 == 0:
        return df_boot_menu.to_dict('records'), '', [], bm_data['name']

    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == 'add-boot-menu-button':
        if not re.match('^\w+$', f'{name}'):
            return df_boot_menu.to_dict('records'), 'invalid name', no_update, no_update
        if operation_system is None or len(operation_system) == 0:
            return df_boot_menu.to_dict('records'), \
                'empty operation system', no_update, no_update

        if name in bm_data['name']:
            return df_boot_menu.to_dict('records'), \
                'already existed, unsupport modify', selected_rows, bm_data['name']
            # index_num = bm_data['name'].index(name)
            # bm_data['operation_system'][index_num] = operation_system
        else:
            iscsi_setting = global_config.get_value('iscsi_setting')
            disks = []
            disks.append(operation_system)
            disks.extend(data_disk)
            disks = util.deduplication(disks)
            initiator_iqn = '%s:sn.%s' % (iscsi_setting['iscsi_target_prefix'], name)
            result_code, result_message = iscsi.create_iscsi_target(name, disks,
                iscsi_setting['iscsi_target_prefix'], initiator_iqn)
            if result_code != 0:
                return df_boot_menu.to_dict('records'), result_message, \
                    no_update, no_update
            bm_data['name'].append(name);
            bm_data['operation_system'].append(operation_system)
            bm_data['data_disk'].append(','.join(data_disk))
    elif trigger_id == 'del-boot-menu-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_boot_menu.to_dict('records'), 'selected none', \
                selected_rows, bm_data['name']
        else:
            for index_num in selected_rows:
                menu_item = bm_data['name'][index_num]
                target_list = iscsi.get_iscsi_target_list()
                iscsi_setting = global_config.get_value('iscsi_setting')
                target_prefix = iscsi_setting['iscsi_target_prefix']
                for target in target_list:
                    if target.startswith(f'{target_prefix}:sn.{menu_item}.'):
                        iscsi.delete_iscsi_target_by_wwn(target)
                for target in target_list:
                    if target == f'{target_prefix}:sn.{menu_item}':
                        iscsi.delete_iscsi_target_by_wwn(target)
                bm_data['name'].pop(index_num)
                bm_data['operation_system'].pop(index_num)
                bm_data['data_disk'].pop(index_num)
            selected_rows.clear()
    elif trigger_id == 'del-boot-menu-snap-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_boot_menu.to_dict('records'), 'selected none', \
                selected_rows, bm_data['name']
        else:
            for index_num in selected_rows:
                menu_item = bm_data['name'][index_num]
                # delete all snap iscsi and storage of disks in boot menu
                # 目的是为了在修改母镜像的时候，断开快照镜像的使用，避免冲突
                iscsi_setting = global_config.get_value('iscsi_setting')
                disks = []
                disks.append(bm_data['operation_system'][index_num])
                disks.extend(bm_data['data_disk'][index_num].split(','))
                disks = util.deduplication(disks)
                iscsi.delete_snap_iscsi_objects(iscsi_setting['iscsi_target_prefix'],
                    menu_item, disks)

    global_config.set_value('boot_menu', bm_data)
    df_boot_menu = pd.DataFrame.from_dict(bm_data)
    global_config.write_config_file()
    return df_boot_menu.to_dict('records'), '', selected_rows, bm_data['name']

@app.callback(
    Output('operate-volume-group-name-state', 'children'),
    Input('volume-group-name-input', 'value')
)
def edit_volume_group_name(volume_group):
    if not lvm2.is_volume_group_existed(volume_group):
        return 'not existed'
    global_config.set_value('volume_group_name', volume_group)
    global_config.write_config_file()
    return 'volume group normal'

@app.callback(
    Output('operate-dhcp-network-name-state', 'children'),
    Input('dhcp-network-name-input', 'value'),
    Input('dhcp-interface-input', 'value')
)
def edit_dhcp_network_name(network_name, network_interface):
    dhcp_server = global_config.get_value('dhcp_server')
    result_code, result_message = dhcp.edit_dhcp_conf_include(
        dhcp_server['network_name'], network_name)
    if result_code != 0:
        return result_message
    dhcp_server['network_name'] = network_name
    dhcp_server['interface'] = network_interface
    global_config.set_value('dhcp_server', dhcp_server)
    global_config.write_config_file()
    return ''

@app.callback(
    Output('operate-dhcp-server-state', 'children'),
    Input('dhcp-subnet-input', 'value'),
    Input('dhcp-subnet-mask-input', 'value'),
    Input('dhcp-range-from-input', 'value'),
    Input('dhcp-range-to-input', 'value'),
    Input('dhcp-routers-input', 'value'),
    Input('dhcp-dns-servers-input', 'value'),
    Input('dhcp-broadcast-address-input', 'value'),
    Input('dhcp-filename-input', 'value'),
    Input('dhcp-next-server-input', 'value')
)
def edit_dhcp_server_subnet(subnet, subnet_mask, range_from, range_to,
    routers, dns_servers, broadcast_address, filename, next_server):
    dhcp_server = global_config.get_value('dhcp_server')
    result_code, result_message = dhcp.edit_dhcp_conf_subnet(
        dhcp_server['network_name'], dhcp_server['interface'], subnet, subnet_mask,
        range_from, range_to, routers, dns_servers, broadcast_address, filename, next_server);
    if result_code != 0:
        return result_message
    dhcp_server['subnet'] = subnet
    dhcp_server['subnet_mask'] = subnet_mask
    dhcp_server['range_from'] = range_from
    dhcp_server['range_to'] = range_to
    dhcp_server['routers'] = routers
    dhcp_server['dns_servers'] = dns_servers
    dhcp_server['broadcast_address'] = broadcast_address
    dhcp_server['filename'] = filename
    dhcp_server['next_server'] = next_server
    global_config.set_value('dhcp_server', dhcp_server)
    global_config.write_config_file()
    return ''

@app.callback(
    Output('operate-http-server-state', 'children'),
    Input('http-root-path-input', 'value'),
    Input('http-base-url-input', 'value'),
    Input('iscsi-server-input', 'value')
)
def edit_http_server_setting(root_path, base_url, iscsi_server):
    result_code = ipxe.edit_global_ipxe_cfg(os.path.join(root_path, 'ipxe'),
        iscsi_server, base_url)
    if result_code == 0:
        http_server = global_config.get_value('http_server')
        http_server['root_path'] = root_path
        http_server['base_url'] = base_url
        iscsi_setting = global_config.get_value('iscsi_setting')
        iscsi_setting['server'] = iscsi_server
        global_config.set_value('http_server', http_server)
        global_config.set_value('iscsi_setting', iscsi_setting)
        global_config.write_config_file()
    return ''

@app.callback(
    Output('operate-iscsi-setting-state', 'children'),
    Input('iscsi-initiator-iqn-input', 'value'),
    Input('iscsi-target-prefix-input', 'value')
)
def edit_iscsi_setting(initiator_iqn, iscsi_target_prefix):
    iscsi_setting = global_config.get_value('iscsi_setting')
    iscsi_setting['initiator_iqn'] = initiator_iqn
    iscsi_setting['iscsi_target_prefix'] = iscsi_target_prefix
    global_config.set_value('iscsi_setting', iscsi_setting)
    global_config.write_config_file()
    return ''

@app.callback(
    Output('operate-smyoo-state', 'children'),
    Input('smyoo-phone-input', 'value'),
    Input('smyoo-password-input', 'value')
)
def edit_smyoo_setting(phone, password):
    # print('phone:', phone, ', password:', password)
    changed = False
    if phone and len(phone) > 0 \
        and phone != global_config.get_cache('smyoo_phone',default=''):
        global_config.set_cache('smyoo_phone', phone)
        changed = True
    if password and len(password) > 0 \
        and password != global_config.get_cache('smyoo_password',default=''):
        global_config.set_cache('smyoo_password', password)
        changed = True
    if changed:
        result_code, result_message = update_smyoo_session(phone, password)
        if result_code != 0:
            global_config.delete_cache('smyoo_session')
            return result_message
    return ''

if __name__ == '__main__':
    tt = Thread(target=rpc_handler.thrift_thread)
    tt.start()
    # app.run_server(debug=True)
    app.run_server(debug=False, host='0.0.0.0')
    print("done!")
