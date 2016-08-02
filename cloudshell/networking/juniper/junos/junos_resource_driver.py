from cloudshell.networking.juniper.autoload.juniper_snmp_autoload import JuniperSnmpAutoload
from cloudshell.networking.juniper.junos.handler.juniper_junos_operations import JuniperJunosOperations
from cloudshell.networking.juniper.junos.junos_driver_bootstrap import JunosDriverBootstrap
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.networking.networking_resource_driver_interface import NetworkingResourceDriverInterface
from cloudshell.networking.juniper.junos.handler.juniper_junos_connectivity_operations import \
    JuniperJunosConnectivityOperations
from cloudshell.shell.core.context_utils import ContextFromArgsMeta
import cloudshell.networking.juniper.junos.junos_config as driver_config


class JunosResourceDriver(ResourceDriverInterface, NetworkingResourceDriverInterface):
    __metaclass__ = ContextFromArgsMeta

    def __init__(self, config=None):
        bootstrap = JunosDriverBootstrap()
        bootstrap.add_config(driver_config)
        if config:
            bootstrap.add_config(config)
        bootstrap.initialize()

    @property
    def connectivity_operations(self):
        return JuniperJunosConnectivityOperations()

    @property
    def operations(self):
        return JuniperJunosOperations()

    @property
    def autoload(self):
        return JuniperSnmpAutoload()

    def initialize(self, context):
        pass

    def cleanup(self):
        pass

    def ApplyConnectivityChanges(self, context, request):
        return self.connectivity_operations.apply_connectivity_changes(request)

    def shutdown(self, context):
        self.operations.shutdown()

    def get_inventory(self, context):
        return self.autoload.discover()

    def save(self, context, folder_path, configuration_type):
        self.operations.save_configuration(folder_path, configuration_type)

    def send_custom_config_command(self, context, command):
        return self.operations.send_config_command(command)

    def send_custom_command(self, context, command):
        return self.operations.send_command(command)

    def update_firmware(self, context, remote_host, file_path):
        return self.operations.update_firmware(remote_host, file_path)

    def restore(self, context, path, config_type, restore_method):
        return self.operations.restore_configuration(path, config_type, restore_method)
