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
# tcpip object class  and tcpip thread object class ---------------------------------------------
#
# Initial version derived from ILPER 1.43
#
# Changelog
#
# 24.09.2015 cg
# - added real IPv4/IPv6 dual stack mode
# - reconnecting server and client work now
# - broken loop don't crash connection any more
# - removed some unused class variables
# 05.10.2015 jsi
# - class statement syntax update
# 26.10.2015 cg
# - stop endless loop in sendFrame() when client connection fail
# 22.11.2015 cg
# - removed remainder call of setsrqbit()
# 23.11.2015 jsi
# - removed all of the SSRQ/CSRQ approach
# 29.11.2015 jsi
# - removed activity timer
# 07.02.2016 jsi
# - setpilbox call removed
# 13.10.2016 jsi
# - remove unregister function
# - store tab name if device is registered
# 30.10.2016 jsi
# - getDevices added (removed by mistake)
# 22.12.2016 jsi
# - raise TcpIpError missing second param added
# 06.01.2017 jsi:
# - check for ConnectionError exception when sendig frame to catch all exceptions
# 16.01.2017 jsi:
# - check for incoming connections to indicate isConnected
# - close_outsocket method added
# 07.01.2017 jsi:
# - timeout parameter added
# - refactoring: move code of process() and sendFrame() and device list handling
#   to thread object
# 03.02.2020 jsi:
# - fixed Python 3.8 syntax warning
# 29.06.2025 jsi:
# - Refactoring: moved tcpip thread class from pilthreads to this file
# - Moved interface configuration GUI from pilwidgets to this file

import select
import socket
from .pilconfig import PILCONFIG
from .pilcore import QTBINDINGS,assemble_frame, disassemble_frame, COMTMOUTREAD, COMTMOUTACK,CLASS_INTERFACE_NET
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtGui, QtWidgets
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtGui, QtWidgets
from .pilthreads import PilThreadError, cls_pilthread_generic, cls_ConfigInterfaceGeneric

MODE_TCPIP=1

class TcpIpError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg = msg
      if add_msg is None:
         self.add_msg=""
      else:
         self.add_msg = add_msg

class cls_piltcpip:

   def __init__(self,port,remotehost,remoteport):
      self.__port__=port       # port for input connection
      self.__remotehost__=remotehost     # host for output connection
      self.__remoteport__=remoteport     # port for output connection

      self.__devices__ = []        # list of virtual devices

      self.__serverlist__ = []
      self.__clientlist__= []
      self.__outsocket__= None
      self.__outconnected__= False
      self.__inconnected__= False

   def isConnected(self):
      return self.__outconnected__ and self.__inconnected__

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
         raise TcpIpError("cannot bind to port","")

   def openclient(self):
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
            self.__outconnected__= True
         except OSError as msg:
            self.__outsocket__.close()
            self.__outsocket__ = None
            continue
         break
      return self.__outconnected__

#
#  Disconnect from Network
#
   def close(self):
      for s in self.__clientlist__:
         s.close()
      for s in self.__serverlist__:
         s.close()
      if self.__outconnected__:
         self.__outsocket__.shutdown(socket.SHUT_WR)
         self.__outsocket__.close()
         self.__outsocket__= None
         self.__outconnected__= False

#
# Close output socket
#
   def close_outsocket(self):
      if self.__outconnected__:
         self.__outsocket__.shutdown(socket.SHUT_WR)
         self.__outsocket__.close()
         self.__outsocket__= None
         self.__outconnected__= False
#
#  Read HP-IL frame from PIL-Box (2 byte), handle connect to server socket
#
   def read(self,timeout):
      readable,writable,errored=select.select(self.__serverlist__ + self.__clientlist__,[],[],timeout)
      for s in readable:
         if self.__serverlist__.count(s) > 0:
            cs,addr = s.accept()
            self.__clientlist__.append(cs)
            self.__inconnected__= True
         else:
            bytrx = s.recv(2)
            if bytrx:
               return (socket.ntohs((bytrx[1] << 8) | bytrx[0]))
            else:
               self.__clientlist__.remove(s)
               s.close()
               self.__inconnected__= False
      return None
#
#     send a IL frame to the virtual loop
#
   def write(self,frame):
      bRetry = True
      b=bytearray(2)
      f=socket.htons(frame)
      b[0]= f & 0xFF
      b[1]= f >> 8
      while bRetry:
         if self.isConnected():
            try:
               self.__outsocket__.send(b)
               break
            except ConnectionError:
               self.__outsocket__.shutdown(socket.SHUT_WR)
               self.__outsocket__.close()
               self.__outsocket__= None
               self.__outconnected__ = False
         else:
            bRetry = self.openclient()

