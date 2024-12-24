# pyILPER Installation Instructions

Index
-----

* [Requirements](#requirements)
* [Overview of the Installation from PyPi](#overview-of-the-installation-from-pypi)
     * [Installation on Windows](#installation-on-windows)
     * [Installation on macOS](#installation-on-macos)
     * [Installation on Linux](#installation-on-linux)
* [Installation from GitHub](#installation-from-github)
* [Installation of the LIFUTILS](#installation-of-the-lifutils)
* [pyILPER Setup](#pyilper-setup)
* [Usage](#usage)
* [Installation of development versions](#installation-of-development-versions)
* [Virtual Environment Maintenance](#virtual-environment-maintenance)


## Requirements

To run pyILPER you need:

* Python version 3.6 or higher. Version 3.11 is currently recommended.
* Qt version 5.9 or higher with the PyQt5 language bindings or Qt version 6.3 or higher (recommended) with the PySide6 language bindings
* The Python bindings for either Qt Webkit (Qt5 only) or Qt Webengine (recommended)
* pySerial  2.7 or higher
* [LIFUTILS](https://github.com/bug400/lifutils/releases) (the most recent version)

Windows 10 requires the installation of the FTDI USB serial driver first. 
See the [FTDI website](http://www.ftdichip.com/Drivers/VCP.htm) for details.

More recent macOS versions already provide an USB serial driver for the
PIL-Box.

LINUX does not require to install any driver software.


## Overview of the Installation from PyPi

The installation of pyILPER and the required runtime software from PyPi requires the following steps:

1. Get a Python interpreter for your system:

* Windows: download and install it from Microsoft Store (free)
* macOS: download and install the universal installer from the [www.python.org](https://www.python.org) website
* Linux: install it from system repositories if not already installed on your system


2. Create a virtual Python environment for pyILPER

A virtual environment is a directory tree that contains a dedicated Python runtime version with pyILPER 
and all the necessary library and software components to run this software for the current user. This environment must be "activated" (see below) and it works isolated from the operating systems or other environments.

Installing pyILPER in a virtual environment does not affect your system configuration.

A virtual environment can be removed by simply removing the directory in question. This does not affect the pyILPER configuration files.

See [this guide](https://docs.python.org/3/library/venv.html#how-venvs-work) if you want to know more about virtual Python environments.

3. Activate the virtual Python environment

To use a virtual Python environment an activation script must be called. An activated environment is indicated
in the prompt string. 

4. Install pyILPER and runtime components

This step fetches pyILPER and the necessary runtime components (Qt6, PySide6 language bindings, pySerial)
from the [Python Package Index (PyPi)](https://pypi.org), which is the official third-party software repository for Python. You can also install additional software in the environment from the Python Package Index.

<b>Warning: always call the Python interpreter "python3" if you create a virtual environment and "python" after the environment has been activated!!!</b>

5. Maintain the virtual environment

See [Virtual environment maintenance](#virtual-environment-maintenance)


### Installation on Windows

Note: use the "Command Line" instead of the "Terminal (PowerShell") application to enter the commands below. Using the "Activate.ps1" PowerShell" script requires issuing the PowerShell command:

     PS C:> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

To install the Python interpreter open the Microsoft Store, enter the search term "Python" and select the recommended version (see above) for installation. Python is installed for the current user.

Example: create a virtual environment "py311" in the home directory of the current user, install and start pyILPER:


     C:\>cd %USERPROFILE%                                  (change to users home directory)
     
     C:\Users\bug400>python3 -m venv py311                 (create environment %USERPROFILE%\py311, use python3 to call the interpreter here!!!)

     C:\Users\bug400>py311\scripts\activate                (activate the environment, the environment name becomes component of the prompt string)
     
     (py311) C:\Users\bug400>python -m pip install pyilper (install pyILPER with the required runtime dependecies)
     Collecting pyilper
       Obtaining dependency information for pyilper from https://files.pythonhosted.org/packages/3e/
     
     ...
     
     Installing collected packages: pyserial, shiboken6, PySide6-Essentials, PySide6-Addons, pyside6, pyilper
     Successfully installed PySide6-Addons-6.6.1 PySide6-Essentials-6.6.1 pyilper-1.8.7 pyserial-3.5 pyside6-6.6.1 shiboken6-6.6.1
     
     [notice] A new release of pip is available: 23.2.1 -> 23.3.2
     [notice] To update, run: python.exe -m pip install --upgrade pip
     
     (py311) C:\Users\bug400>pyilper                        (start pyILPER)



If the Python interpreter is run for the first time, a window opens and requests firewall permissions. To grant permissions for Python applications administrator privileges are needed.

You can invoke pyILPER without activating the environment by calling:

     %USERPROFILE%\py311\scripts\pyilper

Create a desktop shortcut for %USERPROFILE\py311\scripts\pyilper.exe to conveniently start pyILPER.


### Installation on macOS

Install Python for macOS from the [Python website](https://www.python.org/). Choose the recommended Python version (see above), download and install the macOS 64-bit universal installer. You need administrator privileges for that.

See [Using Python on a Mac](https://docs.python.org/3/using/mac.html) for further details.

Example: create a virtual environment "py311" in the home directory of the current user, install and start pyILPER:

     node1-mac:~ bug400$ python3 -m venv py311                  (create virtual environment ~/py311)
     node1-mac:~ bug400$ source py311/bin/activate              (activate virtual environment ~/py311)
     (py311) node1-mac:~ bug400$ python -m pip install pyilper  (install pyILPER and required runtime components)
     Collecting pyilper
       Obtaining dependency information for pyilper from https://files.pythonhosted.org/packages/3e

     ...

     Using cached shiboken6-6.6.1-cp38-abi3-macosx_11_0_universal2.whl (406 kB)
     Installing collected packages: pyserial, shiboken6, PySide6-Essentials, PySide6-Addons, pyside6, pyilper
     Successfully installed PySide6-Addons-6.6.1 PySide6-Essentials-6.6.1 pyilper-1.8.7 pyserial-3.5 pyside6-6.6.1 shiboken6-6.6.1
     
     [notice] A new release of pip is available: 23.2.1 -> 23.3.2
     [notice] To update, run: pip install --upgrade pip
     (py311) node1-mac:~ bug400$ pyilper                        (start pyILPER)
     
You can invoke pyILPER without activating the environment by calling:

     node1-mac:~ bug400$ ~/py311/bin/pyilper

Build a macOS Automator application to create a desktop shortcut. Use the "run shell script" action and enter the full path to the pyilper script in the virtual environment. Save it as a program and drag it to the desktop. See [this guide](https://www.hpmuseum.org/forum/thread-3824-post-150519.html#pid150519) for details, but enter your proper pyILPER path.


### Installation on Linux

Generally, it is recommended to use the Python Interpreter provided by the Linux distribution. 

To install pyILPER from PyPI, follow the macOS installation instructions.


## Installation from GitHub

To install pyILPER this way, the above mentioned system requirements must be installed on your computer.

Download the latest pyILPER source code zip-file from the [pyILPER Releases page](https://github.com/bug400/pyilper/releases/) and unzip it in an arbitrary location. You get the pyILPER directory pyilper-x.y.z, where x.y.z is the version number.

Now you can start the assembler with:

      python <Path to the pyILPER directory>/start.py 

Note: it depends on your operaing system configuration whether the Python interpreter is invoked as "python" or "python3".

The [pyILPER Releases page](https://github.com/bug400/pyilper/releases/) also provides an installation package for the current Debian release. Installing this package will add the necessary dependencies to the system and create a menu entry to start the program. This package might also be installable on Linux distributions which were derived from the Debian release in question (Ubuntu, Raspberry PI OS).
     
## Installation of the LIFUTILS

In order to use the file and disk management functions and the virtual HP7470A plotter
an up to date version of the [LIFUTILS](https://github.com/bug400/lifutils/releases)
must be installed. See the [Installation Instructions](https://github.com/bug400/lifutils/blob/master/INSTALL.md) for further details.


## pyILPER Setup

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


## Usage

See the online documentation which can be launched from the Help menu.

If the user manual is not available in pyilper due to missing language bindings, you can also display it with your web browser. Search for the pyilper installation in the virtual environment (usually below the site-packages directory) and open the file pyilper/Manual/index.html.


## Installation of development versions

Beta versions of pyILPER are published on the [release page](https://github.com/bug400/pyilper/releases). Download the source code zip file and proceed as described below.

To use development versions of pyILPER download the pyilper-master.zip file from GitHub [front page of pyILPER](https://github.com/bug400/pyilper) ("Download ZIP" button). 

Unzip the downloaded file to an arbitrary location of your file system.

Now you can start the beta or development version with:

      python <Path to the unzipped directory>/start.py

If you get the error message "This script requires Python 3.6 or newer!" use python3 instead.

Note:
* Development versions are work in progress and were tested roughly. They are not testet on all platforms.  They may crash and may ruin your data at worst.
* Beta versions are tested more thoroughly on all supported platforms. They are intended for public testing but should not be used for production.
* The beta or development versions do not affect the configuration of an already installed production version because a different naming convention is used for the configuration files.

To obtain more recent development versions of pyILPER download the pyilper-master.zip file again. If you are familiar with a git client you can synchronize a local pyilper-master directory with the remote GitHub repository.


## Virtual Environment Maintenance

Generally, it is recommended to check whether a new version of pyILPER exists and to upgrade that package only.

Note: To upgrade the python interpreter itself it is safest to uninstall the old interpreter, remove the environment and reinstall/recreate interpreter and environment.

To do virtual environment maintenance you have to activate it first:

     <path to venv directory>/scripts/activate (Windows)
     or
     source <path to venv directory>/bin/activate (macOS, Linux)


Deactivate an environment:

     deactivate

Check for packages that can be updated:

     python -m pip list -o

Update pyILPER:

     python -m pip install --upgrade pyilper


Further maintenance commands:

List installed packages:

     python -m pip list

Install a package:

     python -m pip install <packagename>

Show details of a package:

     python -m pip show <packagename>

Remove a package:

     python -m pip uninstall <packagename>

Check for new versions of a package

     python -m pip list -o

Upgrade a package (pip itself can be upgraded with pip)

     python -m pip install --upgrade <packagename>

Clear package cache (saves space on disk):

     python -m pip cache  purge

Remove an environment:

     delete the entire directory tree of the environment

