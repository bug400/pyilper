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
# tcpip object class  ---------------------------------------------
#
# Initial version derived from ILPER 1.43
#
# Changelog
#

import time
import select
import socket
import threading


class TcpIpError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg=msg;
      self.add_msg= add_msg


class cls_piltcpip(object):

   def __init__(self,port,remotehost,remoteport):
      self.__port__=port       # port for input connection
      self.__remotehost__=remotehost     # host for output connection
      self.__remoteport__=remoteport     # port for output connection
   
      self.__running__ = False     # Connected to Network
      self.__srq__= False          # PIL-Box SRQ State
      self.__devices__ = []        # list of virtual devices
      self.srqflags = 0            # flag of devices to set srqflag
      self.__devicecounter__=0     # counter of added devices
      self.__timestamp__= time.time()   # time of last activity
      self.__timestamp_lock__= threading.Lock()

      self.__inconn__= None
      self.__outconn__= None
      self.__inaddr__= None
      self.__outaddr__= None
      self.__insocket__= None
      self.__outsocket__= None
      self.__readlist__= []
      self.__outconnected__= False

   def isConnected(self):
      return(self.__outconnected__)

   def gettimestamp(self):
      self.__timestamp_lock__.acquire()
      t= self.__timestamp__
      self.__timestamp_lock__.release()
      return t
#
#  Connect to Network
#
   def open(self):
#
#     open network connections
# 
      host= None
      self.__insocket__= None
      for res in socket.getaddrinfo(host, self.__port__, socket.AF_UNSPEC,
                              socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
         af, socktype, proto, canonname, sa = res
         try:
            self.__insocket__ = socket.socket(af, socktype, proto)
         except OSError as msg:
            self.__insocket__ = None
            continue
         try:
            self.__insocket__.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.__insocket__.bind(sa)
            self.__insocket__.listen(1)
            self.__read_list__=[self.__insocket__]
         except OSError as msg:
            self.__insocket__.close()
            self.__insocket__ = None
            continue
         break
      if self.__insocket__ is None:
         raise TcpIpError("cannot bind to port")
#
#     connect to remote host
#
      self.__outsocket__ = None
      self.__outconnected__= False
      for res in socket.getaddrinfo(self.__remotehost__, self.__remoteport__, socket.AF_UNSPEC, socket.SOCK_STREAM):
         af, socktype, proto, canonname, sa = res
         try:
            self.__outsocket__ = socket.socket(af, socktype, proto)
         except OSError as msg:
            self.__outsocket__ = None
            continue
         try:
            self.__outsocket__.connect(sa)
         except OSError as msg:
            self.__outsocket__.close()
            self.__outsocket__ = None
            continue
         break
      if self.__outsocket__ is None:
         raise TcpIpError("cannot connect to next virtual HP-IL Device")
      self.__outconnected__= True


#
#  Disconnect from Network
#
   def close(self):
      if self.__inconn__ in self.__readlist__:
         self.__inconn__.shutdown(socket.SHUT_RD)
         self.__inconn__.close()
         self.__inconn__= None
      if self.__insocket__ is not None:
         try:
            self.__insocket__.shutdown(socket.SHUT_RD)
         except OSError:
            pass
         self.__insocket__.close()
         self.__insocket__= None
      if self.__outconnected__:
         self.__outsocket__.shutdown(socket.SHUT_WR)
         self.__outsocket__.close()
         self.__outsocket__= None

#
#  Read HP-IL frame from PIL-Box (2 byte), handle connect to server socket
#
   def read(self):
      readable,writable,errored=select.select(self.__read_list__,[],[],0.1)
      for s in readable:
         if s is self.__insocket__:
            self.__inconn__,addr= self.__insocket__.accept()
            self.__read_list__.append(self.__inconn__)
         else:
            bytrx= self.__inconn__.recv(2)
            if bytrx:
               lo= bytrx[0]
               hi=bytrx[1]
               return(socket.ntohs((hi <<8) | lo))
            else:
               raise TcpIpError ("previous virtual HP-IL device  disconnected from pyilper")
      return None

#
#  Enable SRQ Mode 
#
   def setServiceRequest(self):
      self.__srq__= True

#
#  Disable PIL-Box SRQ Mode
#
   def clearServiceRequest(self):
      self.__srq__= False

#
#     send a IL frame to the PIL-Box
#
   def sendFrame(self,frame):
      b=bytearray(2)
      f=socket.htons(frame)
      b[0]= f  & 0xFF
      b[1]= (f & 0xFF00) >> 8
      try:
         self.__outsocket__.send(b)
      except BrokenPipeError:
         raise TcpIpError ("remote program not available","")

#
#  process frame
#
   def process(self,frame):

      self.__timestamp_lock__.acquire()
      self.__timestamp__= time.time()   # time of last activity
      self.__timestamp_lock__.release()
#
#     process virtual HP-IL devices
#
      for i in self.__devices__:
         frame=i.process(frame)
#     self.request_service()
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
         switched=True
         self.__srq__= True
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
