#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pyILPER 1.2.4 for Linux
#
# An emulator for virtual HP-IL devices for the PIL-Box
# derived from ILPER 1.4.5 for Windows
# Copyright (c) 2008-2013   Jean-Francois Garnier
# C++ version (c) 2013 Christoph Gießelink
# Python Version (c) 2015 Joachim Siebold
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
# Script to run pyilper as a module with python -m pyilper [options]
# Starting pyILPER with command line arguments is only possible if called as module
# Some maintenance functions which are called by a command line options are located here
#
# Change log
# 29.03.2026 jsi
# - initial version
# 31.03.2026 jsi
# - diagnostics option added
# 05.04.2026 jsi
# - show version option added
# - Pylint error fixes
# - Renamed PILGLOBALS.Config_Version to PILGLOBALS.ConfigVersion
# 11.04.2026
# - exit on -v option
# - moved moveWindowsConfig to pilcore
#
import os
import sys
import shutil
import argparse
from .pyilpermain import main
from .pilglobals import PILGLOBALS
from .pilconfig import cls_pilconfig, PilConfigError
from .pilcore import buildconfigfilename, moveWindowsConfig
from pyilper import __version__, __isProduction__

# copy configuration data from devel to production and vice versa
# - a development/beta version of pyILPER copies the files of the
#   production version
# - a production version of pyILPER copies the files of the development/beta
#   version
#
def copyConfig(args):
   count=0
#
#  get version numbers
#
   from_config=cls_pilconfig()
   to_config=cls_pilconfig()
   try:
      from_config.open(PILGLOBALS.ConfigVersion,args.instance, not PILGLOBALS.Production,False)
      from_version=from_config.get("pyilper","version","0.0.0")
      to_config.open(PILGLOBALS.ConfigVersion,args.instance, PILGLOBALS.Production,False)
      to_version=to_config.get("pyilper","version","0.0.0")
   except PilConfigError as e:
      print("Error reading pyILPER configuration file(s): ",e.msg+': '+e.add_msg)
      return
   if from_version == "0.0.0":
      print("Error: there are no configuration files to copy")
      return
#
#  ask for confirmation
#
   print("\nW A R N I N G!")
   print("This overwrites the configuration files")
   if PILGLOBALS.Production:
      print("of the production version: ", to_version)
   else:
      print("of the development/beta version: ", to_version)
   print("with the configuration files")
   if PILGLOBALS.Production:
      print("of the development/beta version: ",from_version)
   else:
      print("of the production version: ",from_version)
   inp= input("Continue? (enter 'YES' uppercase): ")
   if inp !="YES":
      print("cancelled")
      return
#
#  now copy configuration files
#
   for name in ['pyilper','penconfig','shortcutconfig']:
      from_filename=buildconfigfilename(name,PILGLOBALS.ConfigVersion,args.instance,not PILGLOBALS.Production)[0]
      if not os.path.isfile(from_filename):
         continue
      to_filename=buildconfigfilename(name,PILGLOBALS.ConfigVersion,args.instance, PILGLOBALS.Production)[0]
      try:
         shutil.copy(from_filename,to_filename)
      except OSError as e:
         print("Error copying file "+from_filename+": "+e.strerror)
         return
      except  shutil.SameFileError as e:
         print("Error copying file "+from_filename+" "+"source and destination file are identical")
         return
      print(from_filename)
      print("copied to:")
      print(to_filename)
      count+=1
   print(count,"files copied. Restart pyILPER without the 'cc' option now")

class ValidateScale(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values < 1.0 or values > 4.0:
            parser.error("Scale must between 1.0 and 4.0.")
        setattr(namespace, self.dest, values)

def start():
   parser=argparse.ArgumentParser(description='Start pyILPER with command line parameters',usage="python -m pyilper [options]")
   parser.add_argument('--instance', '-instance', default="", help="Start a pyILPER instance INSTANCE. This instance has an own configuration file.")
   parser.add_argument('--clean','-clean',action='store_true',help="Start pyILPER with a config file which is reset to defaults")
   parser.add_argument('--cc','-cc',action='store_true',help="Copy configuration from development to production version and vice versa")
   if PILGLOBALS.isWindows:
      parser.add_argument('--mc','-mc',action='store_true',help="Move configuration from AppData to user home directory")
   parser.add_argument('--nohelp','-nohelp',action='store_true',help="Disable online help")
   parser.add_argument('--diag','-diag',action='store_true',help=argparse.SUPPRESS)
   parser.add_argument('--scale','-scale',type=float,action=ValidateScale,help="Force scaling for high-DPI displays. 1.0<=SCALE<=4.0")
   parser.add_argument('--v','-v',action='store_true',help="Show pyILPER version")
   args=parser.parse_args()
#
#  show version
#
   if args.v:
      print("pyILPER ",__version__,end="")
      if(__isProduction__):
         print(" (Production)")
      else:
         print(" (Development)")
      sys.exit(0)
#
#  run -cc and -mc commands
#
   if PILGLOBALS.isWindows: 
      if args.mc: 
         if args.cc:
            print("Error: mc and cc options are mutual exclusive")
            sys.exit(1)
         moveWindowsConfig(False)
         sys.exit(1)
   if args.cc: 
      copyConfig(args)
      sys.exit(1) 
#
#  set scaling, if specified
#
   if args.scale:
      os.putenv('QT_SCALE_FACTOR',str(args.scale))
#
#  set command line arguments to PILGLOBALS and run pyILPER
#
   PILGLOBALS.setArgs(args)
   main()

if __name__ == '__main__':
    rc = 1
    try:
        start()
        rc = 0
    except Exception as e:
        print('Error: %s' % e, file=sys.stderr)
    sys.exit(rc)

