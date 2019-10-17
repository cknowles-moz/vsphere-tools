#!/usr/local/bin/python
"""
Canary-test

Takes a VM and moves it between hosts, testing for connectivity to help with verification that all is well post updates

"""

import atexit
from pyVim import connect
from pyVim.connect import SmartConnectNoSSL, Disconnect
from pyVmomi import vim, vmodl # pylint: disable=no-name-in-module
import time

import subprocess
import platform
import os 
import ssl

import argparse
import getpass
import vsphere_tools
import configparser

# TODO: check to make sure that pyVim is not needed.


def get_args():
    """
    Get and parse the args.
    """
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-s', help='The VC to connect to', action='store', dest='vc')
    parser.add_argument('-o', help='the port to connect to', action='store', default=443, type=int, dest='port')
    parser.add_argument('-u', help='user name', action='store', dest='user')
    parser.add_argument('-p', help='password', action='store', dest='password')
    parser.add_argument('-v', help='VM to be canary, by vmname', action='store', dest='vmname', default=None)
    parser.add_argument('-q', help='Quiet mode', action='store_false', dest='verbose', default=True)
    parser.add_argument('-w', help='boolean for wait for keypress between moves', action='store_true',
                        dest='waitbetween', default=False)
    parser.add_argument('-f', help='The config file to use', action='store', dest='configfile', default='vsphere-tools.ini')
    parser.add_argument('--dc', help="DC to use for ini file parsing", dest="dc", default='NONE')
    parser.add_argument('hosts', help='list of hosts to travel across, by DNS name', action='store', nargs='+')
    
    return parser.parse_args()
    
def canary_test(vc, hosts, canary_id, verbose=True):
    """
    With the connection and canary VM, do pings to verify health, and vmotions to test.
    :param vc: The active VC connection.
    :param hosts: The list of hosts to migrate between
    :param canary_id: The identifier for the canary VM, either DNS, or IP
    :param verbose: Print out status as it happens.  Default to true
    :return: Boolean for happiness.  Will also raise exceptions for terrible things.
    """

#        vm = vsphere_tools.find_vm_bydns(vc, canary_id)
    vm = vsphere_tools.get_obj(vc.RetrieveContent(), [vim.VirtualMachine], canary_id)
    if vm.guest.ipAddress is None:
        pingaddr = canary_id
    else:
        pingaddr = vm.guest.ipAddress

    if verbose:
        print("* Found VM : " + vm.name)

    hostobj = []
    for host in hosts:
        newhost = vsphere_tools.find_host(vc, host)
        if verbose:
            print ("* Found host: " + newhost.name)
        hostobj.append(newhost)

    for host in hostobj:
        vsphere_tools.do_a_vmotion(vm, host, pingaddr, verbose)
        if hostobj.index(host) != len(hostobj)-1:
            if verbose:
                print("waiting for 10 seconds between moves")
            time.sleep(10)
        if verbose:
            print("---------")


def main():

    args = get_args()
    # setup inifile
    configfile = configparser.ConfigParser()

    if len(configfile.read(args.configfile)) == 0:
        useConfig = False
    else:
        useConfig = True

    if args.vc is None:
        if args.dc == "NONE":
            raise Exception("No VC and no DC specified.")
        if useConfig:
            server = configfile["DC-"+args.dc.upper()].get("SERVER","NONE")
        if server == "NONE":
            raise Exception("No server/DC matching command line options found")
        else:
            args.vc = server
            if useConfig:
                args.user = configfile["DC-"+args.dc.upper()].get("USERNAME","FOO")
    
    if args.password: 
        password = args.password
    else:
        password = getpass.getpass(prompt='Enter password for host %s and user %s: ' % (args.vc, args.user))

    if args.verbose:
        print("* Prework")

    context = None
    context = ssl._create_unverified_context()
    si = connect.Connect(host=args.vc, user=args.user, pwd=password, sslContext=context)

    atexit.register(Disconnect, si)

    canary_test(si, args.hosts, args.vmname, args.verbose)


if __name__ == '__main__':
    main()
