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
# PIL-Box object class  ---------------------------------------------
#
# Initial version derived from ILPER 1.43
#
# Changelog
#
# 09.02.2014 improvements and changes of ILPER 1.45
# - send RFC to virtual devices after each cmd frame
# - high byte detection
# 
# 07.06.2014 baudrate support
#
# 06.10.2015 jsi:
# - class statement syntax update

#
# PIL-Box Commands
#
CON= 0x496    # initialize in controller on mode
COFF= 0x497   # initialize in controller off mode
TDIS= 0x494   # disconnect
SSRQ= 0x49C   # SRQ on
CSRQ= 0x49D   # SRQ off
TMOUTCMD=1    # time out for PIL-Box commands
TMOUTFRM=0.10 # time out for HP-IL frames

import time
import threading
from .pilrs232 import Rs232Error, cls_rs232

class PilBoxError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg=msg;
      self.add_msg= add_msg


class cls_pilbox:

   def __init__(self,ttydevice,baudrate,use8bits):
      self.__running__ = False     # Connected to PIL-Box
      self.__use8bits__= use8bits  # Use 8 bits for transfer
      self.__baudrate__= baudrate  # baudrate
      self.__srq__= False          # PIL-Box SRQ State
      self.__lasth__ = 0           # Copy of last byte sent
      self.__devices__ = []        # list of virtual devices
      self.srqflags = 0            # flag of devices to set srqflag
      self.__devicecounter__=0     # counter of added devices
      self.__tty__= cls_rs232()    # serial device object
      self.__ttydevice__=ttydevice # serial port name
      self.__timestamp__= time.time()   # time of last activity
      self.__timestamp_lock__= threading.Lock()
#
#  send command to PIL-Box, check return value
#
   def __sendCmd__(self,cmdfrm,tmout):
      sav= self.__lasth__
      self.__lasth__ = 0
      try:
         self.sendFrame(cmdfrm)
         bytrx= self.__tty__.rcv(tmout)
      except Rs232Error as e:
         raise PilBoxError("PIL-Box command error:", e.value)
      if bytrx== None:
         raise PilBoxError("PIL-Box command error: timeout","")
      if ((ord(bytrx) & 0x3F) != (cmdfrm & 0x3F)):
         raise PilBoxError("PIL-Box command error: illegal retval","")
      self.__lasth__= sav

   def gettimestamp(self):
      self.__timestamp_lock__.acquire()
      t= self.__timestamp__
      self.__timestamp_lock__.release()
      return t
#
#  Connect to PIL-Box in controller off mode
#
   def open(self):
#
#     open serial device
# 
      try:
         self.__tty__.open(self.__ttydevice__, self.__baudrate__)
      except Rs232Error as e:
         raise PilBoxError("Cannot connect to PIL-Box", e.value)
      self.__sendCmd__(COFF,TMOUTCMD)
      self.__sendCmd__(CSRQ,TMOUTCMD)
      self.__running__ = True

#
#  Disconnect PIL-Box
#
   def close(self):
      try:
         self.__sendCmd__(TDIS,TMOUTCMD)
         self.__sendCmd__(CSRQ,TMOUTCMD)
         self.__running__ = False
      finally:
         self.__tty__.close()    

#
#  Read HP-IL frame from PIL-Box
#
   def read(self):
      try:
         bytrx= self.__tty__.rcv(TMOUTFRM)
      except Rs232Error as e:
         raise PilBoxError("PIL-Box read frame error", e.value)
      return bytrx

#
#  Enable PIL-Box SRQ Mode (PIL-Box sets SRQ bit in short-circuited IDY frames)
#
   def setServiceRequest(self):
      self.__sendCmd__(SSRQ,TMOUTCMD)
      self.__srq__= True

#
#  Disable PIL-Box SRQ Mode
#
   def clearServiceRequest(self):
      self.__sendCmd__(CSRQ,TMOUTCMD)
      self.__srq__= False

#
#     send a IL frame to the PIL-Box
#
   def sendFrame(self,frame):
      if  not self.__use8bits__ :
#
#        use 7-bit characters for maximum compatibility
#
         hbyt = ((frame >> 6) & 0x1F) | 0x20
         lbyt = (frame & 0x3F) | 0x40
      else:
#
#        use  8-bit format for optimum speed
#
         hbyt = ((frame >> 6) & 0x1E) | 0x20
         lbyt = (frame & 0x7F) | 0x80
  
      if  hbyt != self.__lasth__:
#
#        send high part if different from last one
#
         self.__lasth__ = hbyt
         buf=bytearray(2)
         buf[0] = hbyt
         buf[1] = lbyt
      else:
#
#        otherwise send only low part
#
         buf=bytearray(1)
         buf[0] = lbyt
      try:
         self.__tty__.snd(buf)
      except Rs232Error as e:
         raise PilBoxError("PIL-Box send frame error", e.value)

#
#  process frame
#
   def process(self,byt):

      if (byt & 0xE0) == 0x20 :
#
#        high byte, save it
#
         self.__lasth__ = byt & 0xFF
#
#        send acknowledge
#
         b=bytearray(1)
         b[0]= 0x0d
         try:
            self.__tty__.snd(b)
         except Rs232Error as e:
            raise PilBoxError("PIL-Box send frame error", e.value)
      else:
#
#        low byte, build frame according to format
#
         if( byt & 0x80 ):
            frame = ((self.__lasth__ & 0x1E) << 6) + (byt & 0x7F)
         else:
            frame = ((self.__lasth__ & 0x1F) << 6) + (byt & 0x3F)

         self.__timestamp_lock__.acquire()
         self.__timestamp__= time.time()   # time of last activity
         self.__timestamp_lock__.release()
#
#     process virtual HP-IL devices
#
         for i in self.__devices__:
            frame=i.process(frame)
         self.request_service()
#
#     If received a cmd frame from the PIL-Box send RFC frame to virtual
#     HPIL-Devices
#
         if (frame & 0x700) == 0x400:
            for i in self.__devices__:
               frame=i.process(0x500)
            self.request_service()
#
#     send frame
#
         self.sendFrame(frame)

#
#  toogle service request mode of PIL-Box
#
   def request_service(self):
      if self.srqflags and not self.__srq__:
         self.setServiceRequest()
      if not self.srqflags and self.__srq__:
         self.clearServiceRequest()

   def request_service2(self):
      switched=False
      if self.srqflags and not self.__srq__:
         sav= self.__lasth__
         self.__lasth__ = 0
         switched=True
         try:
            self.sendFrame(SSRQ)
         except Rs232Error as e:
            raise PilBoxError("PIL-Box command error:", e.value)
         self.__srq__= True
         self.__lasth__= sav
      return(switched)

#
#     virtualeHP-IL device
#
   def register(self, obj):
      if self.__devicecounter__ > 16:
         raise PilBoxError("Too many virtual HP-IL devices (max 16)","")
      obj.setsrqbit(self.__devicecounter__)
      obj.setpilbox(self)
      self.__devices__.append(obj)
      self.__devicecounter__+=1
#
#     unregister virtual HP-IL device
#

   def unregister(self,n):
      del self.__devices__[n]
#
#     get-/set-
#
   def isRunning(self):
      return(self.__running__) 
