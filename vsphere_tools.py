#!/usr/local/bin/python

import subprocess
import platform
import os
import time
import sys

from pyVmomi import vim, vmodl # pylint: disable=no-name-in-module

def _create_char_spinner():
    """Creates a generator yielding a char based spinner.
    """
    while True:
        for c in '|/-\\':
            yield c


_spinner = _create_char_spinner()


def spinner(label=''):
    """Prints label with a spinner.
    When called repeatedly from inside a loop this prints
    a one line CLI spinner.
    """
    sys.stdout.write("\r\t%s %s" % (label, next(_spinner)))
    sys.stdout.flush()


def ping(host, verbose=False):
    """
    ping - ping the address/name given

    host - the host/address to ping
    verbose - boolean - if False, don't echo the ping

    Result - True if things succeed, False if not.
    """
    if platform.system().lower() == "windows":
        parameters = "-n 3 -w 100"
        need_sh = False
    else:
        parameters = "-c 3 -W 100"
        need_sh = True

    args = "ping " + parameters + " " + host

    file_discard = open(os.devnull, 'w')

    if verbose:
        return_code = subprocess.call(args, shell=need_sh) == 0
    else:
        return_code = subprocess.call(args, shell=need_sh, stdout=file_discard, stderr=subprocess.STDOUT) == 0

    file_discard.close()

    return return_code

# get_obj is awesome
# Connect using si and smartconnectnossl...
# content = si.RetrieveContent()
# ds = get_obj(content, [pyVmomi.vim.Datastore], 'sas_node1_1')
# now ds is a pointer to the named datacenter

