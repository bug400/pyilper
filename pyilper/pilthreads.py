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
# 21.09.2017 jsi:
# - removed message "suspended"
# 05.10.2017 jsi
# - added global frame counter and store counter of most recent fraame that
#   addressed a device
# 12.11.2017 jsi
# - removed PipPipeThread
# - raise PilThreadError instead of SocketError in cls_PilSocketThread
# - set self.running= False on thread exit
# 13.11.2017 cg
# - made code more robust against illegal ACK in the pil box and pil box
#   simulation interface when receiving byte data from the pil box
# - removed ACK in pil box simulation after receiving a high byte
# - fixed detection and acknowledge of a pil box command
# 04.05.2022 jsi
# - PySide6 migration
# 29.06.2025 jsi
# - refactoring: moved device specific thread classes to the device specific files
# - created base class for interface configuration GUI
# 16.03.2026 jsi
# - refactoring of global variables
# 21.03.2026 jsi
# - autoreconnect for non network devices
# 22.03.2026 jsi
# - added standard USB CDC device name support in TtyWindow for mac os
# 24.03.2026 jsi
# - make autoreconnect configurable (checkDevice)
# 04.04.2026 jsi
# - serial device detection now with serial.tools.list_ports
# - show serial device information in tty selection window
#
import sys
import threading
import re
from pathlib import Path
import serial.tools.list_ports

from .pilglobals import *
if PILGLOBALS.QT_Bindings=="PySide6":
   from PySide6 import QtCore, QtGui, QtWidgets
if PILGLOBALS.QT_Bindings=="PyQt5":
   from PyQt5 import QtCore, QtGui, QtWidgets

if PILGLOBALS.isWindows:
   import winreg
from .pilconfig import PILCONFIG


#
class PilThreadError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg=msg
      self.add_msg= add_msg

#
# abstract class for communication thread
#
class cls_pilthread_generic(QtCore.QThread):

   def __init__(self, parent,mode):
      super().__init__(parent)
      self.parent=parent
      self.mode=mode
      self.pause= False
      self.running=True
      self.cond=QtCore.QMutex()
      self.stop=QtCore.QMutex()
      self.pauseCond=QtCore.QWaitCondition()
      self.stoppedCond=QtCore.QWaitCondition()
      self.interfaceSpec= None                 # set by sub class
      self.commobject= None                    # i/o object (PIL-Box, TCP/IP...)
      self.framecounter=0                      # global frame counter
      self.addr_framecounter=0                 # frame counter of the last
                                               # HP-IL addressing command
      self.devices= []                         # list of devices
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
   def signal_crash(self,reason=0):
         self.parent.emit_crash(reason)
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
#  register devices, make thread object known to the device object
#
   def register(self, obj, name):
      self.devices.append([obj,name])
      obj.setThreadObject(self)
#
#  get device list
#
   def getDevices(self):
      return self.devices
#
#  increase global frame counter
#
   def update_framecounter(self):
      self.framecounter+=1
#
#  get value of global frame counter
#
   def get_framecounter(self):
      return self.framecounter
#
#  update value of addr_framecounter
#
   def update_addr_framecounter(self,value):
      self.addr_framecounter=value
#
#  get value of addr_framecounter
#
   def get_addr_framecounter(self):
      return self.addr_framecounter
#
#  run method
#
   def run(self):
      sys.settrace(threading._trace_hook)
#
#  return interface spec
#
   def get_interfaceSpec(self):
      return self.interfaceSpec
#
#  stub
#
   @classmethod
   def checkDevice(cls,name):
      return(True)

#
# Get TTy  Dialog class ------------------------------------------------------
#

class cls_TtyWindow(QtWidgets.QDialog):

   def __init__(self, tty):
      super().__init__()

      self.oldTty=tty
      self.setWindowTitle("Select serial device")
      self.vlayout= QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.label= QtWidgets.QLabel()
      self.label.setText("Select or enter serial port")
