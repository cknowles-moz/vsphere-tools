#!/usr/local/bin/python
"""
    Unit tests for the canary test script
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-argument
# pylint: disable=too-many-arguments

import sys
import unittest
import os
from pathlib import Path
from unittest import mock
from pyVmomi import vim  # pylint: disable=no-name-in-module
from scripts import canarytest
from scripts.canarytest import *  # pylint: disable=unused-wildcard-import


class CanaryTestCase(unittest.TestCase):
    """
    unittest class for testing canarytest
    """
    def test_specified_get_args(self):
        """
            With a set arg string, verify settings get set properly.
        """
        test_args = ["prog", "-s", "vc1", "-u", "testuser", "-o", "4050",
                     "-p", "password", "-v", "vmname", "-q", "-w", "-f",
                     "test.ini", "--dc", "mdc1", "host1", "host2"]
        with mock.patch.object(sys, 'argv', test_args):
            result = get_args()
            self.assertEqual(result.configfile, 'test.ini',
                             "Config file not set correctly")
            self.assertEqual(result.dc, 'mdc1', "DC not set correctly")
            self.assertEqual(result.hosts, ['host1', 'host2'],
                             "Host list not set correctly")
            self.assertEqual(result.password, 'password',
                             "Password not set correctly")
            self.assertEqual(result.port, 4050, "Port not set correctly")
            self.assertEqual(result.user, 'testuser',
                             "Username not set correctly")
            self.assertEqual(result.vc, 'vc1', "VC not set correctly")
            self.assertEqual(result.verbose, False,
                             "Verbosity not set correctly")
            self.assertEqual(result.vmname, 'vmname',
                             "Canary VM not set correctly")
            self.assertEqual(result.waitbetween, True,
                             "Wait Between not set correctly")

    def test_default_get_args(self):
        """
            With a minimum required arg string,
            verify that intended defaults happen
        """
        test_args = ["prog", "host1"]
        with mock.patch.object(sys, 'argv', test_args):
            result = get_args()
            self.assertEqual(result.configfile, str(Path.home()) +
                             os.path.sep + 'vsphere-tools.ini',
                             "Default config file not set correctly")
            self.assertEqual(result.dc, 'NONE', "Default DC not set correctly")
            self.assertEqual(result.hosts, ['host1'],
                             "Required host list not set correctly")
            self.assertIsNone(result.password,
                              "Default password not set correctly")
            self.assertEqual(result.port, 443,
                             "Default port not set correctly")
            self.assertIsNone(result.user, "Default user not set correctly")
            self.assertIsNone(result.vc, "Default VC not set correctly")
            self.assertTrue(result.verbose,
                            "Default verbosity not set correctly")
            self.assertIsNone(result.vmname,
                              "Default canary is not set correctly")
            self.assertFalse(result.waitbetween,
                             "Default wait between not set correctly")

    @mock.patch.object(vim, 'HostSystem')
    @mock.patch.object(vim, 'ServiceInstance')
    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('scripts.canarytest.vsphere_tools.get_obj')
    @mock.patch('scripts.canarytest.vsphere_tools.find_host')
    @mock.patch('scripts.canarytest.vsphere_tools.do_a_vmotion')
    @mock.patch('scripts.canarytest.time.sleep')
    def test_canary_test(self, mock_sleep, mock_vmotion,
                         mock_fh, mock_go, mock_vm, mock_si, mock_hs):
        """
            Verify that canary calls cause vmotions to be called for
        """
        test_si = vim.ServiceInstance()
        test_vm = vim.VirtualMachine()
        mock_go.return_value = test_vm
        host = vim.HostSystem()
        host.name = 'Foo'
        mock_fh.return_value = host
        canary_test(test_si, ['host1', 'host2'], 'vmname', False)
        test_si.RetrieveContent.assert_called_once()
        self.assertEqual(mock_vmotion.call_count, 2,
                         "Two vmotions should occur")

    @mock.patch.object(vim, 'HostSystem')
    @mock.patch.object(vim, 'ServiceInstance')
    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('scripts.canarytest.vsphere_tools.get_obj')
    @mock.patch('scripts.canarytest.vsphere_tools.find_host')
    @mock.patch('scripts.canarytest.vsphere_tools.do_a_vmotion')
    @mock.patch('scripts.canarytest.time.sleep')
    def test_canary_test_failure(self, mock_sleep, mock_vmotion, mock_fh,
                                 mock_go, mock_vm, mock_si, mock_hs):
        """
            Verify that if an exception occurs, that
            a) the vmotion was asked for, and
            b) an exception happens
        """
        test_si = vim.ServiceInstance()
        test_vm = vim.VirtualMachine()
        mock_go.return_value = test_vm
        host = vim.HostSystem()
        host.name = 'Foo'
        mock_fh.return_value = host
        canarytest.vsphere_tools.do_a_vmotion.side_effect = Exception(
            'vmotion raised an exception Failed')
        with self.assertRaises(Exception):
            canary_test(test_si, ['host1', 'host2'], 'vmname', False)
        test_si.RetrieveContent.assert_called_once()
        self.assertEqual(mock_vmotion.call_count, 1,
                         "One vmotions should occur, raising the exception")

    @mock.patch.object(vim, 'HostSystem')
    @mock.patch.object(vim, 'ServiceInstance')
    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('scripts.canarytest.vsphere_tools.get_obj')
    @mock.patch('scripts.canarytest.vsphere_tools.find_host')
    @mock.patch('scripts.canarytest.vsphere_tools.do_a_vmotion')
    @mock.patch('scripts.canarytest.time.sleep')
    def test_canary_test_ip(self, mock_sleep, mock_vmotion, mock_fh,
                            mock_go, mock_vm, mock_si, mock_hs):
        """
            Given a canary's IP, verify that vmotions get called for
        """
        test_si = vim.ServiceInstance()
        test_vm = vim.VirtualMachine()
        test_vm.guest.ipAddress = '192.168.0.1'
        test_vm.name = "Bob"
        mock_go.return_value = test_vm
        host = vim.HostSystem()
        host.name = 'Foo'
        mock_fh.return_value = host
        canary_test(test_si, ['host1', 'host2'], 'vmname', False)
        test_si.RetrieveContent.assert_called_once()
        self.assertEqual(mock_vmotion.call_count, 2,
                         "Two vmotions should occur")
        mock_vmotion.assert_called_with(test_vm, host, '192.168.0.1', False)

    @mock.patch.object(vim, 'HostSystem')
    @mock.patch.object(vim, 'ServiceInstance')
    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('scripts.canarytest.vsphere_tools.get_obj')
    @mock.patch('scripts.canarytest.vsphere_tools.find_host')
    @mock.patch('scripts.canarytest.vsphere_tools.do_a_vmotion')
    @mock.patch('scripts.canarytest.time.sleep')
    def test_canary_test_vmname(self, mock_sleep, mock_vmotion, mock_fh,
                                mock_go, mock_vm, mock_si, mock_hs):
        """
            Given a canary VM name, vmotions get called for.
        """
        test_si = vim.ServiceInstance()
        test_vm = vim.VirtualMachine()
        test_vm.guest.ipAddress = None
        test_vm.name = "Bob"
        mock_go.return_value = test_vm
        host = vim.HostSystem()
        host.name = 'Foo'
        mock_fh.return_value = host
        canary_test(test_si, ['host1', 'host2'], test_vm.name, False)
        test_si.RetrieveContent.assert_called_once()
        self.assertEqual(mock_vmotion.call_count, 2,
                         "Two vmotions should occur")
        mock_vmotion.assert_called_with(test_vm, host, test_vm.name, False)

    @mock.patch('scripts.canarytest.getpass.getpass')
    @mock.patch.object(connect, "Connect")
    @mock.patch.object(canarytest, 'canary_test')
    @mock.patch.object(configparser, 'ConfigParser')
    def test_canary_no_conf_main(self, mock_parse, mock_canary,
                                 mock_connect, mock_getpass):
        """
            Verify that the main calls the right function with the
            right parameters
        """
        test_args = ["prog", "-s", "vc1", "-u", "testuser", "-o", "4050",
                     "-p", "password", "-v", "vmname", "-q", "-w", "-f",
                     "test.ini", "--dc", "mdc1", "host1", "host2"]
        mock_getpass.return_value = "notapassword"
        mock_parse.read.return_value = []

        with mock.patch.object(sys, 'argv', test_args):
            canarytest.main()
        mock_canary.assert_called_once()
        conn_args = repr(mock_connect.call_args)
        self.assertNotEqual(conn_args.find("user='testuser'"), -1,
                            "Testuser isn't in the config parameters")
        self.assertNotEqual(conn_args.find("host='vc1'"), -1,
                            "vc1 isn't in the config parameters")
        self.assertNotEqual(conn_args.find("pwd='password'"), -1,
                            "password isn't in the config parameters")
