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


import queue
import threading
import time

class cls_terminal:

   def __init__(self):

      self.__aid__ = 0x3E         # accessory id = general interface
      self.__defaddr__ = 8        # default address alter AAU
      self.__did__ = "PILTERM"    # device id
      self.__status__ = 0         # HP-IL status
      self.__addr__ = 0           # HP-IL primary address (by TAD,LAD)
                                  # bits 0-5=AAD or AEP, bit 7=1 means
                                  # auto address taken
      self.__addr2nd__ = 0        # HP-IL secondary address (by SAD)
                                  # bits 0-5=AES, bit 7 means auto addr taken
      self.__fterminal__ =0       # state machine flag
                                  # bit 7, bit 6, bit5, bit 4
                                  # 0      0      0     0 idle
                                  # 0      0      1     0 addressed listener in
                                  #                       second. add. mode
                                  # 0      0      0     1 addressed talker in
                                  #                       second. add. mode
                                  # 1      0      0     0 addressed listen
                                  # 0      1      0     0 addressed talker 
                                  # 1      1      0     0 active talker
                                  # bit 1: SDA, SDI
                                  # bit 0: SST, SDI, SAI 
      self.__ptsdi__ = 0          # output pointer for device id
      self.__ptssi__ = 0          # output pointer for hp-il status
      self.__isactive__= False    # device active in loop
      self.__pilbox__= None       # PIL-Box object
      self.__kbdqueue__= queue.Queue()
      self.__kbdqueue_lock__= threading.Lock()
      self.__status_lock__= threading.Lock()
      self.__islocked__= False
      self.__access_lock__= threading.Lock()
      self.__callback_cldisp__=None
      self.__callback_dispchar__=None
#
# --- public ---
#

   def setpilbox(self,obj):
      self.__pilbox__=obj

   def queueOutput(self,c):
      self.__kbdqueue_lock__.acquire()
      if not self.__kbdqueue__.full():
         self.__kbdqueue__.put(c)
         self.__status__ = 0xE2 # keyboard data available
      self.__kbdqueue_lock__.release()

   def setactive(self, active):
      self.__isactive__= active

   def register_callback_cldisp(self,func):
      self.__callback__cldisp__= func

   def register_callback_dispchar(self,func):
      self.__callback_dispchar__= func

   def getstatus(self):
      return [self.__isactive__, self.__did__, self.__aid__, self.__addr__, self.__addr2nd__, self.__fterminal__]

#
#  lock device, all output is disabled
#
   def setlocked(self,locked):
      self.__access_lock__.acquire()
      self.__islocked__= locked
      self.__access_lock__.release()

#
#  --- private ---
#
   def __getstatus__(self):
      self.__status_lock__.acquire()
      status= self.__status__
      self.__status_lock__.release()
      return(status)
      
   def __setstatus__(self,status):
      self.__status_lock__.acquire()
      self.__status__= status
      self.__status_lock__.release()
      
   
#
#  output characters
#
   def __terminal_str__(self,c):

      if self.__callback_dispchar__ != None:
         self.__access_lock__.acquire()
         locked= self.__islocked__
         self.__access_lock__.release()
         if not locked:
            self.__callback_dispchar__(c)

#
#  clear terminal
#
   def __clear_terminal__(self):
      if self.__callback__cldisp__ != None:
         self.__callback__cldisp__() 
      return

   def __outdta__(self):
      s=self.__getstatus__()
      if s == 0xA2 or s == 0xE2:
         self.__kbdqueue_lock__.acquire()
         outbyte= self.__kbdqueue__.get()
         frame= outbyte
         empty= self.__kbdqueue__.empty()
         if(empty):
            self.__status__= 0 # no data available 
         self.__kbdqueue_lock__.release()
      else:
         frame= 0x540
      if frame == 0x540:
         self.__fterminal__= 0x40 # addressed talker
      return (frame)


#
#  manage HPIL data frames, returns the returned frame
#
   def __do_doe__(self,frame):

      if (self.__fterminal__ & 0x80) !=0: # active talker?

         if (self.__fterminal__ & 0x40) != 0: # addressed talker?
 
            if self.__fterminal__ & 0x02 !=0: # SDA/SDI/SST? 0x02->0x03, set back 0x02
#
               if (self.__fterminal__ & 0x01) != 0: #SST,SDI,SAI
                  if self.__ptssi__ > 0:   # SST
                     self.__ptssi__= self.__ptssi__-1
                     if self.__ptssi__ > 0:
                        frame= (self.__getstatus__() >> (( self.__ptssi__ -1) * 8)) & 0xFF
                  if self.__ptsdi__ > 0:   # SDI
                     if self.__ptsdi__ == len(self.__did__):
                        frame=0
                        self.__ptsdi__=0
                     else: # SDI
                        frame= ord(self.__did__ [self.__ptsdi__])
                        self.__ptsdi__= self.__ptsdi__+1
                  if self.__ptssi__ == 0 and self.__ptsdi__ == 0 : # EOT
                     frame= 0x540
                     self.__fterminal__= 0x40 # set addressed talker
               else: # SDA
                  frame=self.__outdta__() # SDA
            else:
               frame= 0x540 # end of SAI
               self.__fterminal__= 0x40 # set adressed talker
         else:
