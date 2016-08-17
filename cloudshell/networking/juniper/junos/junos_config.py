from collections import OrderedDict

from cloudshell.shell.core.context_utils import get_resource_address, get_attribute_by_name_wrapper
from cloudshell.shell.core.dependency_injection.context_based_logger import get_logger_with_thread_id
from cloudshell.snmp.quali_snmp_cached import QualiSnmpCached

ERROR_MAP = OrderedDict(
    {r'[Ee]rror\s+saving\s+configuration': 'Save configuration error',
     r'syntax\s+error': 'Command syntax error',
     r'[Uu]nknown\s+command': 'Unknown command',
     r'[Ee]rror:\s+configuration\s+check-out\s+failed': 'Configuration checkout failed',
     r'[Ee]rror\s+.+': 'Error'})

DEFAULT_PROMPT = '[%>#]\s*$|[%>#]\s*\n'
CONFIG_MODE_PROMPT = r'.*#\s*$'

QUALISNMP_INIT_PARAMS = {'ip': get_resource_address,
                         'snmp_version': get_attribute_by_name_wrapper('SNMP Version'),
                         'snmp_user': get_attribute_by_name_wrapper('SNMP V3 User'),
                         'snmp_password': get_attribute_by_name_wrapper('SNMP V3 Password'),
                         'snmp_community': get_attribute_by_name_wrapper('SNMP Read Community'),
                         'snmp_private_key': get_attribute_by_name_wrapper('SNMP V3 Private Key')}


def create_snmp_handler():
    kwargs = {}
    for key, value in QUALISNMP_INIT_PARAMS.iteritems():
        if callable(value):
            kwargs[key] = value()
        else:
            kwargs[key] = value
    return QualiSnmpCached(**kwargs)


SNMP_HANDLER_FACTORY = create_snmp_handler

GET_LOGGER_FUNCTION = get_logger_with_thread_id

EXPECTED_MAP = OrderedDict()
EXPECTED_MAP[r'[Mm]ore'] = lambda session: session.send_line('')


def juniper_default_actions(session):
    expected_map = OrderedDict()
    expected_map[r'%\s*'] = lambda session: session.send_line('cli')
    session.hardware_expect(data_str='', re_string='[>#]\s*$|[>#]\s*\n', expect_map=expected_map)
    session.hardware_expect(data_str='set cli screen-length 0', re_string=DEFAULT_PROMPT, expect_map=expected_map)


DEFAULT_ACTIONS = juniper_default_actions

"""Port description char replacement, order is important"""
PORT_NAME_CHAR_REPLACEMENT = OrderedDict()
PORT_NAME_CHAR_REPLACEMENT[':'] = '--'
PORT_NAME_CHAR_REPLACEMENT['/'] = '-'
