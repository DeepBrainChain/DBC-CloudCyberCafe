from dash import Dash, dash_table, dcc, html, callback_context, no_update
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
# import dash_daq as daq
import re
import argparse
from threading import Thread

import dhcp
import global_config
import occ
import rpc_handler

from error_code import ErrorCode

import version as occv

parser = argparse.ArgumentParser(description=occv.__project_name__)
parser.add_argument('--tport', type=int, help='port for thrift server, default 9090',
  default=9090, choices=range(1,65536),metavar='{0...65535}')
parser.add_argument('--dport', type=int, help='port for plotly dashboard, default 8050',
  default=8050, choices=range(1,65536),metavar='{0...65535}')
parser.add_argument('-d', '--debug', action='store_true', help='run plotly dashboard in debug mode')
parser.add_argument('-v', '--version', action='store_true', help='show the version and exit')
args = parser.parse_args()

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# external_stylesheets = ['./style.css']

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
5. 使用开机卡的机器， host_name 应与 APP 上设置的名称保持一致。
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

def serve_layout():
  print('refresh serve layout')
  df_hosts = global_config.get_hosts_dataframe()
  df_os = global_config.get_os_dataframe()
  df_data_disk = global_config.get_data_disk_dataframe()
  df_boot_menu = global_config.get_boot_menu_dataframe()
  return html.Div([
    html.H1(
      children=occv.__project_name__,
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
            #   {
            #     'if': {
            #       'filter_query': '{{{col}}} = "N/A"'.format(col=col),
            #       'column_id': col
            #     },
            #     'backgroundColor': 'tomato',
            #     'color': 'white'
            #   } for col in df_hosts.columns
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
            dcc.Input(id='host-mac-input', type='text', style={'width':120},
              placeholder='11:22:33:AA:BB:CC'),
            html.Label(style={'width':10}),
            html.Label('default menu: '),
            html.Label(style={'width':10}),
            dcc.Dropdown(id='host-default-menu-dropdown',
              options=df_boot_menu['name'].tolist(),
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
            page_size=5,
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
            page_size=5,
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
            page_size=5,
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
              options=df_os['name'].tolist(),
              style={'width':200}),
            html.Label(style={'width':10}),
            html.Label('data disk: '),
            html.Label(style={'width':10}),
            dcc.Dropdown(id='boot-menu-data-disk-dropdown',
              options=df_data_disk['name'].tolist(),
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
              value=global_config.get_cache('volume_group_name')),
            html.Label(style={'width':10}),
            html.Div(id='operate-volume-group-name-state')
          ], style={'display': 'flex', 'flex-direction': 'row'}),
          html.Br(),
          html.Div(children=[
            html.Label('COW LV Size(G): '),
            html.Label(style={'width':10}),
            dcc.Input(id='cow-lv-size-input', type='number',
              value=global_config.get_cache('storage_lv_cow_size', default=10),
              min=1, max=1024, step=1),
            html.Label(style={'width':10}),
            html.Div(id='operate-cow-lv-size-state')
          ], style={'display': 'flex', 'flex-direction': 'row'}),
          html.H2('DHCP'),
          html.Div(children=[
            html.Label('network name: '),
            html.Label(style={'width':10}),
            dcc.Input(id='dhcp-network-name-input', type='text', debounce=True,
              value=global_config.get_cache('dhcp_network_name')),
            html.Label(style={'width':10}),
            html.Label('interface: '),
            html.Label(style={'width':10}),
            dcc.Input(id='dhcp-interface-input', type='text', debounce=True,
              value=global_config.get_cache('dhcp_interface'),
              style={'width':100}),
            html.Label(style={'width':10}),
            html.Div(id='operate-dhcp-network-name-state')
          ], style={'display': 'flex', 'flex-direction': 'row'}),
          html.Br(),
          html.Div(children=[
            html.Label('subnet: '),
            html.Label(style={'width':10}),
            dcc.Input(id='dhcp-subnet-input', type='text', debounce=True,
              value=global_config.get_cache('dhcp_subnet'),
              style={'width':100}),
            html.Label(style={'width':10}),
            html.Label('subnet mask: '),
            html.Label(style={'width':10}),
            dcc.Input(id='dhcp-subnet-mask-input', type='text', debounce=True,
              value=global_config.get_cache('dhcp_subnet_mask'),
              style={'width':100}),
            html.Label(style={'width':10}),
            html.Label('range: '),
            html.Label(style={'width':10}),
            dcc.Input(id='dhcp-range-from-input', type='text', debounce=True,
              value=global_config.get_cache('dhcp_range_from'),
              style={'width':100}),
            html.Label(style={'width':10}),
            html.Label(' - '),
            html.Label(style={'width':10}),
            dcc.Input(id='dhcp-range-to-input', type='text', debounce=True,
              value=global_config.get_cache('dhcp_range_to'),
              style={'width':100}),
          ], style={'display': 'flex', 'flex-direction': 'row'}),
          html.Br(),
          html.Div(children=[
            html.Label('routers: '),
            html.Label(style={'width':10}),
            dcc.Input(id='dhcp-routers-input', type='text', debounce=True,
              value=global_config.get_cache('dhcp_routers')),
            html.Label(style={'width':10}),
            html.Label('dns servers: '),
            html.Label(style={'width':10}),
            dcc.Input(id='dhcp-dns-servers-input', type='text', debounce=True,
              value=global_config.get_cache('dhcp_dns_servers')),
            html.Label(style={'width':10}),
            html.Label('broadcast address: '),
            html.Label(style={'width':10}),
            dcc.Input(id='dhcp-broadcast-address-input', type='text', debounce=True,
              value=global_config.get_cache('dhcp_broadcast_address'),
              style={'width':100}),
          ], style={'display': 'flex', 'flex-direction': 'row'}),
          html.Br(),
          html.Div(children=[
            html.Label('filename: '),
            html.Label(style={'width':10}),
            dcc.Input(id='dhcp-filename-input', type='text', debounce=True,
              value=global_config.get_cache('dhcp_filename'),
              style={'width':300}),
            html.Label(style={'width':10}),
            html.Label('next server: '),
            html.Label(style={'width':10}),
            dcc.Input(id='dhcp-next-server-input', type='text', debounce=True,
              value=global_config.get_cache('dhcp_next_server'),
              style={'width':100}),
          ], style={'display': 'flex', 'flex-direction': 'row'}),
          html.Div(id='operate-dhcp-server-state'),
          html.H2('HTTP'),
          html.Div(children=[
            html.Label('root path: '),
            html.Label(style={'width':10}),
            dcc.Input(id='http-root-path-input', type='text', debounce=True,
              value=global_config.get_cache('http_root_path')),
            html.Label(style={'width':10}),
            html.Label('http ip:port '),
            html.Label(style={'width':10}),
            dcc.Input(id='http-base-url-input', type='text', debounce=True,
              value=global_config.get_cache('http_base_url')),
            html.Div(id='operate-http-server-state'),
          ], style={'display': 'flex', 'flex-direction': 'row'}),
          html.H2('iSCSI'),
          html.Div(children=[
            html.Label('iscsi server: '),
            html.Label(style={'width':10}),
            dcc.Input(id='iscsi-server-input', type='text', debounce=True,
              value=global_config.get_cache('iscsi_server'),
              style={'width':100}),
            html.Label(style={'width':10}),
            html.Label('initiator iqn: '),
            html.Label(style={'width':10}),
            dcc.Input(id='iscsi-initiator-iqn-input', type='text', debounce=True,
              value=global_config.get_cache('iscsi_initiator_iqn'),
              style={'width':300}),
            html.Label(style={'width':10}),
            html.Label('target prefix: '),
            html.Label(style={'width':10}),
            dcc.Input(id='iscsi-target-prefix-input', type='text', debounce=True,
              value=global_config.get_cache('iscsi_target_prefix'),
              style={'width':200}),
          ], style={'display': 'flex', 'flex-direction': 'row'}),
          html.Div(id='operate-iscsi-setting-state'),
          html.H2('Smyoo'),
          html.Div(children=[
            html.Label('phone number: '),
            html.Label(style={'width':10}),
            dcc.Input(id='smyoo-phone-input', type='tel', debounce=True,
              value=global_config.get_cache('smyoo_phone',default=''),
              placeholder='input type telphone number'),
            html.Label(style={'width':10}),
            html.Label('password '),
            html.Label(style={'width':10}),
            dcc.Input(id='smyoo-password-input', type='password', debounce=True,
              value=global_config.get_cache('smyoo_password',default=''),
              placeholder='input type password'),
            html.Label(style={'width':10}),
            html.Div(id='operate-smyoo-state'),
          ], style={'display': 'flex', 'flex-direction': 'row'}),
        ], style={'padding': 10, 'flex': 1})
      ])
    ], style=tabs_styles),
    html.Div(id='tabs-content-props')
    # html.Div(id='thrift-interval-state'),
    # dcc.Interval(id='thrift-interval',interval=1*1000,n_intervals=0)
  ])

