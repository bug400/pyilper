#!/usr/bin/python3
# -*- coding: utf-8 -*-
# penconfig for pyILPER
#
# (c) 2016 Joachim Siebold
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
# penconfig class -------------------------------------------
#
# Changelog
# 17.10.2016 jsi:
# - first version (merged)
#
import copy
from .userconfig import cls_userconfig, ConfigError


class PenConfigError(Exception):
   def __init__(self,msg,add_msg= None):
      self.msg= msg
      self.add_msg = add_msg


class cls_penconfig:
#
#  initialize: set penconfig to the default configuration
#
   def __init__(self):
      self.__penconfig__= None
      self.__userconfig__ = None
      return
#
#  default config
#
   def default_config(self):
      return [
       ["Black   0.3 mm", 0x00,0x00,0x00,0xff,1.0],
       ["Red     0.3 mm", 0xff,0x00,0x00,0xff,1.0],
       ["Green   0.3 mm", 0x00,0xff,0x00,0xff,1.0],
       ["Blue    0.3 mm", 0x00,0x00,0xff,0xff,1.0],
       ["Yellow  0.3 mm", 0xff,0xff,0x00,0xff,1.0],
       ["Cyan    0.3 mm", 0x00,0xff,0xff,0xff,1.0],
       ["Magenta 0.3 mm", 0xff,0x00,0xff,0xff,1.0],
       ["Black   0.7 mm", 0x00,0x00,0x00,0xff,2.0],
       ["Red     0.7 mm", 0xff,0x00,0x00,0xff,2.0],
       ["Green   0.7 mm", 0x00,0xff,0x00,0xff,2.0],
       ["Blue    0.7 mm", 0x00,0x00,0xff,0xff,2.0],
       ["Yellow  0.7 mm", 0x00,0xff,0xff,0xff,2.0],
       ["Cyan    0.7 mm", 0x00,0xff,0xff,0xff,2.0],
       ["Magenta 0.7 mm", 0xff,0x00,0xff,0xff,2.0], 
       ["Custom1 0.3 mm", 0x00,0x00,0x00,0xff,1.0],
       ["Custom2 0.3 mm", 0x00,0x00,0x00,0xff,1.0]]
   

#
#  open: read in the pen configuration. If the configuration file does not exist, the 
#  default configuration is written to the pen config file
#
   def open(self,name,version,instance):
      self.__userconfig__= cls_userconfig(name,"penconfig",version,instance)
      try:
         self.__penconfig__= self.__userconfig__.read(self.default_config())
      except ConfigError as e:
         raise PenConfigError(e.msg,e.add_msg)
#
#  Get the list of pens
#
   def get_penlist(self):
      penlist= []
      for p in self.__penconfig__:
         penlist.append(p[0])
      return penlist 
#
# Get the config of the nth pen 
#
   def get_pen(self,n):
      return(self.__penconfig__[n][1:]) 
#
# Get the whole table as a copy
#
   def get_all(self):
      return copy.deepcopy(self.__penconfig__)
       
#
# Populate the whole table
#
   def set_all(self,newlist):
      self.__penconfig__= []
      self.__penconfig__= copy.deepcopy(newlist)

#
#  Save the penconfig to the configuration file
#
   def save(self):
      try:
         self.__userconfig__.write(self.__penconfig__)
      except ConfigError as e:
         raise PenConfigError(e.msg,e.add_msg)
#
PENCONFIG=  cls_penconfig()
