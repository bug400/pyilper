#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pyILPER 1.2.1 for Linux
#
# An emulator for virtual HP-IL devices for the PIL-Box
# derived from ILPER 1.4.5 for Windows
# Copyright (c) 2008-2013   Jean-Francois Garnier
# C++ version (c) 2013 Christoph Gießelink
# Python Version (c) 2016 Joachim Siebold
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
from .pilpipes import PipesError
#
# PIL-Box thread class --------------------------------------------------------
#
# Changelog


class cls_PilPipesThread(QtCore.QThread):

   def __init__(self, parent,pilpipes):
      super().__init__(parent)
      self.parent=parent
      self.pilpipes= pilpipes
      self.pause= False
      self.running=True
      self.cond=QtCore.QMutex()
      self.stop=QtCore.QMutex()
      self.pauseCond=QtCore.QWaitCondition()
      self.stoppedCond=QtCore.QWaitCondition()
      self.parent.emit_message("not connected to named pipes")

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
      self.parent.emit_message("named pipes connection suspended")
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
      self.parent.emit_message("connected to named pipes")
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
      try:
         self.parent.emit_message("connected to named pipes")
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
#           read frame from input pipe
#
            frame=self.pilpipes.read()
            if frame == None:
               continue
#
#           process frame
#
            self.pilpipes.process(frame)

      except PipesError as e:
         self.parent.emit_message('named pipes disconnected after error. '+e.msg+': '+e.add_msg)
         self.parent.emit_crash()
      else:
         self.parent.emit_message('named pipes disconnected')
