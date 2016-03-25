## pyILPR (Virtual HP-IL Devices)
==============================

![pyilper](https://cdn.rawgit.com/bug400/pyilper/b5544a2/img/pyilper_drive.png)

Index
-----

* [Description](#description)
* [Features](#features)
* [Compatibility](#compatibility)
* [Installation] (#installation)
* [License](#license)
* [Acknowledgements](#acknowledgements)

Description
-----------
HP-IL (Hewlett Packard Interface Loop) is a serial interconnection bus 
introduced by Hewlett-Packard in the early 1980s. It enabled the communication 
between peripheral devices such as printers, floppy disk drives etc. 
with programmable calculators such as the HP-41C, HP71B and HP-75C/D.

The connection to PCs was realized by either an generic ISA bus card or a 
serial interface controller. As these devices are not available any more, 
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

* Entirely written in Python3 using the QT GUI-Framework
* Up to 5 virtual mass storage drives with integrated directory list, file management  (import, export, rename, purge, view) and disk management functions (label, pack, initialize).
* Up to 3 virtual printers emulating the HP-71B and HP-41C character set
* Terminal emulator with keyboard support (HP-71B only)
* HP-IL scope
* Number of virtual devices is configurable
* Log of scope or virtual printer output to file(s)
* HP-IL device status
* Support for the PIL-Box via serial-over-usb interface
* Support for [virtual HP-IL over TCP/IP](http://hp.giesselink.com/hpil.htm) (dual TCP/IP V4/V6 stack)


Compatibility
-------------

pyILPER has been success tested with LINUX, Windows 7 and Mac OS X.


Installation
------------

pyILPER requires the Python interpreter and the Qt framework installed. 
Thanks to the [Anaconda Python distribution system](https://www.continuum.io/) 
pyILPER and the required software components can be easily installed on 
Linux, Windows and Mac OS X.

See the [Installation Instructions](https://github.com/bug400/pyilper/blob/master/INSTALL.md) for details.

In order to use the file and disk management functions an up to date version of the
[LIFUTILS] (https://github.com/bug400/lifutils/releases) are required as well.


License
-------

pyILPER is published under the GNU General Public License v2.0 License 
(see LICENSE file).


Acknowledgements
----------------

Much code was taken from ILPER 1.4.5 for Windows (Copyright (c) 2008-2013 
J-F Garnier, Visual C++ version by Christoph Gießelink 2013. 
The Terminal emulator widget was taken from pyqterm console widget 
by Henning Schroeder. The virtual TCP/IP support of pyILPER was significant
improved by Christoph Gießelink.
