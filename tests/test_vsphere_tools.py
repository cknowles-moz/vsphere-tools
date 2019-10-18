#!/usr/local/bin/python
"""
    testing vsphere-tools library
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-argument
# pylint: disable=too-many-arguments
# pylint: disable=no-self-use

import unittest
from unittest import mock
from pyVmomi import vim  # pylint: disable=no-name-in-module
from vsphere_tools import *  # pylint: disable=unused-wildcard-import


class PowerTestCase(unittest.TestCase):
    """
        Unittests for vsphere-tools power functions
    """

    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('vsphere_tools.wait_for_task')
    def test_poweroff_force(self, mock_wait, mock_vm):
        """
            Verify that proper mocked functions are called on forced poweroff
        """
        testvm = vim.VirtualMachine()
        testvm.name = 'foo'
        vm_poweroff(testvm, True)
        testvm.PowerOffVM_Task.assert_called_once()
        testvm.ShutdownGuest.assert_not_called()

    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('vsphere_tools.wait_for_task')
    def test_poweroff_graceful(self, mock_wait, mock_vm):
        """
            Verify that proper mocked functions are called on graceful poweroff
        """
        testvm = vim.VirtualMachine()
        testvm.name = 'foo'
        vm_poweroff(testvm, False)
        testvm.PowerOffVM_Task.assert_not_called()
        testvm.ShutdownGuest.assert_called_once()

    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('vsphere_tools.wait_for_task')
    def test_poweron(self, mock_wait, mock_vm):
        """
            Verify that proper mocked functions are called on poweron
        """
        testvm = vim.VirtualMachine()
        testvm.name = 'foo'
        vm_poweron(testvm)
        testvm.PowerOnVM_Task.assert_called_once()

    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('vsphere_tools.wait_for_task')
    def test_reboot_force(self, mock_wait, mock_vm):
        """
            Verify that proper mocked functions are called on forced reboot
        """
        testvm = vim.VirtualMachine()
        testvm.name = 'foo'
        vm_reboot(testvm, True)
        testvm.ResetVM_Task.assert_called_once()
        testvm.RebootGuest.assert_not_called()

    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('vsphere_tools.wait_for_task')
    def test_reboot_graceful(self, mock_wait, mock_vm):
        """
            Verify that proper mocked functions are called on graceful reboot
        """
        testvm = vim.VirtualMachine()
        testvm.name = 'foo'
        vm_reboot(testvm, False)
        testvm.ResetVM_Task.assert_not_called()
        testvm.RebootGuest.assert_called_once()


class SnapshotTestCase(unittest.TestCase):
    """
        unittest for vsphere-tools snapshot functions
    """

    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('vsphere_tools.wait_for_task')
    def test_create_snapshot(self, mock_wait, mock_vm):
        """
            Verify that proper mocked functions are called on snapshot create
        """
        testvm = vim.VirtualMachine()
        testvm.name = 'foo'
        create_snapshot(testvm, 'testsnap', 'testdesc')
        testvm.CreateSnapshot_Task.assert_called_with('testsnap', 'testdesc',
                                                      True, True)
        testvm.CreateSnapshot_Task.assert_called_once()

    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch.object(vim, 'VirtualMachineSnapshot')
    @mock.patch('vsphere_tools.wait_for_task')
    @mock.patch('vsphere_tools.get_snapshot')
    def test_delete_snapshot(self, mock_getsnap, mock_wait,
                             mock_snap, mock_vm):
        """
            Verify that proper mocked functions are called on snapshot delete
        """
        mysnap = vim.VirtualMachineSnapshot()
        mock_getsnap.return_value = [mysnap]
        testvm = vim.VirtualMachine()
        testvm.name = 'foo'
        delete_snapshot(testvm, 'testsnap')
        mysnap.snapshot.RemoveSnapshot_Task.assert_called_once()

    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch.object(vim, 'VirtualMachineSnapshot')
    @mock.patch('vsphere_tools.wait_for_task')
    @mock.patch('vsphere_tools.get_snapshot')
    def test_revert_snapshot(self, mock_getsnap, mock_wait,
                             mock_snap, mock_vm):
        """
            Verify that proper mocked functions are called on snapshot revert
        """
        mysnap = vim.VirtualMachineSnapshot()
        mock_getsnap.return_value = [mysnap]
        testvm = vim.VirtualMachine()
        testvm.name = 'foo'
        revert_snapshot(testvm, 'testsnap')
        mysnap.snapshot.RevertToSnapshot_Task.assert_called_once()


class OtherTestCase(unittest.TestCase):
    """
        unittest for vsphere-tools support functions
    """

    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch.object(vim, 'HostSystem')
    @mock.patch.object(vim, 'VirtualMachineRelocateSpec')
    @mock.patch('vsphere_tools.wait_for_task')
    @mock.patch('vsphere_tools.ping')
    @mock.patch('vsphere_tools.time.sleep')
    def test_do_a_vmotion(self, mock_sleep, mock_ping, mock_wait,
                          mock_spec, mock_host, mock_vm):
        """
            Verify that proper mocked functions are called on vmotion call
        """
        testvm = vim.VirtualMachine()
        testhost = vim.HostSystem()
        do_a_vmotion(testvm, testhost, '127.0.0.1')
        testvm.RelocateVM_Task.assert_called_once()

    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch.object(vim, 'HostSystem')
    @mock.patch.object(vim, 'VirtualMachineRelocateSpec')
    @mock.patch('vsphere_tools.wait_for_task')
    @mock.patch('vsphere_tools.ping')
    @mock.patch('vsphere_tools.time.sleep')
    def test_fail_a_prevmotion(self, mock_sleep, mock_ping, mock_wait,
                               mock_spec, mock_host, mock_vm):
        """
            Verify that proper mocked functions are called on
            pre-vmotion ping fail
        """
        testvm = vim.VirtualMachine()
        testhost = vim.HostSystem()
        mock_ping.return_value = False
        with self.assertRaises(Exception,
                               msg="Exception not raised when ping fails"):
            do_a_vmotion(testvm, testhost, '127.0.0.1')
        testvm.RelocateVM_Task.assert_not_called()

    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch.object(vim, 'HostSystem')
    @mock.patch.object(vim, 'VirtualMachineRelocateSpec')
    @mock.patch('vsphere_tools.wait_for_task')
    @mock.patch('vsphere_tools.ping')
    @mock.patch('vsphere_tools.time.sleep')
    def test_fail_a_postvmotion(self, mock_sleep, mock_ping, mock_wait,
                                mock_spec, mock_host, mock_vm):
        """
            Verify that proper mocked functions are called
            post-vmotion ping fail
        """
        testvm = vim.VirtualMachine()
        testhost = vim.HostSystem()
        mock_ping.side_effect = [True, False]
        with self.assertRaises(Exception,
                               msg="Exception not raised when ping fails"):
            do_a_vmotion(testvm, testhost, '127.0.0.1')
        testvm.RelocateVM_Task.assert_called_once()

    @mock.patch.object(vim, 'ServiceInstance')
    def test_find_a_host(self, mock_si):
        """
            Verify that find a host calls the right sub functions
        """
        test_si = vim.ServiceInstance()
        test_si.content.searchIndex.FindAllByDnsName.return_value = ['thehost']
        self.assertEqual(find_host(test_si, 'thehost'), 'thehost')
        test_si.content.searchIndex.FindAllByDnsName.assert_called_once()

    @mock.patch.object(vim, 'ServiceInstance')
    def test_fail_find_a_host(self, mock_si):
        """
            Verify that find a host calls the right sub functions,
            and fails with an exception
        """
        test_si = vim.ServiceInstance()
        test_si.content.searchIndex.FindAllByDnsName.return_value = []
        with self.assertRaises(Exception,
                               msg="Exception not raised \
                                   on failure to find host"):
            find_host(test_si, 'thehost')
        test_si.content.searchIndex.FindAllByDnsName.assert_called_once()

    # @unittest.skip("skipping to avoid 5s wait - enable before shipping out.")
    def test_ping_responding(self):
        """
            ping local host, and verify that works
        """
        self.assertTrue(ping('127.0.0.1'), msg="Can't ping localhost - failed")

    # @unittest.skip("skipping to avoid 5s wait - enable before shipping out.")
    def test_ping_failing(self):
        """
            ping invalid host, and verify that fails
        """
        self.assertFalse(ping('127.0.0.2'),
                         msg="Ping succeeded when it shouldn't")
