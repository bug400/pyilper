pyILPER installation instructions
=================================

Index
-----

* [General](#general)
* [Installation with the ANACONDA platform](#installation-with-the-anaconda-platform)
* [Setup](#setup)
* [Operation](#operation)
* [Installation without the ANACONDA platform](#installation-without-the-anaconda-platform)
* [Installation of development versions](#installation-of-development-versions)

General
-------

pyILPER requires:

* Python 3.4, 3.5
* QT 4.8, 
* PyQt 4.8 
* pyserial  2.7 

It is recommended to use the [ANACONDA platform](https://www.continuum.io) 
to install pyILPER and the required Python software and keep them up to date.

If you already installed the required Python software you can install pyILPER without
ANACONDA. See the last chapter of this manual.

Windows requires the installation of the FTDI USB serial driver first.
See the [FTDI website](http://www.ftdichip.com/Drivers/VCP.htm) for details.

More recent Mac OS X versions already provide a USB serial driver for the
PIL-Box.  By experience you get better results if you use the original FTDI driver. 
See the installation istructions for that driver how to install and how to 
disable the Apple driver.

LINUX does not require to install any driver software.


Installation with the ANACONDA platform
---------------------------------------

You need approximately 700MB free disk space for pyILPER and the Python 
runtime environment. Everything is installed as a local user and thus no 
administrator privileges are needed. 

Note: for the ANACONDA platform pyILPER is only available for Python 3.5.

The following instructions apply to Linux, Windows and Mac OS X:

Follow the [Quick Install Guide](http://conda.pydata.org/docs/install/quick.html)
and install Miniconda first. Note: If you install Miniconda the first time
then let the installer modify the PATH variable of your environment.

Reopen a new terminal window and type:

     conda update conda
     conda config --add channels bug400
     conda install pyilper

This installs pyilper and all required Python runtime components. 

To update pyILPER and the Python runtime type:

     conda update --all

in a terminal window.

To start pyILPER type:

     pyilper

in a terminal window.

You should issue occasionally:

     conda clean --packages --tarballs

to clean the conda package cache and save disk space.


Setup
-----

If pyILPER is started for the first time the serial device of the PIL-Box
and the working directory must be configured.

Open the pyILPER configuration dialog from the file menu. Change the
name of the PIL-Box device to the USB serial device the box is
connected to.

On Linux the device name is usually /dev/ttyUSBn. Check if you have read and
write access to the device. Some Linux distributions require membership of
the dialout group to access the device.

On Windows the device is COMn. If you are uncertain, check the COM ports
in the device manager. 

On Mac OS X the device name is usually /dev/tty.usbserial-FTDBIRU.

The baud rate must match the baud rate the PIL-Box is configured to. See
the PIL-Box documentation for details.

The working directory defaults to the users home directory. Change the working
directory to an appropriate location. The pyILPER log files are stored in the
working directory.

Now reconnect to the PIL-Box in the file menu. pyILPER is ready to use 
if the message "connected to PIL-Box" is displayed in the status line. 


Usage
-----

See the online documentation which can be launched from the Help menu.


Installation without the ANACONDA platform
------------------------------------------

The requirements specified above must be available on the system.

On Debian based Linux systems you can install the pyilper Debian package.

On all other systems unzip the pyilper source code, go to the pyilper 
directory and type:

     python3 setup.py install

in a terminal window.

Installation of development versions
------------------------------------

Download the pyilper-master.zip file from GitHub front page of pyILPER ("Download ZIP" button). Unzip this file to an arbitrary location of your file system.

Now you can start the development version with:

      python <Path to the pyilper-master directory>/start.py

If you get the error message "This script requires Python 3.4 or newer!" use python3 instead.

Note:
* Development versions are work in progress and are only coarse tested. They may crash and may ruin your data at worst.
* The development version does not affect the configuration of your production version because a different naming convention is used.

To obtain more recent development versions of pyILPER download the pyilper-master.zip file again. If you are familiar with a git client you can synchronize a local pyilper-master directory with the remove GitHub repository.
