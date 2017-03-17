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
# LIF image file classes ---------------------------------------------------
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
#
import platform
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
# decode version number of lifutils or emu7470
#
def decode_version(version_number):
   version=str(version_number)
   major=int(version[0])
   minor=int(version[1:3])
   subversion=int(version[3:5])
   return "{:d}.{:d}.{:d}".format(major,minor,subversion)

def encode_version(version_string):
   v=version_string.split(".")
   major="".join(filter(lambda x: x.isdigit(),v[0]))
   minor="".join(filter(lambda x: x.isdigit(),v[1]))
   subversion="".join(filter(lambda x: x.isdigit(),v[2]))
   return int(major)*10000+ int(minor)*100 + int(subversion)

#
# Program constants --------------------------------------------------
#
# General constants:
#
PRODUCION= True       # Production/Development Version
VERSION="1.5.0"       # pyILPR version number
CONFIG_VERSION="2"    # Version number of pyILPER config file, must be string
#
# PIL-Box communication
#
USE8BITS= True        # use 8 bit data transfer to PIL-Box
TMOUTCMD=1    # time out for PIL-Box commands
TMOUTFRM=0.05 # time out for HP-IL frames

#
# Drive tab - directory listing
#
REFRESH_RATE=1000     # period to check whether a drive was altered and is idle
NOT_TALKER_SPAN=3     # time (s) a drive must be inactive to be concidered as idle
#
# Terminal tab
#
UPDATE_TIMER=25                 # Poll timer (ms) for terminal output queue
CURSOR_BLINK=500 / UPDATE_TIMER # 500 ms cursor blink rate

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
# if Development Version append string to VERSION and "d" to config file name
#
if not PRODUCION:
   VERSION=VERSION+" (Development)"
   CONFIG_VERSION= CONFIG_VERSION+"d"
#
# Standard FONT
#
if isLINUX():
   FONT="Monospace"
else:
   FONT="Courier New"
#
# Min, Max Values for font sizes. Note: MIN value means: automatic!!
#
MIN_TERMCHAR_SIZE=14
MAX_TERMCHAR_SIZE=20
MIN_DIRCHAR_SIZE=12
MAX_DIRCHAR_SIZE=18
#
# Tab types
#
TAB_SCOPE=0
TAB_PRINTER=1
TAB_DRIVE=2
TAB_TERMINAL=3
TAB_PLOTTER=4
TAB_NAMES={TAB_SCOPE:'Scope',TAB_PRINTER:'Printer',TAB_DRIVE:'Drive',TAB_TERMINAL:'Terminal',TAB_PLOTTER:'Plotter'}
