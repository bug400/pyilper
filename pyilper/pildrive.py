#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pyILPER 1.2.1 (python) for Linux
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
# Virtual HP-IL drive obect class -------------------------------------------
#
# Initial release derived from ILPER 1.43 for Windows
#
# Changelog
#
# 09.02.2015 improvements and chages of ILPER 1.5 
# - renamed __fetat__ to __ilstate__ 
# - renamed __outdta__ to __outdata__ 
# - fixed increase of __ptout__ in __outdta__ (case 3: block)
# - delete zero __ptout__ in DDT section of do_cmd
# - inserte zero __ptout__ in SDA section of do_rdy
# - fixed __ilstate__ usage in do_cmd (LAD/SAD)
# 03.03.2015 windows i/o compatibility
# - rewritten: __rrec__, __wrec__, __format_disc__ to
# 11.03.2015 more improvements and changes of ILPER 1.5
# - fix first sector of LIF-Image
# - set pyhsical medium information, set id
# - not implemented: enable auto extended address switch
# 21.03.2015 more header fixes for HP-41
# 19.05.2015 getMediumInfo removed
# 30.05.2015 fixed error in handling AP, added getstatus
# 06.10.2015 jsi:
# - class statement syntax update
# 21.11.2015 jsi:
# - removed SSRQ/CSRQ approach
# 29.11.2015 jsi:
# - introduced talker activity timer
# - introduced device lock 
# 30.11.2015 jsi:
# - fixed idle timer mechanism
# - fixed header of HP82161 medium when formatted with an HP-71
# 02.12.2015 jsi:
# - fixed composition of the implementation byte array (4 byt int not byte!)
# - removed fix header of HP82161 medium when formatted with an HP-71 
# 19.02.2016 jsi
# - refactored and merged new Ildev base class of Christoph Giesselink
# - improved os detection
# 08.07.2016 jsi
# - refactoring: windows platform flag is constructor parameter now

import os
import time
import threading
from .pildevbase import cls_pildevbase


def putLifInt(data,offset,length,value):
   i=length - 1
   while i >= 0:
      data[offset+i]= value & 0xFF
      value=value >> 8
      i-=1
   return

def getLifInt(data,offset,length):
   i=0
   value=0
   while i < length:
      value= (value <<8) + data[offset+i]
      i+=1
   return value

class cls_drive(cls_pildevbase):

   def __init__(self, isWindows):
      super().__init__()

#
#     HP-IL data and variables
#
      self.__aid__ = 0x10         # accessory id = mass storage
      self.__defaddr__ = 2        # default address alter AAU
      self.__did__ = None         # device id 
#
#     disk management variables
#
      self.__devl__ =0            # device listener
      self.__devt__ =0            # device talker
      self.__oc__ = 0             # byte pointer
      self.__pe__ = 0             # record pointer
      self.__pe0__=0
      self.__fpt__ = False        # flag pointer
      self.__flpwr__ = 0          # flag partial write
      self.__ptout__ = 0          # pointer out
      self.__modified__= False    # medium modification flag
      self.__tracks__= 0          # no of tracks of medium
      self.__surfaces__= 0        # no of surfaces of medium
      self.__blocks__= 0          # no of blocks of medium

      self.__lif__= bytearray(12) # device info
      self.__nbe__=0              # last record number
      self.__buf0__= bytearray(256) # buffer 0
      self.__buf1__= bytearray(256) # buffer 1
      self.__hdiscfile__= ""        # disc file
      self.__isactive__= False    # device active in loop
      self.__islocked__= False    # locked device
      self.__access_lock__= threading.Lock() 
      self.__timestamp__= time.time() # last time of beeing talker

      self.__isWindows__= isWindows # true, if Windows platform

#
# public ------------
#

#
#  was image modified since last timestamp
#
   def ismodified(self):
      self.__access_lock__.acquire()
      if self.__modified__:
        self.__modified__= False
        self.__access_lock__.release()
        return (True, self.__timestamp__)
      else:
        self.__access_lock__.release()
        return (False, self.__timestamp__)
#
#  lock device
#
   def acquireaccesslock(self):
      self.__access_lock__.acquire()

#
#  release device
#
   def releaseaccesslock(self):
      self.__access_lock__.release()


#
#  set new filename (disk change) and medium information
#
   def sethdisk(self,filename,tracks,surfaces,blocks):
      self.__hdiscfile__= filename
      self.__tracks__= tracks
      self.__surfaces__= surfaces
      self.__blocks__= blocks
      self.__nbe__= tracks*surfaces*blocks
      k=0
      for i in (24,16,8,0):
         self.__lif__[k]= tracks >> i & 0xFF
         k+=1
      for i in (24,16,8,0):
         self.__lif__[k]= surfaces >> i & 0xFF
         k+=1
      for i in (24,16,8,0):
         self.__lif__[k]= blocks >> i & 0xFF
         k+=1
      return
