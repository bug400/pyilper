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
# tcpip single socket communication object class and thread class  -----------------------------
#
# Initial version derived from ILPER 1.43
#
# Changelog
# 03.02.2020 jsi:
# - fixed Python 3.8 syntax warning
# 13.11.2017 cg
# - made code more robust against illegal ACK in the pil box and pil box
#   simulation interface when receiving byte data from the pil box
# - removed ACK in pil box simulation after receiving a high byte
# 29.06.2025 jsi
# - Refactoring: moved socket thread class from pilthreads to this file
# - Moved interface configuration GUI from pilwidgets to this file

import select
import socket
from .pilcore import QTBINDINGS,assemble_frame, disassemble_frame, COMTMOUTREAD, COMTMOUTACK,CLASS_INTERFACE_NET
from .pilconfig import PILCONFIG
from .pilthreads import PilThreadError, cls_pilthread_generic, cls_ConfigInterfaceGeneric
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtGui, QtWidgets
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtGui, QtWidgets

MODE_SOCKET=2

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


#
# TCP/IP socket communication thread with DOSBox or virtualbox serial port
#
class cls_PilSocketThread(cls_pilthread_generic):

   def __init__(self, parent,mode):
      super().__init__(parent,mode,CLASS_INTERFACE_NET)

   def enable(self):
      self.send_message("Not connected to socket")
      socket_name=PILCONFIG.get("pyilper","serverport")
      try:
         self.commobject= cls_pilsocket(socket_name)
         self.commobject.open()
      except SocketError as e:
         self.commobject.close()
         self.commobject=None
         raise PilThreadError(e.msg, e.add_msg)
      return
#
#  thread execution 
#         
   def run(self):
      super().run()
#
      try:
#
#        Thread main loop    
#
         while True:
            if self.check_pause_stop():
               break
            if self.commobject.isConnected():
               self.send_message('client connected')
            else:
               self.send_message('waiting for client')
#
#           read byte from socket
#
            ret=self.commobject.read(COMTMOUTREAD)
            if ret is None:
               continue
      
            byt=ord(ret)
#
#           is not a low byte
#
            if (byt & 0xC0) == 0x00:
#
#              check for high byte, else ignore
#
               if (byt & 0x20) != 0:
#
#                 got high byte, save it and continue
#
                  self.__lasth__ = byt & 0xFF
               continue
#
#           low byte, assemble frame according to 7- oder 8 bit format
#
            frame= assemble_frame(self.__lasth__,byt)
#
#           send acknowledge if we received a pil box command
#
            if frame & 0x7F4 == 0x494:
#
#              send only original low byte as acknowledge
#
               lbyt = byt
#
#           process virtual HP-IL devices 
#
            else:
               self.update_framecounter()
               for i in self.devices:
                  frame=i[0].process(frame)
#
#              disassemble answer frame
#
               hbyt, lbyt= disassemble_frame(frame)

               if  hbyt != self.__lasth__:
#
#                 send high part if different from last one
#
                  self.__lasth__ = hbyt
                  self.commobject.write(hbyt)
#
#                 read acknowledge
#
                  b= self.commobject.read(COMTMOUTACK)
                  if b is None:
                     raise PilThreadError("cannot get acknowledge: ","timeout")
                  if ord(b)!= 0x0D:
                     raise PilThreadError("cannot get acknowledge: ","unexpected value")
#
#        otherwise send only low part
#
            self.commobject.write(lbyt)

      except SocketError as e:
         self.send_message('socket disconnected after error. '+e.msg+': '+e.add_msg)
         self.signal_crash()
      self.running=False

class cls_PILSOCKET_Config(cls_ConfigInterfaceGeneric):

   def __init__(self,configName,configNumber, interfaceText):

      super().__init__(configName,configNumber,interfaceText)
      self.serverport= PILCONFIG.get(configName,"serverport")

      self.intvalidator= QtGui.QIntValidator()
      self.splayout=QtWidgets.QGridLayout()
      self.splayout.addWidget(QtWidgets.QLabel("Server port:"),0,0)
      self.edtServerport=QtWidgets.QLineEdit()
      self.edtServerport.setValidator(self.intvalidator)
      self.splayout.addWidget(self.edtServerport,0,1)
      self.edtServerport.setText(str(self.serverport))
      self.vb.addLayout(self.splayout)

      if cls_ConfigInterfaceGeneric.interfaceMode == self.configNumber:
         self.radBut.setChecked(True)
         self.setActive(True)
      else:
         self.radBut.setChecked(False)
         self.setActive(False)

   def setActive(self,flag):
      self.edtServerport.setEnabled(flag)
      self.radBut.setChecked(flag)

   def check_reconnect(self):
      needs_reconnect= False
      needs_reconnect |= self.check_param("serverport", int(self.edtServerport.text()))
      return needs_reconnect
         
   def store_config(self):
      PILCONFIG.put(self.configName,"serverport",int(self.edtServerport.text()))