def get_obj(content, vimtype, name=None):
    """
    Return an object by name, if name is None the
    first found object is returned
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break
    return obj

def get_dc(si, name):
    """
    Get a datacenter by its name.
    """
    for dc in si.content.rootFolder.childEntity:
        if dc.name == name:
            return dc
    raise Exception('Failed to find datacenter named %s' % name)


def find_vm_byip(service_instance, ip):
    """
    find a VM in a datacenter
    service_instance - the connection to the VC
    ip - ip of the vm
    return - the vm object.
    """

    vm = service_instance.content.searchIndex.FindAllByIp(None, ip, True)
    # if vm is not None:
    if len(vm) > 0:
        return vm[0]
    else:
        raise Exception('Cannot find vm with ip: ' + ip)


def find_vm_bydns(service_instance, dns_name):
    """
    find a VM in a datacenter
    service_instance - the connection to the VC
    ip - ip of the vm
    return - the vm object.
    """

    vm = service_instance.content.searchIndex.FindAllByDnsName(None, dns_name, True)
    # if vm is not None:
    if len(vm) > 0:
        return vm[0]
    else:
        raise Exception('Cannot find vm by DNS: ' + dns_name)


def find_host(service_instance, name):
    """
    find a Host in a datacenter
    service_instance - connection to VC
    name - name of the host - MUST be DNS
    return - the host object.
    """

    host = service_instance.content.searchIndex.FindAllByDnsName(None, name, False)
    if len(host) > 0:
        return host[0]
    else:
        raise Exception('Cannot find host: ' + name)


def wait_for_task(task, verbose=False):
    """
    Wait for task to complete
    task: the vm task
    returns True if successful, False if not.
    """

    while task.info.state not in [vim.TaskInfo.State.success, 
                vim.TaskInfo.State.error]:
        if verbose:
            spinner(task.info.state)
        time.sleep(1)
    if verbose:
            print('')
    if task.info.state == vim.TaskInfo.State.success:
        return True
    if task.info.state == vim.TaskInfo.State.error:
        return False


def do_a_vmotion(vm, host, pingaddr, verbose=False):
    """
    do one repetition of a vmotion.

    Ping the pingaddr,
    migrate the vm
    Ping the pingaddr
    raising exceptions on any failure

    vm - vm object
    host - host object
    pingaddr - the dns or ip to ping.
    """

    spec = vim.VirtualMachineRelocateSpec()
    spec.host = host

    if verbose:
        print('*** Preparing to move VM: ' + vm.name + ' to host: %s' % host.name)

    if ping(pingaddr):
        if verbose:
            print('*** We have initial pings - moving to host: %s' % host.name)
            print('*** VMotion to host %s now' % host.name)
        task = vm.RelocateVM_Task(spec)
    else:
        raise Exception('Pre-VMotion Ping Failed')

    if wait_for_task(task, verbose):
        if verbose:
            print("*** VMotion succeeded")
    else:
        raise Exception("VMotion task failed")

    if verbose:
        print("*** Sleeping 5 seconds to let things settle.")
    time.sleep(5)

    if ping(pingaddr):
        if verbose:
            print('*** Success, we have ping post VMotion to %s' % host.name)
    else:
        raise Exception('Post-VMotion Ping Failed')

def list_snapshots(snapshotlist):
    """
    recursively transit the snapshot tree, returning all snaps

    snapshotlist: the list of snapshots vm.snapshot.rootSnapshotList to start
    """

    result_snapshot_list = []
    snap_text = ""
    for snapshot in snapshotlist:
        snap_text = "VM: %s; Name: %s; Description: %s; Created: %s; VMState: %s" % (
                                        snapshot.vm.name, snapshot.name, 
                                        snapshot.description, snapshot.createTime, 
                                        snapshot.state)
        result_snapshot_list.append(snap_text)
        result_snapshot_list = result_snapshot_list + list_snapshots(
                                        snapshot.childSnapshotList)
    return result_snapshot_list

def get_snapshot(name, snapshotlist):
    """
    Recursively search the snapshot tree, returning the snaps that match name

    name:  Name of the snapshot to look for
    snapshotlist: the list of snapshots vm.snapshot.rootSnapshotList to start
    """
    result_snapshot_list = []
    for snapshot in snapshotlist:
        if snapshot.name == name:
            result_snapshot_list.append(snapshot)
        else:
            result_snapshot_list = result_snapshot_list + get_snapshot(
                                    name, snapshot.childSnapshotList)
    return result_snapshot_list

def create_snapshot(vm, snapname, snapdesc="", verbose=False):
    """
    Create a snapshot of the given VM

    vm : vm object
    snapname : string of the name given
    snapdesc : string of the description of the snapshot - optional
    verbose : should we be printing statuses

    result : vm has a snapshot.
    """
    if verbose:
        print('*** Creating a snapshot for VM %s' % vm.name)
    wait_for_task(vm.CreateSnapshot_Task(snapname, snapdesc, True, True),verbose)

def delete_snapshot(vm, snapname, verbose=False):
    """
    Create a snapshot of the given VM

    vm : vm object
    snapname : string of the name of the snap to delete
    verbose : printing out statuses

    result : Snapshot has been removed
    """
    if verbose:
        print("** Finding snapshot %s" % snapname)
    if snapname == None:
        raise Exception("snapshot name required for delete operations.")
    snapobj = get_snapshot(snapname, vm.snapshot.rootSnapshotList)
    if len(snapobj) == 1:
        #Found our one snapshot
        if verbose:
            print("** Removing snapshot %s from VM %s" % (snapname, vm.name))
        wait_for_task(snapobj[0].snapshot.RemoveSnapshot_Task(True), verbose)
    else:
        raise Exception("** We did not find one and only one snapshot by that name")

def revert_snapshot(vm, snapshot, verbose=False):
    """
    Revert a VM to the referenced snapshot

    vm : a vm object
    snapname : the name of the snapshot to look for
    verbose : printing out statements

    result : VM has been reverted to the referenced snapshot 
    """
    if verbose:
        print("** Finding snapshot %s" % snapshot)
    if snapshot == None:
        raise Exception("snapshot name required for revert operations.")
    snapobj = get_snapshot(snapshot, vm.snapshot.rootSnapshotList)
    if len(snapobj) == 1:
        #Found our one snapshot
        if verbose:
            print("** Reverting VM %s to snapshot %s" % (vm.name, snapshot))
        wait_for_task(snapobj[0].snapshot.RevertToSnapshot_Task(), verbose)
    else:
        raise Exception("** We did not find one and only one snapshot by that name")

def vm_poweron(vm, verbose=False):
    """
    Power a VM on

    vm : a vm object
    verbose : print out statements

    result : VM has had the power turned on
    """
    if not wait_for_task(vm.PowerOnVM_Task(), verbose):
        raise Exception("Power on of vm %s Failed" % vm.name)
    if verbose:
        print("** VM %s powered on" % vm.name)

def vm_poweroff(vm, force=False, verbose=False):
    """
    Power off a VM

    vm : a vm object
    force : if true, power off, if false, try a guest shutdown
    verbose : print out statements

    result : VM has either been shut, or had guest shutdown initiated
    """
    if force:
        if verbose:
            print("** Hard shutdown for %s starting" % vm.name)
        if wait_for_task(vm.PowerOffVM_Task(), verbose):
            if verbose:
                print("** Hard shutdown successful")
        else:
            raise Exception("Hard shutdown of VM %s failed" % vm.name)
    else:
        vm.ShutdownGuest()
        if verbose:
            print("** Shutdown Guest for %s attempted" % vm.name)

def vm_reboot(vm, force=False, verbose=False):
    """
    Restart a VM

    vm : a vm object
    force : if true, force a reset, if false, try a guest restart
    verbose : print out statements

    result : VM is being restarted
    """
    if force:
        if verbose:
            print("** Hard reset for %s starting" % vm.name)
        if wait_for_task(vm.ResetVM_Task(), verbose):
            if verbose:
                print("** Hard reset successful")
        else:
            raise Exception("Hard shutdown of VM %s failed" % vm.name)
    else:
        vm.RebootGuest()
        if verbose:
            print("** Restart for Guest %s attempted" % vm.name)
