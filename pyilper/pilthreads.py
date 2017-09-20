#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pyILPER 1.6.0 for Linux
#
# An emulator for virtual HP-IL devices for the PIL-Box
# derived from ILPER 1.4.5 for Windows
# Copyright (c) 2008-2013   Jean-Francois Garnier
# C++ version (c) 2013 Christoph Gießelink
# Python Version (c) 2017 Joachim Siebold
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
# pyILPER thread classes -------------------------------------------------------
#
# Changelog
# 07.09.2017 jsi:
# - refactored from pilboxthread.py, piltcpipthread.py, pilsocketthread.py
#
from PyQt5 import QtCore
from .pilconfig import PILCONFIG
from .pilbox import cls_pilbox, PilBoxError
from .piltcpip import cls_piltcpip, TcpIpError
from .pilcore import isWINDOWS, isLINUX, isMACOS, assemble_frame, disassemble_frame, COMTMOUTREAD, COMTMOUTACK, COMTMOUTWRITE
if isLINUX() or isMACOS():
   from .pilsocket import cls_pilsocket, SocketError
if isWINDOWS():
   from .pilwinpipe import cls_pilwinpipe, WinPipeError

#
class PilThreadError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg=msg
      self.add_msg= add_msg

#
# abstract class for communication thread
#
class cls_pilthread_generic(QtCore.QThread):

   def __init__(self, parent):
      super().__init__(parent)
      self.parent=parent
      self.pause= False
      self.running=True
      self.cond=QtCore.QMutex()
      self.stop=QtCore.QMutex()
      self.pauseCond=QtCore.QWaitCondition()
      self.stoppedCond=QtCore.QWaitCondition()
      self.commobject= None
      self.devices= []
#
#  report if thread is running
#
   def isRunning(self):
      return(self.running)
#
#  send message to status line of GUI
#
   def send_message(self,message):
      self.parent.emit_message(message)
#
#  signal crash to the main program
#
   def signal_crash(self):
         self.parent.emit_crash()
#
#  pause thread
#   
   def halt(self):
      if self.pause:
         return
      self.cond.lock()
      self.pause= True
      self.cond.unlock()
      self.stop.lock()
      self.stoppedCond.wait(self.stop)
      self.stop.unlock()
      self.send_message("Communication thread suspended")
#
# restart paused thread
#
   def resume(self):
      if not self.pause:
         return
      self.cond.lock()
      self.pause= False
      self.cond.unlock()
      self.pauseCond.wakeAll()
#
#  finish thread
#
   def finish(self):
      if not self.running:
         return
      if self.pause:
         self.terminate()
      else:
         self.cond.lock()
         self.pause= True
         self.running= False
         self.cond.unlock()
         self.stop.lock()
         self.stoppedCond.wait(self.stop)
         self.stop.unlock()
#
#   check pause/stop conditions
#   pauses if pause condition 
#   returns True if stop condition, False otherwise
#
   def check_pause_stop(self):
      self.cond.lock()
      if(self.pause):
         self.stop.lock()
         if not self.running:
            self.stoppedCond.wakeAll()
            self.stop.unlock()
            return True
         self.stoppedCond.wakeAll()
         self.stop.unlock()
         self.pauseCond.wait(self.cond)
      self.cond.unlock()
      return False
#
#  enable/ disable
#
   def enable(self):
      self.devices=[]
      return

   def disable(self):
      if self.commobject is not None:
         try:
            self.commobject.close()
         except:
            pass
      self.commobject= None
      return
#
#  register devices
#
   def register(self, obj, name):
      self.devices.append([obj,name])
#
#  get device list
#
   def getDevices(self):
      return self.devices
#
# PIL-Box communications thread over serial port
#
class cls_PilBoxThread(cls_pilthread_generic):

   def __init__(self,parent):
      super().__init__(parent) 
      self.__lasth__=0
      self.__baudrate__=0


   def enable(self):
      super().enable()
      self.send_message("Not connected to PIL-Box")
      baud=PILCONFIG.get("pyilper",'ttyspeed')
      ttydevice=PILCONFIG.get("pyilper",'tty')
      idyframe=PILCONFIG.get("pyilper",'idyframe')
      self.__lasth__=0
      if ttydevice== "":
         raise PilThreadError("Serial device not configured ","Run pyILPER configuration")
      try:
         self.commobject=cls_pilbox(ttydevice,baud,idyframe)
         self.commobject.open()
      except PilBoxError as e:
         raise PilThreadError(e.msg,e.add_msg)
      self.__baudrate__= self.commobject.getBaudRate()
      return
#
#  thread execution 
#         
   def run(self):
#
      self.send_message("connected to PIL-Box at {:d} baud".format(self.__baudrate__))
      try:
#
#        Thread main loop    
#
         while True:
            if self.check_pause_stop():
               break
#
#           read byte from PIL-Box
#
            ret=self.commobject.read()
            if ret== b'':
               continue
            byt=ord(ret)
#
#           process byte read from the PIL-Box
#
            if (byt & 0xE0) == 0x20:
#
#              high byte, save it
#
               self.__lasth__ = byt & 0xFF
#
#              send acknowledge only at 9600 baud connection
#
               if self.__baudrate__ == 9600:
                  self.commobject.write(0x0d)
               continue
