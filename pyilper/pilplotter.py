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
# HP-IL virtual plotter object class ---------------------------------------
#
# Initial release derived from ILPER 1.43 for Windows
#
# Changelog
# 17.10.2017 jsi:
# - initial version
#

import queue
import threading
from .pildevbase import cls_pildevbase

class cls_plotter(cls_pildevbase):

   def __init__(self):
      super().__init__()

      self.__aid__ = 0x60         # accessory id 
      self.__defaddr__ = 5        # default address alter AAU
      self.__did__ = "HP7470A"    # device id
      self.__outbuf__=bytearray(256) # output buffer
      self.__oc__= 0              # byte pointer in output buffer
      self.__disabled__=False     # flag to disable device permanently
#
# public --------
#
#
#  put output into buffer
#
   def setOutput(self,s):
      self.__status_lock__.acquire()
      self.__oc__=0
      for c in reversed(s):
         self.__outbuf__[self.__oc__]= ord(c)
         self.__oc__+=1
      self.__status__ = self.__status__ | 0x10 # set ready for data bit
      self.__status_lock__.release()

   def set_status(self,s):
      if self.__getstatus__() & 0x10:
         s= s | 0x10
 
      self.__setstatus__(s)
      return s
#
#  get status byte
#
   def get_status(self):
      self.__status_lock__.acquire()
      s= self.__status__
      self.__status_lock__.release()
      return s
#
#  disable permanently, if emu7470 is not available
#
   def disable(self):
      self.__disabled__= True
      self.setactive(False)
#
# public (overloaded)
#
   def setactive(self,active):
      if not self.__disabled__:
         super().setactive(active)
      else:
         super().setactive(False)

#
# private (overloaded) --------
#
#
#  output character to plotter
#
   def __indata__(self,frame):

      if self.__callback_output__ != None:
         self.__access_lock__.acquire()
         locked= self.__islocked__
         self.__access_lock__.release()
         if not locked:
            self.__callback_output__(chr(frame & 0xFF))
#
#  clear device: empty output queue and reset plotter
#
   def __clear_device__(self):
      super().__clear_device__()
      self.__status_lock__.acquire()
      self.__oc__=0
      self.__status__= self.__status__ & 0xEF # clear ready for data
      self.__status_lock__.release()

      if self.__callback__clear__ != None:
         self.__callback__clear__() 
      return
#
#  output data from plotter to controller
#
   def __outdata__(self,frame):
      self.__status_lock__.acquire()
      if self.__oc__ > 0:
         self.__oc__-=1
         frame= self.__outbuf__[self.__oc__]
      else:
         frame= 0x540
         self.__status__= self.__status__ & 0xEF # clear ready for data
      self.__status_lock__.release()
      return (frame)