#
# set aid and did of device
#
   def setdevice(self,did,aid):
      self.__aid__= aid
      if did== "":
         self.__did__= None
      else:
         self.__did__=did
      self.__clear_device__()
      return
#
# private
#
#
# copy buffer 0 to buffer 1
#
   def __copybuf__(self):
      self.__oc__=0
      for i in range (256):
         self.__buf1__[i]= self.__buf0__[i]
      return

#
# exchange buffers
#
   def __exchbuf__(self):
      self.__oc__=0
      for i in range (256):
         x=self.__buf1__[i]
         self.__buf1__[i]= self.__buf0__[i]
         self.__buf0__[i]= x
      return
#
# copy buffer 0 to buffer 1
#
   def __copybuf__(self):
      self.__oc__=0
      for i in range (256):
         self.__buf1__[i]= self.__buf0__[i]
      return

#
# exchange buffers
#
   def __exchbuf__(self):
      self.__oc__=0
      for i in range (256):
         x=self.__buf1__[i]
         self.__buf1__[i]= self.__buf0__[i]
         self.__buf0__[i]= x
      return
# 
# read one sector n* pe (256 bytes) into buf0
#
   def __rrec__(self):
      self.__access_lock__.acquire()
      if self.__islocked__:
         self.__access_lock__.release()
         self.__status__= 20   # no medium error
         return
      try:
         if self.__isWindows__:
            fd= os.open(self.__hdiscfile__,os.O_RDONLY | os.O_BINARY)
         else:
            fd= os.open(self.__hdiscfile__,os.O_RDONLY)
         os.lseek(fd,self.__pe__ * 256, os.SEEK_SET)
         b=os.read(fd,256)
         os.close(fd)
         l=len(b)
#        print("rrec record %d size %d" % (self.__pe__,l))
         for i in range (l):
            self.__buf0__[i]= b[i]
         if l < 256:
            for i in range(l,256):
               self.__buf0__[i]=0x00
      except OSError as e:
         self.__status__= 20
      self.__access_lock__.release()
      return

#
# fix the header if record 0 (LIF header) is written
#
   def __fix_header__(self):
#
#     LIF Version 1 header?
#

      if self.__buf0__[0x00]== 0x80 and self.__buf0__[0x01]== 0x00:
         tracks= getLifInt(self.__buf0__,24,4)
         surfaces=getLifInt(self.__buf0__,28,4)
         blocks=getLifInt(self.__buf0__,32,4)
#
#        wrong media size information (HP firmware bug)?
#
         if(tracks == surfaces and surfaces == blocks):
            putLifInt(self.__buf0__,24,4,self.__tracks__)
            putLifInt(self.__buf0__,28,4,self.__surfaces__)
            putLifInt(self.__buf0__,32,4,self.__blocks__)
#
#       LIF Version 1 fix (for HP41 initialized images)
#
         if self.__buf0__[0x14]!= 0x00 or self.__buf0__[0x15]!= 0x01:
            self.__buf0__[0x14]= 0x00 
            self.__buf0__[0x15]= 0x01
#
#       Fix garbage in label field (for HP41 initialized images)
#
         if self.__buf0__[0x02] != 0x20 and (self.__buf0__[0x02] < 0x41 or self.__buf0__[0x02] > 0x5A):
            for i in range(6):
               self.__buf0__[i+0x02]=0x20

#
#       directory length fix
#
            if self.__buf0__[0x12] & 0x40 != 0:
               self.__buf0__[0x12] &= ~0x40
         
      return
#
# write buffer 0 to one sector n* pe (256 bytes)
#
   def __wrec__(self):
      self.__access_lock__.acquire()
      if self.__islocked__:
         self.__access_lock__.release()
         self.__status__= 20 # no medium error
         return
      try:
         if self.__isWindows__:
            fd= os.open(self.__hdiscfile__, os.O_WRONLY | os.O_BINARY)
         else:
            fd= os.open(self.__hdiscfile__, os.O_WRONLY)
         try:
            os.lseek(fd,self.__pe__ * 256, os.SEEK_SET)
            if self.__pe__ == 0:
               self.__fix_header__()
#           print("wrec record %d" % (self.__pe__))
            os.write(fd,self.__buf0__)
            self.__modified__= True
            self.__timestamp__= time.time()
         except OSError as e:
            self.__status__= 24
         os.close(fd)
      except OSError as e:
         self.__status__= 29
      self.__access_lock__.release()
      return

#
# "format" a lif image file
#
   def __format_disc__(self):
      b= bytearray(256)
      for i in range (0, len(b)):
               b[i]= 0xFF

      self.__access_lock__.acquire()
      if self.__islocked__:
         self.__access_lock__.release()
         self.__status__= 20 # no medium error
         return
      try:
         if self.__isWindows__:
            fd= os.open(self.__hdiscfile__, os.O_WRONLY | os.O_BINARY |  os.O_TRUNC | os.O_CREAT, 0o644)
         else:
            fd= os.open(self.__hdiscfile__, os.O_WRONLY | os.O_TRUNC | os.O_CREAT, 0o644)
         for i in range(0,127):
            os.write(fd,b)
         os.close(fd)
         self.__timestamp__= time.time()
      except OSError:
         self.__status__= 29
      self.__access_lock__.release()
      return
