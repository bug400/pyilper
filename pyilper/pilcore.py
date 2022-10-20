#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# pyILPER 
#
# Python platform dependent classes and constants
# Copyright (c) 2016 J. Siebold
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# pyILPER support and constants  -----------------------------------------------
#
# Changelog
# 08.07.16 - jsi:
# - initial release
# 25.07.2016 - jsi
# - set version to "production"
# 21.08.2016 - jsi
# - set version to 1.3.5 development
# 13.10.2016 - jsi
# - device tab constants and dictionary added
# 18.10.2016 - jsi
# - set version number to 1.4.0 development
# 23.10.2016 - jsi
# - EMU7470_VERSION added
# 25.10.2016 - jsi
# - decode_version moved from lifexec.py
# 26.10.2016 - jsi
# - version 1.4.0 beta1
# 04.11.2016 - jsi
# - version 1.4.0 beta2
# 01.01.2016 - jsi
# - version 1.4.0
# 07.01.2016 - jsi
# - add encode version function
# 03.01.2016 - jsi
# - version - 1.5.0beta1 development
# 16.03.2017 - jsi
# - version - 1.5.0 production
# 01.08.2017 - jsi
# - device HP82162A added
# 10.08.2017 jsi
# - version 1.6.0 development
# 11.08.2017 jsi
# - catch error in decode_version if no version information exists
# 18.08.2017 jsi
# - Tab name plotter renamed to HP7470A
# 21.08.2017 jsi
# - PDF and barcode constants added
# 31.08.2017 jsi
# - parameter TERMINAL_MINIMUM_ROWS added
# 03.09.2017 jsi
# - communication mode constants moved from pyilpermain.py
# 06.09.2017 jsi
# - restructured, assemble_frame and disassemble_frame added
# 07.09.2017 jsi
# - timeout constants for TCP, socket and pipe communication added
# 01.10.2017 jsi
# - 1.6.0 beta1
# 12.11.2017 jsi
# - 1.6.0 beta3
# 13.11.2017 jsi
# - make USE8BITS change depending on data returned by the PIL-Box
# 27.11.2017 jsi
# - version 1.6.0 production
# 04.12.2017 jsi
# - version 1.6.1 development
# 28.12.2017 jsi
# - AUTOSCROLL_RATE parameter introduced
# 16.01.2018 jsi
# - added config type parameters for cls_config_tool_button
# 17.01.2018 jsi
# - added color scheme constants
# - changed version to 1.7.0 because of major enhancements of the GUI
# 21.01.2018 jsi
# - moved cls_config_tool_button and color scheme constants to pilwidget.py
# 22.02.2018 jsi
# - 1.7.1 production
# 18.03.2018 jsi
# - 1.7.2 development, added Python minimum version requirements
# 04.08.2018 jsi
# - 1.7.2 beta1
# 11.08.2018 jsi
# - 1.7.2 beta2
# 20.08.2018 jsi
# - 1.7.2 production
# 12.12.2018 jsi
# - added HP2225B_LINEBUFFERSIZE
# - 1.8.0 development
# 18.12.2018 jsi
# - added HP2225B
# 10.01.2019 jsi
# - renamed Printer tab to Generic Printer
# - prepare Beta1
# 14.01.2019 jsi
# - added constants for keyboard type configuration
# - prepare Beta2
# 27.01.2019 jsi
# - introduced KEYBOARD_DELAY configuration parameter
# 09.01.2019 jsi
# - prepare release
# 31.05.2019 jsi
# - 1.8.1 development
# 05.06.2019
# - 1.8.1 production
# 06.11.2019 jsi
# - 1.8.2 development
# 03.02.2020 jsi
# - prepare release
# 29.04.2020 jsi
# - 1.8.3 development
# 10.01.2021 jsi
# - 1.8.3 release
# 01.03.2021 jsi
# - 1.8.4 development
# 16.11.2021 jsi
# - TAB_RAWDRIVE added
# 28.11.2021 jsi
# - prepare 1.8.5 beta 1
# 12.12.2021 jsi
# - function buildconfigfilename added
# 17.02.2022 jsi
# - 1.8.5 release
# - function to decode the pyILPER release number rewritten
# 18.04.22 jsi
# - 1.8.6 beta1 
# - used raw string in re.compile to avoid DEPRECATED warning
# 29.07.22 jsi
# - added determination of Qt bindings
# 20.10.22 jsi
# - 1.8.6 release
#
import platform
import os
import re
import sys
#
# Program constants --------------------------------------------------
#
# General constants:
#
PRODUCTION=  True      # Production/Development Version
VERSION="1.8.6"        # pyILPR version number
CONFIG_VERSION="2"     # Version number of pyILPER config file, must be string
#
# Python minimum version
#
PYTHON_REQUIRED_MAJOR=3
PYTHON_REQUIRED_MINOR=5
#
# Communication modes and classes
#
MODE_PILBOX=0         # connect to PIL-Box
MODE_TCPIP=1          # connect to virtual HP-IL over TCP/IP
MODE_SOCKET=2         # conect via Unix domain socket

