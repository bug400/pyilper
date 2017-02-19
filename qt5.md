Install and run pyilper 1.5.0beta for Qt5
=========================================

Index
-----

* [General](#general)
* [Installation with the ANACONDA platform](#installation-with-the-anaconda-platform)
* [Installation without the ANACONDA platform](#installation-without-the-anaconda-platform)

General
-------

Starting with version 1.5.0 pyILPER moves to Qt5, the active developed version of the Qt 
framework. Version 1.4.0 will be the last version that supports Qt4. This document
shows how to run beta versions of pyILPER under Qt5.


Installation with the ANACONDA platform
---------------------------------------

The installation on the ANACONDA platform is fairly easy. You can create a
separate conda environment that leaves your pyilper production installation untouched.

First create a conda test environment (In this example the name of the environment 
is "qt5"). Open a new terminal window and type:

     conda create --name qt5 python=3.6

When conda asks you

     proceed ([y]/n)?

Type "y" for "yes".

Now change to the new "qt5" environment:

     source activate qt5 (Linux, MAC OS)
     activate qt5 (Windows)

Install the qt5 version of pyILPER:

     conda install pyilper5

Run pyILPER

     pyilper

Note: if you open a terminal window the default conda environment is active so you have
to change to the "qt5" environment as specified above.

If you want to get rid of the "qt5" environment, type:

     conda remove --name qt5 --all

If you like to update the qt5 environment to get updated beta versions of pyILPER activate 
the qt5 environment and type:

     conda update --all

You should issue occasionally:

     conda clean --all

to clean the conda package cache and save disk space.


Installation without the ANACONDA platform
------------------------------------------

pyILPER 1.5.x needs at least python 3.4, QT5.6,  the corresponding python QT bindings 
and the pyserial package installed on your system.

Go to the pyILPER page on GitHub and select the "qt5" branch. 

Download the pyilper-qt5.zip file from GitHub ("Download ZIP" button). Unzip this file to an arbitrary location of your file system.

Now you can start the qt5 version with:

      python <Path to the pyilper-master directory>/start.py

