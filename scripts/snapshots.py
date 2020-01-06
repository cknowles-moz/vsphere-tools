#!/usr/local/bin/python3
"""
snapshots.py

Used to manage (create, delete, list) snapshots for a vm
"""

import ssl
import argparse
import getpass
import atexit
import configparser
import os
from pathlib import Path
from pyVim import connect
from pyVim.connect import Disconnect
from pyVmomi import vim  # pylint: disable=no-name-in-module
# If called as a script, we assume vsphere tools is a subdir, and voila.
# VScode does something odd here, resulting in an import-error
# If not called as a script, we're assuming it's called from the root 
# directory, and import accordingly.
if __name__ == '__main__':
    import vsphere_tools # pylint: disable=import-error
else:
    from scripts import vsphere_tools


def get_args():
    """
    Get and parse the args.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('-f', help='The config file to use', action='store',
                        dest='configfile', default=str(Path.home()) +
                        os.path.sep + 'vsphere-tools.ini')
    parser.add_argument('--dc', help="DC to use for ini file parsing",
                        dest="dc", default="NONE")
    parser.add_argument('-s', help='The VC to connect to', action='store',
                        dest='vc', default="NONE")
    parser.add_argument('-o', help='the port to connect to', action='store',
                        default=443, type=int, dest='port')
    parser.add_argument('-u', help='user name', action='store', dest='user')
    parser.add_argument('-p', help='password', action='store', dest='password')
    parser.add_argument('-q', help='Quiet mode', action='store_false',
                        dest='verbose', default=True)
    parser.add_argument('operation', help='Operation',
                        choices=['create', 'delete', 'revert', 'list'],
                        default='list', action='store')
    parser.add_argument('vmname', help='The name of the VM to operate on',
                        action='store', nargs="+")
    parser.add_argument('--snapname',
                        help='for create/delete/revert operations,\
                             the name of the snapshot',
                        action='store', dest='snapname')

    return parser.parse_args()


def main():
    """
    main:
        Get cli args, decide which snapshot operation to do on them, and
        do it.
        Operations are: create, delete, revert, list
    """
    args = get_args()

    if args.verbose:
        print("* Prework")

    # setup inifile
    configfile = configparser.ConfigParser()
    configfile.read(args.configfile)

    if args.vc == "NONE":
        if args.dc == "NONE":
            raise Exception("No VC and no DC specified.")
        server = configfile["DC-"+args.dc.upper()].get("SERVER", "NONE")
        if server != "NONE":
            args.vc = server
            args.user = configfile["DC-"+args.dc.upper()].get("USERNAME",
                                                              "FOO")
        else:
            raise Exception("No server/DC matching command line options found")

    if args.password:
        password = args.password
    else:
        password = getpass.getpass(
            prompt='Enter password for host %s and user %s: ' %
            (args.vc, args.user))

    context = None
    # pylint: disable=protected-access
    context = ssl._create_unverified_context()
    si_obj = connect.Connect(host=args.vc, user=args.user, pwd=password,
                             sslContext=context)

    atexit.register(Disconnect, si_obj)

    for this_vm in args.vmname:
        if args.verbose:
            print("** Finding VM to work with: %s" % this_vm)
        vm_obj = vsphere_tools.get_obj(si_obj.RetrieveContent(),
                                       [vim.VirtualMachine],
                                       this_vm)
        if vm_obj is not None:
            if args.verbose:
                print("** Found it")
        else:
            print("VM %s was not found" % (this_vm))
            exit()

        if args.operation == "create":
            if args.snapname is None:
                raise Exception(
                    "snapshot name required for create operations.")
            if args.verbose:
                print("* Creating snapshot %s on VM %s" % (args.snapname,
                                                           vm_obj.name))
            vsphere_tools.create_snapshot(vm_obj, args.snapname, "",
                                          args.verbose)
            if args.verbose:
                print("* Snapshot created")
        if args.operation == "delete":
            if args.snapname is None:
                raise Exception(
                    "snapshot name required for delete operations.")
            if args.verbose:
                print("* Deleting snapshot %s from VM %s" % (args.snapname,
                                                             vm_obj.name))
            vsphere_tools.delete_snapshot(vm_obj, args.snapname,
                                          args.verbose)
            if args.verbose:
                print("* Snapshot deleted")
        if args.operation == "revert":
            if args.snapname is None:
                raise Exception(
                    "snapshot name required for revert operations.")
            if args.verbose:
                print("* Reverting VM %s to snapshot %s" %
                      (vm_obj.name, args.snapname))
            vsphere_tools.revert_snapshot(vm_obj, args.snapname,
                                          args.verbose)
            if args.verbose:
                print("* VM %s reverted to snapshot %s" %
                      (vm_obj.name, args.snapname))
        if args.operation == "list":
            if vm_obj.snapshot is None:
                print("VM: %s; No Snapshots exist" % (vm_obj.name))
            else:
                snaplist = vsphere_tools.list_snapshots(
                    vm_obj.snapshot.rootSnapshotList)
                for item in snaplist:
                    print(item)


if __name__ == '__main__':
    main()
