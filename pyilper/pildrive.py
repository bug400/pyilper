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
# - renamed __fetat__ to __fstate__ 
# - renamed __outdta__ to __outdata__ 
# - fixed increase of __ptout__ in __outdta__ (case 3: block)
# - delete zero __ptout__ in DDT section of do_cmd
# - inserte zero __ptout__ in SDA section of do_rdy
# - fixed __fstate__ usage in do_cmd (LAD/SAD)
#
# 03.03.2015 windows i/o compatibility
# - rewritten: __rrec__, __wrec__, __format_disc__ to
#
# 11.03.2015 more improvements and changes of ILPER 1.5
# - fix first sector of LIF-Image
# - set pyhsical medium information, set id
# - not implemented: enable auto extended address switch
#
# 21.03.2015 more header fixes for HP-41
#
# 19.05.2015 getMediumInfo removed
#
# 30.05.2015 fixed error in handling AP, added getstatus
#
# 06.10.2015 jsi:
# - class statement syntax update
#
# 21.11.2015 jsi:
# - removed SSRQ/CSRQ approach
#
# 29.11.2015 jsi:
# - introduced talker activity timer
# - introduced device lock 

import os
import platform
import time
import threading


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

class cls_drive:

   def __init__(self):

#
#     HP-IL data and variables
#
      self.__aid__ = 0x10         # accessory id = mass storage
      self.__defaddr__ = 2        # default address alter AAU
      self.__did__ = None         # device id 
      self.__status__ = 0         # HP-IL status (always 0 here)
      self.__addr__ = 0           # HP-IL primary address (by TAD,LAD)
                                  # bits 0-5=AAD or AEP, bit 7=1 means
                                  # auto address taken
      self.__addr2nd__ = 0        # HP-IL secondary address (by SAD)
                                  # bits 0-5=AES, bit 7 means auto addr taken
      self.__fstate__ = 0         # HP-IL state machine flag
      self.__ptsdi__ = 0          # output pointer for device id
      self.__ptssi__ = 0          # output pointer for hp-il status
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

      self.__lif__= bytearray(12)
      self.__nbe__=0
      self.__buf0__= bytearray(256) # buffer 0
      self.__buf1__= bytearray(256) # buffer 1
      self.__hdiscfile__= ""        # disc file
      self.__isactive__= False    # device active in loop
      self.__islocked__= False    # locked device
      self.__access_lock__= threading.Lock() 
      self.__timestamp__= time.time() # last time of beeing talker

      self.__isWindows__=False    # platform idicator for i/o
      if platform.win32_ver()[0] != "":
         self.__isWindows__= True

   def setpilbox(self,obj):
      self.__pilbox__=obj

   def setactive(self, active):
      self.__isactive__= active

#
#  lock device, all physical reads or writes issue a "no medium error"
#
   def setlocked(self,locked):
      self.__access_lock__.acquire()
      self.__islocked__= locked
      self.__access_lock__.release()

   def ismodified(self):
      self.__access_lock__.acquire()
      if self.__modified__:
        self.__modified__= False
        self.__access_lock__.release()
        return (True, self.__timestamp__)
      else:
        self.__access_lock__.release()
        return (False, self.__timestamp__)

   def acquireaccesslock(self):
      self.__access_lock__.acquire()

   def releaseaccesslock(self):
      self.__access_lock__.release()

   def getstatus(self):
      return [self.__isactive__, self.__did__, self.__aid__, self.__addr__, self.__addr2nd__, self.__fstate__]

#
#  clear drive reset internal pointers
#
   def __cldrv__ (self):
      self.__fpt__= False
      self.__pe__ = 0    
      self.__oc__ = 0   
      self.__access_lock__.acquire()
      self.__modified__= False
      self.__access_lock__.release()
#
#  set new filename (disk change) and medium information
#
   def sethdisk(self,filename,tracks,surfaces,blocks):
      self.__hdiscfile__= filename
      self.__tracks__= tracks
      self.__surfaces__= surfaces
      self.__blocks__= blocks
      self.__lif__[3]= tracks &0xFF
      self.__lif__[7]= surfaces & 0xFF
      self.__lif__[11]= blocks & 0xFF      # fixme this is 0 for cassette medium
      self.__nbe__= tracks*surfaces*blocks
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
      self.__cldrv__()
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
   def __outdata__(self):
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

      if frame == 0x540:
         self.__fstate__= 0x40
      return (frame)

