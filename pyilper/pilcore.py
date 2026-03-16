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
# pyILPER support -----------------------------------------------
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
# 18.04.2022 jsi
# - 1.8.6 beta1 
# - used raw string in re.compile to avoid DEPRECATED warning
# 29.07.2022 jsi
# - added determination of Qt bindings
# 20.10.2022 jsi
# - 1.8.6 release
# 29.01.2023
# - 1.8.7a1 development
# 23.05.2023
# - 1.8.7a2 development
# 26.08.2023
# - 1.8.7 release 
# 18.01.2024
# - 1.8.8 verion
# 28.01.2024
# - added getEventPosition function
# 28.08.2024
# - 1.8.9a1 development
# 10.09.2024
# - 1.8.9a2 development
# 11.09.2024
# - 1.8.9
# 6.10.2024
# - 1.8.10 development
# 5.12.2024
# - 1.8.10 production
# 01.07.2025
# - refactoring of interface constants
# 03.10.2025
# - use Qt5 bindings instead of PySide6, if FORCE_QT5 environment variable is set
# 15.03.2026
# - removed constant definitions -> pilglobals.py
#
import re
import os

from .pilglobals import *

#
#  portable function to get mouse cursor coordinate
#
if PILGLOBALS.QT_Bindings=="PyQt5":
   def getEventPosition(ev): 
      return(ev.pos())
if PILGLOBALS.QT_Bindings== "PySide6":
   def getEventPosition(ev): 
       return(ev.position().toPoint()) 

#def getEventPosition(ev): 
#   if PILGLOBALS.QT_Bindings=="PyQt5":
#      return(ev.pos())
#   if PILGLOBALS.QT_Bindings== "PySide6":
#      return(ev.position().toPoint()) 
#
# utility functions --------------------------------------------------------------
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
   if( lbyt & 0x80 ):
      PYGLOBALS.set8Bits(True)
      return ((hbyt & 0x1E) << 6) + (lbyt & 0x7F)
   else:
      PYGLOBALS.set8Bits(False)
      return ((hbyt & 0x1F) << 6) + (lbyt & 0x3F)
#
#  disassemble frame from low and high byte according to 7- oder 8-bit format
#

def disassemble_frame(frame):
    if not PYGLOBALS.Use_8Bits :
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

   if PILGLOBALS.isLinux:
#
#     LINUX
#        
      configpath=os.path.join(userhome,".config",progname)
   elif PILGLOBALS.isWindows:
#
#     Windows
#
      configpath=os.path.join(os.environ['APPDATA'],progname)
   elif PILGLOBALS.isMacos:
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
