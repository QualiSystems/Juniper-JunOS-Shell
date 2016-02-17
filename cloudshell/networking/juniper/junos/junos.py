import time
import collections
import socket

from cloudshell.networking.juniper.juniper_base import JuniperBase
from cloudshell.cli import expected_actions
from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.networking.juniper.autoload.juniper_snmp_autoload import JuniperSnmpAutoload
from cloudshell.networking.juniper.junos.command_templates.add_remove_vlan import ADD_REMOVE_VLAN_TEMPLATES
from cloudshell.snmp.quali_snmp import QualiSnmp
import re
from cloudshell.networking.parameters_service.parameters_service import ParametersService


class JunOS(JuniperBase):
    CONFIG_MODE_PROMPT = '.*# *$'
    EXPECTED_MAP = collections.OrderedDict([('Username: *$|Login: *$', expected_actions.send_username),
                                            ('closed by remote host', expected_actions.do_reconnect),
                                            ('continue connecting', expected_actions.send_yes),
                                            ('Got termination signal', expected_actions.wait_prompt_or_reconnect),
                                            ('Broken pipe', expected_actions.send_command),
                                            ('[Yy]es', expected_actions.send_yes),
                                            ('More', expected_actions.send_empty_string),
                                            ('[Pp]assword: *$', expected_actions.send_password)
                                            ])

    SPACE = '<QS_SP>'
    RETURN = '<QS_CR>'
    NEWLINE = '<QS_LF>'

    ERROR_LIST = [r'syntax\s+error,\s+expecting', r'error:\s+configuration\s+check-out\s+failed', r'syntax\s+error',
                  r'error:\s+Access\s+interface']

    def __init__(self, connection_manager, logger=None):
        self._connection_manager = connection_manager
        self._session = None
        self._logger = logger
        self._prompt = '.*[>%#] *$'
        self._params_sep = ' '
        self._command_retries = 3
        self._expected_map = dict(JunOS.EXPECTED_MAP)
        self._snmp_handler = None
        self._cloud_shell_api = None
        self._commands_templates = ADD_REMOVE_VLAN_TEMPLATES

    @property
    def snmp_handler(self):
        if not self._snmp_handler:
            self._snmp_handler = self.create_snmp_handler()
        return self._snmp_handler

    @snmp_handler.setter
    def snmp_handler(self, hsnmp):
        self._snmp_handler = hsnmp

    def cloud_shell_api(self):
        if not self._cloud_shell_api:
            hostname = socket.gethostname()
            testshell_ip = socket.gethostbyname(hostname)
            testshell_user = self.reservation_dict['AdminUsername']
            testshell_password = self.reservation_dict['AdminPassword']
            testshell_domain = self.reservation_dict['Domain']
            self._cloud_shell_api = CloudShellAPISession(testshell_ip, testshell_user, testshell_password,
                                                         testshell_domain)
        return self._cloud_shell_api

    def set_parameters(self, json_object):
        self.resources_dict = json_object['resource']
        self.reservation_dict = json_object['reservation']
        pass

    def _send_command(self, command, expected_str=None, expected_map=None, timeout=30, retry_count=10,
                      is_need_default_prompt=True):
        if expected_map is None:
            expected_map = self._expected_map

        if not expected_str:
            expected_str = self._prompt
        else:
            if is_need_default_prompt:
                expected_str = expected_str + '|' + self._prompt

        if not self._session:
            self.connect()

        out = ''
        for retry in range(self._command_retries):
            try:
                out = self._session.hardware_expect(command, expected_str, timeout, expected_map=expected_map,
                                                    retry_count=retry_count)
                break
            except Exception as e:
                self._logger.error(e)
                if retry == self._command_retries - 1:
                    raise Exception('Can not send command')
                self.reconnect()
        return out

    def send_commands_list(self, commands_list):
        output = ""
        for command in commands_list:
            output += self.send_config_command(command)
        return output

    def _default_actions(self):
        '''Send default commands to configure/clear session outputs

        :return:
        '''
        current_promt = self._send_command('')
        if '%' in current_promt:
            self._send_command('cli')
        self._session.set_unsafe_mode(True)

    def _enter_configuration_mode(self):
        """Send 'enter' to SSH console to get prompt,
        if default prompt received , send 'configure terminal' command, change _prompt to CONFIG_MODE
        else: return

        :return: True if config mode entered, else - False
        """
        if not self._getSessionHandler():
            self.connect()

        if self._session.__class__.__name__ == 'FileManager':
            return ''

        out = None
        for retry in range(3):
            out = self._send_command(' ')
            if not out:
                self._logger.error('Failed to get prompt, retrying ...')
                time.sleep(1)

            elif not re.search(self.CONFIG_MODE_PROMPT, out):
                out = self._send_command('configure', self.CONFIG_MODE_PROMPT)

            else:
                break

        if not out:
            return False
        # self._prompt = self.CONFIG_MODE_PROMPT
        return re.search(self._prompt, out)

    def _exit_configuration_mode(self):
        """Send 'enter' to SSH console to get prompt,
        if config prompt received , send 'exit' command, change _prompt to DEFAULT
        else: return

        :return: console output
        """

        if not self._getSessionHandler():
            self.connect()

        if self._session.__class__.__name__ == 'FileManager':
            return ''

        out = None
        for retry in range(5):
            out = self._send_command(' ')
            if re.search(self.CONFIG_MODE_PROMPT, out):
                self._send_command('exit')
            else:
                break
        # self._prompt = self.ENABLE_PROMPT

        return out

    def _get_resource_full_name(self, port_resource_address, resource_details_map):
        result = None
        for port in resource_details_map.ChildResources:
            if port.FullAddress in port_resource_address and port.FullAddress == port_resource_address:
                return port.Name
            if port.FullAddress in port_resource_address and port.FullAddress != port_resource_address:
                result = self._get_resource_full_name(port_resource_address, port)
            if result is not None:
                return result
        return result

    def configure_vlan(self, vlan_range, ports, switchport_type, additional_info, remove=False):
        """
        Sends snmp get command
        :param vlan_range: range of vlans to be added, if empty, and switchport_type = trunk, trunk mode will be assigned
        :param ports: List of interfaces Resource Full Address
        :param switchport_type: type of adding vlan ('trunk' or 'access')
        :param additional_info: contains QNQ or CTag parameter
        :param remove: remove or add flag
        :return: success message
        :rtype: string
        """

        self._logger.info('Vlan Configuration Started')
        self._logger.info(
            'Ports: ' + ports + ', Vlan_range: ' + vlan_range + ', Typa: ' + switchport_type + ', Additional_info: ' + additional_info)
        if len(ports) < 1:
            raise Exception('Port list is empty')
        if vlan_range == '' and switchport_type == 'access':
            raise Exception('Switchport type is Access, but vlan id/range is empty')
        port_list = []
        for port in ports.split('|'):
            port_resource_map = self.cloud_shell_api().GetResourceDetails(self.resources_dict['ResourceName'])
            temp_port_name = self._get_resource_full_name(port, port_resource_map)
            if not temp_port_name or '/' not in temp_port_name:
                self._logger.error('Interface was not found')
                raise Exception('Interface {0} was not found'.format(port))
            port_name_splited = temp_port_name.split('/')[-1].split('-', 1)
            port_name = "{0}-{1}".format(port_name_splited[0], port_name_splited[1].replace('-', '/'))
            port_list.append(port_name)

        vlan_map = {"vlan-" + name.strip(): name.strip() for name in vlan_range.split(',')}
        self._logger.info('Vlan map: '+str(vlan_map))

        if remove:
            for port in port_list:
                self._remove_vlans_on_port(port, vlan_map.keys())
                # self._remove_port_mode_on_interface(port)
            self._delete_vlans(vlan_map.keys())
        else:
            for vlan_name in vlan_map:
                self._create_vlan(vlan_name, vlan_map[vlan_name], additional_info)
            for port in port_list:
                self._clean_port(port)
                self._add_vlans_on_port(port, vlan_map.keys(), switchport_type)

        self.commit()
        self._exit_configuration_mode()

        self._logger.info('Vlan {0} was assigned to the interfaces {1}'.format(vlan_range, ports))
        return 'Vlan Configuration Completed'

    def _get_ports_for_vlan(self, vlan_name):
        output = self.send_config_command("run show vlans {0}".format(vlan_name))
        ports = re.findall(r'\w+-(?:\d+/)+\d+', re.sub(r'\n|\r', '', output))
        if ports:
            return [port.strip() for port in ports]
        return []

    def _create_vlan(self, vlan_name, vlan_range, additional_info):
        if 'qnq' in additional_info:
            self.configure_interface_ethernet(self._create_qnq_vlan_flow(vlan_name, vlan_range))
        else:
            if re.match(r'\d+-\d+', vlan_range):
                self.configure_interface_ethernet(self._create_vlan_range_flow(vlan_name, vlan_range))
            else:
                self.configure_interface_ethernet(self._create_vlan_flow(vlan_name, vlan_range))

    def _delete_vlan(self, vlan_name):
        for port in self._get_ports_for_vlan(vlan_name):
            self._remove_vlans_on_port(port, [vlan_name])
        self.configure_interface_ethernet(self._delete_vlan_flow(vlan_name))

    def _delete_vlans(self, vlan_list):
        for vlan_name in vlan_list:
            self._delete_vlan(vlan_name)

    def _add_vlans_on_port(self, port, vlan_list, type):
        for vlan_name in vlan_list:
            self.configure_interface_ethernet(self._set_vlan_to_interface_flow(port, type, vlan_name))
            self._logger.info('Vlan {0} will be assigned on interface {1}'.format(vlan_name, port))

    def _remove_vlans_on_port(self, port, vlan_list):
        for vlan_name in vlan_list:
            self.configure_interface_ethernet(self._delete_vlan_on_interface_flow(port, vlan_name))
            self._logger.info('Vlan {0} removed from interface {1}'.format(vlan_name, port))

    def _get_vlans_for_port(self, port):
        output = self.send_config_command('show interfaces {0}'.format(port))
        found_list = re.findall(r'vlan\s*\{\s*members\s*\[*\s*((?:[\w\d-]+\s*)+)\s*\]*\s*;\s*\}',
                                re.sub(r'\n|\r', '', output))
        if len(found_list) > 0:
            return [vlan.strip() for vlan in found_list[0].split()]
        return []

    def _clean_port(self, port):
        vlans = self._get_vlans_for_port(port)
        self._remove_vlans_on_port(port, vlans)
        self._remove_port_mode_on_interface(port)
        self._logger.info("Cleaning port {0}, vlans, {1}".format(port, ", ".join(vlans)))

    def _remove_port_mode_on_interface(self, port):
        self.configure_interface_ethernet(self._delete_port_mode_on_interface_flow(port))
        self._logger.info("Port mode removed for {0}".format(port))

    def _create_vlan_flow(self, vlan_name, vlan_id):
        cmd_map = collections.OrderedDict()
        cmd_map['create_vlan'] = [vlan_name, vlan_id]
        return cmd_map

    def _create_vlan_range_flow(self, vlan_range_name, vlan_range):
        cmd_map = collections.OrderedDict()
        cmd_map['create_vlan_range'] = [vlan_range_name, vlan_range]
        return cmd_map

    def _create_qnq_vlan_flow(self, vlan_name, vlan_id):
        cmd_map = collections.OrderedDict()
        cmd_map['create_vlan'] = [vlan_name, vlan_id]
        cmd_map['create_vlan_qinq'] = [vlan_name]
        return cmd_map

    def _set_vlan_to_interface_flow(self, port, type, vlan_name):
        cmd_map = collections.OrderedDict()
        cmd_map['set_vlan_to_interface'] = [port, type.lower(), vlan_name]
        return cmd_map

    def _delete_vlan_on_interface_flow(self, port, vlan_name):
        cmd_map = collections.OrderedDict()
        cmd_map['delete_vlan_on_interface'] = [port, vlan_name]
        return cmd_map

    def _delete_port_mode_on_interface_flow(self, port):
        cmd_map = collections.OrderedDict()
        cmd_map['delete_port_mode_on_interface'] = [port]
        return cmd_map

    def _delete_vlan_flow(self, vlan_name):
        cmd_map = collections.OrderedDict()
        cmd_map['delete_vlan'] = [vlan_name]
        return cmd_map

    def _commit_flow(self):
        cmd_map = collections.OrderedDict()
        cmd_map['commit'] = []
        return cmd_map

    def _rollback_flow(self):
        cmd_map = collections.OrderedDict()
        cmd_map['rollback'] = []
        return cmd_map

    def configure_interface_ethernet(self, command_map):
        """
        Configures interface ethernet
        :param kwargs: dictionary of parameters
        :return: success message
        :rtype: string
        """

        commands_list = self.get_commands_list(command_map)
        output = self.send_commands_list(commands_list)
        self._check_output_for_errors(output)
        return 'Finished configuration of ethernet interface!'

    def _check_output_for_errors(self, output):
        for error_pattern in self.ERROR_LIST:
            if re.search(error_pattern, output):
                self.rollback()
                raise Exception(
                    'Output contains error with pattern: "{0}", for output: "{1}"'.format(error_pattern, output))

    def discover_snmp(self):
        """Load device structure, and all required Attribute according to Networking Elements Standardization design
        :return: Attributes and Resources matrix,
        currently in string format (matrix separated by '$', lines by '|', columns by ',')
        """
        # ToDo add voperation system validation
        # if not self.is_valid_device_os():
        # error_message = 'Incompatible driver! Please use correct resource driver for {0} operation system(s)'. \
        #    format(str(tuple(self.supported_os)))
        # self._logger.error(error_message)
        # raise Exception(error_message)

        self._logger.info('************************************************************************')
        self._logger.info('Start SNMP discovery process .....')
        generic_autoload = JuniperSnmpAutoload(self.snmp_handler, self._logger)
        result = generic_autoload.get_inventory()
        self._logger.info('Start SNMP discovery Completed')
        return result

    def send_config_command(self, cmd, expected_str=None, timeout=30):
        """Send command into configuration mode, enter to config mode if needed

        :param cmd: command to send
        :param expected_str: expected output string (_prompt by default)
        :param timeout: command timeout
        :return: received output buffer
        """

        self._enter_configuration_mode()

        if expected_str is None:
            expected_str = self._prompt

        out = self._send_command(command=cmd, expected_str=expected_str, timeout=timeout, is_need_default_prompt=False)
        self._logger.info(out)
        return out

    def commit(self):
        self.configure_interface_ethernet(self._commit_flow())

    def rollback(self):
        self.send_config_command('rollback')

    def connect(self):
        self._session = self._connection_manager.get_session(self._prompt)
        self._default_actions()

    def disconnect(self):
        if self._session:
            self._send_command('exit')
            self._send_command('exit')
            self._send_command('exit')
            return self._session.disconnect()

    def reconnect(self, retries_count=5, sleep_time=15):
        if self._session:
            self._session.reconnect(self._prompt, retries_count, sleep_time)

        self._default_actions()
        self._logger.info('Session reconnected successfully!')

    def _getSessionHandler(self):
        return self._session

    def _getLogger(self):
        return self._logger

    def set_expected_map(self, expected_map):
        self._expected_map = expected_map

    def create_snmp_handler(self):
        """
        Creates snmp handler if it is not yet created
        :param json_object: parsed json, to create snmp handler if its None
        """
        ip = self.resources_dict['ResourceAddress']
        user = self.resources_dict['SNMP V3 User']
        password = self.resources_dict['SNMP V3 Password']
        private_key = self.resources_dict['SNMP V3 Private Key']
        community = self.resources_dict['SNMP Read Community']
        version = self.resources_dict['SNMP Version']
        v3_user = None
        # if not self._snmp_handler:
        if '3' in version:
            if user != '' and password != '' and private_key != '':
                # userName=user, authKey=password, privKey=private_key, authProtocol=usmHMACSHAAuthProtocol, privProtocol=usmDESPrivProtocol
                v3_user = {'userName': user, 'authKey': password, 'privKey': private_key}
        else:
            if community == '':
                community = 'public'
        return QualiSnmp(ip=ip, v3_user=v3_user, community=community)

    def normalize_output(self, output):
        return output.replace(' ', self.SPACE).replace('\r\n', self.NEWLINE).replace('\n', self.NEWLINE).replace('\r',
                                                                                                                 self.NEWLINE)

    def get_commands_list(self, command_map):
        prepared_commands = []
        for command, value in command_map.items():
            if command in self._commands_templates:
                command_template = self._commands_templates[command]
                prepared_commands.append(ParametersService.get_validate_list(command_template, value))
        return prepared_commands

    def add_commands_templates(self, commands_templates):
        self._commands_templates.update(commands_templates)