#     self.label.setAlignment(QtCore.Qt.AlignCenter)
      self.vlayout.addWidget(self.label)


      if PILGLOBALS.isWindows:
         pattern="COM\\d+"
      if PILGLOBALS.isLinux:
         pattern="(ttyACM\\d+)|(ttyUSB\\d+)"
      if PILGLOBALS.isMacos:
         pattern="(cu.usbserial-*)|(cu.usbmodem\\d+)"

      self.__ComboBox__ = QtWidgets.QComboBox() 
      self.__ComboBox__.setEditable(True)
      self.vlayout.addWidget(self.__ComboBox__)

      self.gridLayout= QtWidgets.QGridLayout()
      self.gridLayout.addWidget(QtWidgets.QLabel("Description"),0,0)
      self.gridLayout.addWidget(QtWidgets.QLabel("UID"),1,0)
      self.gridLayout.addWidget(QtWidgets.QLabel("Manufacturer"),2,0)
      self.gridLayout.addWidget(QtWidgets.QLabel("Serial Number"),3,0)
      self.gridLayout.addWidget(QtWidgets.QLabel("Product"),4,0)
      self.gridLayout.addWidget(QtWidgets.QLabel("Interface"),5,0)
      self.description= QtWidgets.QLabel("")
      self.gridLayout.addWidget(self.description,0,1)
      self.uid=QtWidgets.QLabel("")
      self.gridLayout.addWidget(self.uid,1,1)
      self.manufacturer=QtWidgets.QLabel("")
      self.gridLayout.addWidget(self.manufacturer,2,1)
      self.serialNumber=QtWidgets.QLabel("")
      self.gridLayout.addWidget(self.serialNumber,3,1)
      self.product=QtWidgets.QLabel("")
      self.gridLayout.addWidget(self.product,4,1)
      self.interface=QtWidgets.QLabel("")
      self.gridLayout.addWidget(self.interface,5,1)
      self.gridLayout.addWidget(QtWidgets.QLabel("Information above may be incomplete or nil"),6,0,1,2)

      self.vlayout.addLayout(self.gridLayout)

      self.buttonBox = QtWidgets.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.hlayout = QtWidgets.QHBoxLayout()
      self.hlayout.addWidget(self.buttonBox)
      self.vlayout.addWidget(self.buttonBox)

      self.portInfo= { }
      for port in serial.tools.list_ports.grep(pattern,False):
         self.__ComboBox__.addItem(port.device)
         self.portInfo[port.device]=port

      self.__device__= ""

      idx=self.__ComboBox__.findText(self.oldTty,QtCore.Qt.MatchExactly)
      if idx  >= 0 :
         self.__ComboBox__.setCurrentIndex(idx)
      self.setDeviceInfo(self.__ComboBox__.currentText())
      self.__ComboBox__.activated[int].connect(self.combobox_choosen)
      self.__ComboBox__.editTextChanged.connect(self.combobox_textchanged)

   def setDeviceInfo(self,device):
      self.description.setText("")
      self.uid.setText("")
      self.manufacturer.setText("")
      self.serialNumber.setText("")
      self.product.setText("")
      self.interface.setText("")
      if device in self.portInfo.keys():
         self.description.setText(self.portInfo[device].description)
         if self.portInfo[device].vid is not None and self.portInfo[device].pid is not None:
            self.uid.setText(hex(self.portInfo[device].vid)+":"+hex(self.portInfo[device].pid))
         self.manufacturer.setText(self.portInfo[device].manufacturer)
         self.serialNumber.setText(self.portInfo[device].serial_number)
         self.product.setText(self.portInfo[device].product)
         self.interface.setText(self.portInfo[device].interface)
      

   def do_ok(self):
      if self.__device__=="":
         self.__device__= self.__ComboBox__.currentText()
         if self.__device__=="":
            return
      super().accept()

   def do_cancel(self):
      super().reject()


   def combobox_textchanged(self, device):
      self.__device__= device
      self.setDeviceInfo(self.__device__)

   def combobox_choosen(self, idx):
      self.__device__= self.__ComboBox__.itemText(idx)
      self.setDeviceInfo(self.__device__)

   def getDevice(self):
      return self.__device__

   @staticmethod
   def getTtyDevice(tty_device):
      dialog= cls_TtyWindow(tty_device)
      dialog.resize(200,100)
      result= dialog.exec()
      if result== QtWidgets.QDialog.Accepted:
         return dialog.getDevice()
      else:
         return ""

#
# generic interface configuration class
#
class cls_ConfigInterfaceGeneric(QtWidgets.QFrame):

   if PILGLOBALS.QT_Bindings=="PySide6":
      buttonCheckedSignal= QtCore.Signal()
   if PILGLOBALS.QT_Bindings=="PyQt5":
      buttonCheckedSignal= QtCore.pyqtSignal()

   interfaceConfigWidgets= []

   interfaceMode= 0

   def __init__(self,configName,configNumber,interfaceText):
      super().__init__()
      cls_ConfigInterfaceGeneric.interfaceConfigWidgets.append(self)
      self.configName= configName
      self.configNumber= configNumber
      self.isChecked = False
      self.vb= QtWidgets.QVBoxLayout(self)
      self.radBut= QtWidgets.QRadioButton()
      self.radBut.setText(interfaceText)
      self.radBut.clicked.connect(self.do_checked)
      self.vb.addWidget(self.radBut)

   def setActive(self,flag):
      return

   def check_reconnect(self):
      return False

   def store_config(self):
      return
      
   def do_checked(self):
      cls_ConfigInterfaceGeneric.interfaceMode=self.configNumber
      for w in cls_ConfigInterfaceGeneric.interfaceConfigWidgets:
         if w is self:
            w.setActive(True)
         else:
            w.setActive(False)

   def check_param(self,param,value):
      oldvalue= PILCONFIG.get(self.configName,param,value)
      return (value!= oldvalue)
     
   @staticmethod
   def check_reconnect(old_mode):
      needs_reconnect = False
      if cls_ConfigInterfaceGeneric.interfaceMode != old_mode:
         needs_reconnect = True
      for w in cls_ConfigInterfaceGeneric.interfaceConfigWidgets:
         needs_reconnect |= w.check_reconnect()
      
      return needs_reconnect

   @staticmethod
   def store_config(configName):
      PILCONFIG.put(configName,"mode",cls_ConfigInterfaceGeneric.interfaceMode)
      for w in cls_ConfigInterfaceGeneric.interfaceConfigWidgets:
         w.store_config()

   @staticmethod
   def reset():
      cls_ConfigInterfaceGeneric.interfaceConfigWidgets= []
