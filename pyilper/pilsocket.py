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
# pilsocket object class (UNIX domain socket) ------------------------------
#
#
# Changelog
# 25.08.2017 jsi
# - first version
#

import select
import threading
import socket
import sys
import os

class SocketError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg = msg
      self.add_msg = add_msg

class cls_pilsocket:

   def __init__(self,socketname):
      self.__socketname__= socketname      # name of socket
      self.__socket__= None                # socket
      self.__connection__=None             # connection
      self.__running__ = False             # Connected to socket
      self.__connected__= False
      self.__lasth__= 0
      self.__devices__= []
      self.__serverlist__= []
      self.__clientlist__= []

   def isConnected(self):
      return self.__connected__ 

#
#  Connect to socket
#
   def open(self):
#
#     delete existing socket, create socket, bind and listen
#
      self.__serverlist__.clear()
      if os.path.exists(self.__socketname__):
         os.unlink(self.__socketname__)
      try:
         self.__socket__= socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
      except OSError as e:
         raise SocketError("cannot create socket",e.strerror)
      try:
         self.__socket__.bind(self.__socketname__)
      except OSError as e:
         raise SocketError("cannot bind socket",e.strerror)
      try:
         self.__socket__.listen(1)
      except OSError as e:
         raise SocketError("cannot listen for incoming connections",e.strerror)
      self.__serverlist__.append(self.__socket__)

#
#  Disconnect from socket
#
   def close(self):
      self.__running__ = False
      self.__connected__= False
      self.__connection__.close()
#
#  Read byte from socket, handle connect to server socket
#
   def read(self):
#
      readable,writable,errored=select.select(self.__serverlist__+self.__clientlist__,[],[],0.1)
      for s in readable:
         if s== self.__socket__ and not self.__connected__ > 0:
           self.__connection__,addr= s.accept()
           self.__connected__= True
           self.__clientlist__.append(self.__connection__)
         if self.__connected__ and s== self.__connection__:
            bytrx= self.__connection__.recv(1)
            if bytrx:
               return(bytrx)
            else:
               self.__connection__.close()
               self.__clientlist__.remove(self.__connection__)
               self.__connected__= False
               self.__connection__= None
      return None

#
#     send a frame to the socket
#
   def sendFrame(self,frame):
      hbyt = ((frame >> 6) & 0x1E) | 0x20
      lbyt = (frame & 0x7F) | 0x80

      if  hbyt != self.__lasth__:
#
#        send high part if different from last one
#
         self.__lasth__ = hbyt
         buf=bytearray(1)
         buf[0] = hbyt
         self.__connection__.sendall(buf)
#
#        read acknowledge
#
         while True:
            b= self.read()
            if b != None:
               if ord(b)== 0x0D:
                  break
#
#        otherwise send only low part
#
      buf=bytearray(1)
      buf[0] = lbyt
      if self.__connection__== None:
         self.__connected__=False
         raise SocketError("cannot send data:"," no connection")
      try:
         self.__connection__.sendall(buf)
      except OSError as e:
         self.__connected__=False
         self.__connection__.close()
         raise SocketError("cannot write to socket",e.strerror)
#
#  process frame
#
   def process(self,byt):
#
#        high byte, save it
#
      if (byt & 0xE0) == 0x20:
         self.__lasth__ = byt & 0xFF
#
#        send acknowledge
#
         buf=bytearray(1)
         buf[0]= 0x0d
         try:
            self.__connection__.sendall(buf)
         except SocketError as e:
            raise SocketError(e.msg, e.add_msg)
         return

#
#        low byte, build frame according to format
#
      if( byt & 0x80 ):
         frame = ((self.__lasth__ & 0x1E) << 6) + (byt & 0x7F)
      else:
         frame = ((self.__lasth__ & 0x1F) << 6) + (byt & 0x3F)
#
#     send acknowledge if pil box command
#
      if frame & 0x794 == 0x494:
          frame= frame & 0x3F
#
#     process virtual HP-IL devices 
#
      else:
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

