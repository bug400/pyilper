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
# Scope tab object classes ----------------------------------------------------
#
# Changelog
#
# 21.11.2015 jsi
# - introduced show IDY frames option in scope tab
# 28.04.2016 jsi
# - enable tabscope to log inbound, outbound and both traffic
# 29.04.2016 jsi
# - log scope unbuffered
# 01.08.2017 jsi
# - refactoring: tab classes moved to this file
# 03.09.2017 jsi
# - register pildevice is now method of comobject
# 14.09.2017 jsi
# - refactoring
# 22.09.2017 jsi
# - get actual number of columns with the get_cols method
# 23.09.2017 jsi
# - output hex code option added
# - fixed bug in form feed condition determination in out_scope
# 25.09.2017 jsi
# - extended options to display frames (mnemonic only, hex only, mnemonic and hex)
# 04.10.2017 jsi
# - display mode of scopes not initialized properly on program start
# 16.01.2018 jsi
# - adapted to cls_tabtermgeneric, implemented new cascading config menu
# 13.08.2018 jsi
# - log file tagging as proposed by Sylvain Cote
# 14.08.2018 jsi
# - added "**" to tag to find tags better in the logfile
# 16.01.2018 jsi
# - send int instead of char to terminal
# 04.05.2022 jsi
# - PySide6 migration

import datetime
from .pilconfig import PILCONFIG
from .pilwidgets import cls_tabtermgeneric, T_BOOLEAN, T_STRING,O_DEFAULT
from .pildevbase import cls_pildevbase
from .pilcore import QTBINDINGS
if QTBINDINGS=="PySide6":
   from PySide6 import QtWidgets
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtWidgets


LOG_INBOUND=0
LOG_OUTBOUND=1
LOG_BOTH=2
DISPLAY_MNEMONIC=0
DISPLAY_HEX=1
DISPLAY_BOTH=2
log_mode= ["Inbound", "Outbound", "Both"]
display_mode= ["Mnemonic","Hex","Both"]

class cls_tabscope(cls_tabtermgeneric):

   def __init__(self,parent,name):
      super().__init__(parent,name)
      self.scope_charpos=0
#
#     init local config parameters
#
      self.showIdy= PILCONFIG.get(self.name,"showidy",False)
      self.displayMode= PILCONFIG.get(self.name,"displaymode",DISPLAY_MNEMONIC)
      self.logMode=PILCONFIG.get(self.name,"logmode",LOG_INBOUND)
#
#     add logging
#
      self.add_logging()
#
#     add tag button
#
      self.tagButton=QtWidgets.QPushButton("Tag Logfile")
      self.add_controlwidget(self.tagButton)
      self.tagButton.setEnabled(False)
      self.tagButton.clicked.connect(self.do_tagbutton)
#
#     add scope config options to cascading menu
#
      self.cBut.add_option("Show IDY frames","showidy",T_BOOLEAN,[True,False])
      self.cBut.add_option("Display Mode","displaymode",T_STRING,display_mode)
      self.cBut.add_option("Log mode","logmode",T_STRING,log_mode)
#
#     create HP-IL devices and let the GUI object know them
#
      self.pildevice= cls_pilscope(True,self)
      self.pildevice2= cls_pilscope(False,self)
      self.guiobject.set_pildevice(self.pildevice)

      self.cBut.config_changed_signal.connect(self.do_tabconfig_changed)
#
#  handle changes of tab configuration
#
   def do_tabconfig_changed(self):
      param= self.cBut.get_changed_option_name()
