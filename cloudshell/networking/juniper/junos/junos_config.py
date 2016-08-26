from collections import OrderedDict

from cloudshell.shell.core.context_utils import get_resource_address, get_attribute_by_name_wrapper
from cloudshell.shell.core.dependency_injection.context_based_logger import get_logger_with_thread_id
from cloudshell.snmp.quali_snmp import QualiSnmp
from cloudshell.snmp.quali_snmp_cached import QualiSnmpCached

"""Default errors patterns"""
ERROR_MAP = OrderedDict(
    {r'[Ee]rror\s+saving\s+configuration': 'Save configuration error',
     r'syntax\s+error': 'Command syntax error',
     r'[Uu]nknown\s+command': 'Unknown command',
     r'[Ee]rror:\s+configuration\s+check-out\s+failed': 'Configuration checkout failed',
     r'ERROR:': 'Error, see logs for more details',
     r'[Ee]rror\s+.+': 'Error, see logs for more details'})

DEFAULT_PROMPT = '[%>#]\s*$|[%>#]\s*\n'
CONFIG_MODE_PROMPT = r'.*#\s*$'

SNMP_ERRORS = [r'No\s+Such\s+Object\s+currently\s+exists']

"""Dictionary used for snmp handler initialization"""
QUALISNMP_INIT_PARAMS = {'ip': get_resource_address,
                         'snmp_version': get_attribute_by_name_wrapper('SNMP Version'),
                         'snmp_user': get_attribute_by_name_wrapper('SNMP V3 User'),
                         'snmp_password': get_attribute_by_name_wrapper('SNMP V3 Password'),
                         'snmp_community': get_attribute_by_name_wrapper('SNMP Read Community'),
                         'snmp_private_key': get_attribute_by_name_wrapper('SNMP V3 Private Key'),
                         'snmp_errors': SNMP_ERRORS}


def create_snmp_handler():
    """
    Factory function which creates CachedSnmpHandler
    :return:
    """
    kwargs = {}
    for key, value in QUALISNMP_INIT_PARAMS.iteritems():
        if callable(value):
            kwargs[key] = value()
        else:
            kwargs[key] = value
    return QualiSnmp(**kwargs)


"""Attribute uses for snmp handler binding"""
SNMP_HANDLER_FACTORY = create_snmp_handler

"""Attribute uses for logger handler binding"""
GET_LOGGER_FUNCTION = get_logger_with_thread_id

"""Default expected_map """
EXPECTED_MAP = OrderedDict()
EXPECTED_MAP[r'[Mm]ore'] = lambda session: session.send_line('')


def juniper_default_actions(session):
    """
    Juniper default actions
    :param session:
    :return:
    """
    expected_map = OrderedDict()
    expected_map[r'%\s*'] = lambda session: session.send_line('cli')
    session.hardware_expect(data_str='', re_string='[>#]\s*$|[>#]\s*\n', expect_map=expected_map)
    session.hardware_expect(data_str='set cli screen-length 0', re_string=DEFAULT_PROMPT, expect_map=expected_map)


"""Attribute uses for default action definition"""
DEFAULT_ACTIONS = juniper_default_actions

"""Port description char replacement, order is important"""
PORT_NAME_CHAR_REPLACEMENT = OrderedDict()
PORT_NAME_CHAR_REPLACEMENT[':'] = '--'
PORT_NAME_CHAR_REPLACEMENT['/'] = '-'

