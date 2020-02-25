#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pyILPER 1.6.1 for Linux
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
# HP-IL virtual device base object class ---------------------------------------
#
# Derived fom IldevBase.cpp from Christoph Gießelink
#
# Changelog
#
# 16.02.2016 jsi:
# - merged new Ildev base class of Christoph Gießelink
# 01.03.2016 cg:
# - removed EOT response from __outdata__ to implement "no response" feature
# 05.03.2016 jsi:
# - wrong variable name __ptdsi__ corrected
# - improved getstatus, use accesss lock and return ilstate as text
# 02.08.2017 jsi:
# - class variable for length of status information introduced, alter
#   statement to clear service request bit to handle multiple byte status data
#   changed the order of status bytes output (least significant byte first)
# - reset service request bit, if DCL odr SDC
# 07.08.2017 jsi:
# - register functions for callbacks removed
# 10.08.2017 jsi
# - check if self.__did__ != "" and not != None
# 05.10.2017 jsi:
# - reset device address if device was reactivated an an HP-IL addressing
#   operation happened in the meantime
# 18.12.2017 jsi:
# - check whether the sent and the incoming data byte are identical if a
#   virtual device is talker. Send ETE if not.
# - fix a bug in handling the SRQ bit in DOE frames
# Both changes are courtesy of Christoph Gießelink
# 16.01.2018 jsi:
# - adapted to new local config parameters for color scheme and terminal width


import threading

class cls_pildevbase:

   def __init__(self):

      self.__aid__ = 0x00          # accessory id 
      self.__defaddr__ = 0         # default address alter AAU
      self.__did__ = ""            # device id
      self.__status__ = 0          # HP-IL status
      self.__addr__ = 0            # HP-IL primary address (by TAD,LAD)
                                   # bits 0-5=AAD or AEP, bit 7=1 means
                                   # auto address taken
      self.__addr2nd__ = 0         # HP-IL secondary address (by SAD)
                                   # bits 0-5=AES, bit 7 means auto addr taken
      self.__ilstate__ =0          # state machine flag
                                   # bit 7, bit 6, bit5, bit 4
                                   # 0      0      0     0 idle
                                   # 0      0      1     0 addressed listener in
                                   #                       second. add. mode
                                   # 0      0      0     1 addressed talker in
                                   #                       second. add. mode
                                   # 1      0      0     0 addressed listener
                                   # 0      1      0     0 addressed talker 
                                   # bit 0 or bit 1 set    active takler
                                   # bit 1: SDA, SDI
                                   # bit 0: SST, SDI, SAI, NRD
      self.__talker_frame__=0      # frame sent as talker
      self.__ptsdi__ = 0           # output pointer for device id
      self.__status_len__=1        # length of device status in bytes
      self.__ptssi__ = 0           # output pointer for hp-il status
      self.__isactive__= False     # device active in loop
      self.__addr_framecounter__=0 # framecounter when device got an address
      self.__threadobject__=None   # reference to the thread object
      self.__status_lock__= threading.Lock()
      self.__islocked__= False
      self.__access_lock__= threading.Lock()
#
# --- public functions ---
#
#  set device active/inactive. If the device becomes active check if an AAU,
#  AAD, AEP or AES happened in the mean time. In this case reset the device
#  address
#
   def setactive(self, active):
      if not self.__isactive__ and active:
         if self.__addr_framecounter__ != self.__threadobject__.get_addr_framecounter():
            self.__addr__=0
            self.__addr2nd__=0
      self.__isactive__= active
#
#  set object reference to thread object
#
   def setThreadObject(self,obj):
      self.__threadobject__= obj
#
#  set local and update globel addr_framecounter
#
   def update_addr_framecounter(self):
      self.__addr_framecounter__= self.__threadobject__.get_framecounter()
      self.__threadobject__.update_addr_framecounter(self.__addr_framecounter__)
#
#  return device status
#
   def getstatus(self):
      self.__access_lock__.acquire()
      status="idle"
      if self.__ilstate__ & 0x03:
         status="act. talker"
      else:
         if self.__ilstate__ & 0xA0:
            status="addr. listener"
         elif self.__ilstate__ & 0x50:
            status="addr. talker"

      ret= [self.__isactive__, self.__did__, self.__aid__, self.__addr__, self.__addr2nd__, status]
      self.__access_lock__.release()
      return ret

