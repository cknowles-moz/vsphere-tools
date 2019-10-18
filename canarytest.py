#!/usr/local/bin/python
"""
Canary-test

Takes a VM and moves it between hosts, testing for connectivity to help with
verification that all is well post updates

"""

import atexit
import time
import ssl
import argparse
import getpass
import configparser
from pyVim import connect
from pyVim.connect import Disconnect
from pyVmomi import vim  # pylint: disable=no-name-in-module
import vsphere_tools


def get_args():
    """
    Get and parse the args.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', help='The VC to connect to', action='store',
                        dest='vc')
    parser.add_argument('-o', help='the port to connect to', action='store',
                        default=443, type=int, dest='port')
    parser.add_argument('-u', help='user name', action='store', dest='user')
    parser.add_argument('-p', help='password', action='store', dest='password')
    parser.add_argument('-v', help='VM to be canary, by vmname',
                        action='store', dest='vmname', default=None)
    parser.add_argument('-q', help='Quiet mode', action='store_false',
                        dest='verbose', default=True)
    parser.add_argument('-w',
                        help='boolean for wait for keypress between moves',
                        action='store_true', dest='waitbetween', default=False)
    parser.add_argument('-f', help='The config file to use', action='store',
                        dest='configfile', default='vsphere-tools.ini')
    parser.add_argument('--dc', help="DC to use for ini file parsing",
                        dest="dc", default='NONE')
    parser.add_argument('hosts',
                        help='list of hosts to travel across, by DNS name',
                        action='store', nargs='+')

    return parser.parse_args()


def canary_test(vc_obj, hosts, canary_id, verbose=True):
    """
    With the connection and canary VM, do pings to verify health,
    and vmotions to test.
    :param vc: The active VC connection.
    :param hosts: The list of hosts to migrate between
    :param canary_id: The identifier for the canary VM, either DNS, or IP
    :param verbose: Print out status as it happens.  Default to true
    :return: Boolean for happiness.  Will also raise exceptions for
             terrible things.
    """

    vm_obj = vsphere_tools.get_obj(vc_obj.RetrieveContent(),
                                   [vim.VirtualMachine], canary_id)
    if vm_obj.guest.ipAddress is None:
        pingaddr = canary_id
    else:
        pingaddr = vm_obj.guest.ipAddress

    if verbose:
        print("* Found VM : " + vm_obj.name)

    hostobj = []
    for host in hosts:
        newhost = vsphere_tools.find_host(vc_obj, host)
        if verbose:
            print("* Found host: " + newhost.name)
        hostobj.append(newhost)

    for host in hostobj:
        vsphere_tools.do_a_vmotion(vm_obj, host, pingaddr, verbose)
        if hostobj.index(host) != len(hostobj)-1:
            if verbose:
                print("waiting for 10 seconds between moves")
            time.sleep(10)
        if verbose:
            print("---------")


def main():
    """
    Collect the args, vet them, and then do the vmotion and testing.
    """
    args = get_args()
    # setup inifile
    configfile = configparser.ConfigParser()

    if not configfile.read(args.configfile):
        use_config = False
    else:
        use_config = True

    if args.vc is None:
        if args.dc == "NONE":
            raise Exception("No VC and no DC specified.")
        if use_config:
            server = configfile["DC-"+args.dc.upper()].get("SERVER", "NONE")
        if server != "NONE":
            args.vc = server
            if use_config:
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

    if args.verbose:
        print("* Prework")

    context = None
    # pylint: disable=protected-access
    context = ssl._create_unverified_context()
    si_obj = connect.Connect(host=args.vc, user=args.user, pwd=password,
                             sslContext=context)

    atexit.register(Disconnect, si_obj)

    canary_test(si_obj, args.hosts, args.vmname, args.verbose)


if __name__ == '__main__':
    main()
