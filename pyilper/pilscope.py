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

from PyQt5 import  QtWidgets
from .pilconfig import PILCONFIG
from .pilwidgets import cls_tabtermgeneric
from .pildevbase import cls_pildevbase

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
      super().__init__(parent,name,True,False)
      self.showIdy= PILCONFIG.get(self.name,"showidy",False)
      self.cbShowIdy= QtWidgets.QCheckBox("Show IDY frames")
      self.cbShowIdy.setChecked(self.showIdy)
      self.cbShowIdy.setEnabled(False)
      self.cbShowIdy.stateChanged.connect(self.do_show_idy)
      self.hbox2.addWidget(self.cbShowIdy)

      self.displayMode= PILCONFIG.get(self.name,"displaymode",LOG_INBOUND)
      self.lbltxtc=QtWidgets.QLabel("Display mode ")
      self.comboDisplayMode=QtWidgets.QComboBox()
      for txt in display_mode:
         self.comboDisplayMode.addItem(txt)
         self.hbox2.addWidget(self.lbltxtc)
         self.hbox2.addWidget(self.comboDisplayMode)
      self.comboDisplayMode.activated[str].connect(self.do_changeDisplayMode)
      self.comboDisplayMode.setCurrentIndex(self.displayMode)
      self.comboDisplayMode.setEnabled(False)

      self.logMode= PILCONFIG.get(self.name,"logmode",LOG_INBOUND)
      self.lbltxtc=QtWidgets.QLabel("Log mode ")
      self.comboLogMode=QtWidgets.QComboBox()
      for txt in log_mode:
         self.comboLogMode.addItem(txt)
         self.hbox2.addWidget(self.lbltxtc)
         self.hbox2.addWidget(self.comboLogMode)
      self.comboLogMode.activated[str].connect(self.do_changeLogMode)
      self.comboLogMode.setCurrentIndex(self.logMode)
      self.comboLogMode.setEnabled(False)

      self.hbox2.addStretch(1)
      self.scope_charpos=0
      self.pildevice= cls_pilscope(True,self)
      self.pildevice2= cls_pilscope(False,self)
      self.guiobject.set_pildevice(self.pildevice)

   def enable(self):
      super().enable()
      self.parent.commthread.register(self.pildevice,self.name)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode == LOG_OUTBOUND))
      self.cbShowIdy.setEnabled(True)
      self.pildevice.set_show_idy(self.showIdy)
      self.comboLogMode.setEnabled(True)
      self.comboDisplayMode.setEnabled(True)

   def post_enable(self):
      self.parent.commthread.register(self.pildevice2,self.name)
      self.pildevice2.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode== LOG_INBOUND))
      self.pildevice2.set_show_idy(self.showIdy)

   def disable(self):
      super().disable()
      self.cbShowIdy.setEnabled(False)
      self.comboLogMode.setEnabled(False)
      self.comboDisplayMode.setEnabled(False)

   def do_changeLogMode(self,text):
      self.logMode=self.comboLogMode.findText(text)
      PILCONFIG.put(self.name,'logmode',self.logMode)
      self.pildevice.setlocked(True)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode == LOG_OUTBOUND))
      self.pildevice.setlocked(False)
      self.pildevice2.setlocked(True)
      self.pildevice2.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode == LOG_INBOUND))
      self.pildevice2.setlocked(False)

   def do_changeDisplayMode(self,text):
      self.displayMode=self.comboDisplayMode.findText(text)
      PILCONFIG.put(self.name,'displaymode',self.displayMode)
      self.pildevice.set_displayMode(self.displayMode)
      self.pildevice2.set_displayMode(self.displayMode)

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
#  action: show idy frames checkbox 
#
   def do_show_idy(self):
      self.cbShowIdy.setEnabled(False)
      self.showIdy= self.cbShowIdy.isChecked()
      PILCONFIG.put(self.name,"showidy",self.showIdy)
      self.pildevice.set_show_idy(self.showIdy)
      self.pildevice2.set_show_idy(self.showIdy)
      self.cbShowIdy.setEnabled(True)
#
#
#  forward character to the terminal frontend widget and do logging
#
   def out_scope(self,s):
#     ts= datetime.datetime.now()
#     print("%s %d:%d:%d:%d %s" % (self.name,ts.hour, ts.minute, ts.second, ts.microsecond, s))
      l=len(s) 
      if self.scope_charpos+l>=self.guiobject.get_cols() :
         self.guiobject.out_terminal("\x0D")
         self.guiobject.out_terminal("\x0A")
         self.cbLogging.logWrite("\n")
         self.cbLogging.logFlush()
         self.scope_charpos=0
      for i in range(0,len(s)):
         self.guiobject.out_terminal(s[i])
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

class cls_pilscope(cls_pildevbase):

   def __init__ (self, inbound,parent):
      super().__init__()
      self.__inbound__= inbound
      self.__mnemo__= ["DAB", "DSR", "END", "ESR", "CMD", "RDY", "IDY", "ISR"]
      self.__scmd0__= ["NUL", "GTL", "???", "???", "SDC", "PPD", "???", "???",
                    "GET", "???", "???", "???", "???", "???", "???", "ELN",
                    "NOP", "LLO", "???", "???", "DCL", "PPU", "???", "???",
                    "EAR", "???", "???", "???", "???", "???", "???", "???" ]
      self.__scmd9__= ["IFC", "???", "REN", "NRE", "???", "???", "???", "???",
                    "???", "???", "AAU", "LPD", "???", "???", "???", "???"]
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
         return (frame)

      n= frame & 255
      s= "{:3s} {:02X}".format(self.__mnemo__[frame // 256], n)
      
#
#     CMD
#
      if (frame & 0x700) == 0x400 :
         t= n // 32
         
         if t == 0:
            s= self.__scmd0__[n & 31 ]
         elif t == 1:
            if (n & 31) == 31:
               s="UNL"
            else:
               s= "LAD {:02X}".format( n & 31)
         elif t == 2:
            if (n & 31) == 31:
               s="UNT"
            else:
               s= "TAD {:02X}".format( n & 31)
         elif t == 3:
            s= "SAD {:02X}".format( n & 31)
         elif t == 4:
            if (n & 31) < 16:
               s= "PPE {:02X}".format( n & 31)
            else:
               s= self.__scmd9__[n & 15]
         elif t == 5:
            s= "DDL {:02X}".format( n & 31)
         elif t == 6:
            s= "DDT {:02X}".format( n & 31)
         if s[0] =="?":
            s="CMD {:02x}".format(n)
      else:
#
#        RDY
#
         if (frame & 0x700) == 0x500:
            if n < 128:
               if n == 0:
                  s= "RFC"
               elif n == 64:
                  s= "ETO"
               elif n == 65:
                  s= "ETE"
               elif n == 66:
                  s= "NRD"
               elif n == 96:
                  s= "SDA"
               elif n == 97:
                  s= "SST"
               elif n== 98:
                  s = "SDI"
               elif n == 99:
                  s = "SAI"
               elif n == 100:
                  s = "TCT"
               else:
                  s = "RDY {:2X}".format(n)
            else:
               t= n // 32
               if t == 4:
                  s = "AAD {:2X}".format(n & 31)
               elif t == 5:
                  s = "AEP {:2X}".format(n & 31)
               elif t == 6:
                  s = "AES {:2X}".format(n & 31)
               elif t == 7:
                  s = "AMP {:2X}".format(n & 31)
               else:
                  s = "RDY {:2X}".format(n)

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
