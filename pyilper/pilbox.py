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
# PIL-Box object class  and thread object class  ---------------------------------------------
#
# Initial version derived from ILPER 1.43
#
# Changelog
#
# 09.02.2014 improvements and changes of ILPER 1.45
# - send RFC to virtual devices after each cmd frame
# - high byte detection
#
# 07.06.2014 jsi
# - introduce configurable baudrate support
# 06.10.2015 jsi:
# - class statement syntax update
# 16.10.2015 jsi:
# - removed SSRQ, CSRQ approach
# - introduced COFI switch to get real IDY frames from the loop (requires firmware 1.6)
# 29.11.2015 jsi:
# - removed activity timer
# 30.11.2015 jsi:
# - introduced idyframe option
# 03.02.2015 jsi
# - set frame timeout to 50 msec
# 07.02.2015 jsi
# - set pilbox call removed
# 22.02.2016 cg
# - send the cmd and not the RFC frame back to the PIL-Box
# 22.03.2016 cg
# - send acknowledge for high byte only at a 9600 baud connection
# 26.04.2016 jsi
# - auto baudrate support, code taken from cgi
# 09.05.2016 jsi
# - reenable baud rate setting in addition to auto baud support
# 11.07.2016 jsi
# - autobaud detection rewritten, hint by cg
# - move constants to pilcore.py
# 13.10.2016 jsi
# - remove unregister function
# - store tab name if device is registered
# 30.10.2016 jsi
# - getDevices added (removed by mistake)
# 07.10.2017 jsi
# - refactoring: moved process(), sendFrame() and device list handling code to
#   thread object
# 13.11.2017 cg
# - made code more robust against illegal ACK in the pil box and pil box
#   simulation interface when receiving byte data from the pil box
# - fixed detection and acknowledge of a pil box command
# 29.06.2025 jsi
# - refactoring, moved PIL-Box thread class from pilthreads to this file
# - moved interface configuration GUI part from pilwidgets to this file

MODE_PILBOX=0
#
# PIL-Box Commands
#
COFF= 0x497   # initialize in controller off mode
TDIS= 0x494   # disconnect
COFI= 0x495   # switch PIL-Box to transmit real IDY frames

from .pilrs232 import Rs232Error, cls_rs232
from .pilconfig import PILCONFIG
from .pilcore import QTBINDINGS,assemble_frame, disassemble_frame, TMOUTCMD, TMOUTFRM, BAUDRATES,CLASS_INTERFACE_BOX
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtGui, QtWidgets
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtGui, QtWidgets
from .pilthreads import PilThreadError, cls_pilthread_generic, cls_TtyWindow, cls_ConfigInterfaceGeneric

class PilBoxError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg=msg
      if add_msg is None:
         self.add_msg=""
      else:
         self.add_msg= add_msg


class cls_pilbox:

   MODE_COFF=0
   MODE_COFI=1
   MODE_PASSTHRU=2

   def __init__(self,ttydevice,baudrate,mode):
      self.__baudrate__= baudrate  # baudrate of connection or 0 for autodetect
      self.__mode__= mode          # switch box to mode
      self.__tty__= cls_rs232()    # serial device object
      self.__ttydevice__=ttydevice # serial port name

#
#  get connection speed
#
   def getBaudRate(self):
      return(self.__baudrate__)
#
#  send command to PIL-Box, check return value. 
#
   def __sendCmd__(self,cmdfrm,tmout):
#     print("about to send command 0x{0:02x}".format(cmdfrm))
      hbyt,lbyt= disassemble_frame(cmdfrm)
      try:
         self.write(lbyt,hbyt)
         bytrx= self.__tty__.rcv(tmout,1)
      except Rs232Error as e:
         raise PilBoxError("PIL-Box command error:", e.value)
      if bytrx is None:
         raise PilBoxError("PIL-Box command error: timeout","")
      try:
         if ((ord(bytrx) & 0x3F) != (cmdfrm & 0x3F)):
#           print("val err ",ord(bytrx))
            raise PilBoxError("PIL-Box command error: illegal retval","")
      except TypeError:
#        print("type err")
         raise PilBoxError("PIL-Box command error: illegal retval","")
#     print("command sent and acknowledged 0x{0:02x}".format(cmdfrm))

#
#  Connect to PIL-Box and set mode
#
   def open(self):

      if self.__mode__== cls_pilbox.MODE_COFF:
         cmd= COFF
      elif self.__mode__== cls_pilbox.MODE_COFI:
         cmd= COFI
      elif self.__mode__== cls_pilbox.MODE_PASSTHRU:
         cmd= PASSTHRU
#
#     open serial device, no autobaud mode
#
      if self.__baudrate__ > 0:
         try:
            self.__tty__.open(self.__ttydevice__, self.__baudrate__)
         except Rs232Error as e:
            raise PilBoxError("Cannot connect to PIL-Box", e.value)
         self.__sendCmd__(cmd,TMOUTCMD)

      else:
#
#     open serial device, detect baud rate, use predefined baudrates in
#     BAUDRATES list in reverse order
#
         success= False
         errmsg=""
         for i in range(len(BAUDRATES)-1,0,-1):
#
#           open device at the beginning of the loop, if error throw exception and exit
#
            baudrate= BAUDRATES[i][1]
            if i== len(BAUDRATES)-1:
               try:
                  self.__tty__.open(self.__ttydevice__, baudrate)
               except Rs232Error as e:
                  raise PilBoxError("Cannot connect to PIL-Box", e.value)
#
#           otherwise reset device and use next baudrate
#
            else:
               try:
                  self.__tty__.flushInput()
                  self.__tty__.setBaudrate(baudrate)
               except Rs232Error as e:
                  raise PilBoxError("Cannot connect to PIL-Box", e.value)