app.layout = serve_layout

@app.callback(
  Output('host-name-input', 'value'),
  Output('host-ip-input', 'value'),
  Output('host-mac-input', 'value'),
  Output('host-default-menu-dropdown', 'value'),
  Output('host-super-tube-checklist', 'value'),
  Input('hosts-table', "data"),
  Input('hosts-table', 'selected_rows')
)
def load_hosts_table_item(rows, selected_rows):
  if rows is None or selected_rows is None:
    raise PreventUpdate
  for index in selected_rows:
    hostname = rows[index]['host_name']
    ipaddr = rows[index]['ip']
    macaddr = rows[index]['mac']
    default_menu = rows[index]['default_menu']
    super_tube = rows[index]['super_tube']
    super_tube_value = ['Super tube'] if super_tube else []
    return hostname, ipaddr, macaddr, default_menu, super_tube_value
  raise PreventUpdate

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
  State('host-mac-input', 'value'),
  State('host-name-input', 'value'),
  State('host-ip-input', 'value'),
  State('host-default-menu-dropdown', 'value'),
  State('host-super-tube-checklist', 'value'),
  State('hosts-table', "data"),
  State('hosts-table', 'selected_rows'),
  State('cow-lv-size-input', 'value')
)
def edit_hosts_table(n_clicks1, n_clicks2, n_clicks3, n_clicks4, n_clicks5,
  n_clicks6, macaddr, hostname, ipaddr, default_menu, super_tube_value, rows,
  selected_rows, snap_lv_size):
  if n_clicks1 == 0 and n_clicks2 == 0 and n_clicks3 == 0 and n_clicks4 == 0 \
    and n_clicks5 == 0 and n_clicks6 == 0:
    raise PreventUpdate

  # 转换所需值
  macaddr = macaddr.upper() if macaddr else ''
  super_tube = True if super_tube_value and super_tube_value.count('Super tube') > 0 else False

  ctx = callback_context
  trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
  if trigger_id == 'add-host-button':
    # if re.match('^[A-F0-9]{2}(:[A-F0-9]{2}){5}$', '00:0C:29:A8:81:F2'):
    if not re.match('^[A-Fa-f0-9]{2}(:[A-Fa-f0-9]{2}){5}$', f'{macaddr}'):
      return no_update, 'invalid mac address', no_update
    if not re.match('^\w+$', f'{hostname}'):
      return no_update, 'invalid host name', no_update
    if not re.match(
      '((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}',
      f'{ipaddr}'):
      return no_update, 'invalid ip address', no_update

    result_code, result_message, index = occ.host_add_item(macaddr, hostname,
      ipaddr, default_menu, super_tube)
    if result_code != 0:
      return no_update, result_message, no_update
    else:
      if index is None:
        rows.append({
          'host_name': hostname,
          'ip': ipaddr,
          'mac': macaddr,
          'default_menu': default_menu,
          'super_tube': super_tube
        })
      else:
        rows[index]['host_name'] = hostname
        rows[index]['ip'] = ipaddr
        rows[index]['default_menu'] = default_menu
        rows[index]['super_tube'] = super_tube
      return rows, '', no_update
  elif trigger_id == 'delete-host-button':
    if rows is None or len(rows) == 0:
      raise PreventUpdate
    if selected_rows is None or len(selected_rows) == 0:
      return no_update, 'selected none', no_update
    else:
      for index_num in selected_rows:
        result_code, result_message = occ.host_del_item(
          hostname=rows[index_num]['host_name'], macaddr=rows[index_num]['mac'])
        if result_code != 0:
          return no_update, result_message, no_update
        else:
          rows.pop(index_num)
          selected_rows.clear()
        break;
      return rows, '', selected_rows
  elif trigger_id == 'power-on-button':
    if rows is None or len(rows) == 0:
      raise PreventUpdate
    if selected_rows is None or len(selected_rows) == 0:
      return no_update, 'selected none', no_update
    else:
      for index_num in selected_rows:
        result_code, result_message = occ.host_power_on_item(
          hostname = rows[index_num]['host_name'])
        return no_update, result_message if result_code != 0 else '', no_update
  elif trigger_id == 'power-off-button':
    if rows is None or len(rows) == 0:
      raise PreventUpdate
    if selected_rows is None or len(selected_rows) == 0:
      return no_update, 'selected none', no_update
    else:
      for index_num in selected_rows:
        result_code, result_message = occ.host_power_off_item(
          hostname = rows[index_num]['host_name'])
        return no_update, result_message if result_code != 0 else '', no_update
  elif trigger_id == 'reset-host-image':
    if rows is None or len(rows) == 0:
      raise PreventUpdate
    if selected_rows is None or len(selected_rows) == 0:
      return no_update, 'selected none', no_update
    else:
      for index_num in selected_rows:
        default_menu = rows[index_num]['default_menu']
        format_mac = ''.join(rows[index_num]['mac'].split(':')).lower()
        super_tube = rows[index_num]['super_tube']
        result_code, result_message = occ.reset_host_boot_menu(
          format_mac, default_menu, snap_lv_size)
        return no_update, result_message if result_code != 0 else '', no_update
  elif trigger_id == 'restart-dhcp-button':
    result_code = dhcp.restart_dhcp_service()
    result_message = 'restart dhcp service failed' if result_code != 0 else ''
    return no_update, result_message, no_update

  return no_update, 'unknown processing', no_update

