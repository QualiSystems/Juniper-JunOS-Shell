import collections

import cloudshell.networking.juniper.junos.command_templates.add_remove_vlan as add_remove_vlan
from cloudshell.networking.operations.connectivity_operations import ConnectivityOperations
from cloudshell.shell.core.config_utils import override_attributes_from_config
from cloudshell.shell.core.context_utils import get_resource_context_attribute
import inject
from cloudshell.configuration.cloudshell_cli_binding_keys import CLI_SERVICE
from cloudshell.configuration.cloudshell_shell_core_binding_keys import LOGGER, API, CONTEXT, CONFIG
import re
import cloudshell.cli.command_template.command_template_service as command_template_service


class JuniperJunosConnectivityOperations(ConnectivityOperations):
    PORT_NAME_CHAR_REPLACEMENT = {'/': '-'}

    def __init__(self, cli_service=None, logger=None, api=None, context=None, config=None):
        self._cli_service = cli_service
        self._logger = logger
        self._api = api
        self._context = context
        self._config = config

        overridden_config = override_attributes_from_config(JuniperJunosConnectivityOperations, config=self.config)
        self._port_name_char_replacement = overridden_config.PORT_NAME_CHAR_REPLACEMENT

    @property
    def logger(self):
        return self._logger or inject.instance(LOGGER)

    @property
    def cli_service(self):
        return self._cli_service or inject.instance(CLI_SERVICE)

    @property
    def api(self):
        return self._api or inject.instance(API)

    @property
    def context(self):
        return self._context or inject.instance(CONTEXT)

    @property
    def config(self):
        return self._config or inject.instance(CONFIG)

    def execute_command_map(self, command_map):
        command_template_service.execute_command_map(command_map, self.cli_service.send_config_command)

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
            port_resource_map = self.api.GetResourceDetails(get_resource_context_attribute('name', self.context))
            temp_port_name = self._get_resource_full_name(port, port_resource_map)
            if not temp_port_name:
                self.logger.error('Interface was not found')
                raise Exception('Interface {0} was not found'.format(port))
            port_list.append(self._convert_port_name(temp_port_name))
        return port_list

    def _convert_port_name(self, port_description):
        port_name_splitted = port_description.split('/')[-1].split('-', 1)
        if len(port_name_splitted) == 2:
            port_suffix, port_location = port_name_splitted
            for replacement, value in self._port_name_char_replacement.iteritems():
                port_location = port_location.replace(value, replacement)
            port_name = "{0}-{1}".format(port_suffix, port_location)
        elif len(port_name_splitted) == 1:
            port_name = port_name_splitted[0]
        else:
            raise Exception(self.__class__.__name__, 'Incorrect port description format')
        return port_name

    def remove_vlan(self, vlan_range, port_list, port_mode):
        self.logger.info('Remove vlan invoked')
        self.logger.info('Ports: {0}, Vlan_range: {1}, Type: {2}'.format(port_list, vlan_range, port_mode))
        if len(port_list) < 1:
            raise Exception('Port list is empty')
        if not vlan_range:
            raise Exception('Vlan range is empty')
        vlan_map = {"vlan-" + name.strip(): name.strip() for name in vlan_range.split(',')}
        self.logger.info('Vlan map: ' + str(vlan_map))

        associated_port_list = self._get_ports_by_resources_path(port_list)

        for port in associated_port_list:
            self._remove_vlans_on_port(port, vlan_map.keys())
        self.cli_service.commit()
        self._delete_vlans(vlan_map.keys())
        self.cli_service.commit()

        self.logger.info('Vlan {0} was removed on interfaces {1}'.format(vlan_range, port_list))
        return 'Vlan Configuration Completed'

    def add_vlan(self, vlan_range, port_list, port_mode, qnq=False, ctag=''):
        self.logger.info('Vlan Configuration Started')
        self.logger.info(
            'Ports: ' + str(port_list) + ', Vlan_range: ' + vlan_range + ', Typa: ' + port_mode)
        if len(port_list) < 1:
            raise Exception('Port list is empty')
        if not vlan_range:
            raise Exception('Vlan range is empty')
        vlan_map = {"vlan-" + name.strip(): name.strip() for name in vlan_range.split(',')}
        self.logger.info('Vlan map: ' + str(vlan_map))

        associated_port_list = self._get_ports_by_resources_path(port_list)

        for vlan_name in vlan_map:
            self._create_vlan(vlan_name, vlan_map[vlan_name], qnq)
        for port in associated_port_list:
            self._clean_port(port)
            self._add_vlans_on_port(port, vlan_map.keys(), port_mode)

        self.cli_service.commit()
        # self.cli_service.exit_configuration_mode()

        self.logger.info('Vlan {0} was assigned to the interfaces {1}'.format(vlan_range, port_list))
        return 'Vlan Configuration Completed'

    def _get_ports_for_vlan(self, vlan_name):
        output = self.cli_service.send_config_command("run show vlans {0}".format(vlan_name))
        ports = re.findall(r'\w+-(?:\d+/)+\d+|ae\d+', re.sub(r'\n|\r', '', output))
        if ports:
            return [port.strip() for port in ports]
        return []

    def _create_vlan(self, vlan_name, vlan_range, qnq):
        if qnq:
            self.execute_command_map(self._create_qnq_vlan_flow(vlan_name, vlan_range))
        else:
            if re.match(r'\d+-\d+', vlan_range):
                self.execute_command_map(self._create_vlan_range_flow(vlan_name, vlan_range))
            else:
                self.execute_command_map(self._create_vlan_flow(vlan_name, vlan_range))

    def _delete_vlan(self, vlan_name):
        # for port in self._get_ports_for_vlan(vlan_name):
        #     self._remove_vlans_on_port(port, [vlan_name])
        # self.execute_command_map(self._delete_vlan_flow(vlan_name))
        if len(self._get_ports_for_vlan(vlan_name)) == 0:
            self.execute_command_map(self._delete_vlan_flow(vlan_name))

    def _delete_vlans(self, vlan_list):
        for vlan_name in vlan_list:
            self._delete_vlan(vlan_name)

    def _add_vlans_on_port(self, port, vlan_list, type):
        for vlan_name in vlan_list:
            self.execute_command_map(self._set_vlan_to_interface_flow(port, type, vlan_name))
            self.logger.info('Vlan {0} will be assigned on interface {1}'.format(vlan_name, port))

    def _remove_vlans_on_port(self, port, vlan_list):
        for vlan_name in vlan_list:
            self.execute_command_map(self._delete_vlan_on_interface_flow(port, vlan_name))
            self.logger.info('Vlan {0} removed from interface {1}'.format(vlan_name, port))

    def _get_vlans_for_port(self, port):
        output = self.cli_service.send_config_command('show interfaces {0}'.format(port))
        found_list = re.findall(r'vlan\s*\{\s*members\s*\[*\s*((?:[\w\d-]+\s*)+)\s*\]*\s*;\s*\}',
                                re.sub(r'\n|\r', '', output))
        if len(found_list) > 0:
            return [vlan.strip() for vlan in found_list[0].split()]
        return []

    def _clean_port(self, port):
        vlans = self._get_vlans_for_port(port)
        self._remove_vlans_on_port(port, vlans)
        self._remove_port_mode_on_interface(port)
        self.logger.info("Cleaning port {0}, vlans, {1}".format(port, ", ".join(vlans)))

    def _remove_port_mode_on_interface(self, port):
        self.execute_command_map(self._delete_port_mode_on_interface_flow(port))
        self.logger.info("Port mode removed for {0}".format(port))

    def _create_vlan_flow(self, vlan_name, vlan_id):
        cmd_map = collections.OrderedDict()
        cmd_map[add_remove_vlan.CREATE_VLAN] = [vlan_name, vlan_id]
        return cmd_map

    def _create_vlan_range_flow(self, vlan_range_name, vlan_range):
        cmd_map = collections.OrderedDict()
        cmd_map[add_remove_vlan.CREATE_VLAN_RANGE] = [vlan_range_name, vlan_range]
        return cmd_map

    def _create_qnq_vlan_flow(self, vlan_name, vlan_id):
        cmd_map = collections.OrderedDict()
        cmd_map[add_remove_vlan.CREATE_VLAN] = [vlan_name, vlan_id]
        cmd_map[add_remove_vlan.CREATE_VLAN_QNQ] = [vlan_name]
        return cmd_map

    def _set_vlan_to_interface_flow(self, port, type, vlan_name):
        cmd_map = collections.OrderedDict()
        cmd_map[add_remove_vlan.SET_VLAN_TO_INTERFACE] = [port, type.lower(), vlan_name]
        return cmd_map

    def _delete_vlan_on_interface_flow(self, port, vlan_name):
        cmd_map = collections.OrderedDict()
        cmd_map[add_remove_vlan.DELETE_VLAN_ON_INTERFACE] = [port, vlan_name]
        return cmd_map

    def _delete_port_mode_on_interface_flow(self, port):
        cmd_map = collections.OrderedDict()
        cmd_map[add_remove_vlan.DELETE_PORT_MODE_ON_INTERFACE] = [port]
        return cmd_map

    def _delete_vlan_flow(self, vlan_name):
        cmd_map = collections.OrderedDict()
        cmd_map[add_remove_vlan.DELETE_VLAN] = [vlan_name]
        return cmd_map
