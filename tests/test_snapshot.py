#!/usr/local/bin/python

import snapshots
from snapshots import * # pylint: disable=unused-wildcard-import
from pyVmomi import vim # pylint: disable=no-name-in-module
import unittest
from unittest import mock 
import sys

class SnapshotScriptTestCase(unittest.TestCase):
    def test_specified_get_args(self):
        """
            Test that with a specified arg string, things get set properly.
        """
        test_args = ["prog", "-s", "vc1", "-u", "testuser", "-o", "4050", "-p", "password", "-q", "-f", "test.ini", "--dc", "mdc2", "--snapname", "testsnap", "create", "testvm1"]
        with mock.patch.object(sys, 'argv', test_args):
            result = get_args()
            self.assertEqual(result.configfile, 'test.ini', "Configfile not set correctly")
            self.assertEqual(result.dc, 'mdc2', "DC not set correctly")
            self.assertEqual(result.operation, 'create', "Operation not set correctly")
            self.assertEqual(result.vmname, ['testvm1'], "VMname list not set correctly")
            self.assertEqual(result.password, 'password', "Password not set correctly")
            self.assertEqual(result.port, 4050, "Port not set correctly")
            self.assertEqual(result.user, 'testuser', "Username not set correctly")
            self.assertEqual(result.vc, 'vc1', "VC not set correctly")
            self.assertEqual(result.snapname, 'testsnap', "Snapname not set correctly")
            self.assertEqual(result.verbose, False, "Verbosity not set correctly")

    def test_default_get_args(self):
        """
            given a minimum required, verify that things are set.
        """
        test_args = ["prog", "create", "testvm1"]
        with mock.patch.object(sys, 'argv', test_args):
            result = get_args()
            self.assertEqual(result.configfile, 'vsphere-tools.ini', "Default configfile not set correctly")
            self.assertEqual(result.dc, 'NONE', "DC is not None")
            self.assertEqual(result.operation, 'create', "Operation is not set correctly")
            self.assertEqual(result.vmname, ['testvm1'], "VMname list not set correctly")
            self.assertEqual(result.password, None, "Default password not set correctly")
            self.assertEqual(result.port, 443, "Default port not set correctly")
            self.assertEqual(result.user, None, "Default user not set correctly")
            self.assertEqual(result.vc, 'NONE', "Default VC not set correctly")
            self.assertEqual(result.snapname, None, "Default snapname not set correctly")
            self.assertEqual(result.verbose, True, "Default Verbosity not set correctly")

    @mock.patch.object(vim, 'ServiceInstance')
    @mock.patch.object(vim, 'VirtualMachine')
    @mock.patch('power.vsphere_tools.list_snapshots')
    @mock.patch('power.vsphere_tools.create_snapshot')
    @mock.patch('power.vsphere_tools.revert_snapshot')
    @mock.patch('power.vsphere_tools.delete_snapshot')
    @mock.patch('power.vsphere_tools.get_obj')
    def test_snapshot_main(self, mock_go, mock_deletesnap, mock_revertsnap, mock_createsnap, mock_listsnap, mock_vm, mock_si):
        """
            Given the various paths in, verify the right sub function is called
        """
        testvm = vim.VirtualMachine()
        testvm.name = "thisisavm"
        test_args = ["prog", "-s", "vc1", "-u", "testuser", "-p", "password", "create", "testvm1", "--snapname", "testsnap", "-q"]
        with mock.patch.object(sys, 'argv', test_args):
            main()
            mock_createsnap.assert_called_once()
        test_args = ["prog", "-s", "vc1", "-u", "testuser", "-p", "password", "delete", "testvm1", "--snapname", "testsnap", "-q"]
        with mock.patch.object(sys, 'argv', test_args):
            main()
            mock_deletesnap.assert_called_once()
        test_args = ["prog", "-s", "vc1", "-u", "testuser", "-p", "password", "revert", "testvm1", "--snapname", "testsnap", "-q"]
        with mock.patch.object(sys, 'argv', test_args):
            main()
            mock_revertsnap.assert_called_once()
        test_args = ["prog", "-s", "vc1", "-u", "testuser", "-p", "password", "list", "testvm1", "-q"]
        with mock.patch.object(sys, 'argv', test_args):
            main()
            mock_listsnap.assert_called_once()

