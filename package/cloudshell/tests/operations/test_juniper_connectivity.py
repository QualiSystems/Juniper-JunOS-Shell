from unittest import TestCase

from mock import MagicMock as Mock
from cloudshell.networking.juniper.junos.handler.juniper_junos_connectivity_operations import \
    JuniperJunosConnectivityOperations
from cloudshell.networking.juniper.junos.junos_config import PORT_NAME_CHAR_REPLACEMENT


class TestJuniperConnectivity(TestCase):
    def setUp(self):
        self._cli_service = Mock()
        self._logger = Mock()
        self._context = Mock()
        self._api = Mock()
        self._context = Mock()
        self._config = Mock()
        self._connectivity_operations_instance = JuniperJunosConnectivityOperations(cli_service=self._cli_service,
                                                                                    logger=self._logger, api=self._api,
                                                                                    context=self._context,
                                                                                    config=self._config)

    # add_vlan
    def test_add_vlan_empty_port_list(self):
        vlan_range = '454'
        port_list = []
        port_mode = 'access'
        self.assertRaises(Exception, self._connectivity_operations_instance.add_vlan, vlan_range, port_list, port_mode)

    def test_add_vlan_empty_vlan_range(self):
        vlan_range = ''
        port_list = ['192.168.28.150/1/1/1/5']
        port_mode = 'access'
        self.assertRaises(Exception, self._connectivity_operations_instance.add_vlan, vlan_range, port_list, port_mode)

    def test_add_vlan_create_vlan_call(self):
        vlan_range = '345'
        port_list = '192.168.28.150/1/1/1/5'
        port_mode = 'access'
        ports = ['ge-0-0-1--32']
        vlan_name = 'vlan-' + vlan_range
        qnq = False
        self._connectivity_operations_instance._get_ports_by_resources_path = Mock()
        self._connectivity_operations_instance._get_ports_by_resources_path.return_value = ports
        self._connectivity_operations_instance._create_vlan = Mock()
        self._connectivity_operations_instance._clean_port = Mock()
        self._connectivity_operations_instance._add_vlans_on_port = Mock()
        self._connectivity_operations_instance.add_vlan(vlan_range, port_list, port_mode, qnq=qnq)
        self._connectivity_operations_instance._create_vlan.assert_called_once_with(vlan_name, vlan_range, qnq)

    def test_add_vlan_add_vlan_on_port_call(self):
        vlan_range = '345'
        port_list = '192.168.28.150/1/1/1/5'
        port_mode = 'access'
        port = 'ge-0-0-1--32'
        vlan_name = 'vlan-' + vlan_range
        qnq = False
        self._connectivity_operations_instance._get_ports_by_resources_path = Mock()
        self._connectivity_operations_instance._get_ports_by_resources_path.return_value = [port]
        self._connectivity_operations_instance._create_vlan = Mock()
        self._connectivity_operations_instance._clean_port = Mock()
        self._connectivity_operations_instance._add_vlans_on_port = Mock()
        self._connectivity_operations_instance.add_vlan(vlan_range, port_list, port_mode, qnq=qnq)
        self._connectivity_operations_instance._add_vlans_on_port.assert_called_once_with(port, [vlan_name], port_mode)

    # remove_vlan
    def test_remove_vlan_empty_port_list(self):
        vlan_range = '454'
        port_list = []
        port_mode = 'access'
        self.assertRaises(Exception, self._connectivity_operations_instance.remove_vlan, vlan_range, port_list,
                          port_mode)

    def test_remove_vlan_empty_vlan_range(self):
        vlan_range = ''
        port_list = ['192.168.28.150/1/1/1/5']
        port_mode = 'access'
        self.assertRaises(Exception, self._connectivity_operations_instance.remove_vlan, vlan_range, port_list,
                          port_mode)

    def test_remove_vlan_remove_vlans_on_port_call(self):
        vlan_range = '345'
        port_list = '192.168.28.150/1/1/1/5'
        port_mode = 'access'
        port = 'ge-0-0-1--32'
        vlan_name = 'vlan-' + vlan_range
        self._connectivity_operations_instance._get_ports_by_resources_path = Mock()
        self._connectivity_operations_instance._get_ports_by_resources_path.return_value = [port]
        self._connectivity_operations_instance._remove_vlans_on_port = Mock()
        self._connectivity_operations_instance._delete_vlans = Mock()
        self._connectivity_operations_instance.remove_vlan(vlan_range, port_list, port_mode)
        self._connectivity_operations_instance._remove_vlans_on_port.assert_called_once_with(port, [vlan_name])

    def test_remove_vlan_delete_vlans_call(self):
        vlan_range = '345'
        port_list = '192.168.28.150/1/1/1/5'
        port_mode = 'access'
        port = 'ge-0-0-1--32'
        vlan_name = 'vlan-' + vlan_range
        self._connectivity_operations_instance._get_ports_by_resources_path = Mock()
        self._connectivity_operations_instance._get_ports_by_resources_path.return_value = [port]
        self._connectivity_operations_instance._remove_vlans_on_port = Mock()
        self._connectivity_operations_instance._delete_vlans = Mock()
        self._connectivity_operations_instance.remove_vlan(vlan_range, port_list, port_mode)
        self._connectivity_operations_instance._delete_vlans.assert_called_once_with([vlan_name])

    def test_remove_vlan_commit_call(self):
        vlan_range = '345'
        port_list = '192.168.28.150/1/1/1/5'
        port_mode = 'access'
        port = 'ge-0-0-1--32'
        vlan_name = 'vlan-' + vlan_range
        self._connectivity_operations_instance._get_ports_by_resources_path = Mock()
        self._connectivity_operations_instance._get_ports_by_resources_path.return_value = [port]
        self._connectivity_operations_instance._remove_vlans_on_port = Mock()
        self._connectivity_operations_instance._delete_vlans = Mock()
        self._connectivity_operations_instance.remove_vlan(vlan_range, port_list, port_mode)
        self._cli_service.commit.assert_any_call()

    # convert port name
    def test_convert_port_name(self):
        port_descr = 'ge-0-0-1--32'
        self._connectivity_operations_instance._port_name_char_replacement = PORT_NAME_CHAR_REPLACEMENT
        converted_port = self._connectivity_operations_instance._convert_port_name(port_descr)
        self.assertTrue(converted_port == 'ge-0/0/1:32')

