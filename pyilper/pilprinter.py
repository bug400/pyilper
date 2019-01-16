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
from .pilconfig import PILCONFIG
from .pilwidgets import cls_tabtermgeneric, T_STRING
from .pildevbase import cls_pildevbase
from .pilcharconv import CHARSET_HP71, charsets, icharconv
#
# Generic printer tab classes -------------------------------------------------
#
# Changelog
# 01.08.2017 jsi
# - refactoring: printer tab classes moved to this file
# 03.09.2017 jsi
# - register pildevice is now method of commobject
# 04.01.2018 jsi
# - flush log after a line feed was encountered
# 16.01.2018 jsi
# - adapted to cls_tabtermgeneric, implemented cascading config menu
# 28.01.2018 jsi
# - fixed charset configuration
# 16.01.2018 jsi
# - use int instead char for printer data
#
class cls_tabprinter(cls_tabtermgeneric):

   def __init__(self,parent,name):
      super().__init__(parent,name)
#
#     init local configuration parameters
#
      self.charset=PILCONFIG.get(self.name,"charset",CHARSET_HP71)
#
#     add logging
#
      self.add_logging()
#
#     add printer config options to cascading menu
#
      self.cBut.add_option("Character set","charset",T_STRING,charsets)
#
#     create HP-IL device and let the GUI object know it
#
      self.pildevice= cls_pilprinter(self,self.guiobject)
      self.guiobject.set_pildevice(self.pildevice)
      self.guiobject.set_charset(self.charset)

      self.cBut.config_changed_signal.connect(self.do_tabconfig_changed)
#
#  handle changes of the character set
#
   def do_tabconfig_changed(self):
      param= self.cBut.get_changed_option_name()
#
#     change local config parameters
#
      if param=="charset":
         self.charset= PILCONFIG.get(self.name,"charset")
         self.guiobject.set_charset(self.charset)

      super().do_tabconfig_changed()

   def enable(self):
      super().enable()
      self.parent.commthread.register(self.pildevice,self.name)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active"))
#
#   output a character to the terminal and perform logging
#
   def out_printer(self,t):
      self.guiobject.out_terminal(t)
      if t !=8 and t != 13:
         self.cbLogging.logWrite(icharconv(t,self.charset))
      if t== 10:
         self.cbLogging.logFlush()
#
#  callback reset terminal
#
   def reset_printer(self):
      self.guiobject.reset()
#
# Generic HPIL printer class -------------------------------------------------
#
# Initial release derived from ILPER 1.4.3 for Windows
#
# Changelog
#
# 09.02.2015 Improvements and changes of IPLER 1.5
# - fixed __fprinter__ handling in do_cmd LAD/SAD
# - not implemented: auto extended address support switch
# - not implemeted: set/get AID, ID$
# 30.05.2015 fixed error in handling AP, added getstatus
# 06.10.2015 jsi:
# - class statement syntax update
# 23.11.2015 jsi:
# - removed SSRQ/CSRQ approach
# 29.11.2015 jsi:
# - introduced device lock
# 07.02.2016 jsi
# - refactored and merged new Ildev base class of Christoph Giesselink
# 09.02.2016 jsi
# - clear device implemented
# 09.07.2017 jsi
# - register_callback_output and register_callback_clear implemented (from base 
#   class)
class cls_pilprinter(cls_pildevbase):

   def __init__(self,parent,guiobject):

      super().__init__()
      self.__aid__ = 0x2E         # accessory id = printer
      self.__defaddr__ = 3        # default address alter AAU
      self.__did__ = "PRINTER"    # device id
      self.__fesc__ = False       # no escape sequence
      self.__parent__= parent     # parent object
      self.__guiobject__= guiobject
#
#
# private (overloaded) ----------
#
#
#  print and handle special characters
#
   def __indata__(self,frame):

      t=frame & 0xFF
#
#     no escape squence 
#
      if not self.__fesc__:
         if t == 27:
            self.__fesc__ = True
         if not self.__fesc__:
            self.__access_lock__.acquire()
            locked= self.__islocked__
            self.__access_lock__.release()
            if not locked:
               self.__parent__.out_printer(t)
#
#     ignore escape sequences
#
      else:
         self.__fesc__= False

#
#  clear device: reset terminal via callback
#
   def __clear_device__(self):
      super().__clear_device__()
      self.__guiobject__.reset_terminal()
      return