@app.callback(
  Output('restore-after-restart-state', 'children'),
  Input('restore-after-restart-button', 'n_clicks')
)
def restore_after_restart(n_clicks):
  if n_clicks == 0:
    raise PreventUpdate
  result_code, result_message = occ.restore_after_restart()
  if result_code != 0:
    return result_message
  return ''

@app.callback(
  Output('os-name-input', 'value'),
  Output('os-description-input', 'value'),
  Output('os-capacity-input', 'value'),
  Input('os-table', 'data'),
  Input('os-table', 'selected_rows')
)
def load_os_table_item(rows, selected_rows):
  if rows is None or selected_rows is None:
    raise PreventUpdate
  for index in selected_rows:
    # 此处使用dff.loc[index].name可能有歧义，会返回pandas Series的行序号
    name = rows[index]['name']
    description = rows[index]['description']
    capacity = rows[index]['capacity']
    # print(type(dff.iloc[index].capacity))
    return name, description, capacity
  raise PreventUpdate

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
  State('os-table', 'data'),
  State('os-table', 'selected_rows')
)
def edit_operation_system_table(n_clicks1, n_clicks2,
  name, description, capacity, rows, selected_rows):
  if n_clicks1 == 0 and n_clicks2 == 0:
    raise PreventUpdate

  ctx = callback_context
  trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
  if trigger_id == 'add-os-button':
    if not re.match('^\w+$', f'{name}'):
      return no_update, 'invalid name', no_update, no_update

    result_code, result_message = occ.operation_system_add_item(
      name, description, capacity)
    if result_code != 0:
      return no_update, result_message, no_update, no_update
    else:
      rows.append({
        'name': name,
        'description': description,
        'capacity': capacity
      })
      return rows, '', no_update, [item['name'] for item in rows]
  elif trigger_id == 'del-os-button':
    if rows is None or len(rows) == 0:
      raise PreventUpdate
    if selected_rows is None or len(selected_rows) == 0:
      return no_update, 'selected none', no_update, no_update
    else:
      for index_num in selected_rows:
        result_code, result_message = occ.operation_system_del_item(
          rows[index_num]['name'])
        if result_code != 0:
          return no_update, result_message, no_update, no_update
        else:
          rows.pop(index_num)
          selected_rows.clear()
        break;
      return rows, '', selected_rows, [item['name'] for item in rows]

  return no_update, 'unknown processing', no_update, no_update

