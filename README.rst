pyILPR (Virtual HP-IL Devices)
==============================


Index
-----

* [Description](#description)
* [Features](#features)
* [Compatibility](#compatibility)
* [License](#license)
* [Acknowledgements](#acknowledgements)

Description
-----------
HP-IL (Hewlett Packard Interface Loop) is a serial interconnection bus 
introduced by Hewlett-Packard in the early 1980s. It enabled the communication 
between peripheral devices such as printers, floppy disk drives etc. 
with programmable calculators such as the HP-41C, HP71B and HP-75C/D.

The connection to PCs was realized by either an generic ISA bus card or a 
serial interface controller. As these devices are not avaibalbe any more, 
Jean-Francois Garnier published his 
[PIL-Box project](http://http://www.jeffcalc.hp41.eu/hpil/)
in 2009 to link a PC via USB to the HP-IL system.

The PC operating system communicates with the PIL-Box as a virtual serial 
device over USB. The PIL-Box reads incoming frames from the loop.

pyPIL is a program that reads HP-IL frames from the PIL-Box, processes them 
by emulating some virtual HPIL devices, like a printer, a disk drive or 
a terminal and sends the processed frames back to the loop.


Features
--------

* Entirely written in Python3 using the QT GUI-Framework
* Up to 5 virtual mass storage drives with integrated directory list
* Up to 3 virtual printers emulating the HP-71B and HP-41C character set
* Terminal emulator with experimental keyboard support (HP-71B only)
* HP-IL scope
* Number of virtual devices is configurable
* Log of scope or virtual printer output to file(s)
* HP-IL device status
* Support for the PIL-Box via serial-over-usb interface
* Experimental support for [virtual HP-IL over TCP-IP](http://http://hp.giesselink.com/hpil.htm)


Compatibility
-------------

pyILPER has been success tested with LINUX and Windows 7. It should work
with Mac OS/X but has not been tested up to now.

License
-------

pyILPER is under th GNU General Public License v3.0 License (see LICENSE file).


Acknowledgements
----------------

Much code was taken from ILPER 1.4.5 for Windows (Copyright (c) 2008-2013 
J-F Garnier, Visual C++ version by Christoph Gießelink 2013. 
The Terminal emulator widget was taken from pyqterm console widget 
by Henning Schroeder.


Install pyILPER
---------------

See the INSTALL file.
