#!/usr/local/bin/python
"""
    Intermediate functions for the vsphere-tools scripts
"""

import subprocess
import platform
import os
import time
import sys

from pyVmomi import vim  # pylint: disable=no-name-in-module


def _create_char_spinner():
    """Creates a generator yielding a char based spinner.
    """
    while True:
        for char in '|/-\\':
            yield char


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
        return_code = subprocess.call(args, shell=need_sh, stdout=file_discard,
                                      stderr=subprocess.STDOUT) == 0

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
    for current_obj in container.view:
        if name:
            if current_obj.name == name:
                obj = current_obj
                break
        else:
            obj = current_obj
            break
    return obj


def get_dc(si_obj, name):
    """
    Get a datacenter by its name.

    si_obj - a connection to a vCenter
    name - the name of the dc to look for
    return - the dc_obj
    """
    for dc_obj in si_obj.content.rootFolder.childEntity:
        if dc_obj.name == name:
            return dc_obj
    raise Exception('Failed to find datacenter named %s' % name)


def find_vm_byip(service_instance, ip_addr):
    """
    find a VM in a datacenter
    service_instance - the connection to the VC
    ip_addr - ip of the vm
    return - the vm object.
    """

    vm_obj = service_instance.content.searchIndex.FindAllByIp(None, ip_addr,
                                                              True)
    # if vm is not None:
    if vm_obj:
        return vm_obj[0]
    else:
        raise Exception('Cannot find vm with ip: ' + ip_addr)


def find_vm_bydns(service_instance, dns_name):
    """
    find a VM in a datacenter
    service_instance - the connection to the VC
    dns_name - fqdn of the vm
    return - the vm object.
    """

    vm_obj = service_instance.content.searchIndex.FindAllByDnsName(None,
                                                                   dns_name,
                                                                   True)
    # if vm is not None:
    if vm_obj:
        return vm_obj[0]
    else:
        raise Exception('Cannot find vm by DNS: ' + dns_name)


def find_host(service_instance, name):
    """
    find a Host in a datacenter
    service_instance - connection to VC
    name - name of the host - MUST be DNS
    return - the host object.
    """

    host = service_instance.content.searchIndex.FindAllByDnsName(None, name,
                                                                 False)
    if host:
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


def do_a_vmotion(vm_obj, host, pingaddr, verbose=False):
    """
    do one repetition of a vmotion.

    Ping the pingaddr,
    migrate the vm
    Ping the pingaddr
    raising exceptions on any failure

    vm_obj - vm object
    host - host object
    pingaddr - the dns or ip to ping.
    """

    spec = vim.VirtualMachineRelocateSpec()
    spec.host = host

    if verbose:
        print('*** Preparing to move VM: ' + vm_obj.name + ' to host: %s' %
              host.name)

    if ping(pingaddr):
        if verbose:
            print('*** We have initial pings - moving to host: %s' % host.name)
            print('*** VMotion to host %s now' % host.name)
        task = vm_obj.RelocateVM_Task(spec)
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
        snap_text = "VM: %s; Name: %s; Description: %s; \
                    Created: %s; VMState: %s" % (
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


def create_snapshot(vm_obj, snapname, snapdesc="", verbose=False):
    """
    Create a snapshot of the given VM

    vm_obj : vm object
    snapname : string of the name given
    snapdesc : string of the description of the snapshot - optional
    verbose : should we be printing statuses

    result : vm has a snapshot.
    """
    if verbose:
        print('*** Creating a snapshot for VM %s' % vm_obj.name)
    wait_for_task(vm_obj.CreateSnapshot_Task(snapname, snapdesc, True, True),
                  verbose)


def delete_snapshot(vm_obj, snapname, verbose=False):
    """
    Create a snapshot of the given VM

    vm_obj : vm object
    snapname : string of the name of the snap to delete
    verbose : printing out statuses

    result : Snapshot has been removed
    """
    if verbose:
        print("** Finding snapshot %s" % snapname)
    if snapname is None:
        raise Exception("snapshot name required for delete operations.")
    snapobj = get_snapshot(snapname, vm_obj.snapshot.rootSnapshotList)
    if len(snapobj) == 1:
        # Found our one snapshot
        if verbose:
            print("** Removing snapshot %s from VM %s" % (snapname,
                                                          vm_obj.name))
        wait_for_task(snapobj[0].snapshot.RemoveSnapshot_Task(True), verbose)
    else:
        raise Exception(
            "** We did not find one and only one snapshot by that name")


def revert_snapshot(vm_obj, snapshot, verbose=False):
    """
    Revert a VM to the referenced snapshot

    vm_obj : a vm object
    snapname : the name of the snapshot to look for
    verbose : printing out statements

    result : VM has been reverted to the referenced snapshot
    """
    if verbose:
        print("** Finding snapshot %s" % snapshot)
    if snapshot is None:
        raise Exception("snapshot name required for revert operations.")
    snapobj = get_snapshot(snapshot, vm_obj.snapshot.rootSnapshotList)
    if len(snapobj) == 1:
        # Found our one snapshot
        if verbose:
            print("** Reverting VM %s to snapshot %s" % (vm_obj.name,
                                                         snapshot))
        wait_for_task(snapobj[0].snapshot.RevertToSnapshot_Task(), verbose)
    else:
        raise Exception(
            "** We did not find one and only one snapshot by that name")


def vm_poweron(vm_obj, verbose=False):
    """
    Power a VM on

    vm_obj : a vm object
    verbose : print out statements

    result : VM has had the power turned on
    """
    if not wait_for_task(vm_obj.PowerOnVM_Task(), verbose):
        raise Exception("Power on of vm %s Failed" % vm_obj.name)
    if verbose:
        print("** VM %s powered on" % vm_obj.name)


def vm_poweroff(vm_obj, force=False, verbose=False):
    """
    Power off a VM

    vm_obj : a vm object
    force : if true, power off, if false, try a guest shutdown
    verbose : print out statements

    result : VM has either been shut, or had guest shutdown initiated
    """
    if force:
        if verbose:
            print("** Hard shutdown for %s starting" % vm_obj.name)
        if wait_for_task(vm_obj.PowerOffVM_Task(), verbose):
            if verbose:
                print("** Hard shutdown successful")
        else:
            raise Exception("Hard shutdown of VM %s failed" % vm_obj.name)
    else:
        vm_obj.ShutdownGuest()
        if verbose:
            print("** Shutdown Guest for %s attempted" % vm_obj.name)


def vm_reboot(vm_obj, force=False, verbose=False):
    """
    Restart a VM

    vm_obj : a vm object
    force : if true, force a reset, if false, try a guest restart
    verbose : print out statements

    result : VM is being restarted
    """
    if force:
        if verbose:
            print("** Hard reset for %s starting" % vm_obj.name)
        if wait_for_task(vm_obj.ResetVM_Task(), verbose):
            if verbose:
                print("** Hard reset successful")
        else:
            raise Exception("Hard shutdown of VM %s failed" % vm_obj.name)
    else:
        vm_obj.RebootGuest()
        if verbose:
            print("** Restart for Guest %s attempted" % vm_obj.name)