#
#  lock device, all output is disabled
#
   def setlocked(self,locked):
      self.__access_lock__.acquire()
      self.__islocked__= locked
      self.__access_lock__.release()

#
#  Process device
#
   def process(self,frame):

#
#     if device is not active, return
#
      if not self.__isactive__:
         return(frame)
#
#     process frames
#
      if (frame & 0x400) == 0:
         frame= self.__do_doe__(frame)
      elif (frame & 0x700) == 0x400:
         frame= self.__do_cmd__(frame)
      elif (frame & 0x700) == 0x500:
         frame= self.__do_rdy__(frame)
#
#     set service request bit if data available status bit set
#
      if self.__getstatus__() & 0x40:
         if (frame & 0x700) == 0x000:  # data 00x xxxx xxxx -> 001 xxxx xxxx
            frame= frame | 0x100
         if (frame & 0x700) == 0x200:  # end  01x xxxx xxxx -> 011 xxxx xxxx
            frame= frame | 0x100
         if (frame & 0x700) == 0x600:  # idy  11x xxxx xxxx -> 111 xxxx xxxx
            frame= frame | 0x100
      return(frame)

#
#  --- private ---
#
#
#  get status byte from device thread safe
#
   def __getstatus__(self):
      self.__status_lock__.acquire()
      status= self.__status__
      self.__status_lock__.release()
      return(status)
#
# set status byte of device thread safe
#
   def __setstatus__(self,status):
      self.__status_lock__.acquire()
      self.__status__= status
      self.__status_lock__.release()
#
#  output data stub
#
   def __outdata__(self,frame):
      return frame

#
#  input data stub
#
   def __indata__(self,frame):
      return

#
#  device clear stub
#
   def __clear_device__(self):
      # reset service request bit
      s= self.__getstatus__()
      s &= ~ 0x40
      self.__setstatus__(s)
      return
#
#  stub for extended sad commands
#
   def __cmd_sad_ext__(self,frame):
      return frame

#
# stub for extended commands
#
   def __cmd_ext__(self,frame):
      return frame

#
#  manage HPIL data frames, returns the returned frame
#
   def __do_doe__(self,frame):
      talker_error= False

      if (self.__ilstate__ & 0xC0) == 0x40: # addressed talker?

         if (self.__ilstate__ & 0x03) != 0: # active talker?

#           compare last talker frame with actual frame without SRQ bit
            talker_error = ((frame & 0x6FF) != (self.__talker_frame__ &0x6FF))

#           data (SDA) status (SST) or accessory ID (SDI)
            if (not talker_error) and (self.__ilstate__ & 0x02 !=0): # talker

#              save current SRQ bit
               SrqBit= frame & 0x100 

#              status (SST) or accessory ID (SDI)
               if (self.__ilstate__ & 0x01) != 0: 

#                 0x43: active talker (multibyte status)
                  if self.__ptssi__ > 0:   # SST
                     self.__ptssi__= self.__ptssi__-1
                     if self.__ptssi__ > 0:
                        frame= (self.__getstatus__() >> (( self.__status_len__-self.__ptssi__ ) * 8)) & 0xFF
                  if self.__ptsdi__ > 0:   # SDI
                     if self.__ptsdi__ == len(self.__did__):
                        frame=0
                        self.__ptsdi__=0
                     else: # SDI
                        frame= ord(self.__did__ [self.__ptsdi__])
                        self.__ptsdi__= self.__ptsdi__+1
                  if self.__ptssi__ == 0 and self.__ptsdi__ == 0 : 
#                    EOT for SST and SDI
                     frame= 0x540
               else: # 0x42 active talker (data)
                  frame=self.__outdata__(frame) # SDA
#              a set SRQ bit doesn't matter on ready class frames
               frame |= SrqBit
            else: # 0x41 active talker (single byte status)
               frame= 0x540 # end of SAI or NRD or talker error

         if frame == 0x540: # EOT
#           check for error and set ETE frame
            if talker_error:
               frame= 0x541 # ETE
            self.__ilstate__ &= ~ 0x03 # delete active talker
         self.__talker_frame__= frame

      if (self.__ilstate__ & 0xC0)==0x80:  # listener
            self.__indata__(frame)
      return(frame)
