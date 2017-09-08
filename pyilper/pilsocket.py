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
# 07.09.2017 jsi
# - read timeout as parameter, moved process(), sendFrame() and device list handling
#   code to thread object
#

import select
import threading
import socket
import sys
import os

class SocketError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg = msg
      if add_msg== None:
         self.add_msg=""
      else:
         self.add_msg = add_msg

class cls_pilsocket:

   def __init__(self,socketname):
      self.__socketname__= socketname      # name of socket
      self.__socket__= None                # socket
      self.__connection__=None             # connection
      self.__connected__= False
      self.__lasth__= 0
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
      self.__connected__= False
      self.__connection__.close()
#
#  Read byte from socket with timeout, handle connect to server socket
#
   def read(self,timeout):
#
      readable,writable,errored=select.select(self.__serverlist__+self.__clientlist__,[],[],timeout)
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
# write bytes to the socket
#
   def write(self,lbyt,hbyt=None):
      if self.__connection__== None:
         self.__connected__= False
         raise SocketError("cannot send data: ", " no connection")
      if hbyt== None:
         buf=bytearray([lbyt])
      else:
         buf=bytearray([lbyt,hbyt])
      try:
         self.__connection__.sendall(buf)
      except OSError as e:
         raise SocketError("cannot send data:",e.strerror)
