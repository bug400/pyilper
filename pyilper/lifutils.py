#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# LIF utilities
#
# Python classes to handle LIF image files 
# derived from the LIF utilities of Tony Duell
# Copyright (c) 2008 A. R. Duell
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
# LIF image file classes ---------------------------------------------------
#
# Changelog
# 01.10.2015 cg
# - fixed wrong file type for "ROM75"
# 05.10.2015 jsi:
# - class statement syntax update
# 29.11.2015 jsi:
# - do not check for lif medium type
# 30.11.2015 jsi:
# - raise error in lifopen if not a valid lif image file
# 08.01.2016 jsi:
# - introduced lifcore.py, refactoring
# 09.01.2016 jsi:
# - added filetypes
# 08.02.2016 jsi:
# - changed os detection to platform.system()
# 11.07.2016 jsi:
# - use functions from pilcore.py for platform detection
# 04.12.2016 jsi
# - allow directory not starting at record 2
#
import os
from .lifcore import *
from .pilcore import isWINDOWS

class LifError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg=msg
      self.add_msg= add_msg

class cls_LifDir:

   def __init__(self,liffile):
      self.liffile=liffile
      self.lifdir= { }
      self.lastblock=0
      self.num_entries=0
      self.cur_entry= None
      self.isOpen= False

   def open(self):
      recno= self.liffile.dir_start
      lastdirrec= recno+self.liffile.dir_length-1
      i=0
      while True:
         if recno > lastdirrec:
            break
         if i == 0:
            self.liffile.rrec(recno)
         entry= bytearray(32)
         for j in range(32):
            entry[j]= self.liffile.buffer[j+i*32]
         ft= getLifInt(entry,10,2)
         if ft == 0xFFFF:
            break
         if self.cur_entry is None:
            self.cur_entry=0
         else:
            self.cur_entry+=1
         self.lifdir[self.cur_entry]= entry
         if ft != 0x0000:
            self.num_entries+=1
            start_block= getLifInt(self.lifdir[self.cur_entry],12,4)
            alloc_blocks= getLifInt(self.lifdir[self.cur_entry],16,4)
            endblock= start_block+alloc_blocks
            if endblock > self.lastblock:
               self.lastblock= endblock
         i+=1
         if i==8:
            i=0
            recno+=1
            
      if self.lastblock == 0:
         self.lastblock= self.liffile.dir_start+self.liffile.dir_length-1
      self.isOpen=True

   def rewind(self):
      if not self.isOpen:
         raise LifError("Directory not open","")
      self.cur_entry=0

   def getNextEntry(self):
      if self.num_entries==0:
        return []
      if self.cur_entry == len(self.lifdir):
        return []
      while True:
         ft= getLifInt(self.lifdir[self.cur_entry],10,2)
         if ft != 0x0000:
            break
         self.cur_entry+=1
         if self.cur_entry == len(self.lifdir):
            return[]
      name=getLifString(self.lifdir[self.cur_entry],0,10)
      start_block= getLifInt(self.lifdir[self.cur_entry],12,4)
      alloc_blocks= getLifInt(self.lifdir[self.cur_entry],16,4)
      datetime=getLifDateTime(self.lifdir[self.cur_entry],20)
      tl= self.getTypeLen()
      self.cur_entry+=1
      return [name, ft,start_block, alloc_blocks, datetime, tl[0], tl[1]]

   def getTypeLen(self):
      e=self.lifdir[self.cur_entry]
      ft=getLifInt(e,10,2)
#    LIF1 (Text)
      if ft == 1 or ft== 0xE0D1:
         t=get_finfo_type(ft)[0]
         l=getLifInt(e,16,4)* 256
#     D-LEX
      elif ft== 0x00FF:
         t=get_finfo_type(ft)[0]
         l= int((( e[28] + (e[29] <<8) + (e[30]<<16))+1)/2)
#     SDATA
      elif ft == 0xE0D0:
         t=get_finfo_type(ft)[0]
         l= getLifInt(e,28,2)*8
#     HP-71 Data file
      elif ft== 0xE0F0 or ft== 0xE0F1:
         t=get_finfo_type(ft)[0]
         l= (e[28] + (e[29] <<8)) * (e[30] + (e[31]<<8))
#     HP-71 BIN
      elif ft >= 0xE204 and ft<= 0xE207:
         t=get_finfo_type(ft)[0]
         l= int((( e[28] + (e[29] <<8) + (e[30]<<16))+1)/2)
#     HP-71 LEX
      elif ft>= 0xE208 and ft <= 0xE20B:
         t=get_finfo_type(ft)[0]
         l= int((( e[28] + (e[29] <<8) + (e[30]<<16))+1)/2)
#     HP-71 KEY
      elif ft==0xE20C or ft== 0xE20D:
         t=get_finfo_type(ft)[0]
         l= int((( e[28] + (e[29] <<8) + (e[30]<<16))+1)/2)
#     HP-71 Basic
      elif ft>= 0xE214 and ft<=0xE217:
         t=get_finfo_type(ft)[0]
         l= int((( e[28] + (e[29] <<8) + (e[30]<<16))+1)/2)
#     HP-71 Forth
      elif ft>= 0xE218 and ft<=0xE21B:
         t=get_finfo_type(ft)[0]
         l=getLifInt(e,16,4)* 256
#     HP-71 ROM
      elif ft == 0xE21C:
         t=get_finfo_type(ft)[0]
         l= int((( e[28] + (e[29] <<8) + (e[30]<<16))+1)/2)
#     HP-71 Graphics
      elif ft == 0xE222:
         t=get_finfo_type(ft)[0]
         l= int((( e[28] + (e[29] <<8) + (e[30]<<16))+1)/2)
