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
# pilpipes object class  ---------------------------------------------
#
#
# Changelog
#

import select
import threading
import os

class PipesError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg = msg
      self.add_msg = add_msg

class cls_pilpipes:

   def __init__(self,inpipename,outpipename):
      self.__inpipename__= inpipename      # name of input pipe
      self.__outpipename__= outpipename    # name of output pipe
      self.__inpipe__= None
      self.__outpipe__= None
      self.__running__ = False             # Connected to pipes
      self.__devices__= []

   def isConnected(self):
      return self.__running__

#
#  Connect to pipes
#
   def open(self):
#
#     create and open pipes
#
      if not os.path.exists(self.__inpipename__):
         os.mkfifo(self.__inpipename__)
      if not os.path.exists(self.__outpipename__):
         os.mkfifo(self.__outpipename__)
      try:
         self.__inpipe__ = os.open(self.__inpipename__, os.O_RDONLY| os.O_NONBLOCK)
         self.__outpipe__ = os.open(self.__outpipename__, os.O_RDWR|os.O_NONBLOCK)
      except OSError as e:
         raise PipesError("cannot open pipes",e.strerror)

#
#  Disconnect from pipes
#
   def close(self):
      self.__running__ = False
      if self.__inpipe__!= None:
         os.close(self.__inpipe__)
         self.__inpipe__= None
      if self.__outpipe__!= None:
         os.close(self.__outpipe__)
         self.__outpipe__= None
      try:
         os.unlink(self.__inpipename__)
         os.unlink(self.__outpipename__)
      except OSError as e:
         raise PipesError("cannot unlink pipes",e.strerror)

#
#  Read HP-IL frame from PIL-Box (2 byte), handle connect to server socket
#
   def read(self):
      readable,writable,errored=select.select([self.__inpipe__],[],[],0.1)
      for s in readable:
         try:
            bytrx = os.read(self.__inpipe__,2)
         except OSError as e:
            raise PipesError("cannot read from pipe",e.strerror)
            return None
         if (len(bytrx) < 2):
            raise PipesError("cannot read from pipe","")
            return None
         return ((bytrx[1] << 8) | bytrx[0])
      return None
#
#     send a IL frame to the virtual loop
#
   def sendFrame(self,frame):
      b=bytearray(2)
      b[0]= frame & 0xFF
      b[1]= frame >> 8
      try:
         l=os.write(self.__outpipe__,b)
      except OSError as e:
         raise PipesError("cannot write to pipe",e.strerror)
#
#  process frame
#
   def process(self,frame):

#
#     process virtual HP-IL devices
#
      for i in self.__devices__:
         frame=i[0].process(frame)
#
#     If received a cmd frame from the PIL-Box send RFC frame to virtual
#     HPIL-Devices
#
#     if (frame & 0x700) == 0x400:
#        for i in self.__devices__:
#           frame=i.process(0x500)
#        self.request_service()
#
#     send frame
#
      self.sendFrame(frame)
#
#     virtual HP-IL device
#
   def register(self, obj, name):
      self.__devices__.append([obj,name])

#
#     get-/set-
#
   def isRunning(self):
      return self.__running__
#
#  def Device list
#
   def getDevices(self):
      return self.__devices__

