pyILPER installation instructions
=================================

Index
-----

* [General](#general)
* [Installation of the LIFUTILS](#installation-of-the-lifutils)
* [Installation with the ANACONDA platform](#installation-with-the-anaconda-platform)
* [Setup](#setup)
* [Operation](#operation)
* [Installation without the ANACONDA platform](#installation-without-the-anaconda-platform)
* [Installation of beta or development versions](#installation-of-beta-or-development-versions)

General
-------

pyILPER requires:

* Python 3.5 or higher (Python 3.10 is not supported at the moment)
* QT 5.6 or higher
* PyQt compatible to the Python and Qt version
* The Python bindings for either Qt Webkit or Qt Webengine
* Pyserial  2.7 
* [LIFUTILS](https://github.com/bug400/lifutils/releases) (the most recent version)

It is recommended to use the [ANACONDA platform](https://www.continuum.io) 
to install pyILPER and the required Python software and keep them up to date.

If you already installed the required Python software you can install pyILPER [without ANACONDA](#installation-without-the-anaconda-platform).

Windows requires the installation of the FTDI USB serial driver first.
See the [FTDI website](http://www.ftdichip.com/Drivers/VCP.htm) for details.

More recent macOS versions already provide a USB serial driver for the
PIL-Box.  By experience, you get better results if you use the original FTDI driver. 

LINUX does not require to install any driver software.


Installation of the LIFUTILS
----------------------------

In order to use the file and disk management functions and the virtual HP7470A plotter
an up to date version of the [LIFUTILS](https://github.com/bug400/lifutils/releases)
must be installed. See the [Installation Instructions](https://github.com/bug400/lifutils/blob/master/INSTALL.md) for further details.


Installation with the ANACONDA platform
---------------------------------------

Anaconda is a Python distribution widely used in Data Science applications.
It provides an Python environment that is easy to install and maintain
on Windows, macOS and Linux. The Anaconda cloud gives access to more than
1000 Python applications.

The Anaconda distribution installs more than 150 Python packages on your
computer which are not needed to run pyILPER. Therefore, it is recommended
to use the Miniconda installer instead which only provides Python and the
Anaconda package manager.

You need approximately 700 MB free disk space for pyILPER and the Python 
runtime environment. Everything is installed as a local user and thus no 
administrator privileges are needed. 

Download the Python 3.9 version of [Miniconda](https://docs.conda.io/en/latest/miniconda.html) and follow the [Installation Instructions](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) and install Miniconda first.

**Windows**: Do not instruct the installer to change the PATH. 
Use always the Anaconda Prompt which is available from the start menu.

**Linux and macOS**: If you install Miniconda the first time
then let the installer modify the PATH variable of your environment.

Reopen a new terminal window (Linux, macOS) or Anaconda Prompt (Windows) 
and type:

     conda update conda
     conda config --add channels bug400
     conda install pyilper

This installs pyILPER and all required Python runtime components. 

To update pyILPER and the Python runtime type:

     conda update --all

in a terminal window (Linux and macOS) or Anaconda Prompt (Windows).

To start pyILPER type:

     pyilper

in a terminal window (Linux and macOS) or Anaconda Prompt (Windows).

You should issue occasionally:

     conda clean --all

to clean the conda package cache and save disk space.

Note: pyILPER requires at least Python 3.9. If you get no pyILPER updates check your Anaconda/Miniconda Python version with:

     conda list

You can upgrade the Python version to 3.9 with:

     conda install python=3.9

**Windows**:
If an update to a current Python version fails, do a clean reinstallation of the
Anaconda/Miniconda environment.


Setup
-----

If pyILPER is started for the first time the serial device of the PIL-Box
and the working directory must be configured.

Open the pyILPER configuration dialog from the file menu. Change the
name of the PIL-Box device to the USB serial device the box is
connected to. pyILPER tries to make an appropriate proposal for the device name.

On Linux the device name is usually /dev/ttyUSBn. Check if you have read and
write access to the device. Some Linux distributions require membership of
the dialout group to access the device.

On Windows the device is COMn. If you are uncertain, check the COM ports
in the device manager. 

On macOS the device name is usually /dev/tty.usbserial-FTDxxxx.

pyILPER tries to determine the baud rate of the PIL-BOX serial device.
If that does not work, set the baud rate manually to the baud rate the
PIL-Box is configured to. See the PIL-Box documentation for further details.

pyILPER stores all log files in a working directory. The default
of that directory is the users home directory. Change the working directory
to an appropriate location.

If the message "connected to PIL-BOX at xxx baud" is displayed in the
status bar, pyILPER is ready to run. Now you have to enable each
virtual device (check box in the lower left corner of a device tab), because
they are disabled by default.


Usage
-----

See the online documentation which can be launched from the Help menu.


Installation without the ANACONDA platform
------------------------------------------

The requirements specified above must be available on the system.

On Debian based Linux systems you can install the pyILPER Debian package.

On all other systems unzip the pyILPER source code, go to the pyILPER 
directory and type:

     python3 setup.py install

in a terminal window.


Installation of beta or development versions
--------------------------------------------

Beta versions of pyILPER are published on the [release page](https://github.com/bug400/pyilper/releases). Download the source code zip file and proceed as described below.

To use development versions of pyILPER download the pyilper-master.zip file from GitHub [front page of pyILPER](https://github.com/bug400/pyilper) ("Download ZIP" button). 

Unzip the downloaded file to an arbitrary location of your file system.

Now you can start the beta or development version with:

      python <Path to the unzipped directory>/start.py

If you get the error message "This script requires Python 3.5 or newer!" use python3 instead.

Note:
* Development versions are work in progress and were tested roughly. They are not testet on all platforms.  They may crash and may ruin your data at worst.
* Beta versions are tested more thoroughly on all supported platforms. They are intended for public testing but should not be used for production.
* The beta or development versions do not affect the configuration of an already installed production version because a different naming convention is used for the configuration files.

To obtain more recent development versions of pyILPER download the pyilper-master.zip file again. If you are familiar with a git client you can synchronize a local pyilper-master directory with the remote GitHub repository.
