pyILPR (Virtual HP-IL Devices)
==============================

![pyilper](https://github.com/bug400/pyilper/raw/master/img/pyilper_drive.png)

Index
-----

* [Description](#description)
* [Features](#features)
* [Compatibility](#compatibility)
* [Installation](#installation)
* [License](#license)
* [Acknowledgements](#acknowledgements)

Description
-----------
HP-IL (Hewlett Packard Interface Loop) is a serial interconnection bus 
introduced by Hewlett-Packard in the early 1980s. It enabled the communication 
between peripheral devices such as printers, floppy disk drives etc. 
with programmable calculators such as the HP-41C, HP71B and HP-75C/D.

The connection to PCs was realized by either a generic ISA bus card or a 
serial interface controller. As these devices are not available anymore, 
Jean-Francois Garnier published his 
[PIL-Box project](http://www.jeffcalc.hp41.eu/hpil/)
in 2009 to link a PC via USB to the HP-IL system.

The PC operating system communicates with the PIL-Box as a virtual serial 
device over USB. The PIL-Box is connected to the HP-IL Loop.

pyILPER is a program that reads incoming HP-IL frames from the PIL-Box, 
processes them by emulating some virtual HP-IL devices, like a printer, 
a disk drive or a terminal and sends the processed frames back to the loop.


Features
--------

* Entirely written in Python3 using the Qt GUI-Framework (Qt5 and Qt6)
* Virtual mass storage drive with integrated directory list, file management  (import, export, rename, purge, view) and disk management functions (label, pack, initialize)
* Virtual generic printer emulating the HP-71B, HP-41C, HP-75 and ROMAN-8 character sets
* Terminal emulator with keyboard support for HP-71B and HP-75.
* Virtual plotter emulating the HP-7470A HP-IL plotter
* Virtual printer emulating the HP-82162A thermal printer
* Virtual printer emulating the ThinkJet HP-2225B printer
* HP-IL scope
* The number of virtual devices is configurable,
* The virtual devices can be either organized in a compact tabbed view or in independent floating windows
* The output of the scope or the virtual printer(s) is logged to file(s)
* Monitoring the status of the virtual HP-IL devices
* Support for the PIL-Box via serial-over-usb interface
* Support for [virtual HP-IL over TCP/IP](http://hp.giesselink.com/hpil.htm) (dual TCP/IP V4/V6 stack)
* Support to connect the emulators [EMU41, EMU71 and EMU75](http://www.jeffcalc.hp41.eu/index.html) running on DOSBox to pyILPER.

See the [pyILPER virtual devices gallery](https://github.com/bug400/pyilper/blob/master/GALLERY.md) for details.


Compatibility
-------------

pyILPER has been successful tested with LINUX, Windows 10 and macOS.


Installation
------------

pyILPER requires the Python interpreter and the Qt framework installed. 
Thanks to the [Anaconda Python distribution system](https://www.continuum.io/) 
pyILPER and the required software components can be easily installed on 
Linux, Windows and macOS.

See the [Installation Instructions](https://github.com/bug400/pyilper/blob/master/INSTALL.md) for details.

In order to use the file and disk management functions and the virtual HP7470A plotter 
an up to date version of the [LIFUTILS](https://github.com/bug400/lifutils/releases) 
is required as well.


License
-------

pyILPER is published under the GNU General Public License v2.0 License 
(see LICENSE file).


Acknowledgements
----------------

Much code was taken from ILPER for Windows (Copyright (c) 2008-2013 
J-F Garnier, Visual C++ version by Christoph Gießelink 2016). 
The terminal emulator code was taken from the pyqterm console widget written
by Henning Schroeder. The virtual TCP/IP support of pyILPER was significantly
improved by Christoph Gießelink who also provided many other improvements. The virtual
HP7470A plotter engine was derived from the HP2XX software (Heinz W. Werntges, Martin 
Kroeker).
