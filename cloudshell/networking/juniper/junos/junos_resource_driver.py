from cloudshell.networking.juniper.autoload.juniper_snmp_autoload import JuniperSnmpAutoload as Autoload
from cloudshell.networking.juniper.junos.handler.juniper_junos_operations import JuniperJunosOperations as Operations

from cloudshell.networking.juniper.junos.junos_driver_bootstrap import JunosDriverBootstrap as Bootstrap
from cloudshell.shell.core.driver_utils import GlobalLock

from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.networking.networking_resource_driver_interface import NetworkingResourceDriverInterface
from cloudshell.networking.juniper.junos.handler.juniper_junos_connectivity_operations import \
    JuniperJunosConnectivityOperations as ConnectivityOperations
from cloudshell.shell.core.context_utils import ContextFromArgsMeta
import cloudshell.networking.juniper.junos.junos_config as driver_config


class JunosResourceDriver(ResourceDriverInterface, NetworkingResourceDriverInterface, GlobalLock):
    """
    Resource driver
    """

    """Wrap commands with context_from_args, get context from method args and put it to context container"""
    __metaclass__ = ContextFromArgsMeta

    def __init__(self, config=None, connectivity_operations=None, operations=None, autoload=None):
        """
            Constructor

            :param config: use for test to override configuration attributes
            :param connectivity_operations: use for test to override connectivity_operations instance
            :param operations: use for test to override operations instance
            :param autoload: use for test to override autoload instance
            :return:
            """
        super(JunosResourceDriver, self).__init__()
        self._connectivity_operations = connectivity_operations
        self._operations = operations
        self._autoload = autoload
        bootstrap = Bootstrap()
        bootstrap.add_config(driver_config)
        if config:
            bootstrap.add_config(config)
        bootstrap.initialize()

    @property
    def connectivity_operations(self):
        return self._connectivity_operations or ConnectivityOperations()

    @property
    def operations(self):
        return self._operations or Operations()

    @property
    def autoload(self):
        return self._autoload or Autoload()

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

    def save(self, context, folder_path, configuration_type, vrf_management_name=None):
        self.operations.save(folder_path, configuration_type, vrf_management_name)

    def run_custom_config_command(self, context, custom_command):
        return self.operations.run_custom_config_command(custom_command)

    def run_custom_command(self, context, custom_command):
        return self.operations.run_custom_command(custom_command)

    def orchestration_save(self, context, mode, custom_params=None):
        if not mode:
            mode = 'shallow'

        return self.operations.orchestration_save(mode=mode, custom_params=custom_params)

    def orchestration_restore(self, context, saved_artifact_info, custom_params=None):
        return self.operations.orchestration_restore(saved_artifact_info=saved_artifact_info,
                                                     custom_params=custom_params)

    @GlobalLock.lock
    def update_firmware(self, context, remote_host, file_path):
        """Left for supporting old network standard < v4.0"""
        return self.operations.load_firmware(remote_host)

    @GlobalLock.lock
    def load_firmware(self, context, path, vrf_management_name=None):
        return self.operations.load_firmware(path)

    @GlobalLock.lock
    def restore(self, context, path, configuration_type='running', restore_method='override', vrf_management_name=None):
        return self.operations.restore(path=path,
                                       configuration_type=configuration_type,
                                       restore_method=restore_method,
                                       vrf_management_name=vrf_management_name)
