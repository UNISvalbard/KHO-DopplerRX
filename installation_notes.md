# Installation notes

The basic setup procedure is to first prepare a linux machine and then compile and install UHD from Ettus. For the development, an Ubuntu 18.04.4LTS (64-bit) is used. A "minimal installation" is used as the starting point and these notes are mostly a record of additional steps that were required.

## Using VirtualBox

1. Install VirtualBox
2. Download the VirtualBox Guest Additions
3. Download a disk image for Ubuntu 18.04.4LTS
4. Install the linux "normally"
5. Optionally, in the account Settings, remove automatic screen locking (Privacy) and blanking (Power)

For installing the VirtualBox Guest Additions, you will need more software
```
sudo apt update
sudo apt install install gcc make perl
```

6. Install the guest additions (VirtualBox menu "Devices")
7. Eject the guest additions virtual DVD
8. Reboot the linux
9. Choose a larger virtual screen for the linux (VirtualBox menu "View")
10. In the VirtualBox settings for the virtual machine, change the default mouse handling to allow copying of text between the host and the VM (Settings-General-Advanced-Shared Clipboard-Birectional)

## Personal preferences for the Ubuntu configuration

While there are really nice text editors, it is often convenient to use a pretty minimal editor such as `vim` when doing configurations of the system or small changes in the software remotely via `ssh`, which is also needed when remote editing from, e.g., `atom`. So, there are a few additional packages to install
```
sudo apt install vim openssh-server
```

The Doppler software uses only Python3, so it is convenient to define an alias in `.bashrc`
```
alias python=python3
```

## Install UHD with python API

See https://files.ettus.com/manual/page_install.html for more details

Installing from source requires some additional packages. Also, the actual Doppler software needs `SciPy` and `Matplotlib`.
```
sudo apt install wget python3-pip git
sudo apt-get install libboost-all-dev libusb-1.0-0-dev python-mako doxygen python-docutils cmake build-essential
python3 -m pip install --user numpy scipy matplotlib ipython jupyter pandas sympy nose
```
Compile the source, note that you should choose the LTS branch, the latest version froze when trying to record from the USRP
```
git clone https://github.com/EttusResearch/uhd.git
git checkout UHD-3.15.LTS
cd uhd/host
mkdir build
cd build
cmake -DENABLE_PYTHON_API=ON ../
make
make test
sudo make install
sudo ldconfig
```
The python API will be installed in a directory that needs to be added to the path. The simplest way is to add the following in `.bashrc`
```
export PYTHONPATH="/usr/local/lib/python3/dist-packages/"
```

## Additional configuration for USRP

Increase buffer size by adding the following to `/etc/sysctl.conf`
```
net.core.rmem_max=50000000
net.core.wmem_max=50000000
```
Set thread priority, see https://files.ettus.com/manual/page_general.html#general_threading

```
sudo addgroup usrp
sudo adduser myuser usrp
```
Add the following line to `/etc/security/limits.conf`
```
@usrp  - rtprio 99
```
