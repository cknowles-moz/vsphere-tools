#!/usr/bin/env python
"""
Module for doing stats collection from VC's
"""

import atexit
import getpass
import time
import ssl

from argparse import ArgumentParser
from pyvim import connect
from pyvim.connect import Disconnect
from pyVmomi import vim, vmodl # pylint: disable=no-name-in-module

def iterate_vmtree(item, vm_data):
    """
        Work to iterate through trees and collect on only VMs info
        input - a resource pool
    """

#   if there's a sub pool, iterate it too.
    for pool in item.resourcePool:
        vm_data = iterate_vmtree(pool, vm_data)

    for vmachine in item.vm:
        vm_data = get_vminfo(vmachine, vm_data)


    return vm_data

def get_vminfo(vmachine, vm_data):
    """
    Get the info from VM

    Input: VirtualMachine object
    Output: modifies vmdata var for #CPU allocated, # of CPU allocated, and # of total VMs
    """

    vm_hardware = vmachine.config.hardware

    print(vmachine.name+','+str(vm_hardware.numCPU)+','+\
        str(int(round(vm_hardware.memoryMB/1024.0)))+\
        ','+vmachine.runtime.powerState)

    return vm_data

def get_args():
    """
    Get and parse the command line args
    """

    parser = ArgumentParser(description='Args needed to retrieve data from VC')

    parser.add_argument('-s', '--host', action='store', help='Remote VC to connect to', dest='host')
    parser.add_argument('-o', '--port', action='store', type=int, default=443, \
      help='Port to connect on', dest='port')
    parser.add_argument('-u', '--user', action='store', help='User to connect as', \
      dest='user')
    parser.add_argument('-p', '--password', action='store', \
      help='Password to use when connecting to host', dest='password')
    parser.add_argument('-d', action='store_true', help='debug/verbose mode.', \
      dest='debug', default=True)

    #(options, args) = parser.parse_args()
    options = parser.parse_args()
    return options

#def disable_warnings():
#    """
#        Some versions of pyvmomi use urllib3 and it whines about certs -
#        rather than jump through hoops for stats collection
#        let's just ignore the warnings.
#    """
#    try:
#        # Surpress urllib warnings
#        import urllib3
#        import urllib3.exceptions
#        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#    except:
#        pass

def main():
    """
    Put the pieces together, connect to the VC, and being aware of clusters,
    chew through and get the data.
    """


    starttime = int(time.time())

    result_data = {}

    args = get_args()
    if args.password:
        password = args.password
    else:
        password = getpass.getpass(prompt='Enter password for host %s and user %s: '\
            % (args.host, args.user))

    try:
        connect_result = None
        try:
#            disable_warnings()
#            connect_result = SmartConnectNoSSL(host=args.host, user=args.user, pwd=password, \
#                port=int(args.port))
            context = None
            context = ssl._create_unverified_context() # pylint: disable=protected-access
            connect_result = connect.Connect(host=args.host, user=args.user,
                             pwd=password, port=int(args.port), sslContext=context)
        except IOError:
            pass
        if not connect_result:
            print("Could not connect to the specified host with provided user/pass")
            return -1
    #No matter what, disconnect
        atexit.register(Disconnect, connect_result)

        content = connect_result.RetrieveContent()

        datacenter = content.rootFolder.childEntity[0]

        hostfolder = datacenter.hostFolder

        dc_name = datacenter.name


    #Grab the hardware:
        for compute_resource in hostfolder.childEntity:
            cluster_name = compute_resource.name
#      if type(compute_resource) == pyVmomi.vim.ClusterComputeResource:
#        result_data[dcName+'.'+clusterName+'.hardware'] = \
#            {'totalMB':compute_resource.summary.effectiveMemory,\
#            'totalCPU':compute_resource.summary.numCpuThreads}
            if isinstance(compute_resource, vim.ClusterComputeResource):
                result_data[dc_name+'.'+cluster_name+'.hardware'] = \
                    {'totalMB':compute_resource.summary.effectiveMemory,\
                        'totalCPU':compute_resource.summary.numCpuThreads}
      #Now to cycle through the VMs.
            result_data[dc_name+'.'+cluster_name+'.virtualmachines.allocated'] = \
                {}.fromkeys(('onCPU', 'onMB', 'onTotal', 'offCPU', 'offMB', 'offTotal'), 0)
            iterate_vmtree(compute_resource.resourcePool, \
                result_data[dc_name+'.'+cluster_name+'.virtualmachines.allocated'])

    #Time to get the time and print out the results

        timestamp = int(time.time())

        if args.debug:
            print("elapsed time: ", timestamp - starttime)

    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1
#  except Exception, e:
#    print "Caught exception : " + str(e)
#    return -1

    return 0

if __name__ == "__main__":
    main()