#
#           low byte, build frame 
#
            frame= assemble_frame(self.__lasth__,byt)
#
#           process virtual HP-IL devices
#
            for i in self.devices:
               frame=i[0].process(frame)
#
#           If received a cmd frame from the PIL-Box send RFC frame to virtual
#           HPIL-Devices
#
            if (frame & 0x700) == 0x400:
               for i in self.devices:
                  i[0].process(0x500)
#
#           disassemble into low and high byte 
#
            hbyt, lbyt= disassemble_frame(frame)

            if hbyt != self.__lasth__:
#
#              send high part if different from last one and low part
#
               self.__lasth__ = hbyt
               self.commobject.write(lbyt,hbyt)
            else:
#
#              otherwise send only low part
#
               self.commobject.write(lbyt)

      except PilBoxError as e:
         self.send_message('PIL-Box disconnected after error. '+e.msg+': '+e.add_msg)
         self.signal_crash()

#
# HP-IL over TCP-IP communication thread (see http://hp.giesselink.com/hpil.htm)
#
class cls_PilTcpIpThread(cls_pilthread_generic):

   def __init__(self, parent):
      super().__init__(parent)

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
#
# Unix/Mac OS domain socket communication thread with vmware or virtualbox serial port
#
class cls_PilSocketThread(cls_pilthread_generic):

   def __init__(self, parent):
      super().__init__(parent)

   def enable(self):
      self.send_message("Not connected to socket")
      socket_name=PILCONFIG.get("pyilper","socketname")
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
            if (byt & 0xE0) == 0x20:
#
#              got high byte, save it, send ack and continue
#
               self.__lasth__ = byt & 0xFF
#
#              send acknowledge
#
               self.commobject.write(0x0d)
               continue
#
#           low byte, assemble frame according to 7- oder 8 bit format
#
            frame= assemble_frame(self.__lasth__,byt)
#
#           send acknowledge if we received a pil box command
#
            if frame & 0x794 == 0x494:
               frame= frame & 0x3F
#
#           process virtual HP-IL devices 
#
            else:
               for i in self.devices:
                  frame=i[0].process(frame)
#
#           disassemble frame
#
            hbyt, lbyt= disassemble_frame(frame)
            if  hbyt != self.__lasth__:
#
#              send high part if different from last one
#
               self.__lasth__ = hbyt
               self.commobject.write(hbyt)
#
#              read acknowledge
#
               b= self.commobject.read(COMTMOUTACK)
               if b is None:
                  raise SocketError("cannot get acknowledge: ","timeout")
               if ord(b)!= 0x0D:
                  raise SocketError("cannot get acknowledge: ","unexpected value")
#
#        otherwise send only low part
#
            self.commobject.write(lbyt)

      except SocketError as e:
         self.send_message('socket disconnected after error. '+e.msg+': '+e.add_msg)
         self.signal_crash()
#
# Windows named pipe communication thread with vmware or virtualbox (to do)
#
class cls_PilPipeThread(cls_pilthread_generic):

   def __init__(self, parent):
      super().__init__(parent)

   def enable(self):
      self.pipe_name=PILCONFIG.get("pyilper","winpipename")
      self.send_message("Not connected to named pipe")
      try:
         self.commobject= cls_pilwinpipe(self.pipe_name)
         self.commobject.open()
      except WinPipeError as e:
         self.commobject.close()
         self.commobject=None
         raise PilThreadError(e.msg, e.add_msg)
      return
#
#  thread execution 
#         
   def run(self):
#
      try:
#
#        Thread main loop    
#
         while True:
            if self.check_pause_stop():
               continue
            if self.commobject.isConnected():
               self.send_message('client connected')
            else:
               self.send_message('waiting for client')
#
#           read byte from pipe
#
            ret=self.commobject.read(COMTMOUTREAD)
            if ret is None:
               continue

            byt=ord(ret)
            if (byt & 0xE0) == 0x20:
#
#              got high byte, save it, send ack and continue
#
               self.__lasth__ = byt & 0xFF
#
#              send acknowledge
#
               self.commobject.write(0x0d,COMTMOUTWRITE)
               continue
#
#           low byte, assemble frame according to 7- or 8 bit format
#
            frame = assemble_frame(self.__lasth__,byt)
#
#           send acknowledge if pil box command
#
            if frame & 0x794 == 0x494:
               frame= frame & 0x3F
#
#           process virtual HP-IL devices 
#
            else:
               for i in self.devices:
                  frame=i[0].process(frame)
#
#           send frame
#
            hbyt, lbyt= disassemble_frame(frame)

            if  hbyt != self.__lasth__:
#
#              send high part if different from last one
#
               self.__lasth__ = hbyt
               self.commobject.write(hbyt,COMTMOUTWRITE)
#
#              read acknowledge
#
               b= self.commobject.read(COMTMOUTACK)
               if b is None:
                  raise WinPipeError("cannot get acknowledge: ","timeout")
               if ord(b)!= 0x0D:
                  raise WinPipeError("cannot get acknowledge: ","unexpected value")
#
#        otherwise send only low part
#
            self.commobject.write(lbyt,COMTMOUTWRITE)


      except WinPipeError as e:
         self.send_message('socket disconnected after error. '+e.msg+': '+e.add_msg)
         self.signal_crash()
