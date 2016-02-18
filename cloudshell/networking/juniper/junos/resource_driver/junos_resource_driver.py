from cloudshell.shell.core.driver_builder_wrapper import DriverFunction
from cloudshell.networking.juniper.resource_driver.juniper_generic_resource_dirver import juniper_generic_resource_driver
from cloudshell.networking.resource_driver.networking_generic_resource_dirver import networking_generic_resource_driver
import cloudshell.networking.juniper.junos

class junos_resource_driver(networking_generic_resource_driver):
    ATTRIBUTE_MATRIX = {"resource": ["ResourceAddress", "User", "Password", "Enable Password", "Console Server IP Address",
                                   "Console User", "Console Password", "Console Port", "CLI Connection Type",
                                   "SNMP Version", "SNMP Read Community", "SNMP V3 User", "SNMP V3 Password",
                                   "SNMP V3 Private Key"]}

    @DriverFunction(extraMatrixRows=ATTRIBUTE_MATRIX)
    def Init(self, matrixJSON):
        self.handler_name = 'JUNOS'
        networking_generic_resource_driver.Init(self, matrixJSON)

if __name__ == '__main__':

    data_json = str("""{
            "resource" : {
                    "ResourceAddress": "192.168.28.150",
                    "User": "root",
                    "Password": "Juniper",
                    "CLI Connection Type": "ssh",
                    "Console User": "",
                    "Console Password": "",
                    "Console Server IP Address": "",
                    "ResourceName" : "junos_us",
                    "ResourceFullName" : "Juniper",
                    "Enable Password": "",
                    "Console Port": "",
                    "SNMP Read Community": "public",
                    "SNMP Version": "2",
                    "SNMP V3 Password": "",
                    "SNMP V3 User": "",
                    "SNMP V3 Private Key": "",
                    "Filename": "/tmp/qsoutput.log",
                    "HandlerName": "JUNOS"
                },
            "reservation" : {
                    "Username" : "admin",
                    "Password" : "admin",
                    "Domain" : "Global",
                    "AdminUsername" : "admin",
                    "AdminPassword" : "admin"}
            }""")


    # data_json = str("""{
    #         "resource" : {
    #                 "ResourceAddress": "192.168.28.150",
    #                 "User": "root",
    #                 "Password": "Juniper",
    #                 "CLI Connection Type": "ssh",
    #                 "Console User": "",
    #                 "Console Password": "",
    #                 "Console Server IP Address": "",
    #                 "ResourceName" : "junos_us",
    #                 "ResourceFullName" : "Juniper",
    #                 "Enable Password": "",
    #                 "Console Port": "",
    #                 "SNMP Read Community": "public",
    #                 "SNMP Version": "2",
    #                 "SNMP V3 Password": "",
    #                 "SNMP V3 User": "",
    #                 "SNMP V3 Private Key": ""
    #             },
    #         "reservation" : {
    #                 "Username" : "admin",
    #                 "Password" : "admin",
    #                 "Domain" : "Global",
    #                 "AdminUsername" : "admin",
    #                 "AdminPassword" : "admin"}
    #         }""")
    # import os
    # os.environ['QS_CONFIG'] = "/home/yar/QualiSystems/Git/TFS/Packages/qualipy/qs_config.ini"
    resource_driver = junos_resource_driver('77', data_json)
    print(resource_driver._resource_handler._delete_vlans(["vlan-247"]))
    print(resource_driver._resource_handler._add_vlans_on_port('ge-0/0/2', ['vlan-247'], 'trunk'))
    print(resource_driver._resource_handler._get_ports_for_vlan("vlan-238"))
    # resource_driver.Add_VLAN(data_json, '192.168.28.150/0/1/0/7|192.168.28.150/0/1/0/2', '1022, 1023-1028', "trunk", "")
    # resource_driver.Remove_VLAN(data_json, '192.168.28.150/0/1/0/7|192.168.28.150/0/1/0/2', '1022, 1023-1028', "trunk", "")
    # resource_driver.Remove_VLAN(data_json, '192.168.28.150/0/1/0/7', '234', 'access', 'qnq')
    # print(resource_driver.GetInventory(data_json))
