#!/usr/local/bin/python
"""
    testing power script
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-argument
# pylint: disable=too-many-arguments

import unittest
from unittest import mock
import sys
import os
from pathlib import Path
from pyVmomi import vim  # pylint: disable=no-name-in-module
from scripts.power import *  # pylint: disable=unused-wildcard-import


class PowerScriptTestCase(unittest.TestCase):
    """
        unittest module to test the various parts of the power scripts.
    """
    def test_specified_get_args(self):
        """
            Test that with a specified arg string, things get set properly.
        """
        test_args = ["prog", "-s", "vc1", "-u", "testuser", "-o", "4050",
                     "-p", "password", "-q", "-f", "test.ini", "--dc",
                     "mdc1", "on", "testvm", "testvm2"]
        with mock.patch.object(sys, 'argv', test_args):
            result = get_args()
            self.assertEqual(result.configfile, 'test.ini',
                             "Config file not set correctly")
            self.assertEqual(result.dc, 'mdc1', "DC not set correctly")
            self.assertEqual(result.operation, 'on',
                             "Operation not set correctly")
            self.assertEqual(result.vmname, ['testvm', 'testvm2'],
                             "VMNames not set correctly")
            self.assertEqual(result.password, 'password',
                             "Password not set correctly")
            self.assertEqual(result.port, 4050, "Port not set correctly")
            self.assertEqual(result.user, 'testuser',
                             "Username not set correctly")
            self.assertEqual(result.vc, 'vc1', "Target VC not set correctly")
            self.assertEqual(result.verbose, False,
                             "Verbosity not set correctly")

    def test_default_get_args(self):
        """
            Test that default options get set properly.
        """
        test_args = ["prog", "query", "vmname"]
        with mock.patch.object(sys, 'argv', test_args):
            result = get_args()
            self.assertEqual(result.configfile, str(Path.home()) +
                             os.path.sep + 'vsphere-tools.ini',
                             "Default Config file not set correctly")
            self.assertEqual(result.dc, 'NONE', "Default DC not None")
            self.assertEqual(result.operation, 'query',
                             "Required operation not set correctly")
            self.assertEqual(result.password, None,
                             "Default password not set correctly")
            self.assertEqual(result.port, 443,
                             "Default port not set correctly")
            self.assertEqual(result.user, None,
                             "Default user not set correctly")
            self.assertEqual(result.vc, "NONE", "Default VC not None")
            self.assertEqual(result.verbose, True,
                             "Default verbosity not True")
            self.assertEqual(result.vmname, ["vmname"],
                             "Required vmname list not set correctly")

    @mock.patch.object(vim, 'ServiceInstance')
    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('scripts.power.vsphere_tools.vm_poweron')
    @mock.patch('scripts.power.vsphere_tools.vm_poweroff')
    @mock.patch('scripts.power.vsphere_tools.vm_reboot')
    @mock.patch('scripts.power.vsphere_tools.get_obj')
    def test_main_gentle(self, mock_go, mock_reboot,
                         mock_poweroff, mock_poweron, mock_vm, mock_si):
        """
            Testing on/off/reboot with forced option not set
        """
        testvm = vim.VirtualMachine()
        testvm.name = 'ThisIsATest'
        testvm.runtime.powerState.return_value = True
        mock_go.return_value = testvm
        test_args = ["prog", "-s", "vc1", "-p", "password",
                     "-u", "username", "-q", "on", "vmname"]
        with mock.patch.object(sys, 'argv', test_args):
            main()
            mock_poweron.assert_called_once()
        test_args = ["prog", "-s", "vc1", "-p", "password",
                     "-u", "username", "-q", "off", "vmname"]
        with mock.patch.object(sys, 'argv', test_args):
            main()
            mock_poweroff.assert_called_once()
            self.assertNotEqual(repr(mock_poweroff.call_args_list).find(
                "False, False"), -1,
                                "Poweroff not called with graceful options")
        test_args = ["prog", "-s", "vc1", "-p", "password",
                     "-u", "username", "-q", "reboot", "vmname"]
        with mock.patch.object(sys, 'argv', test_args):
            main()
            mock_reboot.assert_called_once()
            self.assertNotEqual(repr(mock_reboot.call_args_list).find(
                "False, False"), -1,
                                "Reboot not called with graceful options")

    @mock.patch.object(vim, 'ServiceInstance')
    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('scripts.power.vsphere_tools.vm_poweron')
    @mock.patch('scripts.power.vsphere_tools.vm_poweroff')
    @mock.patch('scripts.power.vsphere_tools.vm_reboot')
    @mock.patch('scripts.power.vsphere_tools.get_obj')
    def test_main_force(self, mock_go, mock_reboot, mock_poweroff,
                        mock_poweron, mock_vm, mock_si):
        """
            Testing on/off/reboot with forced option set
        """
        testvm = vim.VirtualMachine()
        testvm.name = 'ThisIsATest'
        testvm.runtime.powerState.return_value = True
        mock_go.return_value = testvm
        test_args = ["prog", "-s", "vc1", "-p", "password",
                     "-u", "username", "-q", "off", "vmname", "--force"]
        with mock.patch.object(sys, 'argv', test_args):
            main()
            mock_poweroff.assert_called_once()
            self.assertNotEqual(repr(mock_poweroff.call_args_list).find(
                "True, False"), -1,
                                "Poweroff not called with forceful options")
        test_args = ["prog", "-s", "vc1", "-p", "password",
                     "-u", "username", "-q", "reboot", "vmname", "--force"]
        with mock.patch.object(sys, 'argv', test_args):
            main()
            mock_reboot.assert_called_once()
            self.assertNotEqual(repr(mock_reboot.call_args_list).find(
                "True, False"), -1,
                                "Reboot not called with forceful options")
