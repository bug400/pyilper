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
#
from PyQt5 import QtCore
from .piltcpip import TcpIpError
#
# tcpip thread class --------------------------------------------------------
#
# Chnagelog
# 06.10.2015 jsi:
# - adjust super statements to python3+ syntax
# 23.11.2015 jsi:
# - removed all of the SSRQ/CSRQ approach
# 16.01.2017 jsi:
# - change message to "not connected to .." if not connected
# - close outsocket, if not connected any more
#
class cls_PilTcpIpThread(QtCore.QThread):

   def __init__(self, parent,tcpip):
      super().__init__(parent)
      self.parent=parent
      self.tcpip=tcpip
      self.pause= False
      self.running=True
      self.cond=QtCore.QMutex()
      self.stop=QtCore.QMutex()
      self.pauseCond=QtCore.QWaitCondition()
      self.stoppedCond=QtCore.QWaitCondition()
      self.parent.emit_message("not connected to virtual HP-IL devices")

   def isRunning(self):
      return(self.running)
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
      self.parent.emit_message("Network connection suspended")
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
      self.parent.emit_message("Network connection resumed")
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
            self.cond.lock()
            if(self.pause):
               self.stop.lock()
               if not self.running:
                  self.stoppedCond.wakeAll()
                  self.stop.unlock()
                  break
               self.stoppedCond.wakeAll()
               self.stop.unlock()
               self.pauseCond.wait(self.cond)
            self.cond.unlock()
#
#           read byte from Network
#
            frame=self.tcpip.read()
#
#           if timeout check whether a virtual HP-IL device requests service
#           if a device requests service then send s SSRQ to the PIL-Box
#           without handshake. This does not work reliable, because
#           - a SSRQ sent to the PIL-Box may disturb a frame byte that
#             arrives at the PIL-Box at the same time
#           - the handshake byte may be overtaken by a frame byte
#             discarding the handshake byte may discard a frame byte instead
#
            if self.tcpip.isConnected():
               if not connected:
                  connected=True
                  self.parent.emit_message('connected to virtual HP-IL devices')
            else:
               if connected:
                  connected= False
                  self.tcpip.close_outsocket()
                  self.parent.emit_message('not connected to virtual HP-IL devices')
               
            if frame== None:
               continue
#
#           process byte read from the Network
#
            self.tcpip.process(frame)

      except TcpIpError as e:
         self.parent.emit_message(e.msg)
         self.parent.emit_crash()
      else:
         self.parent.emit_message('Not connected to virtual HP-IL devices')
