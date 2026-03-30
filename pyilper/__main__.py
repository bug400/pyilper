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
#
import os
import sys
import shutil
import argparse
from .pyilpermain import main
from .pilglobals import PILGLOBALS
from .pilconfig import cls_pilconfig
from .pilcore import buildconfigfilename
#
#   move configfiles from %APPDATA%\pyilper to %HOMEDRIVE%%HOMEPATH%\pyilper_config
#
def moveWindowsConfig(args):
   if not PILGLOBALS.isWindows:
      return
   oldConfigPath=os.path.join(os.environ['APPDATA'],"pyilper")
   newConfigPath=os.path.join(os.environ['HOMEDRIVE'],os.environ['HOMEPATH'],PILGLOBALS.StandardConfigDir)
   print("Copy pyILPER configuration files from AppData to ",newConfigPath)
   if not os.path.isdir(oldConfigPath):
      print("Error: Directory "+oldConfigPath+" does not exist. Nothing to copy")
      return
   if os.path.isdir(newConfigPath):
      print("Warning: Directory "+newConfigPath+" already exists. Files in that directory are overwritten!")
      inp= input("Continue? (enter 'YES' uppercase): ")
      if inp !="YES":
         print("cancelled")
         return
   try:
      shutil.copytree(oldConfigPath,newConfigPath,dirs_exist_ok=True)
   except OSError as e:
      print("Error copying config files: "+e.strerror)
      return
   print("pyILPER config files copied from AppData to ",newConfigPath)

#
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
      from_config.open(PILGLOBALS.Config_Version,args.instance, not PILGLOBALS.Production,False)
      from_version=from_config.get("pyilper","version","0.0.0")
      to_config.open(PILGLOBALS.Config_Version,args.instance, PILGLOBALS.Production,False)
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
      from_filename=buildconfigfilename(name,PILGLOBALS.Config_Version,args.instance,not PILGLOBALS.Production)[0]
      if not os.path.isfile(from_filename):
         continue
      to_filename=buildconfigfilename(name,PILGLOBALS.Config_Version,args.instance, PILGLOBALS.Production)[0]
      try:
         shutil.copy(from_filename,to_filename)
      except OSError as e:
         print("Error copying file "+from_filename+": "+e.strerror)
         return
      except  SameFileError as e:
         print("Error copying file "+from_filename+" "+"source and destination file are identical")
         return
      print(from_filename)
      print("copied to:")
      print(to_filename)
      count+=1
   print(count,"files copied. Restart pyILPER without the 'cc' option now")


def start():
   parser=argparse.ArgumentParser(description='Start pyILPER with command line parameters',usage="python -m pyilper [options]")
   parser.add_argument('--instance', '-instance', default="", help="Start a pyILPER instance INSTANCE. This instance has an own configuration file.")
   parser.add_argument('--clean','-clean',action='store_true',help="Start pyILPER with a config file which is reset to defaults")
   parser.add_argument('--cc','-cc',action='store_true',help="Copy configuration from development to production version and vice versa")
   if PILGLOBALS.isWindows:
      parser.add_argument('--mc','-mc',action='store_true',help="Move configuration from AppData to user home directory")
   parser.add_argument('--nohelp','-nohelp',action='store_true',help="Disable online help")
   args=parser.parse_args()
#
#  run -cc and -mc commands
#
   if PILGLOBALS.isWindows: 
      if args.mc: 
         if args.cc:
            print("Error: mc and cc options are mutual exclusive")
            sys.exit(1)
         moveWindowsConfig(args)
         sys.exit(1)
   if args.cc: 
      copyConfig(args)
      sys.exit(1) 
#
#  set command line arguments to PILGLOBALS and run pyILPER
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

