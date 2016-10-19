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
# 07.06.2014 jsi
# - introduce configurable baudrate support
# 06.10.2015 jsi:
# - class statement syntax update
# 16.10.2015 jsi:
# - removed SSRQ, CSRQ approach
# - introduced COFI switch to get real IDY frames from the loop (requires firmware 1.6)
# 29.11.2015 jsi:
# - removed activity timer
# 30.11.2015 jsi:
# - introduced idyframe option
# 03.02.2015 jsi
# - set frame timeout to 50 msec
# 07.02.2015 jsi
# - set pilbox call removed
# 22.02.2016 cg
# - send the cmd and not the RFC frame back to the PIL-Box
# 22.03.2016 cg
# - send acknowledge for high byte only at a 9600 baud connection
# 26.04.2016 jsi
# - auto baudrate support, code taken from cgi
# 09.05.2016 jsi
# - reenable baud rate setting in addition to auto baud support
# 11.07.2016 jsi
# - autobaud detection rewritten, hint by cg
# - move constants to pilcore.py
# 13.10.2016 jsi
# - remove unregister function
# - store tab name if device is registered
#
# PIL-Box Commands
#
COFF= 0x497   # initialize in controller off mode
TDIS= 0x494   # disconnect
COFI= 0x495   # switch PIL-Box to transmit real IDY frames

import threading
from .pilrs232 import Rs232Error, cls_rs232
from .pilcore import *

class PilBoxError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg=msg;
      self.add_msg= add_msg


class cls_pilbox:

   def __init__(self,ttydevice,baudrate,idyframe,use8bits):
      self.__running__ = False     # Connected to PIL-Box
      self.__use8bits__= use8bits  # Use 8 bits for transfer
      self.__baudrate__= baudrate  # baudrate of connection or 0 for autodetect
      self.__idyframe__= idyframe  # switch box to send idy frames
      self.__lasth__ = 0           # Copy of last byte sent
      self.__devices__ = []        # list of virtual devices
      self.__tty__= cls_rs232()    # serial device object
      self.__ttydevice__=ttydevice # serial port name

#
#  get connection speed
#
   def getBaudRate(self):
      return(self.__baudrate__)
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
      try:
         if ((ord(bytrx) & 0x3F) != (cmdfrm & 0x3F)):
            raise PilBoxError("PIL-Box command error: illegal retval","")
      except TypeError:
         raise PilBoxError("PIL-Box command error: illegal retval","")
      self.__lasth__= sav

#
#  Connect to PIL-Box in controller off mode
#
   def open(self):
#
#     open serial device, no autobaud mode
#
      if self.__baudrate__ > 0:
         try:
            self.__tty__.open(self.__ttydevice__, self.__baudrate__)
         except Rs232Error as e:
            raise PilBoxError("Cannot connect to PIL-Box", e.value)
         self.__sendCmd__(COFF,TMOUTCMD)

      else:
#
#     open serial device, detect baud rate, use predefined baudrates in
#     BAUDRATES list in reverse order
#
         success= False
         for i in range(len(BAUDRATES)-1,0,-1):
#
#           open device at the beginning of the loop, if error throw exception and exit
#
            baudrate= BAUDRATES[i][1]
            if i== len(BAUDRATES)-1:
               try:
                  self.__tty__.open(self.__ttydevice__, baudrate)
               except Rs232Error as e:
                  raise PilBoxError("Cannot connect to PIL-Box", e.value)
#
#           otherwise reset device and use next baudrate
#
            else:
               try:
                  self.__tty__.flushInput()
                  self.__tty__.setBaudrate(baudrate)
               except Rs232Error as e:
                  raise PilBoxError("Cannot connect to PIL-Box", e.value)
#
#           initialize PIL-Box with current baud rates
#
            try:
               self.__sendCmd__(COFF,TMOUTCMD)
               success= True
               self.__baudrate__=baudrate
               break
            except PilBoxError as e:
               errmsg=e.msg
#
#        no success with any baud rate, throw exception and exit
#
         if not success:
            self.__tty__.close()
            raise PilBoxError("Cannot connect to PIL-Box", errmsg)

      if self.__idyframe__:
         self.__sendCmd__(COFI,TMOUTCMD)
      self.__running__ = True

#
#  Disconnect PIL-Box
#
   def close(self):
      try:
         self.__sendCmd__(TDIS,TMOUTCMD)
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

      if (byt & 0xE0) == 0x20:
#
#        high byte, save it
#
         self.__lasth__ = byt & 0xFF

#
#        send acknowledge only at 9600 baud connection
#
         if self.__baudrate__ == 9600:
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

#
#     process virtual HP-IL devices
#
         for i in self.__devices__:
            frame=i[0].process(frame)
#
#     If received a cmd frame from the PIL-Box send RFC frame to virtual
#     HPIL-Devices
#
         if (frame & 0x700) == 0x400:
            for i in self.__devices__:
               i[0].process(0x500)
#
#     send frame
#
         self.sendFrame(frame)
#        if frame & 0x700 == 0x100 or frame & 0x700 == 0x300 or frame & 0x700 == 0x700:
#           print("srq bit set")

#
#     virtualeHP-IL device
#
   def register(self, obj, name):
      self.__devices__.append([obj,name])
#
#     get-/set-
#
   def isRunning(self):
      return(self.__running__)
