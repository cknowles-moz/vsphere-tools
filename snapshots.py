#!/usr/local/bin/python
"""
snapshots.py

Used to manage (create, delete, list) snapshots for a vm
"""

import atexit
from pyVim import connect
from pyVim.connect import SmartConnectNoSSL, Disconnect
from pyVmomi import vim, vmodl # pylint: disable=no-name-in-module
import ssl
import argparse
import getpass
import vsphere_tools
import configparser

def get_args():
    """
    Get and parse the args.
    """
    parser = argparse.ArgumentParser()
    
    parser.add_argument('operation', help='Operation', choices=['create', 'delete', 'revert', 'list'], default='list', action='store')
    parser.add_argument('vmname', help='The name of the VM to operate on', action='store', nargs="+")
    parser.add_argument('--snapname', help='for create/delete/revert operations, the name of the snapshot', action='store', dest='snapname')
    parser.add_argument('-f', help='The config file to use', action='store', dest='configfile', default='vsphere-tools.ini')
    parser.add_argument('-s', help='The VC to connect to', action='store', dest='vc', default="NONE")
    parser.add_argument('-o', help='the port to connect to', action='store', default=443, type=int, dest='port')
    parser.add_argument('-u', help='user name', action='store', dest='user')
    parser.add_argument('-p', help='password', action='store', dest='password')
    parser.add_argument('-q', help='Quiet mode', action='store_false', dest='verbose', default=True)
    parser.add_argument('--dc', help="DC to use for ini file parsing", dest="dc", default="NONE")

    return parser.parse_args()

def main():

    args = get_args()

    if args.verbose:
        print("* Prework")

    # setup inifile
    configfile = configparser.ConfigParser()
    configfile.read(args.configfile)

    if args.vc == "NONE":
        if args.dc == "NONE":
            raise Exception("No VC and no DC specified.")
        server = configfile["DC-"+args.dc.upper()].get("SERVER","NONE")
        if server == "NONE":
            raise Exception("No server/DC matching command line options found")
        else:
            args.vc = server
            args.user = configfile["DC-"+args.dc.upper()].get("USERNAME","FOO")

    if args.password: 
        password = args.password
    else:
        password = getpass.getpass(prompt='Enter password for host %s and user %s: ' % (args.vc, args.user))

    context = None
    context = ssl._create_unverified_context()
    si = connect.Connect(host=args.vc, user=args.user, pwd=password, sslContext=context)

    atexit.register(Disconnect, si)

    for this_vm in args.vmname:
        if args.verbose:
            print("** Finding VM to work with: %s" % this_vm)
        vm = vsphere_tools.get_obj(si.RetrieveContent(), [vim.VirtualMachine], this_vm)
        if vm is not None:
            if args.verbose:
                print("** Found it")

        if args.operation == "create":
            if args.snapname == None:
                raise Exception("snapshot name required for create operations.")
            if args.verbose:
                print ("* Creating snapshot %s on VM %s" % (args.snapname, vm.name))
            vsphere_tools.create_snapshot(vm, args.snapname, "", args.verbose)
            if args.verbose:
                print("* Snapshot created")
        if args.operation == "delete":
            if args.snapname == None:
                raise Exception("snapshot name required for delete operations.")
            if args.verbose:
                print("* Deleting snapshot %s from VM %s" % (args.snapname, vm.name))
            vsphere_tools.delete_snapshot(vm, args.snapname, args.verbose)
            if args.verbose:
                print("* Snapshot deleted")
        if args.operation == "revert":
            if args.snapname == None:
                raise Exception("snapshot name required for revert operations.")
            if args.verbose:
                print("* Reverting VM %s to snapshot %s" % (vm.name, args.snapname))
            vsphere_tools.revert_snapshot(vm, args.snapname, args.verbose)
            if args.verbose:
                print("* VM %s reverted to snapshot %s" % (vm.name, args.snapname))
        if args.operation == "list":
            snaplist = vsphere_tools.list_snapshots(vm.snapshot.rootSnapshotList)
            for item in snaplist:
                print(item)


if __name__ == '__main__':
    main()