#
# listener
#
            self.__terminal_str__(chr(frame & 0xFF))

      return(frame)
#
# manage HP-IL command frames
#
   def __do_cmd__(self,frame):

      n= frame & 0xff
      t= n >> 5
      if t == 0:
         if n == 4:   # SDC
            if (self.__fterminal__ & 0x80) != 0: # not addressed listener?
               self.__clear_terminal__()
         elif n == 20: # DCL
             self.__clear_terminal__()
      elif t == 1:  # LAD
         n= n & 31
         if n == 31: # UNL, if not talker then go to idle state
             if (self.__fterminal__ & 0x50) == 0: # not talker ?
                self.__fterminal__= 0 # idle
         else:       # if MLA go to listen state
             if (self.__fterminal__ &0x80) ==0 and  n == (self.__addr__ & 31):
                if (self.__addr2nd__ & 0x80) == 0:
                   self.__fterminal__ = 0x80 # set addressed listener
                else:
                   self.__fterminal__ = 0x20 # set addressed listener second. add mode
      elif t == 2:  # TAD  
         n= n & 31
         if n == (self.__addr__ & 31):
            if (self.__addr2nd__ & 0x80) == 0: # if MTA go to talker state
               self.__fterminal__= 0x40 # set addressed talker
            else:
               self.__fterminal__= 0x10 # set addressed talker, second. add. mode
         else:
            if ( self.__fterminal__ & 0x50) != 0: # addressed talker?
               self.__fterminal__= 0 # idle
      elif t == 3: # SAD
         if (self.__fterminal__ & 0x30) !=0: # addressed talker or listener 2nd addr mode?
            n = n & 31
            if n == (self.__addr2nd__ & 31):
               self.__fterminal__<<=2  # switch to addressed listener/talker
            else:
               self.__fterminal__=0 # idle
      elif t == 4: 
         n= n & 31
         if n == 16: # IFC
            self.__fterminal__= 0x0 # idle
         elif n == 26: # AAU
            self.__addr__=  self.__defaddr__
            self.__addr2nd__= 0
      return(frame)
            
#
# HP-IL ready frames
#
   def __do_rdy__(self,frame):

      n= frame & 0xFF
      if n <= 127:
         if ( self.__fterminal__ & 0x40) !=0:  # SOT, addressed talker?
            if  n == 66:  #NRD
               self.__ptdsi__ = 0
               self.__ptssi__ = 0
               self.__fterminal__ &= 0xFD # abort transfer, clear SDA/SDI
#              it should send an EOT
            elif n == 96: # SDA
               self.__fterminal__= 0xC2 # active talker, SDA/SDI
               frame=self.__outdta__()

            elif n == 97: # SST
                # reset keyboard data available bit
                s= self.__getstatus__()
                s &= 0xBF
                self.__setstatus__(s)
                # update IL status and return no. of status bytes
                self.__ptssi__ = 1
                if self.__ptssi__ > 0: # response to status request
                   frame = (self.__getstatus__() >> ((self.__ptssi__ -1) * 8)) & 0xFF
                   self.__fterminal__= 0xC0 # active talker
            elif n == 98:  # SDI
               if self.__did__ != None:
                  frame= ord(self.__did__[0])
                  self.__ptsdi__ = 1 # other 2
                  self.__fterminal__= 0xC3 # active talker, SDA/SDI, SST/SDI/SAI
            elif n == 99: # SAI
                  frame= self.__aid__ & 0xFF
                  self.__fterminal__= 0xC1 # active talker, SST/SDI/SAI
      else:
         if n < 0x80 +31: # AAD
            if ((self.__addr__ & 0x80) == 0 and self.__addr2nd__ ==0):
               # AAD, if not already an assigned address, take it
               self.__addr__ = n
               frame=frame+1
         elif  (n >= 0xA0 and n < 0xA0 + 31): # AEP
            # AEP, if not already an assigned address and got an AES frame,
            if ((self.__addr__ & 0x80) == 0 and (self.__addr2nd__ & 0x80) != 0):
               # take it
               self.__addr__= n & 0x9F
         elif (n >= 0xC0 and n < 0xC0 +31): # AES
            if (self.__addr__ & 0x80) == 0:
               self.__addr2nd__= n & 0x9F
               frame=frame + 1
      return (frame)
#
#  Process device
#
   def process(self,frame):

      if not self.__isactive__:
         return(frame)
      if (frame & 0x400) == 0:
         frame= self.__do_doe__(frame)
      elif (frame & 0x700) == 0x400:
         frame= self.__do_cmd__(frame)
      elif (frame & 0x700) == 0x500:
         frame= self.__do_rdy__(frame)
#
#     set service request bit if keyboard data available
#
      if self.__getstatus__() & 0x40:
#     if not self.__kbdqueue__.empty():
         if (frame & 0x700) == 0x000:  # data 00x xxxx xxxx -> 001 xxxx xxxx
            frame= frame | 0x100;
         if (frame & 0x700) == 0x200:  # end  01x xxxx xxxx -> 011 xxxx xxxx
            frame= frame | 0x100;
         if (frame & 0x700) == 0x600:  # idy  11x xxxx xxxx -> 111 xxxx xxxx
            frame= frame | 0x100;
      return(frame)
