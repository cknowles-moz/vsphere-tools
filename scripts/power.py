#!/usr/local/bin/python
"""
power.py

Used to manage (on, off) power state for a vm
"""

import atexit
import ssl
import argparse
import getpass
import configparser
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

    parser.add_argument('operation', help='Operation, on, off, reboot, or \
        query the status', choices=['on', 'off', 'reboot', 'query'],
                        default='query', action='store')
    parser.add_argument('vmname', help='The name of the VM to operate on',
                        action='store', nargs="+")
    parser.add_argument('-f', help='The config file to use', action='store',
                        dest='configfile', default='vsphere-tools.ini')
    parser.add_argument('-s', help='The VC to connect to', action='store',
                        dest='vc', default="NONE")
    parser.add_argument('-o', help='the port to connect to', action='store',
                        default=443, type=int, dest='port')
    parser.add_argument('-u', help='user name', action='store', dest='user')
    parser.add_argument('-p', help='password', action='store', dest='password')
    parser.add_argument('--dc', help="DC to use for ini file parsing",
                        dest="dc", default="NONE")
    parser.add_argument('--force', help="do a hard shutdown/restart",
                        action="store_true", dest="hardware", default=False)
    parser.add_argument('-q', help='Quiet mode', action='store_false',
                        dest='verbose', default=True)
    return parser.parse_args()


def main():
    """
        main: Collect cli args, and then perform the approrpiate power function
        on the right VMs.  on, off, reboot.  off/reboot can be graceful
        (default) or forced
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
            args.user = configfile["DC-"+args.dc.upper()].get(
                "USERNAME", "FOO")
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
            print("* Finding VM to work with: %s" % this_vm)
        vm_obj = vsphere_tools.get_obj(si_obj.RetrieveContent(),
                                       [vim.VirtualMachine],
                                       this_vm)
        if vm_obj is not None:
            if args.verbose:
                print("** Found it")
        else:
            raise Exception("Cannot find VM named "+this_vm)
        if args.operation == "on":
            vsphere_tools.vm_poweron(vm_obj, args.verbose)
        elif args.operation == "off":
            vsphere_tools.vm_poweroff(vm_obj, args.hardware, args.verbose)
        elif args.operation == "reboot":
            vsphere_tools.vm_reboot(vm_obj, args.hardware, args.verbose)
        elif args.operation == "query":
            print("%s is %s" % (vm_obj.name, vm_obj.runtime.powerState))
        else:
            raise Exception(
                "only supporting on, and off, and query, and yet somehow, \
                    you got to this error")


if __name__ == '__main__':
    main()
