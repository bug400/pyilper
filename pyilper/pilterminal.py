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
# HP-IL virtual terminal object class ---------------------------------------
#
# Initial release derived from ILPER 1.43 for Windows
#
# Changelog
#
# 09.02.2015: Improvements and fixes from ILPER 1.50
# - fixed __fterminal__ handling in do_cmd LAD/SAD
# - not implemented: auto extended address support switch
# - not implemeted: set/get AID, ID$
#
# 30.05.2015 jsi:
# - fixed error in handling AP, added getstatus
# 06.10.2015 jsi:
# - class statement syntax updates
# 14.11.2015 jsi:
# - idy frame srq bit handling
# 21.11.2015 jsi:
# - removed SSRQ/CSRQ approach
# - set SRQ flag if keyboard buffer is not empty
# 28.11.2015 jsi:
# - removed delay in __outdta__
# 29.11.2015 jsi:
# - introduced device lock
# 29.01.2016 cg:
# - fixed Python syntax error in SST frame handler
# 01.02.2016 jsi:
# - corrected check SDA/SDI/SST? against 0x02 in do_doe
# - improved internal documentation
# 07.02.2016 jsi:
# - refactored to use new pildevbase class
# 08.02.2016 jsi:
# - removed kbdqueue lock, used status_lock instead, rearranged locked code in
#   queueOutput and __outdata__
# - reset keyboard queue if device clear
# - rearrange code in __outdata__, keyboard data avialable flag is cleared after
#   the last byte in the buffer was sent.
# 20.02.2016 jsi:
# - queueOutput now handles complete escape sequences
# - ATTN is ignored if the keyboard queue is not empty
# 06.03.2016 jsi:
# - use no blocking queue get   


import queue
import threading
from .pildevbase import cls_pildevbase

class cls_terminal(cls_pildevbase):

   def __init__(self):
      super().__init__()

      self.__aid__ = 0x3E         # accessory id = general interface
      self.__defaddr__ = 8        # default address alter AAU
      self.__did__ = "PILTERM"    # device id
      self.__kbdqueue__= queue.Queue()
#
# public --------
#
#  put character or escape sequence to keyboard queue
#
   def queueOutput(self,c,esc):
      self.__status_lock__.acquire()
      if not self.__kbdqueue__.full():
         if esc:
#           do not queue ATTN if queue not empty
            if not (self.__status__ & 0x40 and c== 76):
               self.__kbdqueue__.put(0x1B)
               self.__kbdqueue__.put(c)
         else:
            self.__kbdqueue__.put(c)
         self.__status__ = 0xE2 # keyboard data available
      self.__status_lock__.release()

#
# private (overloaded) --------
#
#
#  output character to terminal
#
   def __indata__(self,frame):

      if self.__callback_output__ != None:
         self.__access_lock__.acquire()
         locked= self.__islocked__
         self.__access_lock__.release()
         if not locked:
            self.__callback_output__(chr(frame & 0xFF))
#
#  clear device: empty keyboard queue and reset terminal via callback
#
   def __clear_device__(self):
      super().__clear_device__()
      self.__status_lock__.acquire()
      while True:
         try:
            self.__kbdqueue__.get_nowait() 
            self.__kbdqueue__.task_done()
         except queue.Empty:
            break
      self.__status_lock__.release()
      if self.__callback__clear__ != None:
         self.__callback__clear__() 
      return
#
#  output data from keyboard queue to controller
#
   def __outdata__(self,frame):
      self.__status_lock__.acquire()
      if self.__status__ == 0xE2:
         try:
            outbyte= self.__kbdqueue__.get_nowait()
            self.__kbdqueue__.task_done()
            frame= outbyte
         except queue.Empty:
            self.__status__=0
            self.__status_lock__.release()
            return 0x540
      else:
         frame= 0x540
      self.__status_lock__.release()
      return (frame)