#
# PIL-Box communication
#
USE8BITS= True        # use 8 bit data transfer to PIL-Box
TMOUTCMD=1            # time out for PIL-Box commands
TMOUTFRM=0.05         # time out for HP-IL frames

#
# TCP/IP, socket and pipe communication
#
COMTMOUTREAD=0.1      # time out for read
COMTMOUTACK=1         # time out for receiving an acknowledge
COMTMOUTWRITE=1       # tine out for write

#
# Drive tab - directory listing
#
REFRESH_RATE=1000     # period to check whether a drive was altered and is idle
NOT_TALKER_SPAN=3     # time (s) a drive must be inactive to be concidered as idle
#
# Terminal tab
#
UPDATE_TIMER=25                 # Poll timer (ms) for terminal output queue
CURSOR_BLINK=500                # 500 ms cursor blink rate
CURSOR_BLINK_INTERVAL= CURSOR_BLINK / UPDATE_TIMER
AUTOSCROLL_RATE=100             # 500 ms cursor blink rate
TERMINAL_MINIMUM_ROWS=24        # can't get beyond that
KEYBOARD_DELAY=500              # autorepeat delay to prevent too fast kbd input

#
# predefined baudrates
# the list controlles the baudrates that are supported by the application:
# - the first list element sets the text in the combobox
# - the second list element is the baud rate, a value of 0 means auto baud detection
# the baudrates must be defined in ascending order
BAUDRATES= [ ["Auto", 0], ["9600", 9600 ] , [ "115200", 115200 ], ["230400", 230400]]

#
# plotter tab, required version of emu7470
#
EMU7470_VERSION=900

#
# thermal printer tab
#
HP82162A_LINEBUFFERSIZE=2000

#
# if Development Version append string to VERSION and "d" to config file name
#
if not PRODUCTION:
   VERSION=VERSION+" (Development)"
#
# Tab types
#
TAB_SCOPE=0
TAB_PRINTER=1
TAB_DRIVE=2
TAB_TERMINAL=3
TAB_PLOTTER=4
TAB_HP82162A=5
TAB_HP2225B=6
TAB_RAWDRIVE=7
#
TAB_NAMES={TAB_SCOPE:'Scope',TAB_PRINTER:'Generic Printer',TAB_DRIVE:'Drive',TAB_TERMINAL:'Terminal',TAB_PLOTTER:'HP7470A',TAB_HP82162A:'HP82162A', TAB_HP2225B: 'HP2225B', TAB_RAWDRIVE: 'Raw Drive'}
#
# PDF Constants in 1/10 mm
#
PDF_MARGINS=100   
PDF_FORMAT_A4=0
PDF_FORMAT_LETTER=1
PDF_ORIENTATION_PORTRAIT=0
PDF_ORIENTATION_LANDSCAPE=1
#
# Barcode Constants in 1/10 mm
#
BARCODE_HEIGHT=100
BARCODE_NARROW_W= 5
BARCODE_WIDE_W= 10
BARCODE_SPACING= 5

#
# determine QT Bindings
#
QTBINDINGS="None"
HAS_WEBENGINE=False
HAS_WEBKIT=False
# already loaded
for _b in('PyQt5','PySide6'):
   if _b+'.QtCore' in sys.modules:
      QTBINDINGS=_b
      break
