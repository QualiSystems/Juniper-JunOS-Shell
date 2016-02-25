import time
import collections
import socket

import re
from cloudshell.cli import expected_actions

from cloudshell.networking.juniper.junos.command_templates.add_remove_vlan import ADD_REMOVE_VLAN_TEMPLATES
from cloudshell.networking.juniper.junos.command_templates.save_restore import SAVE_RESTORE
from cloudshell.networking.networking_handler_interface import NetworkingHandlerInterface
from cloudshell.networking.juniper.handler.juniper_base_handler import JuniperBaseHandler

class JuniperJunosHandler(JuniperBaseHandler, NetworkingHandlerInterface):
    EXPECTED_MAP = collections.OrderedDict([('Username: *$|Login: *$', expected_actions.send_username),
                                            ('closed by remote host', expected_actions.do_reconnect),
                                            ('continue connecting', expected_actions.send_yes),
                                            ('Got termination signal', expected_actions.wait_prompt_or_reconnect),
                                            ('Broken pipe', expected_actions.send_command),
                                            ('[Yy]es', expected_actions.send_yes),
                                            ('More', expected_actions.send_empty_string),
                                            ('[Pp]assword: *$', expected_actions.send_password)
                                            ])

    ERROR_LIST = []

    def __init__(self, connection_manager, logger=None):
        JuniperBaseHandler.__init__(self, connection_manager, logger)
        self._prompt = '.*[>%#] *$'
        self._expected_map = JuniperJunosHandler.EXPECTED_MAP
        self.add_command_templates(ADD_REMOVE_VLAN_TEMPLATES)
        self.add_command_templates(SAVE_RESTORE)
        self.add_error_list(JuniperJunosHandler.ERROR_LIST)

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
            'Ports: ' + port_list + ', Vlan_range: ' + vlan_range + ', Typa: ' + port_mode + ', Additional_info: ' + additional_info)
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
            'Ports: ' + port_list + ', Vlan_range: ' + vlan_range + ', Typa: ' + port_mode + ', Additional_info: ' + additional_info)
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
            self.execute_command_map(self._create_qnq_vlan_flow(vlan_name, vlan_range))
        else:
            if re.match(r'\d+-\d+', vlan_range):
                self.execute_command_map(self._create_vlan_range_flow(vlan_name, vlan_range))
            else:
                self.execute_command_map(self._create_vlan_flow(vlan_name, vlan_range))

    def _delete_vlan(self, vlan_name):
        for port in self._get_ports_for_vlan(vlan_name):
            self._remove_vlans_on_port(port, [vlan_name])
        self.execute_command_map(self._delete_vlan_flow(vlan_name))

    def _delete_vlans(self, vlan_list):
        for vlan_name in vlan_list:
            self._delete_vlan(vlan_name)

    def _add_vlans_on_port(self, port, vlan_list, type):
        for vlan_name in vlan_list:
            self.execute_command_map(self._set_vlan_to_interface_flow(port, type, vlan_name))
            self._logger.info('Vlan {0} will be assigned on interface {1}'.format(vlan_name, port))

    def _remove_vlans_on_port(self, port, vlan_list):
        for vlan_name in vlan_list:
            self.execute_command_map(self._delete_vlan_on_interface_flow(port, vlan_name))
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
        self.execute_command_map(self._delete_port_mode_on_interface_flow(port))
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

    def restore_configuration(self, source_file, clear_config='override'):
        if not source_file or source_file is '':
            raise Exception('JuniperJunosHandler', 'Config source cannot be empty')
        self.execute_command_map({'restore': source_file})
        return "Config file {0} has been restored".format(source_file)

    def update_firmware(self, remote_host, file_path):
        pass

    def backup_configuration(self, destination_host, source_filename):
        file_name = "config-{0}".format(time.strftime("%d%m%y-%H%M%S", time.localtime()))
        if not destination_host or destination_host is '':
            full_path = file_name
        else:
            full_path = "{0}/{1}".format(destination_host, file_name)
        self.execute_command_map({'save': full_path})
        return "Config file {0} has been saved".format(full_path)

    def send_command(self, cmd, expected_str=None, timeout=30):
        self._exit_configuration_mode()
        return self._send_command(cmd, expected_str=expected_str, timeout=timeout, is_need_default_prompt=False)


