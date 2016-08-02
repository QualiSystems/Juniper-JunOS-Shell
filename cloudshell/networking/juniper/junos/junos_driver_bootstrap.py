from cloudshell.configuration.cloudshell_snmp_binding_keys import SNMP_HANDLER
from cloudshell.shell.core.driver_bootstrap import DriverBootstrap
import inject


class JunosDriverBootstrap(DriverBootstrap):
    def bindings(self, binder):
        try:
            binder.bind_to_provider(SNMP_HANDLER, self._config.SNMP_HANDLER_FACTORY)
        except inject.InjectorException:
            pass