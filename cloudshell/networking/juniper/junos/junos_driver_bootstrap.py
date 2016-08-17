from cloudshell.networking.juniper.cli.juniper_cli_service import JuniperCliService
from cloudshell.configuration.cloudshell_cli_binding_keys import CLI_SERVICE
from cloudshell.configuration.cloudshell_snmp_binding_keys import SNMP_HANDLER
from cloudshell.shell.core.driver_bootstrap import DriverBootstrap
import inject


class JunosDriverBootstrap(DriverBootstrap):
    def bindings(self, binder):
        """
        Bindings for junos driver
        :param binder:
        :return:
        """
        """Binding for SNMP service"""
        try:
            binder.bind_to_provider(SNMP_HANDLER, self._config.SNMP_HANDLER_FACTORY)
        except inject.InjectorException:
            pass

        """Binding for CLI service, use JuniperCliService"""
        try:
            binder.bind_to_constructor(CLI_SERVICE, JuniperCliService)
        except inject.InjectorException:
            pass
