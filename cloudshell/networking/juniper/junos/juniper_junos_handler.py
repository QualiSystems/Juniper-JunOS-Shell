import time
import collections
import socket

import re
from cloudshell.cli import expected_actions
from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.networking.juniper.autoload.juniper_snmp_autoload import JuniperSnmpAutoload
from cloudshell.networking.juniper.junos.command_templates.add_remove_vlan import ADD_REMOVE_VLAN_TEMPLATES
from cloudshell.networking.parameters_service.parameters_service import ParametersService
from cloudshell.networking.networking_handler_interface import NetworkingHandlerInterface
from cloudshell.shell.core.handler_base import HandlerBase


class JuniperJunosHandler(HandlerBase, NetworkingHandlerInterface):
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
        HandlerBase.__init__(self, connection_manager, logger)
        self._prompt = '.*[>%#] *$'
        self._expected_map = JuniperJunosHandler.EXPECTED_MAP
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

    def _get_ports_by_resources_path(self, ports):
        port_list = []
        for port in ports.split('|'):
            port_resource_map = self.cloud_shell_api().GetResourceDetails(self.attributes_dict['ResourceName'])
            temp_port_name = self._get_resource_full_name(port, port_resource_map)
            if not temp_port_name or '/' not in temp_port_name:
                self._logger.error('Interface was not found')
                raise Exception('Interface {0} was not found'.format(port))
            port_name_splited = temp_port_name.split('/')[-1].split('-', 1)
            port_name = "{0}-{1}".format(port_name_splited[0], port_name_splited[1].replace('-', '/'))
            port_list.append(port_name)
        return port_list

    def remove_vlan(self, vlan_range, port_list, port_mode, additional_info):
        self._logger.info('Remove vlan invoked')
        self._logger.info(
            'Ports: ' + port_list+ ', Vlan_range: ' + vlan_range + ', Typa: ' + port_mode + ', Additional_info: ' + additional_info)
        if len(port_list) < 1:
            raise Exception('Port list is empty')
        if vlan_range == '':
            raise Exception('Vlan range is empty')
        vlan_map = {"vlan-" + name.strip(): name.strip() for name in vlan_range.split(',')}
        self._logger.info('Vlan map: ' + str(vlan_map))

        associated_port_list = self._get_ports_by_resources_path(port_list)

        for port in associated_port_list:
            self._remove_vlans_on_port(port, vlan_map.keys())
        self._delete_vlans(vlan_map.keys())
        self.commit()
        self._exit_configuration_mode()

        self._logger.info('Vlan {0} was removed on interfaces {1}'.format(vlan_range, port_list))
        return 'Vlan Configuration Completed'

    def add_vlan(self, vlan_range, port_list, port_mode, additional_info):
        self._logger.info('Vlan Configuration Started')
        self._logger.info(
            'Ports: ' + port_list+ ', Vlan_range: ' + vlan_range + ', Typa: ' + port_mode + ', Additional_info: ' + additional_info)
        if len(port_list) < 1:
            raise Exception('Port list is empty')
        if vlan_range == '':
            raise Exception('Vlan range is empty')
        vlan_map = {"vlan-" + name.strip(): name.strip() for name in vlan_range.split(',')}
        self._logger.info('Vlan map: ' + str(vlan_map))

        associated_port_list = self._get_ports_by_resources_path(port_list)

        for vlan_name in vlan_map:
            self._create_vlan(vlan_name, vlan_map[vlan_name], additional_info)
        for port in associated_port_list:
            self._clean_port(port)
            self._add_vlans_on_port(port, vlan_map.keys(), port_mode)

        self.commit()
        self._exit_configuration_mode()

        self._logger.info('Vlan {0} was assigned to the interfaces {1}'.format(vlan_range, port_list))
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
        result = generic_autoload.discover_snmp()
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

    def _getSessionHandler(self):
        return self._session

    def _getLogger(self):
        return self._logger

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

    def restore_configuration(self, source_file, clear_config='override'):
        pass

    def update_firmware(self, remote_host, file_path):
        pass

    def backup_configuration(self, destination_host, source_filename):
        pass

    def send_command(self, cmd, expected_str=None, timeout=30):
        pass
