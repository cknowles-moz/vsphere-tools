# VC scripts

A set of scripts to help with common/annoying operations with VMWare vCenter, 6.0+

## Requirements

Python3 and pyvmomi.

## ini file

Standard ini file with sections \[DC-\<STRING>] which help by setting the username and server name.  Defaults to "vsphere-tools.ini" in the directory with the scripts

The ini file location defaults to your home directory, but you can specify a different location in the command line.

    [DC-MYDC]
    SERVER=vc1.example.com
    USERNAME=myuser@vsphere.local


In the above example, you'd specify "MYDC" to the --dc parameter, and the server and username would be used.  as many DC sections as you like can be specified, in case there are multiple VC/User settings you need/desire.

## Scripts

Scripts are located in ```./scripts``` and you can either run them as ```./scripts/<scriptname>``` or you can cd into scripts. 

### power.py

Used to manage power for VMs

    power.py --dc <DC> <OPERATION> <LIST OF VMs> --force

Where:
- DC - the DC-\<DC> section of the ini file to use for username/server setup
- OPERATION is one of "on" "off" "reboot" "list"
- LIST OF VMs - a space delimited list of all VMs you want to apply the power operation to - handy for use with xargs
- --force is for if you want to not do a request to the guest OS - this is like pulling the power out.

the --help parameter will give you more server/port type settings you can use from the commands line.

### snapshots.py

Used to manage snapshots for VMs

    snapshot.py --dc <DC> <OPERATION> <LIST OF VMS> --snapname <NAME>

Where:
- DC - the DC-\<DC> section of the ini file to use for username/server setup
- OPERATION is one of "create" "delete" "revert" "list"
  - list - list the current snapshots of all VMs listed - snapname is not required
  - create - create a snapshot named with the provided snapname on each of the VMs in question - quiesces the system if possible.
  - delete - delete the snapshot named with the provided snapname on each of the VMs named - if any don't have that snapshot, an exception will be raised, and things will stop.
  - revert - revert the VMs listed to the snapname snapshot.

### canarytest.py

This one's a little unique - when doing Host ESX updates, or vetting new hardware, before we fully bring a host into play, we like to make sure that VMs will survive.  
Currently, assumed, the environment has DRS set to manual, and the hosts named are out of maintenance mode.  And also that VMs are named by their FQDN

Canary test then pings the VM to determine that it's responding.  
Then it vMotions the VM to a host in the host list
Then pings again to make sure the VM is happy in its new home.  
Then repeats the above for every host in the host list, throwing an exception and stopping if there's a ping problem.

    canarytest.py --dc <DC> -v <CANARYVM FQDN> <HOST LIST>

- DC - the DC-\<DC> section of the ini file to use for username/server setup
- CANARYVM - the name/FQDN of the canary test VM
- HOST LIST - a space delimited list of the hosts to move the canary VM between.  