#
#  private (overloaded) -------------------------
#
#  clear drive reset internal pointers
#
   def __clear_device__ (self):
      self.__fpt__= False
      self.__pe__ = 0    
      self.__oc__ = 0   
      self.__access_lock__.acquire()
      self.__modified__= False
      self.__access_lock__.release()

#
# receive data to disc according to DDL command
#
   def __indata__(self,n):

      if (self.__devl__== 0) or (self.__devl__== 2) or (self.__devl__==6):
         self.__buf0__[self.__oc__]= n & 255
         self.__oc__+=1
         if self.__oc__ > 255:
            self.__oc__= 0
            self.__wrec__()
            self.__pe__+=1
            if self.__flpwr__ != 0:
               self.__rrec__()
         else:
           if ( n & 0x200) !=0:
              self.__wrec__()  # END
              if self.__flpwr__ == 0:
                 self.__pe__+=1

      elif self.__devl__ == 1:
         self.__buf1__[self.__oc__] = n & 255
         self.__oc__+=1
         if self.__oc__ > 255:
            self.__oc__ =0

      elif self.__devl__== 3:
         self.__oc__= n & 255

      elif self.__devl__ == 4:
         n= n & 255
         if self.__fpt__:
            self.__pe0__= self.__pe0__ & 0xFF00
            self.__pe0__= self.__pe0__ | n
            if self.__pe0__ < self.__nbe__:
               self.__pe__= self.__pe0__
               self.__status__= 0
            else:
               self.__status__= 28
            self.__fpt__= False
         else:
            self.__pe0__= self.__pe0__ & 255
            self.__pe0__= self.__pe0__ | (n <<8)
            self.__fpt__= True
      return
#
# send data from disc according to DDT command
#
   def __outdata__(self,frame):
      if frame== 0x560 :   # initial SDA
         self.__ptout__=0

      if (self.__devt__== 0) or (self.__devt__==2): # send buffer 0, read
         frame= self.__buf0__[self.__oc__]
         self.__oc__+=1
         if self.__oc__ > 255:
            self.__oc__=0
            self.__rrec__()
            self.__pe__+=1

      elif self.__devt__== 1: # send buffer 1
         frame= self.__buf1__[self.__oc__]
         self.__oc__+=1
         if self.__oc__ > 255:
            self.__oc__=0
            self.__devt__= 15  # send EOT on the next SDA

      elif self.__devt__ == 3:  # send position
         if self.__ptout__ == 0:
            frame= self.__pe__ >> 8
            self.__ptout__+=1
         elif self.__ptout__ == 1:
            frame= self.__pe__ & 255
            self.__ptout__+=1
         elif self.__ptout__ == 2:
            frame=  self.__oc__ & 255
            self.__ptout__+=1
         else:
            frame = 0x540 # EOT

      elif self.__devt__==6: # send implementation
         if self.__ptout__ < 12:
            frame= self.__lif__[self.__ptout__]
            self.__ptout__+=1
         else:
            frame= 0x540 # EOT

      elif self.__devt__ == 7:  # send max record
         if self.__ptout__ == 0:
            frame= self.__nbe__ >> 8
            self.__ptout__+=1
         elif self.__ptout__ == 1:
            frame= self.__nbe__ & 255
            self.__ptout__+=1
         else:
            frame = 0x540 # EOT

      else:
         frame= 0x540

      return (frame)

#
#  extended DDL/DDT commands
#
   def __cmd_ext__(self,frame):
      n= frame & 0xff
      t= n >> 5

      if t == 5: # DDL
         n=n & 31
         if (self.__ilstate__ & 0xC0) == 0x80: # are we listener?
            self.__devl__= n & 0xFF
            if n== 1:
               self.__flpwr__=0
            elif n== 2:
               self.__oc__= 0
               self.__flpwr__=0
            elif n==4:
               self.__flpwr__=0
               self.__fpt__= False
            elif n==5:
               self.__format_disc__()
            elif n == 6:
               self.__flpwr__= 0x80
               self.__rrec__()
            elif n == 7:
               self.__fpt__= False
               self.__pe__ = 0
               self.__oc__ = 0
            elif n == 8:
               self.__wrec__()
               if self.__flpwr__ ==0:
                  self.__pe__+=1
            elif n == 9:
               self.__copybuf__()
            elif n == 10:
                self.__exchbuf__()

      elif t == 6: # DDT
         n= n& 31
         if (self.__ilstate__ & 0x40) == 0x40:
            self.__devt__= n & 0xFF
            if n== 0:
               self.__flpwr__=0
            elif n == 2:
               self.__rrec__()
               self.__oc__=0
               self.__flpwr__=0
               self.__pe__+=1
            elif n == 4:
               self.__exchbuf__()
      return(frame)
