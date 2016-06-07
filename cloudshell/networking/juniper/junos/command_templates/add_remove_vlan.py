from cloudshell.cli.command_template.command_template import CommandTemplate

ADD_REMOVE_VLAN_TEMPLATES = {'create_vlan': CommandTemplate('set vlans {0} vlan-id {1}', [r'.+', r'.+'],
                                                    ['Wrong vlan name', 'Wrong vlan id']),
                     'create_vlan_qinq': CommandTemplate('set vlans {0} dot1q-tunneling', [r'.+'],
                                                         ['Wrong vlan name']),
                     'set_vlan_to_interface': CommandTemplate(
                         'set interfaces {0} unit 0 family ethernet-switching port-mode {1} vlan members {2}',
                         [r'.+', r'.+', r'.+'],
                         ['Wrong interface name', 'Wrong port mode', 'Wrong vlan name']),
                     'enable_interface': CommandTemplate('delete interfaces {0} disable', [r'.+'],
                                                         ['Wrong interface name']),
                     'disable_interface': CommandTemplate('set interfaces {0} disable', [r'.+'],
                                                          ['Incorrect interface']),
                     'delete_vlan_on_interface': CommandTemplate(
                         'delete interfaces {0} unit 0 family ethernet-switching vlan members {1}', [r'.+', r'.+'],
                         ['Incorrect interface name', 'Incorrect vlan name']),
                     'delete_port_mode_on_interface': CommandTemplate(
                         'delete interfaces {0} unit 0 family ethernet-switching port-mode', [r'.+'],
                         ['Incorrect interface name']),
                     'delete_vlan': CommandTemplate('delete vlans {0}', [r'.+'], ["Incorrect vlan name"]),
                     'create_vlan_range': CommandTemplate('set vlans {0} vlan-range {1}', [r'.+', r'.+'],
                                                          ['Incorrect vlan range name', 'Incorrect vlan range'])
                     }
