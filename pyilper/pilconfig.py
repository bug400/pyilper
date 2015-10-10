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
#
from .userconfig import cls_userconfig, ConfigError

class PilConfigError(Exception):
   def __init__(self,msg,add_msg= None):
      self.msg= msg;
      self.add_msg = add_msg


class cls_pilconfig:
#
#  initialize: read in the configuration file into the dictionary
#  if the configuration file does not exist, an empty file is created
#
   def __init__(self,version):
      self.__config__= { } 
      self.__userconfig__= cls_userconfig("pyilper",version)
      try:
         self.__config__= self.__userconfig__.read(self.__config__)
      except ConfigError as e:
         raise PilConfigError(e.msg,e.add_msg)
#
#  Get a key from the configuration dictionary. To initialize a key a default 
#  valiue can be specified
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