#     HP-71 Address
      elif ft == 0xE224:
         t=get_finfo_type(ft)[0]
         l= int((( e[28] + (e[29] <<8) + (e[30]<<16))+1)/2)
#     HP-71 Symbol file??
      elif ft == 0xE22E:
         t=get_finfo_type(ft)[0]
         l= int((( e[28] + (e[29] <<8) + (e[30]<<16))+1)/2)
#     HP-41 WALL with X-MEM
      elif ft== 0xE020:
         t=get_finfo_type(ft)[0]
         l= (getLifInt(e,28,2)*8)+1
#     HP-41 X-MEM
      elif ft== 0xE030:
         t=get_finfo_type(ft)[0]
         l= (getLifInt(e,28,2)*8)+1
#     HP-41 WALL
      elif ft== 0xE040:
         t=get_finfo_type(ft)[0]
         l= (getLifInt(e,28,2)*8)+1
#     HP-41 KEYS
      elif ft== 0xE050:
         t=get_finfo_type(ft)[0]
         l= (getLifInt(e,28,2)*8)+1
#     HP-41 Status
      elif ft== 0xE060:
         t=get_finfo_type(ft)[0]
         l= (getLifInt(e,28,2)*8)+1
#     HP-41 ROM/MLDL dump
      elif ft== 0xE070:
         t=get_finfo_type(ft)[0]
         l= (getLifInt(e,28,2)*8)+1
#     HP-41 FOCAL program
      elif ft== 0xE080:
         t=get_finfo_type(ft)[0]
         l= getLifInt(e,28,2)+1
#     HP-75 text
      elif ft== 0xE052:
         t=get_finfo_type(ft)[0]
         l= getLifInt(e,16,4)*256
#     HP-75 Appointments
      elif ft== 0xE053:
         t=get_finfo_type(ft)[0]
         l= getLifInt(e,16,4)*256
#     HP-75 Data
      elif ft== 0xE058:
         t=get_finfo_type(ft)[0]
         l= getLifInt(e,16,4)*256
#     HP-75 LEX
      elif ft== 0xE089:
         t=get_finfo_type(ft)[0]
         l= getLifInt(e,16,4)*256
#     HP-75 Visicalc
      elif ft== 0xE08A:
         t=get_finfo_type(ft)[0]
         l= getLifInt(e,16,4)*256
#     HP-75 Basic
      elif ft== 0xE0FE or ft==0xE088:
         t=get_finfo_type(ft)[0]
         l= getLifInt(e,16,4)*256
#     HP-75 ROM
      elif ft== 0xE08B:
         t=get_finfo_type(ft)[0]
         l= getLifInt(e,16,4)*256
#     other ...
      else:
         t= "0x{:4X}".format(ft)
         l= getLifInt(e,16,4)* 256
      return [t , l]

      

class cls_LifFile:

   def __init__(self):
      self.filename= None           # Name of LIF File
      self.filehd= None             # File descriptor
      self.isWindows=False          # platform idicator for i/o
      self.isLifFile= False         # Valid lif file
      self.buffer= bytearray(256)   # read write buffer
      self.header= bytearray(256)   # lif header
      self.label = None
      self.dir_start=0
      self.dir_length=0
      self.no_tracks=0
      self.no_surfaces=0
      self.no_blocks=0
      if isWINDOWS():
         self.isWindows= True

   def set_filename(self,name):
      self.filename= name

   def __open__(self):
      if self.filename is None:
         raise LifError("No file specified","")
      try:
         if self.isWindows:
            self.filefd= os.open(self.filename,os.O_RDONLY | os.O_BINARY)
         else:
            self.filefd= os.open(self.filename,os.O_RDONLY)
      except OSError as e:
         raise LifError("Cannot open file",e.strerror)
        
   def __close__(self):
      if self.filefd is None:
         raise LifError("File not open","")
      try:
          os.close(self.filefd)
      except OSError as e:
          raise LifError("Cannot close file",e.strerror)


   def rrec(self,recno):
      try:
         os.lseek(self.filefd,recno * 256, os.SEEK_SET)
         b=os.read(self.filefd,256)
         if len(b) < 256:
            raise LifError("Cannot read from file","")
         for i in range (256):
            self.buffer[i]= b[i]
      except OSError as e:
         raise LifError("Cannot read from file",e.strerror)


   def lifopen(self):
      self.__open__()
      try:
         self.rrec(0)
      except LifError:
         return
      for i in range(256):
         self.header[i]= self.buffer[i]
      lifmagic= getLifInt(self.header,0,2)
      liftype= getLifInt(self.header,20,2)
      dirstart=getLifInt(self.header,8,4)
#     if lifmagic == 0x8000 and liftype == 1 and dirstart == 2:
#     if lifmagic == 0x8000 and dirstart == 2:
      if lifmagic == 0x8000:
         self.isLifFile= True
         self.dir_start= dirstart
         self.dir_length= getLifInt(self.header,16,4)
         self.no_tracks= getLifInt(self.header,24,4)
         self.no_surfaces= getLifInt(self.header,28,4)
         self.no_blocks= getLifInt(self.header,32,4)
         self.label= getLifString(self.header,2,6)
         self.initdatetime= getLifDateTime(self.header,36)
      else:
         raise LifError("No valid LIF image file")

   def lifclose(self):
      self.__close__()

   def getLifHeader(self):
      if self.isLifFile:
         return([self.dir_start, self.dir_length,self.no_tracks, self.no_surfaces,self.no_blocks,self.label,self.initdatetime])
      else:
         return None