#
#
#  manage HPIL data frames, returns the returned frame
#
   def __do_doe__(self,frame):

      if (self.__fstate__ & 0x80) !=0:
#
#        addressed
#
         if (self.__fstate__ & 0x40) != 0:
#
#           talker
#
            if self.__fstate__ & 0x02 !=0:
#
#              data(SDA) status (SST) or accessory ID (SDI)
#
               if (self.__fstate__ & 0x01) != 0:
                  if self.__ptssi__ > 0:   # SST
                     self.__ptssi__= self.__ptssi__-1 
                     if self.__ptssi__ > 0:
                        frame= (self.__status__ >> (( self.__ptssi__ -1) * 8)) & 0xFF
                  if self.__ptsdi__ > 0:   # SDI
                     if self.__ptsdi__ == len(self.__did__):
                        frame=0
                        self.__ptsdi__=0
                     else:
                        frame= ord(self.__did__ [self.__ptsdi__])
                        self.__ptsdi__= self.__ptsdi__+1
                  if self.__ptssi__ == 0 and self.__ptsdi__ == 0 : # EOT
                     frame= 0x540
                     self.__fstate__= 0x40
               else:
                  frame=self.__outdata__() # SDA
            else:
               frame= 0x540 # end of SAI
               self.__fstate__= 0x40
         else:
#
# listener
#
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
            if (self.__fstate__ & 0x80) != 0:
               self.__cldrv__()
         elif n == 20: # DCL
             self.__cldrv__()

      elif t == 1:  # LAD
         n= n & 31
         if n == 31: # UNL, if not talker then go to idle state
             if (self.__fstate__ & 0x50) == 0: 
                self.__fstate__= 0
         else:       # if MLA go to listen state
             if (self.__fstate__ & 0x80)==0 and  n == (self.__addr__ & 31):
                if (self.__addr2nd__ & 0x80) == 0:
                   self.__fstate__ = 0x80  
                else:
                   self.__fstate__ = 0x20

      elif t == 2:  # TAD  
         n= n & 31
         if n == (self.__addr__ & 31):
            if (self.__addr2nd__ & 0x80) == 0: # if MTA go to talker state
               self.__fstate__= 0x40   # addressed talker
            else:
               self.__fstate__= 0x10   # addressed talker in second. addr.
         else:
            if ( self.__fstate__ & 0x50) != 0:
               self.__fstate__= 0

      elif t == 3: # SAD
         if (self.__fstate__ & 0x30) != 0: # LAD or TAD address matched
            n = n & 31
            if n == (self.__addr2nd__ & 31):
               self.__fstate__<<=2  # switch to addressed listener/talker
            else:
               self.__fstate__=0

      elif t == 4: 
         n= n & 31
         if n == 16: # IFC
            self.__fstate__= 0x00
         elif n == 26: # AAU
            self.__addr__=  self.__defaddr__
            self.__addr2nd__= 0

      elif t == 5: # DDL
         n=n & 31
         if (self.__fstate__ & 0xC0) == 0x80:
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
         if (self.__fstate__ & 0x40) == 0x40:
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
            
#
# HP-IL ready frames
#
   def __do_rdy__(self,frame):

      n= frame & 0xFF
      if n <= 127:
         if ( self.__fstate__ & 0x40) !=0:  # SOT

#           if addressed talker
            if  n == 66:  #NRD
               self.__ptdsi__ = 0
               self.__ptssi__=0
               self.__fstate__ &=0xFD # abort Transfer

            elif n == 96: # SDA
               self.__ptout__= 0
               self.__fstate__= 0xC2
               frame=self.__outdata__()

            elif n == 97: # SST
                # update IL status and return no. of status bytes
                self.__ptssi__ = 1
                if self.__ptssi__ > 0: # response to status request
                   frame = (self.__status__ >> ((self.__ptssi__ -1) * 8)) & 0xFF
                   self.__status__ &= 0xE0
                   self.__fstate__= 0xC0 # active talker

            elif n == 98:  # SDI
               if self.__did__ != None:
                  frame= ord(self.__did__[0])
                  self.__ptsdi__ = 1 # other 2
                  self.__fstate__= 0xC3

            elif n == 99: # SAI
                  frame= self.__aid__ & 0xFF
                  self.__fstate__= 0xC1
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
      return(frame)