#
# HP-IL over TCP-IP communication thread (see http://hp.giesselink.com/hpil.htm)
#
class cls_PilTcpIpThread(cls_pilthread_generic):

   def __init__(self, parent,mode):
      super().__init__(parent,mode,CLASS_INTERFACE_NET)

   def enable(self):
      port= PILCONFIG.get("pyilper","port")
      remote_host=PILCONFIG.get("pyilper","remotehost")
      remote_port=PILCONFIG.get("pyilper","remoteport")
      self.send_message('Not connected to virtual HP-IL devices')
      try:
         self.commobject= cls_piltcpip(port, remote_host, remote_port)
         self.commobject.open()
      except TcpIpError as e:
         self.commobject.close()
         self.commobject=None
         raise PilThreadError(e.msg, e.add_msg)
      return

   def disable(self):
      super().disable()
      return
#
#  thread execution 
#         
   def run(self):
      super().run()
#
      connected=False
      try:
#
#        Thread main loop    
#
         while True:
            if self.check_pause_stop():
               break
#
#           read frame from Network
#
            frame=self.commobject.read(COMTMOUTREAD)
            if self.commobject.isConnected():
               if not connected:
                  connected=True
                  self.send_message('connected to virtual HP-IL devices')
            else:
               if connected:
                  connected= False
                  self.commobject.close_outsocket()
                  self.send_message('not connected to virtual HP-IL devices')
               
            if frame is None:
               continue
#
#           process frame and return it to loop
#
            self.update_framecounter()
            for i in self.devices:
               frame=i[0].process(frame)
#
#           send frame
#
            self.commobject.write(frame)

      except TcpIpError as e:
         self.send_message('disconnected after error. '+e.msg+': '+e.add_msg)
         self.send_message(e.msg)
         self.signal_crash()
      self.running=False

class cls_PILTCPIP_Config(cls_ConfigInterfaceGeneric):

   def __init__(self,configName,configNumber, interfaceText):

      super().__init__(configName,configNumber,interfaceText)
      self.configNumber=configNumber
      self.configName=configName

      self.port= PILCONFIG.get(configName,"port")
      self.remoteport= PILCONFIG.get(configName,"remoteport")
      self.remotehost= PILCONFIG.get(configName,"remotehost")

      self.intvalidator= QtGui.QIntValidator()
      self.glayout=QtWidgets.QGridLayout()
      self.lbltxt3=QtWidgets.QLabel("Port:")
      self.glayout.addWidget(self.lbltxt3,0,0)
      self.lbltxt4=QtWidgets.QLabel("Remote host:")
      self.glayout.addWidget(self.lbltxt4,1,0)
      self.lbltxt5=QtWidgets.QLabel("Remote port:")
      self.glayout.addWidget(self.lbltxt5,2,0)
      self.edtPort= QtWidgets.QLineEdit()
      self.glayout.addWidget(self.edtPort,0,1)
      self.edtPort.setText(str(self.port))
      self.edtPort.setValidator(self.intvalidator)
      self.edtRemoteHost= QtWidgets.QLineEdit()
      self.glayout.addWidget(self.edtRemoteHost,1,1)
      self.edtRemoteHost.setText(self.remotehost)
      self.edtRemotePort= QtWidgets.QLineEdit()
      self.glayout.addWidget(self.edtRemotePort,2,1)
      self.edtRemotePort.setText(str(self.remoteport))
      self.edtRemotePort.setValidator(self.intvalidator)
      self.vb.addLayout(self.glayout)

      if cls_ConfigInterfaceGeneric.interfaceMode == self.configNumber:
         self.radBut.setChecked(True)
         self.setActive(True)
      else:
         self.radBut.setChecked(False)
         self.setActive(False)


   def setActive(self,flag):
      self.edtPort.setEnabled(flag)
      self.edtRemoteHost.setEnabled(flag)
      self.edtRemotePort.setEnabled(flag)
      self.radBut.setChecked(flag)

   def check_reconnect(self):
      needs_reconnect= False
      needs_reconnect |= self.check_param("port", int(self.edtPort.text()))
      needs_reconnect |= self.check_param("remotehost", self.edtRemoteHost.text())
      needs_reconnect |= self.check_param("remoteport", int(self.edtRemotePort.text()))
      return needs_reconnect

   def store_config(self):
      PILCONFIG.put(self.configName,"port", int(self.edtPort.text()))
      PILCONFIG.put(self.configName,"remotehost", self.edtRemoteHost.text())
      PILCONFIG.put(self.configName,"remoteport", int(self.edtRemotePort.text()))
