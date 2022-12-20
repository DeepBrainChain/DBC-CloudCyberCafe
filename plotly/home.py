from dash import Dash, dash_table, dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
# import dash_daq as daq
import os
import re
import global_config
import lvm2
import iscsi
import dhcp
import ipxe
import util

global_config._init()

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
        children='Open Cloud Cybercafe',
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
                    html.Button('Reset Host iSCSI', id='reset-host-button', n_clicks=0),
                    # html.Label(style={'width':10}),
                    # dcc.Checklist(id='super-tube-checklist', options=['Super tube']),
                    html.Label(style={'width':10}),
                    html.Button('Restart DHCP', id='restart-dhcp-button', n_clicks=0),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(id='operate-host-state'),
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
                        value=global_config.get_value('volume_group_name')),
                    html.Label(style={'width':10}),
                    html.Div(id='operate-volume-group-name-state')
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.H2('DHCP'),
                html.Div(children=[
                    html.Label('network name: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-network-name-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['network_name']),
                    html.Label(style={'width':10}),
                    html.Label('interface: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-interface-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['interface'],
                        style={'width':100}),
                    html.Label(style={'width':10}),
                    html.Div(id='operate-dhcp-network-name-state')
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(children=[
                    html.Label('subnet: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-subnet-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['subnet'],
                        style={'width':100}),
                    html.Label(style={'width':10}),
                    html.Label('subnet mask: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-subnet-mask-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['subnet_mask'],
                        style={'width':100}),
                    html.Label(style={'width':10}),
                    html.Label('range: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-range-from-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['range_from'],
                        style={'width':100}),
                    html.Label(style={'width':10}),
                    html.Label(' - '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-range-to-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['range_to'],
                        style={'width':100}),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(children=[
                    html.Label('routers: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-routers-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['routers']),
                    html.Label(style={'width':10}),
                    html.Label('dns servers: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-dns-servers-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['dns_servers']),
                    html.Label(style={'width':10}),
                    html.Label('broadcast address: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-broadcast-address-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['broadcast_address'],
                        style={'width':100}),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(children=[
                    html.Label('filename: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-filename-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['filename'],
                        style={'width':300}),
                    html.Label(style={'width':10}),
                    html.Label('next server: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='dhcp-next-server-input', type='text', debounce=True,
                        value=global_config.get_value('dhcp_server')['next_server'],
                        style={'width':100}),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Div(id='operate-dhcp-server-state'),
                html.H2('HTTP'),
                html.Div(children=[
                    html.Label('root path: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='http-root-path-input', type='text', debounce=True,
                        value=global_config.get_value('http_server')['root_path']),
                    html.Label(style={'width':10}),
                    html.Label('http ip:port '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='http-base-url-input', type='text', debounce=True,
                        value=global_config.get_value('http_server')['base_url']),
                    html.Div(id='operate-http-server-state'),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.H2('iSCSI'),
                html.Div(children=[
                    html.Label('iscsi server: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='iscsi-server-input', type='text', debounce=True,
                        value=global_config.get_value('iscsi_setting')['server'],
                        style={'width':100}),
                    html.Label(style={'width':10}),
                    html.Label('initiator iqn: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='iscsi-initiator-iqn-input', type='text', debounce=True,
                        value=global_config.get_value('iscsi_setting')['initiator_iqn'],
                        style={'width':300}),
                    html.Label(style={'width':10}),
                    html.Label('target prefix: '),
                    html.Label(style={'width':10}),
                    dcc.Input(id='iscsi-target-prefix-input', type='text', debounce=True,
                        value=global_config.get_value('iscsi_setting')['iscsi_target_prefix'],
                        style={'width':200}),
                ], style={'display': 'flex', 'flex-direction': 'row'}),
                html.Br(),
                html.Div(id='operate-iscsi-setting-state')
            ], style={'padding': 10, 'flex': 1})
        ])
    ], style=tabs_styles),
    html.Div(id='tabs-content-props')
])

def reset_host_boot_menu(mac_addr, boot_item, super_tube):
    target_name = boot_item if super_tube else f'{boot_item}.{mac_addr}'
    iscsi_setting = global_config.get_value('iscsi_setting')
    iscsi.delete_iscsi_target(target_name, iscsi_setting['iscsi_target_prefix'], not super_tube)

    boot_menu = global_config.get_value('boot_menu')
    if boot_item not in boot_menu['name']:
        return 1, 'boot item not existed'

    volume_group = global_config.get_value('volume_group_name')
    if not super_tube:
        lv_list = lvm2.get_logical_volume_list(volume_group)
        for item in lv_list:
            if item.endswith(mac_addr):
                lvm2.remove_logical_volume(volume_group, item)

    menu_index = boot_menu['name'].index(boot_item)
    disks = []
    disks.append(boot_menu['operation_system'][menu_index])
    disks.extend(boot_menu['data_disk'][menu_index].split(','))
    disks = util.deduplication(disks)
    if not super_tube:
        for index, disk in enumerate(disks):
            result_code, result_message = lvm2.create_snapshot_logical_volume(
                volume_group, disk, mac_addr, 1)
            if result_code != 0:
                return result_code, result_message
            disks[index] = f'{disk}_{mac_addr}'

    result_code, result_message = iscsi.create_iscsi_target(target_name, disks,
        iscsi_setting['iscsi_target_prefix'], iscsi_setting['initiator_iqn'])
    if result_code != 0:
        for disk in disks:
            lvm2.remove_logical_volume(volume_group, disk)
        return result_code, result_message
    return 0, 'reset successful'

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
    Input('reset-host-button', 'n_clicks'),
    Input('restart-dhcp-button', 'n_clicks'),
    State('host-mac-input', 'value'),
    State('host-name-input', 'value'),
    State('host-ip-input', 'value'),
    State('host-default-menu-dropdown', 'value'),
    State('host-super-tube-checklist', 'value'),
    State('hosts-table', 'selected_rows')
)
def edit_hosts_table(n_clicks1, n_clicks2, n_clicks3, n_clicks4,  n_clicks5,
    n_clicks6, macaddr, hostname, ipaddr, default_menu,
    super_tube_value, selected_rows):
    hosts_data = global_config.get_value('hosts')
    df_hosts = pd.DataFrame.from_dict(hosts_data)

    if n_clicks1 == 0 and n_clicks2 == 0 and n_clicks3 == 0 and n_clicks4 == 0 \
        and n_clicks5 == 0 and n_clicks6 == 0:
        return df_hosts.to_dict('records'), '', []

    # 转换所需值
    macaddr = macaddr.upper()
    super_tube = True if super_tube_value and super_tube_value.count('Super tube') > 0 else False

    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == 'add-host-button':
        # if re.match('^[A-F0-9]{2}(:[A-F0-9]{2}){5}$', '00:0C:29:A8:81:F2'):
        if not re.match('^[A-Fa-f0-9]{2}(:[A-Fa-f0-9]{2}){5}$', f'{macaddr}'):
            return df_hosts.to_dict('records'), 'invalid mac address', selected_rows
        if not re.match('^\w+$', f'{hostname}'):
            return df_hosts.to_dict('records'), 'invalid host name', selected_rows
        if not re.match(
            '((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}',
            f'{ipaddr}'):
            return df_hosts.to_dict('records'), 'invalid ip address', selected_rows

        result_code, result_message = dhcp.bind_mac_address_and_ip_address(
            global_config.get_value('dhcp_server')['network_name'],
            hostname, macaddr, ipaddr)
        if result_code != 0:
            return df_hosts.to_dict('records'), 'bind mac and ip failed', selected_rows

        if macaddr in hosts_data['mac']:
            index_num = hosts_data['mac'].index(macaddr)
            hosts_data['host_name'][index_num] = hostname
            hosts_data['ip'][index_num] = ipaddr
            hosts_data['default_menu'][index_num] = default_menu
            hosts_data['super_tube'][index_num] = super_tube
            if hosts_data['host_name'].count(hostname) > 1:
                return df_hosts.to_dict('records'), 'host name duplicated', selected_rows
            if hosts_data['ip'].count(ipaddr) > 1:
                return df_hosts.to_dict('records'), 'ip address duplicated', selected_rows
        else:
            if hostname in hosts_data['host_name']:
                return df_hosts.to_dict('records'), 'host name duplicated', selected_rows
            if ipaddr in hosts_data['ip']:
                return df_hosts.to_dict('records'), 'ip address duplicated', selected_rows
            hosts_data['mac'].append(macaddr)
            hosts_data['host_name'].append(hostname)
            hosts_data['ip'].append(ipaddr)
            hosts_data['default_menu'].append(default_menu)
            hosts_data['super_tube'].append(super_tube)
        root_path = global_config.get_value('http_server')['root_path']
        format_mac = ''.join(macaddr.split(':')).lower()
        iscsi_setting = global_config.get_value('iscsi_setting')
        boot_menu = global_config.get_value('boot_menu')
        ipxe.edit_ipxe_cfg(os.path.join(root_path, 'ipxe', 'cfg'), format_mac,
            iscsi_setting['initiator_iqn'], iscsi_setting['iscsi_target_prefix'],
            boot_menu['name'], default_menu, super_tube)
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
                hosts_data['host_name'].pop(index_num)
                hosts_data['ip'].pop(index_num)
                hosts_data['mac'].pop(index_num)
                hosts_data['default_menu'].pop(index_num)
                hosts_data['super_tube'].pop(index_num)
            selected_rows.clear()
    elif trigger_id == 'power-on-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_hosts.to_dict('records'), 'selected none', selected_rows
        else:
            print(f'power on item {selected_rows}')
    elif trigger_id == 'power-off-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_hosts.to_dict('records'), 'selected none', selected_rows
        else:
            print(f'power off item {selected_rows}')
    elif trigger_id == 'reset-host-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_hosts.to_dict('records'), 'selected none', selected_rows
        else:
            for index_num in selected_rows:
                default_menu = hosts_data['default_menu'][index_num]
                format_mac = ''.join(hosts_data['mac'][index_num].split(':')).lower()
                super_tube = hosts_data['super_tube'][index_num]
                result_code, result_message = reset_host_boot_menu(
                    format_mac, default_menu, super_tube)
                if result_code != 0:
                    return df_hosts.to_dict('records'), result_message, selected_rows
    elif trigger_id == 'restart-dhcp-button':
        result_code = dhcp.restart_dhcp_service()
        result_message = 'restart dhcp service failed' if result_code != 0 else ''
        return df_hosts.to_dict('records'), result_message, selected_rows

    global_config.set_value('hosts', hosts_data)
    df_hosts = pd.DataFrame.from_dict(hosts_data)
    global_config.write_config_file()
    return df_hosts.to_dict('records'), '', selected_rows

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
            return df_os.to_dict('records'), 'invalid name', selected_rows, os_data['name']

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
                return df_os.to_dict('records'), result_message, selected_rows, os_data['name']
            os_data['name'].append(name);
            os_data['description'].append(description)
            os_data['capacity'].append(capacity)
    elif trigger_id == 'del-os-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_os.to_dict('records'), 'selected none', selected_rows, os_data['name']
        else:
            for index_num in selected_rows:
                result_code, result_message = lvm2.remove_logical_volume(
                    global_config.get_value('volume_group_name'),
                    os_data['name'][index_num])
                if result_code != 0:
                    return df_os.to_dict('records'), result_message, selected_rows, os_data['name']
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
            return df_data_disk.to_dict('records'), 'invalid name', selected_rows, os_data['name']

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
                return df_os.to_dict('records'), result_message, selected_rows, os_data['name']
            os_data['name'].append(name);
            os_data['description'].append(description)
            os_data['capacity'].append(capacity)
    elif trigger_id == 'del-data-disk-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_data_disk.to_dict('records'), 'selected none', selected_rows, os_data['name']
        else:
            for index_num in selected_rows:
                result_code, result_message = lvm2.remove_logical_volume(
                    global_config.get_value('volume_group_name'),
                    os_data['name'][index_num])
                if result_code != 0:
                    return df_os.to_dict('records'), result_message, selected_rows, os_data['name']
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
    State('boot-menu-name-input', 'value'),
    State('boot-menu-operation-system-dropdown', 'value'),
    State('boot-menu-data-disk-dropdown', 'value'),
    State('boot-menu-table', 'selected_rows')
)
def edit_boot_menu_table(n_clicks1, n_clicks2,
    name, operation_system, data_disk, selected_rows):
    os_data = global_config.get_value('boot_menu')
    df_boot_menu = pd.DataFrame.from_dict(os_data)
    if n_clicks1 == 0 and n_clicks2 == 0:
        return df_boot_menu.to_dict('records'), '', [], os_data['name']

    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == 'add-boot-menu-button':
        if not re.match('^\w+$', f'{name}'):
            return df_boot_menu.to_dict('records'), 'invalid name', selected_rows, os_data['name']

        if name in os_data['name']:
            return df_boot_menu.to_dict('records'), \
                'already existed, unsupport modify', selected_rows, os_data['name']
            # index_num = os_data['name'].index(name)
            # os_data['operation_system'][index_num] = operation_system
        else:
            os_data['name'].append(name);
            os_data['operation_system'].append(operation_system)
            os_data['data_disk'].append(','.join(data_disk))
    elif trigger_id == 'del-boot-menu-button':
        if selected_rows is None or len(selected_rows) == 0:
            return df_boot_menu.to_dict('records'), 'selected none', \
                selected_rows, os_data['name']
        else:
            for index_num in selected_rows:
                menu_item = os_data['name'][index_num]
                target_list = iscsi.get_iscsi_target_list()
                iscsi_setting = global_config.get_value('iscsi_setting')
                target_prefix = iscsi_setting['iscsi_target_prefix']
                for target in target_list:
                    if target.startswith(f'{target_prefix}:sn.{menu_item}.'):
                        iscsi.delete_iscsi_target_by_wwn(target)
                for target in target_list:
                    if target == f'{target_prefix}:sn.{menu_item}':
                        iscsi.delete_iscsi_target_by_wwn(target)
                os_data['name'].pop(index_num)
                os_data['operation_system'].pop(index_num)
                os_data['data_disk'].pop(index_num)
            selected_rows.clear()

    global_config.set_value('boot_menu', os_data)
    df_boot_menu = pd.DataFrame.from_dict(os_data)
    global_config.write_config_file()
    return df_boot_menu.to_dict('records'), '', selected_rows, os_data['name']

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

if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server(debug=True, host='0.0.0.0')