@app.callback(
  Output('data-disk-name-input', 'value'),
  Output('data-disk-description-input', 'value'),
  Output('data-disk-capacity-input', 'value'),
  Input('data-disk-table', 'data'),
  Input('data-disk-table', 'selected_rows')
)
def load_data_disk_table_item(rows, selected_rows):
  if rows is None or selected_rows is None:
    raise PreventUpdate
  for index in selected_rows:
    name = rows[index]['name']
    description = rows[index]['description']
    capacity = rows[index]['capacity']
    return name, description, capacity
  raise PreventUpdate

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
  State('data-disk-table', 'data'),
  State('data-disk-table', 'selected_rows')
)
def edit_data_disk_table(n_clicks1, n_clicks2,
  name, description, capacity, rows, selected_rows):
  if n_clicks1 == 0 and n_clicks2 == 0:
    raise PreventUpdate

  ctx = callback_context
  trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
  if trigger_id == 'add-data-disk-button':
    if not re.match('^\w+$', f'{name}'):
      return no_update, 'invalid name', no_update, no_update

    result_code, result_message = occ.data_disk_add_item(
      name, description, capacity)
    if result_code != 0:
      return no_update, result_message, no_update, no_update
    else:
      rows.append({
        'name': name,
        'description': description,
        'capacity': capacity
      })
      return rows, '', no_update, [item['name'] for item in rows]
  elif trigger_id == 'del-data-disk-button':
    if rows is None or len(rows) == 0:
      raise PreventUpdate
    if selected_rows is None or len(selected_rows) == 0:
      return no_update, 'selected none', no_update, no_update
    else:
      for index_num in selected_rows:
        result_code, result_message = occ.data_disk_del_item(
          rows[index_num]['name'])
        if result_code != 0:
          return no_update, result_message, no_update, no_update
        else:
          rows.pop(index_num)
          selected_rows.clear()
        break;
      return rows, '', selected_rows, [item['name'] for item in rows]

  return no_update, 'unknown processing', no_update, no_update

