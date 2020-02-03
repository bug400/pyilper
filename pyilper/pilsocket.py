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
# tcpip single socket communication object class  -----------------------------
#
# Initial version derived from ILPER 1.43
#
# Changelog
# 03.02.2020 jsi:
# - fixed Python 3.8 syntax warning

import select
import socket

class SocketError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg = msg
      if add_msg is None:
         self.add_msg=""
      else:
         self.add_msg = add_msg

class cls_pilsocket:

   def __init__(self,port):
      self.__port__=port       # port for input connection

      self.__devices__ = []        # list of virtual devices

      self.__serverlist__ = []
      self.__clientlist__= []
      self.__outsocket__= None
      self.__inconnected__= False

   def isConnected(self):
      return self.__inconnected__

#
#  Connect to Network
#
   def open(self):
#
#     open network connections
#
      host= None
      self.__serverlist__.clear()
      self.__clientlist__.clear()
      for res in socket.getaddrinfo(host, self.__port__, socket.AF_UNSPEC,
                              socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
         af, socktype, proto, canonname, sa = res
         try:
            s = socket.socket(af, socktype, proto)
         except OSError as msg:
            s = None
            continue
         try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(sa)
            s.listen(1)
            self.__serverlist__.append(s)
         except OSError as msg:
            s.close()
            continue
      if len(self.__serverlist__) == 0:
         raise SocketError("cannot bind to port","")
#
#  Disconnect from Network
#
   def close(self):
      for s in self.__clientlist__:
         s.close()
      for s in self.__serverlist__:
         s.close()

#
#  Read HP-IL frame from PIL-Box (1 byte), handle connect to server socket
#
   def read(self,timeout):
      readable,writable,errored=select.select(self.__serverlist__ + self.__clientlist__,[],[],timeout)
      for s in readable:
         if self.__serverlist__.count(s) > 0:
            cs,addr = s.accept()
            self.__clientlist__.append(cs)
            self.__inconnected__= True
         else:
            bytrx = s.recv(1)
            if bytrx:
               return (bytrx)
            else:
               self.__clientlist__.remove(s)
               s.close()
               self.__inconnected__= False
      return None
#
# write bytes to the socket
#
   def write(self,lbyt,hbyt=None):
      if self.__inconnected__ == False:
         raise SocketError("cannot send data: ", " no connection")
      if hbyt is None:
         buf=bytearray([lbyt])
      else:
         buf=bytearray([lbyt,hbyt])
      try:
         self.__clientlist__[0].sendall(buf) ## correct ?
      except OSError as e:
         raise SocketError("cannot send data:",e.strerror)