#
#           initialize PIL-Box with current baud rates
#
            try:
               self.__sendCmd__(COFF,TMOUTCMD)
               success= True
               self.__baudrate__=baudrate
               break
            except PilBoxError as e:
               errmsg=e.msg
#
#        no success with any baud rate, throw exception and exit
#
         if not success:
            self.__tty__.close()
            raise PilBoxError("Cannot connect to PIL-Box", errmsg)

#
#  Disconnect PIL-Box
#
   def close(self):
      try:
         self.__sendCmd__(TDIS,TMOUTCMD)
      finally:
         self.__tty__.close()
#
#  Read byte from PIL-Box
#
   def read(self):
      try:
         bytrx= self.__tty__.rcv(TMOUTFRM,1)
      except Rs232Error as e:
         raise PilBoxError("PIL-Box read frame error", e.value)
      return bytrx
#
# Send one or two bytes to the PIL-Box
#
   def write(self,lbyt,hbyt=None):
      if hbyt is None:
         buf=bytearray([lbyt])
      else:
         buf=bytearray([hbyt,lbyt])
      try:
         self.__tty__.snd(buf)
      except Rs232Error as e:
         raise PilBoxError("PIL-Box send frame error", e.value)
#
# PIL-Box communications thread over serial port
#
class cls_PilBoxThread(cls_pilthread_generic):

   def __init__(self,parent,mode):
      super().__init__(parent,mode,CLASS_INTERFACE_BOX) 
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
      super().run()
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
#           process byte read from the PIL-Box, is not a low byte
#
            if (byt & 0xC0) == 0x00:
#
#              check for high byte, else ignore
#
               if (byt & 0x20) != 0:
#
#                 got high byte, save it
#
                  self.__lasth__ = byt & 0xFF
#
#                 send acknowledge only at 9600 baud connection
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
            self.update_framecounter()
            for i in self.devices:
               frame=i[0].process(frame)
#
#           If received a cmd frame from the PIL-Box send RFC frame to virtual
#           HPIL-Devices
#
            if (frame & 0x700) == 0x400:
               self.update_framecounter()
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
      self.running=False


class cls_PILBOX_Config(cls_ConfigInterfaceGeneric):

   def __init__(self,configName,configNumber, interfaceText):

      super().__init__(configName,configNumber,interfaceText)
      self.tty= PILCONFIG.get(configName,"tty")
      self.ttyspeed= PILCONFIG.get(configName,"ttyspeed")
      self.idyframe= PILCONFIG.get(configName,"idyframe")

#
#     serial device
#
      self.hboxtty= QtWidgets.QHBoxLayout()
      self.lbltxt1=QtWidgets.QLabel("Serial Device: ")
      self.hboxtty.addWidget(self.lbltxt1)
      self.lblTty=QtWidgets.QLabel()
      self.lblTty.setText(self.tty)
      self.hboxtty.addWidget(self.lblTty)
      self.hboxtty.addStretch(1)
      self.butTty=QtWidgets.QPushButton()
      self.butTty.setText("change")
      self.butTty.pressed.connect(self.do_config_interface)
      self.hboxtty.addWidget(self.butTty)
      self.vb.addLayout(self.hboxtty)
#
#     tty speed combo box
#
      self.hboxbaud= QtWidgets.QHBoxLayout()
      self.lbltxt2=QtWidgets.QLabel("Baud rate ")
      self.hboxbaud.addWidget(self.lbltxt2)
      self.comboBaud=QtWidgets.QComboBox()
      i=0
      for baud in BAUDRATES:
         self.comboBaud.addItem(baud[0])
         if self.ttyspeed== baud[1]:
            self.comboBaud.setCurrentIndex(i)
         i+=1
 
      self.hboxbaud.addWidget(self.comboBaud)
      self.hboxbaud.addStretch(1)
      self.vb.addLayout(self.hboxbaud)

#
#     idy frames
#
      self.cbIdyFrame= QtWidgets.QCheckBox('Enable IDY frames')
      self.cbIdyFrame.setChecked(self.idyframe)
      self.cbIdyFrame.setEnabled(True)
      self.cbIdyFrame.stateChanged.connect(self.do_cbIdyFrame)
      self.vb.addWidget(self.cbIdyFrame)

      if cls_ConfigInterfaceGeneric.interfaceMode == self.configNumber:
         self.radBut.setChecked(True)
         self.setActive(True)
      else:
         self.radBut.setChecked(False)
         self.setActive(False)


   def do_cbIdyFrame(self):
      self.idyframe= self.cbIdyFrame.isChecked()

   def do_config_interface(self):
      interface= cls_TtyWindow.getTtyDevice(self.tty)
      if interface == "" :
         return
      self.tty= interface
      self.lblTty.setText(self.tty)

   def setActive(self,flag):
      self.butTty.setEnabled(flag)
      self.cbIdyFrame.setEnabled(flag)
      self.comboBaud.setEnabled(flag)
      self.radBut.setChecked(flag)

   def check_reconnect(self):
      needs_reconnect= False
      needs_reconnect |= self.check_param("tty", self.lblTty.text())
      needs_reconnect |= self.check_param("ttyspeed", BAUDRATES[self.comboBaud.currentIndex()][1])
      needs_reconnect |= self.check_param("idyframe",self.idyframe)
      return needs_reconnect

   def store_config(self):
      PILCONFIG.put(self.configName,"tty", self.tty)
      PILCONFIG.put(self.configName,"ttyspeed", BAUDRATES[self.comboBaud.currentIndex()][1])
      PILCONFIG.put(self.configName,"idyframe",self.idyframe)
