from cloudshell.cli.command_template.command_template import CommandTemplate
from cloudshell.networking.juniper.junos.command_templates.AddRemoveVlan import AddRemoveVlan

from cloudshell.networking.juniper.junos.command_templates.juniper_errors import COMMON_ERRORS

ACTION_MAP = {}
ERROR_MAP = {}

CREATE_VLAN = CommandTemplate('set vlans {0} vlan-id {1}', [r'.+', r'.+'], ['Wrong vlan name', 'Wrong vlan id'])
CREATE_VLAN_QNQ = CommandTemplate('set vlans {0} dot1q-tunneling', [r'.+'], ['Wrong vlan name'])
SET_VLAN_TO_INTERFACE = CommandTemplate(
    'set interfaces {0} unit 0 family ethernet-switching port-mode {1} vlan members {2}', [r'.+', r'.+', r'.+'],
    ['Wrong interface name', 'Wrong port mode', 'Wrong vlan name'])

ENABLE_INTERFACE = CommandTemplate('delete interfaces {0} disable', [r'.+'], ['Wrong interface name'])
DISABLE_INTERFACE = CommandTemplate('set interfaces {0} disable', [r'.+'], ['Incorrect interface'])

DELETE_VLAN_ON_INTERFACE = CommandTemplate('delete interfaces {0} unit 0 family ethernet-switching vlan members {1}',
                                           [r'.+', r'.+'], ['Incorrect interface name', 'Incorrect vlan name'])

DELETE_PORT_MODE_ON_INTERFACE = CommandTemplate('delete interfaces {0} unit 0 family ethernet-switching port-mode',
                                                ACTIONS,
                                              SAVE_RESTORE_ERRORS)

ADD_REMOVE_VALN_NEW=AddRemoveVlan()

DELETE_VLAN = CommandTemplate('delete vlans {0}', [r'.+'], ["Incorrect vlan name"])

CREATE_VLAN_RANGE = CommandTemplate('set vlans {0} vlan-range {1}', [r'.+', r'.+'],
                                    ['Incorrect vlan range name', 'Incorrect vlan range'])
