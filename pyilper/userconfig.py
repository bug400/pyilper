#!/usr/bin/python3
# -*- coding: utf-8 -*-
# userconfig for Linux
#
# (c) 2015 Joachim Siebold
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
# userconfig class ---------------------------------------------------------
#
# Changelog
# 06.10.2015 jsi:
# - class statement syntax update
# 08.02.2016 jsi:
# - changed os detection to platform.system()
# 14.04.2016 jsi
# - use APPDATA environment variable for config directory on Windows
# - use json to serialize program configuration
# 18.04.2016 jsi
# - use pretty print json
# 18.09.2016 jsi
# - add instance to configuration file name
# 14.10.2016 jsi
# - added filename parameter to __init__
# 17.08.2016 jsi
# - added diagnostics to JSON encode/decode error messages
# 12.12.2021 jsi
# - add configversion parameter to constructor
# - use buildconfigfilename function from pilcore

import json
import os
from  .pilcore import buildconfigfilename

class ConfigError(Exception):
   def __init__(self,msg,add_msg= None):
      self.msg= msg
      self.add_msg = add_msg


class cls_userconfig:

   def __init__(self,progname,filename,configversion,instance,production):
#
#  determine config file name
#
      self.__configfile__,self.__configpath__=buildconfigfilename(progname,filename,configversion,instance,production)

#
#  read configuration, if no configuration exists write default configuration
#
   def read(self,default):
      if not os.path.isfile(self.__configfile__):
         if not os.path.exists(self.__configpath__):
            try:
               os.makedirs(self.__configpath__)
            except OSError as e:
               raise ConfigError("Cannot create path for configuration file", e.strerror)
         try:
            self.write(default)
         except OSError as e:
            raise ConfigError("Cannot write default configuration file", e.strerror)
         return default
      f=None
      try:
         f= open(self.__configfile__,"r")
         config= json.load(f)
      except json.JSONDecodeError as e:
         add_msg="File: "+self.__configfile__+". Error: "+e.msg+" at line: "+str(e.lineno)
         raise ConfigError("Cannot decode configuration data",add_msg)
      except OSError as e:
         raise ConfigError("Cannot read configuration file", e.strerror)
      finally:
         if f is not None:
            f.close()

      return config
#
#  Store configuration, create file if it does not exist
#
   def write(self,config):
      f=None
      try:
         f= open(self.__configfile__,"w")
         json.dump(config,f,sort_keys=True,indent=3)
      except json.JSONDecodeError as e:
         add_msg="File: "+self.__configfile__+". Error: "+e.msg+" at line: "+str(e.lineno)
         raise ConfigError("Cannot encode configuration data",add_msg)
      except OSError as e:
         raise ConfigError("Cannot write to configuration file", e.strerror)
      finally:
         if f is not None:
            f.close()

