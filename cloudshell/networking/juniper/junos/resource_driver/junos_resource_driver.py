from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.networking.networking_resource_driver_interface import NetworkingResourceDriverInterface
from cloudshell.networking.juniper.junos.junos_bootstrap import JunosBootstrap
from cloudshell.networking.juniper.autoload.juniper_snmp_autoload_70 import JuniperSnmpAutoload70
from cloudshell.shell.core.context_utils import context_from_args
from cloudshell.networking.juniper.junos.handler.juniper_junos_connectivity_operations import \
    JuniperJunosConnectivityOperations

import cloudshell.networking.juniper.junos.junos_config as package_config


class JunosResourceDriver(ResourceDriverInterface, NetworkingResourceDriverInterface):
    def __init__(self):
        bootstrap = JunosBootstrap()
        bootstrap.add_config(package_config)
        bootstrap.initialize()

    def initialize(self, context):
        pass

    def cleanup(self):
        pass

    @context_from_args
    def ApplyConnectivityChanges(self, context, request):
        connectivity_handler = JuniperJunosConnectivityOperations()
        connectivity_handler.apply_connectivity_changes(request)

    def shutdown(self, context):
        pass

    @context_from_args
    def get_inventory(self, context):
        juniper_autoload = JuniperSnmpAutoload70()
        return juniper_autoload.discover_snmp()

    def save(self, context, folder_path, configuration_type):
        pass

    def send_custom_config_command(self, context, command):
        pass

    def send_custom_command(self, context, command):
        pass

    def update_firmware(self, context, remote_host, file_path):
        pass

    def restore(self, context, path, config_type, restore_method):
        pass