else:
   try:
      import PySide6.QtCore
   except ImportError:
      if "PySide6" in sys.modules:
         del sys.modules["Pyside6"]
      try:
         import PyQt5.QtCore
      except ImportError:
         if "PyQt5" in sys.modules:
            del sys.modules["Pyside6"]
         raise ImportError("No Qt bindings found")
      else:
         QTBINDINGS="PyQt5"
         from PyQt5 import QtPrintSupport
         QT_FORM_A4=QtPrintSupport.QPrinter.A4
         QT_FORM_LETTER=QtPrintSupport.QPrinter.Letter
         try:
            from PyQt5 import QtWebKitWidgets
            HAS_WEBKIT=True
         except:
            pass
         try:
            from PyQt5 import QtWebEngineWidgets
            HAS_WEBENGINE=True
         except:
            pass
         if HAS_WEBKIT and HAS_WEBENGINE:
           HAS_WEBENGINE=False
   else:
      QTBINDINGS="PySide6"
      from PySide6 import QtGui
      QT_FORM_A4=QtGui.QPageSize.A4
      QT_FORM_LETTER=QtGui.QPageSize.Letter
      try:
         from PySide6 import QtWebEngineWidgets
         HAS_WEBENGINE=True
      except:
         pass
#
# utility functions --------------------------------------------------------------
#
#  get platform
#
def isLINUX():
   return platform.system()=="Linux"
def isWINDOWS():
   return platform.system()=="Windows"
def isMACOS():
   return platform.system()=="Darwin"
#
# Standard FONT
# Note: It would be more elegant to use "Andale Mono" on Macos and "Consolas" on 
# Windows. "Consolas" is not available on XP and older Windows versions.
#
if isLINUX():
   FONT="Monospace"
else:
   FONT="Courier New"
#
# decode version number of lifutils or emu7470
#
def decode_version(version_number):
   if version_number==0:
      return "(unknown)"
   version=str(version_number)
   major=int(version[0])
   minor=int(version[1:3])
   subversion=int(version[3:5])
   return "{:d}.{:d}.{:d}".format(major,minor,subversion)
#
# decode version number of pyilper as a list
#
def decode_pyILPERVersion(version_string):
#
#  parse the pyILPER version string as a list:
#  major version, minor version, subversion, a/b, devel-version
#  only major version, minor version and subersion are returned as a
#  single integer. Returns 0 if no valid release information was found.
#
#  Fixed DEPRECATED escape sequence \. using raw string
   reg=re.compile(r'^([0-9]+)\.([0-9]+)\.([0-9]+)(?:(b)([0-9]+)?)?.*$')
   ret=reg.findall(version_string)
   try:
     major=int(ret[0][0])
     minor=int(ret[0][1])
     subversion=int(ret[0][2])
     return major*10000+minor*100+subversion
   except ValueError:
      return 0
   except IndexError:
      return 0
#
#  assemble frame from low and high byte according to 7- oder 8-bit format
#
def assemble_frame(hbyt,lbyt):
   global USE8BITS
   if( lbyt & 0x80 ):
      USE8BITS= True
      return ((hbyt & 0x1E) << 6) + (lbyt & 0x7F)
   else:
      USE8BITS= False
      return ((hbyt & 0x1F) << 6) + (lbyt & 0x3F)
#
#  disassemble frame from low and high byte according to 7- oder 8-bit format
#

def disassemble_frame(frame):
    if not USE8BITS :
       hbyt = ((frame >> 6) & 0x1F) | 0x20
       lbyt = (frame & 0x3F) | 0x40
    else:
       hbyt = ((frame >> 6) & 0x1E) | 0x20
       lbyt = (frame & 0x7F) | 0x80
    return(hbyt,lbyt)
#
#  assemble file name of config file
#
def buildconfigfilename(progname,filename,configversion,instance,production):
#
#  determine config file name
#
   fname=filename+instance+configversion
   if not production:
      fname+= "d"
#
#  determine path (os dependend)
#
   userhome=os.path.expanduser("~")

   if platform.system()=="Linux":
#
#     LINUX
#        
      configpath=os.path.join(userhome,".config",progname)
   elif platform.system()=="Windows":
#
#     Windows
#
      configpath=os.path.join(os.environ['APPDATA'],progname)
   elif platform.system()=="Darwin":
#
#     Mac OS X
#
      configpath=os.path.join(userhome,"Library","Application Support",progname)
#
   else:
#
#     Fallback
#
      configpath=os.path.join(userhome,progname)
   configfilename=os.path.join(configpath,fname)
    
   return configfilename,configpath