@app.callback(
  Output('boot-menu-name-input', 'value'),
  Output('boot-menu-operation-system-dropdown', 'value'),
  Output('boot-menu-data-disk-dropdown', 'value'),
  Input('boot-menu-table', 'data'),
  Input('boot-menu-table', 'selected_rows')
)
def load_boot_menu_table_item(rows, selected_rows):
  if rows is None or selected_rows is None:
    raise PreventUpdate
  for index in selected_rows:
    name = rows[index]['name']
    operation_system = rows[index]['operation_system']
    data_disk = rows[index]['data_disk'].split(",")
    return name, operation_system, data_disk
  raise PreventUpdate

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
  State('boot-menu-table', 'data'),
  State('boot-menu-table', 'selected_rows')
)
def edit_boot_menu_table(n_clicks1, n_clicks2, n_clicks3,
  name, operation_system, data_disk, rows, selected_rows):
  if n_clicks1 == 0 and n_clicks2 == 0 and n_clicks3 == 0:
    raise PreventUpdate

  ctx = callback_context
  trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
  if trigger_id == 'add-boot-menu-button':
    if not re.match('^\w+$', f'{name}'):
      return no_update, 'invalid name', no_update, no_update
    if operation_system is None or len(operation_system) == 0:
      return no_update, 'empty operation system', no_update, no_update

    result_code, result_message = occ.boot_menu_add_item(
      name, operation_system, data_disk)
    if result_code != 0:
      return no_update, result_message, no_update, no_update
    else:
      rows.append({
        'name': name,
        'operation_system': operation_system,
        'data_disk': ','.join(data_disk)
      })
      return rows, '', no_update, [item['name'] for item in rows]
  elif trigger_id == 'del-boot-menu-button':
    if rows is None or len(rows) == 0:
      raise PreventUpdate
    if selected_rows is None or len(selected_rows) == 0:
      return no_update, 'selected none', no_update, no_update
    else:
      for index_num in selected_rows:
        result_code, result_message = occ.boot_menu_del_item(
          rows[index_num]['name'])
        if result_code != 0:
          return no_update, result_message, no_update, no_update
        else:
          rows.pop(index_num)
          selected_rows.clear()
        break;
      return rows, '', selected_rows, [item['name'] for item in rows]
  elif trigger_id == 'del-boot-menu-snap-button':
    if rows is None or len(rows) == 0:
      raise PreventUpdate
    if selected_rows is None or len(selected_rows) == 0:
      return no_update, 'selected none', no_update, no_update
    else:
      for index_num in selected_rows:
        occ.boot_menu_del_item_snap(rows[index_num]['name'])
      return no_update, '', no_update, no_update

  return no_update, 'unknown processing', no_update, no_update

