#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pyILPER 1.2.1 for Linux
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
# serial device object class --------------------------------------------
#
# Changelog
# 
# 07.06.2014 jsi:
# - baudrate support
# 06.10.2015 jsi:
# - class statement syntax update
# 16.05.2016 jsi
# - use Windows device naming syntax for serial device (hint by cg)
# 03.07.2016 jsi
# - introduced setBaudrate and flushInput methods
# 11.07.2016 jsi
# - use platform function from pilcore.py
#
import serial,time
from .pilcore import isWINDOWS

#
class Rs232Error(Exception):
   def __init__(self,value):
      self.value=value
   def __str__(self):
      return repr(self.value)


class cls_rs232:
 
   def __init__(self,parent=None):
      self.__device__= None
      self.__isOpen__= False
      self.__timeout__=0

#
#  Windows needs much time to reconfigure the timeout value of the serial
#  device, so alter the device settings only if necessary. Give the device
#  some time to settle.
#
   def __settimeout__(self,timeout):
      if timeout != self.__timeout__:
         try:
            self.__ser__.timeout= timeout
         except:
            raise Rs232Error('cannot set timeout value of serial device')
         self.__timeout__=timeout

   def isOpen(self):
      return self.__isOpen__


   def open(self,device,baudrate):
#
#     use Windows device naming (hint by cg)
#
      if isWINDOWS():
         self.__device__="\\\\.\\"+device
      else:
         self.__device__= device

      self.__device__= device
      try:
         self.__ser__= serial.Serial(port=device,baudrate=baudrate,timeout=0.10)
         self.__isOpen__= True
         time.sleep(0.5)
      except:
          self.__device__=""
          raise Rs232Error('cannot open serial device')
   def close(self):
      try:
         self.__ser__.close()
         self.__isOpen__=False
      except:
         raise Rs232Error('cannot close serial device')
      self.__device__=""

   def snd(self,buf):
      try:
         self.__ser__.write(buf)
      except:
         raise Rs232Error('cannot write to serial device')

   def rcv(self,timeout):
      self.__settimeout__(timeout)
      try:
         c= self.__ser__.read(1)
      except:
         raise Rs232Error('cannot read from serial device')
      return c

   def flushInput(self):
      try:
         self.__ser__.flushInput()
      except:
         raise Rs232Error('cannot reset serial device')

   def setBaudrate(self,baudrate):
      try:
         self.__ser__.baudrate= baudrate
      except:
         raise Rs232Error('cannot set baudrate')