#
# manage HP-IL command frames
#
   def __do_cmd__(self,frame):

      n= frame & 0xff
      t= n >> 5
      if t == 0:
         if n == 4:   # SDC
            if (self.__ilstate__ & 0x80) != 0: # listener
               self.__clear_device__()
         elif n == 20: # DCL
             self.__clear_device__()
      elif t == 1:  # LAD
         n= n & 31
         if n == 31: # UNL, if not talker then go to idle state
             if (self.__ilstate__ & 0xA0) != 0: # not talker ?
                self.__ilstate__ &= 0x50 # idle
         else:       # if MLA go to listen state
             if (self.__ilstate__ &0x80) ==0 and  n == (self.__addr__ & 31):
                if (self.__addr2nd__ & 0x80) == 0:
                   self.__ilstate__ = 0x80 # set addressed listener
                else:
                   self.__ilstate__ = 0x20 # set addressed listener second. add mode
      elif t == 2:  # TAD  
         n= n & 31
         if n == (self.__addr__ & 31):
            if (self.__addr2nd__ & 0x80) == 0: # if MTA go to talker state
               self.__ilstate__= 0x40 # set addressed talker
            else:
               self.__ilstate__= 0x10 # set addressed talker, second. add. mode
         else:
            if ( self.__ilstate__ & 0x50) != 0: # addressed talker?
               self.__ilstate__ &= 0xA0 # idle
      elif t == 3: # SAD
         if (self.__ilstate__ & 0x30) !=0: # addressed talker or listener 2nd addr mode?
            n = n & 31
            if n == (self.__addr2nd__ & 31):
               self.__ilstate__<<=2  # switch to addressed listener/talker
            else:
               self.__ilstate__=0 # idle
         else:
            frame= self.__cmd_sad_ext__(frame)
      elif t == 4: 
         n= n & 31
         if n == 16: # IFC
            self.__ilstate__= 0x0 # idle
         elif n == 26: # AAU
            self.update_addr_framecounter()
            self.__addr__=  self.__defaddr__
            self.__addr2nd__= 0
      else:
         frame= self.__cmd_ext__(frame)
      return(frame)
            
#
# HP-IL ready frames
#
   def __do_rdy__(self,frame):

      n= frame & 0xFF
      if n <= 127:
         if ( self.__ilstate__ & 0x40) !=0:  # SOT, addressed talker?
            if  n == 66:  #NRD
               self.__ptsdi__ = 0
               self.__ptssi__ = 0
               self.__ilstate__ = 0x41 # abort transfer, clear SDA/SDI

            elif n == 96: # SDA
               frame=self.__outdata__(frame)
               if frame != 0x560: # not sda received data
                  self.__ilstate__= 0x42 # active talker, SDA/SDI
                  self.__talker_frame__= frame # last talker frame
            elif n == 97: # SST
                # reset service request bit
                s= self.__getstatus__()
                s &= ~ 0x40
                self.__setstatus__(s)
                # update IL status and return no. of status bytes
                self.__ptssi__ = self.__status_len__
                if self.__ptssi__ > 0: # response to status request
                   frame = (self.__getstatus__() >> ((self.__status_len__-self.__ptssi__) * 8)) & 0xFF
                   self.__ilstate__= 0x43 # active talker
                   self.__talker_frame__= frame # last talker frame
            elif n == 98:  # SDI
               if self.__did__ != "":
                  frame= ord(self.__did__[0])
                  self.__ptsdi__ = 1 # other 2
                  self.__ilstate__= 0x43 # active talker, SDA/SDI, SST/SDI/SAI
                  self.__talker_frame__= frame
            elif n == 99: # SAI
                  frame= self.__aid__ & 0xFF
                  self.__ilstate__= 0x41 # active talker, SST/SDI/SAI
                  self.__talker_frame__= frame
      else:
         if n < 0x80 +31: # AAD
            if ((self.__addr__ & 0x80) == 0 and self.__addr2nd__ ==0):
               # AAD, if not already an assigned address, take it
               self.update_addr_framecounter()
               self.__addr__ = n
               frame=frame+1
         elif  (n >= 0xA0 and n < 0xA0 + 31): # AEP
            # AEP, if not already an assigned address and got an AES frame,
            if ((self.__addr__ & 0x80) == 0 and (self.__addr2nd__ & 0x80) != 0):
               # take it
               self.update_addr_framecounter()
               self.__addr__= n & 0x9F
         elif (n >= 0xC0 and n < 0xC0 +31): # AES
            if (self.__addr__ & 0x80) == 0:
               self.update_addr_framecounter()
               self.__addr2nd__= n & 0x9F
               frame=frame + 1
      return (frame)
