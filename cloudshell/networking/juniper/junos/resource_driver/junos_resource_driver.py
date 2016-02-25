from cloudshell.shell.core.driver_builder_wrapper import DriverFunction
from cloudshell.networking.resource_driver.networking_generic_resource_dirver import networking_generic_resource_driver
import cloudshell.networking.juniper.junos

class junos_resource_driver(networking_generic_resource_driver):
    ATTRIBUTE_MATRIX = {"resource": ["ResourceAddress", "User", "Password", "Enable Password", "Console Server IP Address",
                                   "Console User", "Console Password", "Console Port", "CLI Connection Type",
                                   "SNMP Version", "SNMP Read Community", "SNMP V3 User", "SNMP V3 Password",
                                   "SNMP V3 Private Key"]}

    @DriverFunction(extraMatrixRows=networking_generic_resource_driver.REQUIRED_RESORCE_ATTRIBUTES)
    def Init(self, matrixJSON):
        self.handler_name = 'JUNOS'
        networking_generic_resource_driver.Init(self, matrixJSON)

    @DriverFunction(alias='Shutdown', extraMatrixRows=networking_generic_resource_driver.REQUIRED_RESORCE_ATTRIBUTES)
    def Shutdown(self, matrixJSON):
        # self.__check_for_attributes_changes(matrixJSON)
        self._check_for_attributes_changes(matrixJSON)
        return self._resource_handler.shutdown()

    @DriverFunction(alias='Send Config Command', extraMatrixRows=networking_generic_resource_driver.REQUIRED_RESORCE_ATTRIBUTES)
    def SendCustomConfigCommand(self, matrixJSON, command):
        self._check_for_attributes_changes(matrixJSON)
        result_str = self._resource_handler.send_config_command(cmd=command)
        return self._resource_handler.normalize_output(result_str)



