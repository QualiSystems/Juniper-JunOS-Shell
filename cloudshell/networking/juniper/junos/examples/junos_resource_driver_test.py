from cloudshell.networking.juniper.junos.resource_driver.junos_resource_driver import \
    junos_resource_driver

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
#             "resource" : {
#                     "ResourceAddress": "192.168.28.150",
#                     "User": "root",
#                     "Password": "Juniper",
#                     "CLI Connection Type": "ssh",
#                     "Console User": "",
#                     "Console Password": "",
#                     "Console Server IP Address": "",
#                     "ResourceName" : "junos_us",
#                     "ResourceFullName" : "Juniper",
#                     "Enable Password": "",
#                     "Console Port": "",
#                     "SNMP Read Community": "public",
#                     "SNMP Version": "2",
#                     "SNMP V3 Password": "",
#                     "SNMP V3 User": "",
#                     "SNMP V3 Private Key": ""
#                 },
#             "reservation" : {
#                     "Username" : "admin",
#                     "Password" : "admin",
#                     "Domain" : "Global",
#                     "AdminUsername" : "admin",
#                     "AdminPassword" : "admin"}
#             }""")
# import os
# os.environ['QS_CONFIG'] = "/home/yar/QualiSystems/Git/TFS/Packages/qualipy/qs_config.ini"
resource_driver = junos_resource_driver('77', data_json)
# print(resource_driver._resource_handler._delete_vlans(["vlan-247"]))
# print(resource_driver._resource_handler._add_vlans_on_port('ge-0/0/2', ['vlan-247'], 'trunk'))
# print(resource_driver._resource_handler._get_ports_for_vlan("vlan-238"))
# resource_driver.Add_VLAN(data_json, '192.168.28.150/0/1/0/7|192.168.28.150/0/1/0/2', '1022, 1023-1028', "trunk", "")
# resource_driver.Remove_VLAN(data_json, '192.168.28.150/0/1/0/7|192.168.28.150/0/1/0/2', '1022, 1023-1028', "trunk", "")
# resource_driver.Remove_VLAN(data_json, '192.168.28.150/0/1/0/7', '234', 'access', 'qnq')
# print(resource_driver.GetInventory(data_json)
# print(resource_driver.Save(data_json, "/var/tmp", "test"))
print(resource_driver.Restore(data_json, "/var/tmp/dsds", "", "Override"))
# print(resource_driver.Shutdown(data_json))
# print(resource_driver.UpdateFirmware(data_json, 'ftp://192.168.23.45/', '/sdf/dsd'))
# print(resource_driver.SendCustomConfigCommand(data_json, 'dsdsdsd'))
# print(resource_driver.SendCustomCommand(data_json, 'dsdsdsd'))

