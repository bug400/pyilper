pyILPER installation instructions
=================================

Index
-----

* [General](#general)
* [Installation with the ANACONDA platform](#Installation with the ANACONDA platform)
* [Installation without the ANACONDA platform](#installation without the ANACONDA platform)

General
-------
pyILPER requires Python 3.4, QT4.8, pyqt4.8 and pyserial to run. It is
recommended to use the ANACONDA platform to install pyILPER and the required
software components and keep them up to date.

If you already installed the Python runtime you can install pyILPER without
ANACONDA. See the last chapter of this manual.

Installation with the ANACONDA platform
---------------------------------------

You need approximately 700MB free disk space for the Python runtime environment.
Everything is installed as local user so no administrator privileges are
needed for installation. The following instructions apply to Linux, Windows
and Mac OS X.

Follow the [Quick Install Guide](http://http://conda.pydata.org/docs/install/quick.html)
and install Miniconda.

Reopen a new terminal window and type:

conda config --add channel bug400
conda install pyilper

This installs pyilper and all required Python runtime components. 

To update pyILPER and the Python runtime type:

conda update

in a terminal window.

To start pyILPER type:

pyilper

in a Terminal window.

Installation withput the ANACONDA platform
------------------------------------------

pyILPER needs Python3.4, PyQT4.8 and pyserial 2.7 installed on the system.

On LINUX Debian based system you can install the pyilper Debian package.

On all other systems unzip the pyilper zip file, go to the distribution
directory and type:

python3 setup.py install