#
#     change local config parameters
#
      if param=="showidy":
         self.showIdy= PILCONFIG.get(self.name,"showidy")
         self.pildevice.set_show_idy(self.showIdy)
         self.pildevice2.set_show_idy(self.showIdy)
      elif param=="displaymode":
         self.displayMode= PILCONFIG.get(self.name,"displaymode")
         self.pildevice.set_displayMode(self.displayMode)
         self.pildevice2.set_displayMode(self.displayMode)
      elif param=="logmode":
         self.logMode= PILCONFIG.get(self.name,"logmode")
         self.pildevice.setlocked(True)
         self.pildevice.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode == LOG_OUTBOUND))
         self.pildevice.setlocked(False)
         self.pildevice2.setlocked(True)
         self.pildevice2.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode == LOG_INBOUND))
         self.pildevice2.setlocked(False)
      super().do_tabconfig_changed()

   def enable(self):
      super().enable()
      self.parent.commthread.register(self.pildevice,self.name)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode == LOG_OUTBOUND))
      self.pildevice.set_show_idy(self.showIdy)
      self.pildevice.set_displayMode(self.displayMode)
      if self.logging:
         self.tagButton.setEnabled(True)

   def post_enable(self):
      self.parent.commthread.register(self.pildevice2,self.name)
      self.pildevice2.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode== LOG_INBOUND))
      self.pildevice2.set_show_idy(self.showIdy)
      self.pildevice2.set_displayMode(self.displayMode)

   def disable(self):
      super().disable()

   def do_cbActive(self):
      self.active= self.cbActive.isChecked()
      PILCONFIG.put(self.name,"active",self.active)
      self.pildevice.setlocked(True)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode == LOG_OUTBOUND))
      self.pildevice.setlocked(False)
      self.pildevice2.setlocked(True)
      self.pildevice2.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode == LOG_INBOUND))
      self.pildevice2.setlocked(False)

      try:
         self.toggle_active()
      except AttributeError:
         pass
      return
#
#  set tag button active/inactive
#
   def do_cbLogging(self):
      super().do_cbLogging()
      if self.logging:
         self.tagButton.setEnabled(True)
      else:
         self.tagButton.setEnabled(False)
#
# exec tag button, because we may write it asynchronous pause the thread
#
   def do_tagbutton(self):
      text,okPressed=QtWidgets.QInputDialog.getText(self,"Tag Logfile","Logfile tag",QtWidgets.QLineEdit.Normal,"")
      if okPressed and text != "":
          if self.parent.commthread is not None:
              if self.parent.commthread.isRunning():
                 self.parent.commthread.halt()
