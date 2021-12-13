#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pilconfig for pyILPER
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
# pilconfig class -------------------------------------------
#
# Changelog
# 06.10.2015 jsi:
# - class statement syntax update
# 17.09.2016 jsi:
# - open method introduced
# 14.10.2016 jsi:
# - added filename parameter to cls_userconfig
# 17.08.2017 jsi:
# - assign "" to self.add_msg if parameter is none in PilConfigError
# 20.01.2018 jsi
# - added get_dual method
# 12.02.2018 jsi
# - added the clean parameter to the open method
# 12.12.2021 jsi
# - add configversion parameter to open method
#
from .userconfig import cls_userconfig, ConfigError


class PilConfigError(Exception):
   def __init__(self,msg,add_msg= None):
      self.msg= msg
      if add_msg is None:
         self.add_msg=""
      else:
         self.add_msg = add_msg


class cls_pilconfig:
#
#  initialize: create instance
#
   def __init__(self):
      self.__config__= { } 
      self.__userconfig__ = None
      return

#
#  open: read in the configuration file into the dictionary
#  if the configuration file does not exist, an empty file is created
#  If clean is true do not read the config file
#
   def open(self,name,configversion,instance,production,clean):
      self.__userconfig__= cls_userconfig(name,name,configversion,instance,production)
      if clean:
         return
      try:
         self.__config__= self.__userconfig__.read(self.__config__)
      except ConfigError as e:
         raise PilConfigError(e.msg,e.add_msg)
#
#  Get a key from the configuration dictionary. To initialize a key a default 
#  value can be specified
#
   def get(self,name,param,default=None):
      pname= name+"_"+param
      try:
         p= self.__config__[pname]
      except KeyError:
         if default is None:
            raise PilConfigError("configuration parameter not found: "+pname)
         else:
            self.__config__[pname]= default
            p=default
      return(p)
#
#  Get a key, first a local key, if the value is -1 then get the global key
#
   def get_dual(self,name,param):
      p = self.get(name,param)
      if p == -1:
         p = self.get("pyilper",param)
      return(p)
#
#  Put a key into the configuration dictrionary
#
   def put(self,name,param,value):
      pname= name+"_"+param
      self.__config__[pname]= value 
       
#
#  Save the dictionary to the configuration file
#
   def save(self):
      try:
         self.__userconfig__.write(self.__config__)
      except ConfigError as e:
         raise PilConfigError(e.msg,e.add_msg)
#
#  Get the keys of the configuration file
#
   def getkeys(self):
      return(self.__config__.keys())
#
#  remove an entry
#
   def remove(self,key):
      try:
         del(self.__config__[key])
      except KeyError:
         pass
#
#  create config instance
#
PILCONFIG=  cls_pilconfig()
