from unittest import TestCase, main

import inject
from cloudshell.networking.juniper.junos.junos_resource_driver import JunosResourceDriver
from mock import MagicMock as Mock
from mock import NonCallableMagicMock


class TestJuniperDriver(TestCase):

    def setUp(self):
        inject.clear()
        self._operations = NonCallableMagicMock()
        self._connectivity_operations = NonCallableMagicMock()
        self._autoload = NonCallableMagicMock()
        self._driver_instance = JunosResourceDriver(operations=self._operations, autoload=self._autoload,
                                                    connectivity_operations=self._connectivity_operations)

    def test_initialization(self):
        self.assertTrue(inject.is_configured())

    def test_call_autoload(self):
        self._driver_instance.get_inventory(Mock())
        self.assertTrue(self._autoload.discover.called)

    def test_call_ApplyConnectivityChanges(self):
        self._driver_instance.ApplyConnectivityChanges(Mock(), Mock())
        self.assertTrue(self._connectivity_operations.apply_connectivity_changes.called)

    def test_call_shutdown(self):
        self._driver_instance.shutdown(Mock())
        self.assertTrue(self._operations.shutdown.called)

    def test_call_save(self):
        self._driver_instance.save(Mock(), 'test', 'test')
        self.assertTrue(self._operations.save.called)

    def test_call_restore(self):
        self._driver_instance.restore(Mock(), 'test', 'test', 'test')
        self.assertTrue(self._operations.restore.called)

    def test_call_orchestration_save(self):
        self._driver_instance.orchestration_save(Mock(), 'test', 'test')
        self.assertTrue(self._operations.orchestration_save.called)

    def test_call_orchestration_restore(self):
        self._driver_instance.orchestration_restore(Mock(), 'test', 'test')
        self.assertTrue(self._operations.orchestration_restore.called)

    def test_call_update_firmware(self):
        self._driver_instance.update_firmware(Mock(), 'test', 'test')
        self.assertTrue(self._operations.load_firmware.called)

    def test_call_load_firmware(self):
        self._driver_instance.update_firmware(Mock(), 'test', 'test')
        self.assertTrue(self._operations.load_firmware.called)

    def test_call_run_custom_command(self):
        self._driver_instance.run_custom_command(Mock(), 'test')
        self.assertTrue(self._operations.run_custom_command.called)

    def test_call_health_check(self):
        self._driver_instance.health_check(Mock())
        self.assertTrue(self._operations.health_check.called)

    def test_call_run_custom_config_command(self):
        self._driver_instance.run_custom_config_command(Mock(), 'test')
        self.assertTrue(self._operations.run_custom_config_command.called)

    def test_call_send_custom_command(self):
        self._driver_instance.send_custom_command(Mock(), 'test')
        self.assertTrue(self._operations.run_custom_command.called)

    def test_call_send_custom_config_command(self):
        self._driver_instance.send_custom_config_command(Mock(), 'test')
        self.assertTrue(self._operations.run_custom_config_command.called)