@app.callback(
  Output('operate-volume-group-name-state', 'children'),
  Input('volume-group-name-input', 'value')
)
def edit_volume_group_name(volume_group):
  result_code, result_message = occ.set_volume_group_name(volume_group)
  return result_message

@app.callback(
  Output('operate-cow-lv-size-state', 'children'),
  Input('cow-lv-size-input', 'value')
)
def edit_cow_lv_size(size):
  result_code, result_message = occ.set_cow_lv_size(size)
  if result_code != 0:
    return result_message
  return ''

@app.callback(
  Output('operate-dhcp-network-name-state', 'children'),
  Input('dhcp-network-name-input', 'value')
)
def edit_dhcp_network_name(network_name):
  result_code, result_message = occ.set_dhcp_network_name(network_name)
  if result_code != 0:
    return result_message
  return ''

@app.callback(
  Output('operate-dhcp-server-state', 'children'),
  Input('dhcp-interface-input', 'value'),
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
def edit_dhcp_server_subnet(network_interface, subnet, subnet_mask, range_from,
  range_to, routers, dns_servers, broadcast_address, filename, next_server):
  result_code, result_message = occ.set_dhcp_server_subnet(network_interface,
    subnet, subnet_mask, range_from, range_to, routers, dns_servers,
    broadcast_address, filename, next_server)
  if result_code != 0:
    return result_message
  return ''

@app.callback(
  Output('operate-http-server-state', 'children'),
  Input('http-root-path-input', 'value'),
  Input('http-base-url-input', 'value'),
  Input('iscsi-server-input', 'value')
)
def edit_http_server_setting(root_path, base_url, iscsi_server):
  result_code, result_message = occ.set_http_server_setting(
    root_path, base_url, iscsi_server)
  if result_code != 0:
    return result_message
  return ''

@app.callback(
  Output('operate-iscsi-setting-state', 'children'),
  Input('iscsi-initiator-iqn-input', 'value'),
  Input('iscsi-target-prefix-input', 'value')
)
def edit_iscsi_setting(initiator_iqn, iscsi_target_prefix):
  occ.set_iscsi_setting(initiator_iqn, iscsi_target_prefix)
  raise PreventUpdate

@app.callback(
  Output('operate-smyoo-state', 'children'),
  Input('smyoo-phone-input', 'value'),
  Input('smyoo-password-input', 'value')
)
def edit_smyoo_setting(phone, password):
  # print('phone:', phone, ', password:', password)
  result_code, result_message = occ.set_smyoo_account(phone, password)
  if result_code != 0:
    return result_message
  return ''

if __name__ == '__main__':
  if args.version:
    print(occv.__version__)
  else:
    tt = Thread(target=rpc_handler.thrift_thread, args=(args.tport,))
    tt.start()
    if args.debug:
      app.run_server(debug=True, host='0.0.0.0', port=args.dport)
    else:
      app.run_server(debug=False, host='0.0.0.0', port=args.dport)
    print("done!")
