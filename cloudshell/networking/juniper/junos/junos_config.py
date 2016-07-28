from collections import OrderedDict
from cloudshell.shell.core.dependency_injection.context_based_logger import get_logger_with_thread_id

ERROR_MAP = OrderedDict(
    {r'[Ee]rror\s+saving\s+configuration': 'Save configuration error',
     r'syntax\s+error': 'Syntax error',
     r'[Uu]nknown\s+command': 'Uncnown command',
     r'[Ee]rror\s+.+': 'Error'})

DEFAULT_PROMPT = '[>%#]\s*$|[>%#]\s*\n'
CONFIG_MODE_PROMPT = r'.*#\s*$'
# EXPECTED_MAP = OrderedDict([('Username: *$|Login: *$', expected_actions.send_username),
#                                         ('closed by remote host', expected_actions.do_reconnect),
#                                         ('continue connecting', expected_actions.send_yes),
#                                         ('Got termination signal', expected_actions.wait_prompt_or_reconnect),
#                                         ('Broken pipe', expected_actions.send_command),
#                                         ('[Yy]es', expected_actions.send_yes),
#                                         ('[Mm]ore', expected_actions.send_empty_string),
#                                         ('[Pp]assword: *$', expected_actions.send_password)
#                                         ])


GET_LOGGER_FUNCTION = get_logger_with_thread_id