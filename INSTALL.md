pyILPER installation instructions
=================================

Index
-----

* [General](#general)
* [Installation with the ANACONDA platform](#Installation with the ANACONDA platform)
* [Installation without the ANACONDA platform](#installation without the ANACONDA platform)

General
-------

pyILPER requires:

* Python 3.4 
* QT 4.8, 
* PyQt 4.8 
* pyserial > 2.7 

It is recommended to use the [ANACONDA platform](https://www.continuum.io) 
to install pyILPER and the required Python software and keep them up to date.

If you already installed the required Python software you can install pyILPER without
ANACONDA. See the last chapter of this manual.

Installation with the ANACONDA platform
---------------------------------------

You need approximately 700MB free disk space for pyILPER and the Python 
runtime environment. Everything is installed as a local user and thus no 
administrator privileges are needed. 

The following instructions apply to Linux, Windows and Mac OS X:

Follow the [Quick Install Guide](http://conda.pydata.org/docs/install/quick.html)
and install Miniconda first.

Reopen a new terminal window and type:

     conda config --add channel bug400
     conda install pyilper

This installs pyilper and all required Python runtime components. 

To update pyILPER and the Python runtime type:

     conda update

in a terminal window.

To start pyILPER type:

     pyilper

in a terminal window.


Installation withput the ANACONDA platform
------------------------------------------

The requirements specified above must be available on the system.

On Debian based Linux systems you can install the pyilper Debian package.

On all other systems unzip the pyilper archive, go to the pyilper software
directory and type:

     python3 setup.py install

in a terminal window.
