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

import queue
import threading
import array
from .pilconfig import PILCONFIG
from .pilwidgets import cls_tabtermgeneric, T_STRING
from .pilkeymap import KEYBOARD_TYPE_HP71, keyboardtypes
from .pildevbase import cls_pildevbase
from .pilcharconv import CHARSET_HP71, charsets
#
# Terminal tab object classes ----------------------------------------------
#
# Changelog
#
# 03.09.2017 jsi
# - register pildevice is now method of commobject
# 14.09.2017 jsi
# - refactoring, keyboard input is disabled if device not active
# 17.11.2017 jsi
# - moved reconfigure method to cls_tabtermgeneric
# 16.01.2018 jsi
# - adapted to cls_tabtermgeneric, implemented cascading config menu
# 28.01.2018 jsi
# - fixed charset configuration
# 14.02.2019 jsi
# - added keyboard type configuration
# 16.02.2019 jsi
# - put int not char on termqueue

class cls_tabterminal(cls_tabtermgeneric):

   def __init__(self,parent,name):
      super().__init__(parent,name)
#
#     init local configuration parameters
#
      self.charset=PILCONFIG.get(self.name,"charset",CHARSET_HP71)
      self.keyboardtype=PILCONFIG.get(self.name,"keyboardtype",KEYBOARD_TYPE_HP71)
#
#     add terminal config options to cascading menu
#
      self.cBut.add_option("Character set","charset",T_STRING,charsets)
      self.cBut.add_option("Keyboard type","keyboardtype",T_STRING,keyboardtypes)
#
#     create HP-IL device and let the GUI object know it
#
      self.pildevice= cls_pilterminal(self.guiobject)
      self.guiobject.set_pildevice(self.pildevice)
      self.guiobject.set_charset(self.charset)
      self.guiobject.set_keyboardtype(self.keyboardtype)
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

      if param=="keyboardtype":
         self.keyboardtype= PILCONFIG.get(self.name,"keyboardtype")
         self.guiobject.set_keyboardtype(self.keyboardtype)

      super().do_tabconfig_changed()
#
#     enable/disable
#
   def enable(self):
      super().enable()
      self.parent.commthread.register(self.pildevice,self.name)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active"))
      self.guiobject.enable_keyboard()

   def disable(self):
      super().disable()
      self.guiobject.disable_keyboard()
#
#     enable keyboard only if terminal active
#
   def toggle_active(self):
      if self.active:
         self.guiobject.enable_keyboard()
      else:
         self.guiobject.disable_keyboard()
#
# HP-IL virtual terminal object class ---------------------------------------
#
# Initial release derived from ILPER 1.43 for Windows
#
# Changelog
#
# 09.02.2015: Improvements and fixes from ILPER 1.50
# - fixed __fterminal__ handling in do_cmd LAD/SAD
# - not implemented: auto extended address support switch
# - not implemeted: set/get AID, ID$
#
# 30.05.2015 jsi:
# - fixed error in handling AP, added getstatus
# 06.10.2015 jsi:
# - class statement syntax updates
# 14.11.2015 jsi:
# - idy frame srq bit handling
# 21.11.2015 jsi:
# - removed SSRQ/CSRQ approach
# - set SRQ flag if keyboard buffer is not empty
# 28.11.2015 jsi:
# - removed delay in __outdta__
# 29.11.2015 jsi:
# - introduced device lock
# 29.01.2016 cg:
# - fixed Python syntax error in SST frame handler
# 01.02.2016 jsi:
# - corrected check SDA/SDI/SST? against 0x02 in do_doe
# - improved internal documentation
# 07.02.2016 jsi:
# - refactored to use new pildevbase class
# 08.02.2016 jsi:
# - removed kbdqueue lock, used status_lock instead, rearranged locked code in
#   queueOutput and __outdata__
# - reset keyboard queue if device clear
# - rearrange code in __outdata__, keyboard data avialable flag is cleared after
#   the last byte in the buffer was sent.
# 20.02.2016 jsi:
# - queueOutput now handles complete escape sequences
# - ATTN is ignored if the keyboard queue is not empty
# 06.03.2016 jsi:
# - use no blocking queue get   
# 09.08.2017 jsi:
# - register_callback_output and register_callback_clear implemented (from base
#   class
# 14.09.2017 jsi:
# - refactoring
# 27.09.2017 jsi
# - code to output data to HP-IL rewritten
#
class cls_pilterminal(cls_pildevbase):

   def __init__(self,guiobject):
      super().__init__()

      self.__aid__ = 0x3E              # accessory id = general interface
      self.__defaddr__ = 8             # default address alter AAU
      self.__did__ = "PILTERM"         # device id
      self.__guiobject__= guiobject    # terminal gui object
#
#     initialize HP-IL outdata buffer
#
      self.__outbuf__= array.array('i')
      self.__oc__=0

#
# public --------
#
#  put character or escape sequence to HP-IL outdata queue, called by terminal frontend
#
   def putDataToHPIL(self,c):
      self.__status_lock__.acquire()
      self.__outbuf__.insert(0, c)
      self.__oc__+=1
      self.__status__ = self.__status__ | 0x50 # set ready for data and srq bit
      self.__status_lock__.release()
#
# private (overloaded) --------
#
#  forward data coming from HP-IL to the terminal frontend widget
#
   def __indata__(self,frame):
      self.__access_lock__.acquire()
      locked= self.__islocked__
      self.__access_lock__.release()
      if not locked:
         self.__guiobject__.out_terminal(frame & 0xFF)
#
#  clear device: empty HP-IL outdata buffer and reset terminal
#
   def __clear_device__(self):
      super().__clear_device__()              # this clears srq
      self.__status_lock__.acquire()
      self.__oc__=0
      self.__outbuf__= array.array('i')
      self.__status__= self.__status__ & 0xEF # clear ready for data
      self.__status_lock__.release()

#
#     reset device
#
      self.__guiobject__.reset_terminal() 
      return
#
#  send data from HP-IL outdata buffer to the loop
#
   def __outdata__(self,frame):
      self.__status_lock__.acquire()
      self.__status__= self.__status__ & 0xBF # clear srq bit
      if self.__oc__== 0:
         frame= 0x540 # EOT
      else:
         frame= self.__outbuf__.pop()
         self.__oc__-=1
         if self.__oc__== 0:
            self.__status__= self.__status__ & 0xEF # clear ready for data bit
      self.__status_lock__.release()
      return(frame)
