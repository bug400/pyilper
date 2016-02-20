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
# HP-IL virtual printer object class ----------------------------------------
#
# Initial release derived from ILPER 1.4.3 for Windows
#
# Changelog
#
# 09.02.2015 Improvements and changes of IPLER 1.5
# - fixed __fprinter__ handling in do_cmd LAD/SAD
# - not implemented: auto extended address support switch
# - not implemeted: set/get AID, ID$
# 30.05.2015 fixed error in handling AP, added getstatus
# 06.10.2015 jsi:
# - class statement syntax update
# 23.11.2015 jsi:
# - removed SSRQ/CSRQ approach
# 29.11.2015 jsi:
# - introduced device lock
# 07.02.2016 jsi
# - refactored and merged new Ildev base class of Christoph Giesselink
#
import threading
from .pildevbase import cls_pildevbase


class cls_printer(cls_pildevbase):

   def __init__(self):

      super().__init__()
      self.__aid__ = 0x2E         # accessory id = printer
      self.__defaddr__ = 3        # default address alter AAU
      self.__did__ = "PRINTER"    # device id
      self.__fesc__ = False       # no escape sequence

#
# private (overloaded) ----------
#
#
#  print and handle special characters
#
   def __indata__(self,frame):

      c= chr(frame & 0xFF)
#
#     no escape squence 
#
      if not self.__fesc__:
         t= ord(c)
         if t == 27:
            self.__fesc__ = True
         if not self.__fesc__:
            if self.__callback_output__ != None:
               self.__access_lock__.acquire()
               locked= self.__islocked__
               self.__access_lock__.release()
               if not locked:
                  self.__callback_output__(c)
#
#     ignore escape sequences
#
      else:
         self.__fesc__= False