#
#  all errors that might occur during log write are handled from the
#  cbLogging methods, we do not need to catch errors
#
          self.cbLogging.logWrite("\n")
          self.cbLogging.logWrite(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
          self.cbLogging.logWrite(" ** ")
          self.cbLogging.logWrite(text)
          self.cbLogging.logWrite("\n")
          if self.parent.commthread is not None:
             self.parent.commthread.resume()
#
#
#  forward character to the terminal frontend widget and do logging
#
   def out_scope(self,s):
      l=len(s)
      if self.scope_charpos+l>=self.guiobject.get_cols() :
         self.guiobject.out_terminal(0x0D)
         self.guiobject.out_terminal(0x0A)
         self.cbLogging.logWrite("\n")
         self.cbLogging.logFlush()
         self.scope_charpos=0
      for i in range(0,len(s)):
         self.guiobject.out_terminal(ord(s[i]))
      self.cbLogging.logWrite(s)
      self.scope_charpos+=l
#
# HP-IL scope class -----------------------------------------------------------
#
# Changelog
# 06.10.2015 jsi:
# - class statement syntax update
# 21.11.2015 jsi:
# - removed SSRQ/CSRQ approach
# - introduced show IDY frames option
# 29.11.2015 jsi:
# - introduced device lock
# 07.02.2016 jsi
# - refactored and merged new Ildev base class of Christoph Giesselink
# 28.04.2016 jsi:
# - introduced inbound parameter, if True use uppercase letters if False use loweercase
# 09.08.2017 jsi:
# - register_callback_output implemented (from base class)
# 14.09.2017 jsi
# - refactoring
# 05.05.2023 cg
# - new implementation with single table

class cls_pilscope(cls_pildevbase):

   def __init__ (self, inbound,parent):
      super().__init__()
      self.__inbound__= inbound

      # opcode, mask, mnemonic
      self.__mnemo__= [[0x000, 0x700, "DAB"],
                       [0x100, 0x700, "DSR"],
                       [0x200, 0x700, "END"],
                       [0x300, 0x700, "ESR"],
                       [0x400, 0x7FF, "NUL"],
                       [0x401, 0x7FF, "GTL"],
                       [0x404, 0x7FF, "SDC"],
                       [0x405, 0x7FF, "PPD"],
                       [0x408, 0x7FF, "GET"],
                       [0x40F, 0x7FF, "ELN"],
                       [0x410, 0x7FF, "NOP"],
                       [0x411, 0x7FF, "LLO"],
                       [0x414, 0x7FF, "DCL"],
                       [0x415, 0x7FF, "PPU"],
                       [0x418, 0x7FF, "EAR"],
                       [0x43F, 0x7FF, "UNL"],
                       [0x420, 0x7E0, "LAD"],
                       [0x45F, 0x7FF, "UNT"],
                       [0x440, 0x7E0, "TAD"],
                       [0x460, 0x7E0, "SAD"],
                       [0x480, 0x7F0, "PPE"],
                       [0x490, 0x7FF, "IFC"],
                       [0x492, 0x7FF, "REN"],
                       [0x493, 0x7FF, "NRE"],
                       [0x49A, 0x7FF, "AAU"],
                       [0x49B, 0x7FF, "LPD"],
                       [0x4A0, 0x7E0, "DDL"],
                       [0x4C0, 0x7E0, "DDT"],
                       [0x400, 0x700, "CMD"],
                       [0x500, 0x7FF, "RFC"],
                       [0x540, 0x7FF, "ETO"],
                       [0x541, 0x7FF, "ETE"],
                       [0x542, 0x7FF, "NRD"],
                       [0x560, 0x7FF, "SDA"],
                       [0x561, 0x7FF, "SST"],
                       [0x562, 0x7FF, "SDI"],
                       [0x563, 0x7FF, "SAI"],
                       [0x564, 0x7FF, "TCT"],
                       [0x580, 0x7E0, "AAD"],
                       [0x5A0, 0x7E0, "AEP"],
                       [0x5C0, 0x7E0, "AES"],
                       [0x5E0, 0x7E0, "AMP"],
                       [0x500, 0x700, "RDY"],
                       [0x600, 0x700, "IDY"],
                       [0x700, 0x700, "ISR"]]

      self.__show_idy__= False
      self.__displayMode__= DISPLAY_MNEMONIC
      self.__parent__= parent

#
# public -------
#

   def set_show_idy(self,flag):
      self.__show_idy__= flag

   def set_displayMode(self,flag):
      self.__displayMode__= flag
#
#  public (overloaded) -------
#
#  convert frame to readable text and call the parent method out_scope
#
   def process (self,frame):
      if not self.__isactive__:
         return(frame)

#
#     ignore IDY frames
#
      if ((frame & 0x700) == 0x600) and not self.__show_idy__:
         return(frame)

#
#     single table solution
#
      for i in self.__mnemo__:
         if (frame & i[1]) == i[0]:
            # mnemonic
            s = i[2]
            # has argument
            arg = (~i[1]) & 0xFF
            if arg != 0:
               # add argument
               s += " {:02X}".format(frame & arg)
            break

#
#     inbound frames are lowercase, outbound frames are uppercase
#
      if self.__displayMode__== DISPLAY_MNEMONIC:
         s="{:6s}  ".format(s)
      elif self.__displayMode__== DISPLAY_HEX:
         s="{:03X}  ".format(frame)
      elif self.__displayMode__== DISPLAY_BOTH:
         s="{:6s} ({:03X}) ".format(s,frame)
      if not self.__inbound__:
         s= s.lower()
      self.__access_lock__.acquire()
      locked= self.__islocked__
      self.__access_lock__.release()
      if not locked:
         self.__parent__.out_scope(s)
      return (frame)
