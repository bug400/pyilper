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
# pyILPER widget classes ----------------------------------------------------
#
# Changelog
# 24.09.2015 cg
# - fixed loading file in cls_HelpWindow() when file path contain special characters
# - fixed name in cls_AboutWindow() text
# - fixed some errors at error condition
# - expanded LIF filename filter with *.lif and *.LIF extention
# 05.10.2015 jsi: 
# - new style signal/slot handling for quit, crash and show_message
# - new style signal/slot handling for bottonBox widget
# - adjust super statements to python3+ syntax
# - removed unusable code to resize main window
# 20.10.2015 jsi
# - fix leading // for docpath (OSX)
# 24.10.2015 jsi
# - use non native menus only (OSX issues)
# - removed ) from date of medium formatted
# 21.11.2015 jsi
# - introduced show IDY frames option in scope tab
# 29.11.2015 jsi
# - working directory is default when opening lif files
# - do not check lif medium version
# - invalid layout if all media information are zero
# - refresh dir list if drive has not been talker for nn seconds
# - use device lock instead of pausing PIL-Loop
# 30.11.2015 jsi
# - introduced idy frame option
# 01.12.2015 jsi
# - clear dirlist if illegal medium is mounted
# 18.12.2015 jsi
# - added dropdown command button in drive tab
# - added context menu for entries in directory listing
# 22.12.2015 jsi
# - added navigation buttons to the help window 
# - make help window resizeable
# 28.12.2015 jsi
# - do_cbActive: check for method toggle_active fixed
# 31.12.2015 jsi
# - add view option to context menu
# 03.01.2016 jsi
# - added label option to dropdown command menu
# - filename and drivetype controls are disabled if the drive is enabled
# - rename 'Help' menu entry to 'Manual'
# 05.01.2016 jsi
# - initialize filename an drivetype controls properly at program start
# 06.01.2016 jsi
# - initialize charset properly at program start
# - use utf-8-sig as charset for logging
# 08.01.2016 jsi
# - introduced lifcore, refactoring
# - do not lock pildevice, if pyilper is disabled
# 10.01.2016 jsi
# - show tooltips for disabled controls in the drive tab
# 16.01.2016 jsi
# - revert disabling filename and drivetype controls if the drive is enabled
# - allow arbitrary disk layouts 
# 29.01.2016 jsi
# - improve os detection
# 30.01.2016 jsi
# - enable file management controls only if a compatible version of the LIF
#   utilities is installed
# - use font metrics to determine terminal window size
# - removed experimental mark from TCP/IP configuration
# 31.01.2016 jsi
# - added workdir parameter to call of cls_lifview
# 01.02.2016 jsi
# - added InstallCheck menu callback
# 07.02.2016 jsi:
# - renamed register callbacks because of code recatoring of the virtual HP-IL devices
# 19.02.2016 jsi:
# - added character set combo box to cls_tabdrive
# - put text in front of the combo boxes at the bottom of the tabs
# 26.02.2016 jsi:
# - do not update terminal, if not visible
# 28.02.2016 jsi:
# - removed insert/replace indicator for the terminal widget
# 02.03.2016 jsi:
# - removed the terminal size combobox for the terminal widget
# - added the following configuration options to the pyilper configuration for
#   the generic terminal: terminal size, color scheme, character size
# 05.03.2016 jsi:
# - improved HP-IL device status window
# 12.03.2016 jsi:
# - set terminal output queue poll timer to 25ms
# 13.03.2016 jsi:
# - modified exit of modal dialogs
# 21.03.2016 jsi:
# - refactored interface to HPTerm
# - modified parameters of cls_ui
# 27.03.2016 jsi:
# - moved virtual HP-IL device status to utilities menu
# 01.04..2016 jsi:
# - added copy function for PILIMAGE.DAT to the utlity menu
# 05.04.2016 jsi:
# - issue warinings about invalid LIF headers only when mounting those files, hint by cg
# 07.04.2016 cg
# added 230400 baud to baudrate combo box
# 12.04.2016 cg
# get available Windows COM ports from registry
# 14.04.2016 jsi
# - corrected all files filter to * in the file dialog
# 17.04.2016 jsi
# - catch winreg access error if no COM port is available
# 19.04.2016 jsi
# - modified serial device filtering for MAC OS X
# 25.04.2016 jsi
# - remove baudrate configuration
# 27.04.2016 jsi
# - do not set path for QFileDialog, it remembers the last directory automatically
# 28.04.2016 jsi
# - enable tabscope to log inbound, outbound and both traffic
# 29.04.2016 jsi
# - log scope unbuffered
# 07.05.2016 jsi
# - make scroll up buffer size configurable
# 08.05.2016 jsi
# - refactoring of PilConfigWindow, make autobaud/baudrate setting configurable again
# 17.06.2016 jsi
# - refactoring, use constant to access configuration
# - refactoring, move constants to pilcore.py
# - refactoring, use platform functions from pilcore.py
# 27.08.2016 jsi
# - tab configuration rewritten
# 18.09.2016 jsi
# - configurable device sequence added
# 04.10.2016 jsi
# - renamed sequence to position in the menu entry
# 05.10.2016 jsi
# - redraw terminal widgets if parent window was resized
# 13.10.2016 jsi
# - device configuration rewritten, configure devices and their position in one dialogue
#   now.
# 19.10.2016 jsi
# - plotter tab widget added (merged)
# - pen definition dialog added (merged)
# - webkit/webendine handling added (experimental)
# 24.10.2016 jsi
# - show python and qt version in the About window
# 04.12.2016 jsi
# - allow LIF directories not starting at record 2
# 11.12.2016 jsi
# - extend configuration regarding pipes (Linux and Mac OS only)
# 07.01.2016 jsi
# - extended cls_HelpWindow to load arbitrary html files
# 04.02.2016 jsi
# - added missing argument to sortbyColumn (QT5 fix)
# 19.02.2017 jsi
# - font size of the directory listing of the LifDirWidget can now be configured. The
#   row height is now properly adjusted to the font height
#
import os
import glob
import datetime
import time
import re
import pyilper
import sys
from PyQt4 import QtCore, QtGui
HAS_WEBKIT=False
HAS_WEBENGINE=False
try:
   from PyQt4 import QtWebKit
   HAS_WEBKIT= True
except:
   pass
try:
   from PyQt4 import QtWebEngineWidgets
   HAS_WEBENGINE=True
except:
   pass
if HAS_WEBKIT and HAS_WEBENGINE:
   HAS_WEBENGINE=False
from .lifutils import cls_LifFile,cls_LifDir,LifError, getLifInt
from .pyplotter import cls_PlotterWidget, cls_HP7470
from .pilqterm import QScrolledTerminalWidget,HPTerminal
from .pilscope import cls_scope
from .pilprinter import cls_printer
from .pilterminal import cls_terminal
from .pildrive import cls_drive
from .pilplotter import cls_plotter
from .pilcharconv import charconv, CHARSET_HP71, CHARSET_HP41, CHARSET_ROMAN8, charsets
from .pilconfig import PilConfigError, PILCONFIG
from .penconfig import PenConfigError, PENCONFIG
from .pilcore import *
if isWINDOWS():
   import winreg
from .lifcore import *
from .lifexec import cls_lifpack, cls_lifpurge, cls_lifrename, cls_lifexport, cls_lifimport, cls_lifview, cls_liflabel, check_lifutils


#
# Logging check box
#
class LogCheckboxWidget(QtGui.QCheckBox):
   def __init__(self,text,filename):
      super().__init__(text)
      self.filename=filename
      self.log= None

   def logOpen(self):
      try:
         self.log=open(self.filename,"a",encoding="UTF-8-SIG")
         self.log.write("\nBegin log "+self.filename+" at ")
         self.log.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
         self.log.write("\n")
      except OSError as e:
         reply=QtGui.QMessageBox.critical(self,'Error',"Cannot open log file: "+ e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)

   def logClose(self):
      try:
         self.log.write("\nEnd log "+self.filename+" at ")
         self.log.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
         self.log.write("\n")
         self.log.close()
         self.log= None
      except OSError as e:
         reply=QtGui.QMessageBox.critical(self,'Error',"Cannot close log file: "+ e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)

   def logWrite(self,line):
      if self.log is None:
         return
      try:
         self.log.write(line)
      except OSError as e:
         reply=QtGui.QMessageBox.critical(self,'Error',"Cannot write to log file: "+ e.strerror+". Logging disabled",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         try:
            self.log.close()
         except OSError:
            pass
         self.log = None

   def logFlush(self):
      if self.log is None:
         return
      try:
         self.log.flush()
      except OSError as e:
         reply=QtGui.QMessageBox.critical(self,'Error',"Cannot write to log file: "+ e.strerror+". Logging disabled",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         try:
            self.log.close()
         except OSError:
            pass
         self.log = None

#
# abstract class
#
class cls_tabgeneric(QtGui.QWidget):

   def __init__(self,parent,name):

      super().__init__()
      self.name= name
      self.active= PILCONFIG.get(self.name,"active",False)
      self.parent=parent
      self.font_name=FONT
      self.font_size=0
      self.font_width=0
      self.font_height=0
      self.width= 0
      self.height= 0

      self.cbActive= QtGui.QCheckBox('Device enabled')
      self.cbActive.setChecked(self.active)
      self.cbActive.setEnabled(False)
      self.cbActive.stateChanged.connect(self.do_cbActive)

      self.pildevice=None


   def disable(self):
      self.cbActive.setEnabled(False)

   def enable(self):
      self.cbActive.setEnabled(True)

   def do_cbActive(self):
      self.active= self.cbActive.isChecked()
      PILCONFIG.put(self.name,"active",self.active)
      self.pildevice.setactive(self.active)
      try:
         self.toggle_active()
      except AttributeError:
         pass
      return
#
# plotter widget ----------------------------------------------------------
#
class cls_tabplotter(cls_tabgeneric):

   LOGLEVEL=["HP-GL","HP-GL+Status","HP-GL+Status+Commands"]

   def __init__(self,parent,name):
      super().__init__(parent,name)
      self.name=name
      self.logging= PILCONFIG.get(self.name,"logging",False)
      self.loglevel= PILCONFIG.get(self.name,"loglevel",0)
#
#     Build gui
#
      self.qplotter=cls_PlotterWidget(self,self.name)

      self.hbox1= QtGui.QHBoxLayout()
      self.hbox1.addWidget(self.qplotter)
      self.hbox1.setAlignment(self.qplotter,QtCore.Qt.AlignHCenter)
      self.hbox1.setContentsMargins(20,20,20,20)
      self.hbox2= QtGui.QHBoxLayout()
      self.hbox2.addWidget(self.cbActive)
      self.hbox2.setAlignment(self.cbActive,QtCore.Qt.AlignLeft)

      self.cbLogging= LogCheckboxWidget("Log "+self.name,self.name+".log")
      self.hbox2.addWidget(self.cbLogging)
      self.hbox2.setAlignment(self.cbLogging,QtCore.Qt.AlignLeft)

      self.lbltxtc=QtGui.QLabel("Log level ")
      self.comboLoglevel=QtGui.QComboBox()
      for txt in self.LOGLEVEL:
          self.comboLoglevel.addItem(txt)
      self.hbox2.addWidget(self.lbltxtc)
      self.hbox2.addWidget(self.comboLoglevel)

      self.hbox2.addStretch(1)

      self.hbox2.setContentsMargins(10,3,10,3)
      self.vbox= QtGui.QVBoxLayout()
      self.vbox.addLayout(self.hbox1)
      self.vbox.addLayout(self.hbox2)
      self.setLayout(self.vbox)
      self.plotter=cls_HP7470(self,self.name)

      self.cbLogging.setChecked(self.logging)
      self.cbLogging.setEnabled(False)
      self.cbLogging.stateChanged.connect(self.do_cbLogging)

      self.comboLoglevel.activated[str].connect(self.do_changeLoglevel)
      self.comboLoglevel.setCurrentIndex(self.loglevel)
      self.comboLoglevel.setEnabled(False)

   def do_cbLogging(self):
      self.cbLogging.setEnabled(False)
      self.logging= self.cbLogging.isChecked()
      self.pildevice.setlocked(True)
      if self.logging:
         self.cbLogging.logOpen()
      else:
         self.cbLogging.logClose()
      PILCONFIG.put(self.name,"logging",self.logging)
      self.pildevice.setlocked(False)
      self.cbLogging.setEnabled(True)

   def do_changeLoglevel(self,text):
      self.loglevel=self.comboLoglevel.currentIndex()
      PILCONFIG.put(self.name,'loglevel',self.loglevel)

   def enable(self):
      super().enable()
      self.pildevice= cls_plotter()
      self.parent.commobject.register(self.pildevice,self.name)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active"))
      self.pildevice.register_callback_output(self.plotter.process_char)
      self.pildevice.register_callback_clear(self.plotter.reset)
      self.plotter.set_outfunc(self.pildevice.setOutput)
      self.plotter.set_statfunc(self.pildevice.set_status)
      self.cbLogging.setEnabled(True)
      self.comboLoglevel.setEnabled(True)
      if self.logging:
         self.cbLogging.logOpen()
      self.plotter.enable()
      self.qplotter.enable()

   def disable(self):
      self.plotter.disable()
      self.qplotter.disable()
      if self.logging:
         self.cbLogging.logClose()
      self.cbLogging.setEnabled(False)
      self.comboLoglevel.setEnabled(False)
      super().disable()
#
#  becomes visible, refresh content, activate update and blink
#
   def becomes_visible(self):
      self.qplotter.becomes_visible()
      return
#
#  becomes invisible, deactivate update and blink
#
   def becomes_invisible(self):
      self.qplotter.becomes_invisible()
      return
#
# generic terminal widget ----------------------------------------------------
#
class cls_tabtermgeneric(cls_tabgeneric):

   def __init__(self,parent,name,cblog,cbcharset):
      super().__init__(parent,name)
      self.cblog= cblog
      self.cbcharset= cbcharset
      self.kbd_delay=False
#
#     Set default values
#
      self.termsize=PILCONFIG.get("pyilper","terminalsize")
      self.cols=int(self.termsize.split(sep="x")[0])
      self.rows=int(self.termsize.split(sep="x")[1])
#
      self.colorscheme=PILCONFIG.get("pyilper","colorscheme")
#
      self.font_size=PILCONFIG.get("pyilper","terminalcharsize")
#
      if self.cblog:
         self.logging= PILCONFIG.get(self.name,"logging",False)
      if self.cbcharset:
         self.charset= PILCONFIG.get(self.name,"charset",CHARSET_HP71)

#
#     Build GUI 
#
      self.scrollupbuffersize=PILCONFIG.get("pyilper","scrollupbuffersize")
      if self.scrollupbuffersize < self.rows:
         self.scrollupbuffersize= self.rows

      self.qterminal=QScrolledTerminalWidget(self,self.font_name, self.font_size, self.cols, self.rows,self.colorscheme)

      self.hbox1= QtGui.QHBoxLayout()
      self.hbox1.addStretch(1)
      self.hbox1.addWidget(self.qterminal)
      self.hbox1.setAlignment(self.qterminal,QtCore.Qt.AlignHCenter)
      self.hbox1.setContentsMargins(20,20,20,20)
      self.hbox1.addStretch(1)
      self.hbox2= QtGui.QHBoxLayout()
      self.hbox2.addWidget(self.cbActive)
      self.hbox2.setAlignment(self.cbActive,QtCore.Qt.AlignLeft)
      if self.cblog:
         self.cbLogging= LogCheckboxWidget("Log "+self.name,self.name+".log")
         self.hbox2.addWidget(self.cbLogging)
         self.hbox2.setAlignment(self.cbLogging,QtCore.Qt.AlignLeft)
      if self.cbcharset:
         self.lbltxtc=QtGui.QLabel("Charset ")
         self.comboCharset=QtGui.QComboBox()
         for txt in charsets:
            self.comboCharset.addItem(txt)
         self.hbox2.addWidget(self.lbltxtc)
         self.hbox2.addWidget(self.comboCharset)
      self.hbox2.setContentsMargins(10,3,10,3)
      self.hbox2.addStretch(1)
      self.vbox= QtGui.QVBoxLayout()
      self.vbox.addLayout(self.hbox1)
      self.vbox.setAlignment(self.hbox1,QtCore.Qt.AlignTop)
      self.vbox.addLayout(self.hbox2)
      self.vbox.setAlignment(self.hbox2,QtCore.Qt.AlignTop)
      self.setLayout(self.vbox)
      self.hpterm=HPTerminal(self.cols,self.rows,self.scrollupbuffersize,self.qterminal)
#
#     initialize logging checkbox
#
      if self.cblog:
         self.cbLogging.setChecked(self.logging)
         self.cbLogging.setEnabled(False)
         self.cbLogging.stateChanged.connect(self.do_cbLogging)
#
#     initialize charset combo box
#
      if self.cbcharset:
         self.comboCharset.activated[str].connect(self.do_changeCharset)
         self.comboCharset.setCurrentIndex(self.charset)
         self.comboCharset.setEnabled(False)
         self.hpterm.set_charset(self.charset)
#
#     catch resize event to redraw the terminal window
#
   def resizeEvent(self,event):
      self.qterminal.redraw()


   def do_cbLogging(self):
      self.cbLogging.setEnabled(False)
      self.logging= self.cbLogging.isChecked()
      self.pildevice.setlocked(True)
      if self.logging:
         self.cbLogging.logOpen()
      else:
         self.cbLogging.logClose()
      PILCONFIG.put(self.name,"logging",self.logging)
      self.pildevice.setlocked(False)
      self.cbLogging.setEnabled(True)

   def do_changeCharset(self,text):
      self.charset=self.comboCharset.findText(text)
      PILCONFIG.put(self.name,'charset',self.charset)
      self.pildevice.setlocked(True)
      self.hpterm.set_charset(self.charset)
      self.pildevice.setlocked(False)

   def enable(self):
      super().enable()
      if self.cblog:
         self.cbLogging.setEnabled(True)
         if self.logging:
            self.cbLogging.logOpen()
      if self.cbcharset:
         self.comboCharset.setEnabled(True)

   def disable(self):
      super().disable()
      if self.cblog:
         if self.logging:
            self.cbLogging.logClose()
         self.cbLogging.setEnabled(False)
      if self.cbcharset:
         self.comboCharset.setEnabled(False)
      self.pildevice= None
#
#  becomes visible, refresh content, activate update and blink
#
   def becomes_visible(self):
      self.hpterm.becomes_visible()
      return
#
#  becomes invisible, deactivate update and blink
#
   def becomes_invisible(self):
      self.hpterm.becomes_invisible()
      return
#
# tabscope widget ----------------------------------------------------
#
LOG_INBOUND=0
LOG_OUTBOUND=1
LOG_BOTH=2
log_mode= ["Inbound", "Outbound", "Both"]

class cls_tabscope(cls_tabtermgeneric):

   def __init__(self,parent,name):
      super().__init__(parent,name,True,False)
      self.showIdy= PILCONFIG.get(self.name,"showidy",False)
      self.cbShowIdy= QtGui.QCheckBox("Show IDY frames")
      self.cbShowIdy.setChecked(self.showIdy)
      self.cbShowIdy.setEnabled(False)
      self.cbShowIdy.stateChanged.connect(self.do_show_idy)
      self.hbox2.addWidget(self.cbShowIdy)
      self.hbox2.setAlignment(self.cbShowIdy,QtCore.Qt.AlignLeft)

      self.logMode= PILCONFIG.get(self.name,"logmode",LOG_INBOUND)
      self.lbltxtc=QtGui.QLabel("Log mode ")
      self.comboLogMode=QtGui.QComboBox()
      for txt in log_mode:
         self.comboLogMode.addItem(txt)
         self.hbox2.addWidget(self.lbltxtc)
         self.hbox2.addWidget(self.comboLogMode)
      self.comboLogMode.activated[str].connect(self.do_changeLogMode)
      self.comboLogMode.setCurrentIndex(self.logMode)
      self.comboLogMode.setEnabled(True)
      self.hbox2.addStretch(1)
      self.scope_charpos=0
      self.pildevice2= None

   def enable(self):
      super().enable()
      self.pildevice= cls_scope(True)
      self.parent.commobject.register(self.pildevice,self.name)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode == LOG_OUTBOUND))
      self.pildevice.register_callback_output(self.out_scope)
      self.cbShowIdy.setEnabled(True)
      self.pildevice.set_show_idy(self.showIdy)

   def post_enable(self):
      self.pildevice2= cls_scope(False)
      self.parent.commobject.register(self.pildevice2,self.name)
      self.pildevice2.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode== LOG_INBOUND))
      self.pildevice2.register_callback_output(self.out_scope)
      self.pildevice2.set_show_idy(self.showIdy)

   def disable(self):
      super().disable()
      self.cbShowIdy.setEnabled(False)

   def do_changeLogMode(self,text):
      self.logMode=self.comboLogMode.findText(text)
      PILCONFIG.put(self.name,'logmode',self.logMode)
      self.pildevice.setlocked(True)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode == LOG_OUTBOUND))
      self.pildevice.setlocked(False)
      self.pildevice2.setlocked(True)
      self.pildevice2.setactive(PILCONFIG.get(self.name,"active") and not (self.logMode == LOG_INBOUND))
      self.pildevice2.setlocked(False)

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

   def do_show_idy(self):
      self.cbShowIdy.setEnabled(False)
      self.showIdy= self.cbShowIdy.isChecked()
      PILCONFIG.put(self.name,"showidy",self.showIdy)
      self.pildevice.set_show_idy(self.showIdy)
      self.pildevice2.set_show_idy(self.showIdy)
      self.cbShowIdy.setEnabled(True)
#
#  callback output char to console
#
   def out_scope(self,s):
#     ts= datetime.datetime.now()
#     print("%s %d:%d:%d:%d %s" % (self.name,ts.hour, ts.minute, ts.second, ts.microsecond, s))
      self.scope_charpos+=len(s)
      if self.scope_charpos>self.cols :
         self.hpterm.putchar("\x0D")
         self.hpterm.putchar("\x0A")
         self.cbLogging.logWrite("\n")
         self.cbLogging.logFlush()
         self.scope_charpos=0
      for i in range(0,len(s)-1):
         self.hpterm.putchar(s[i])
      self.cbLogging.logWrite(s)
      self.cbLogging.logFlush()
#
# tabprinter widget ------------------------------------------------------
#
class cls_tabprinter(cls_tabtermgeneric):

   def __init__(self,parent,name):
      super().__init__(parent,name,True,True)
      self.hbox2.addStretch(1)

   def enable(self):
      super().enable()
      self.pildevice= cls_printer()
      self.parent.commobject.register(self.pildevice,self.name)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active"))
      self.pildevice.register_callback_output(self.out_printer)
      self.pildevice.register_callback_clear(self.hpterm.reset)

#
#  callback for virtual printer device to output a character 
#
   def out_printer(self,s):
      self.hpterm.putchar(s)
      t=ord(s)
      if t !=8 and t != 13:
         self.cbLogging.logWrite(charconv(s,self.charset))
#
# tabterminal widget ----------------------------------------------
#
class cls_tabterminal(cls_tabtermgeneric):

   def __init__(self,parent,name):
      super().__init__(parent,name, False, True)
      self.hbox2.addStretch(1)
#
#     enable/disable
#
   def enable(self):
      super().enable()
      self.pildevice= cls_terminal()
      self.parent.commobject.register(self.pildevice,self.name)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active"))
      self.pildevice.register_callback_output(self.out_terminal)
      self.pildevice.register_callback_clear(self.hpterm.reset)
      self.hpterm.set_kbdfunc(self.pildevice.queueOutput)

   def disable(self):
      super().disable()
#
#  callback to output character to teminal
#
   def out_terminal(self,s):
      self.hpterm.putchar(s)
#
class cls_tabdrive(cls_tabgeneric):

   DEV_CASS=0
   DEV_DISK=1
   DEV_HDRIVE1=2

   deviceinfo= { }
   deviceinfo[DEV_CASS]=["",0x10]
   deviceinfo[DEV_DISK]=["HP9114B",0x10]
   deviceinfo[DEV_HDRIVE1]=["HDRIVE1",0x10]

   # Medium types
   MEDIUM_CASS=0
   MEDIUM_DISK=1
   MEDIUM_HDRIVE1=2
   MEDIUM_HDRIVE2=3
   MEDIUM_HDRIVE4=4
   MEDIUM_HDRIVE8=5
   MEDIUM_HDRIVE16=6
   MEDIUM_UNKNOWN= -1
   
   mediainfo= { }
   mediainfo[MEDIUM_CASS]=['HP82161A Cassette',2,1,256]
   mediainfo[MEDIUM_DISK]=['HP9114B double sided disk',77,2,16]
   mediainfo[MEDIUM_HDRIVE1]=['HDRIVE1 640K disk',80,2,16]
   mediainfo[MEDIUM_HDRIVE2]=['HDRIVE1 2MB disk',125,1,64]
   mediainfo[MEDIUM_HDRIVE4]=['HDRIVE1 4MB disk',125,2,64]
   mediainfo[MEDIUM_HDRIVE8]=['HDRIVE1 8MB disk',125,4,64]
   mediainfo[MEDIUM_HDRIVE16]=['HDRIVE1 16MB disk',125,8,64]
   mediainfo[MEDIUM_UNKNOWN]=['unknown',0,0,0]
   
   
   def __init__(self,parent,name):
      super().__init__(parent,name)
#
#     Set default values
#
      self.filename= PILCONFIG.get(self.name,"filename","")
      self.drivetype= PILCONFIG.get(self.name,"drivetype",self.DEV_HDRIVE1)
      self.charset= PILCONFIG.get(self.name,"charset",CHARSET_HP71)

#
#     Build GUI 
#
      self.hbox1= QtGui.QHBoxLayout()
      self.lbltxt1=QtGui.QLabel("LIF Image File: ")
      self.lblFilename=QtGui.QLabel()
      self.butFilename=QtGui.QPushButton()
      self.butFilename.setText("change")
      self.hbox1.addWidget(self.lbltxt1)
      self.hbox1.setAlignment(self.lbltxt1,QtCore.Qt.AlignLeft)
      self.hbox1.addWidget(self.lblFilename)
      self.hbox1.setAlignment(self.lblFilename,QtCore.Qt.AlignLeft)
      self.hbox1.addStretch(1)
      self.hbox1.addWidget(self.butFilename)
      self.hbox1.setAlignment(self.butFilename,QtCore.Qt.AlignRight)
      self.hbox1.setContentsMargins(15,10,10,5)

      self.gbox = QtGui.QGroupBox()
      self.gbox.setFlat(True)
      self.gbox.setTitle("Drive Type")
      self.vbox2= QtGui.QVBoxLayout()
      self.radbutCass = QtGui.QRadioButton(self.gbox)
      self.radbutCass.setText("HP82161A")
      self.vbox2.addWidget(self.radbutCass)
      self.radbutDisk = QtGui.QRadioButton(self.gbox)
      self.radbutDisk.setText("HP9114A")
      self.radbutHdrive1 = QtGui.QRadioButton(self.gbox)
      self.vbox2.addWidget(self.radbutDisk)
      self.radbutHdrive1.setText("HDRIVE1")
      self.vbox2.addWidget(self.radbutHdrive1)
      self.gbox.setLayout(self.vbox2)
      self.gbox_buttonlist=[self.radbutCass, self.radbutDisk, self.radbutHdrive1]
      self.vbox3= QtGui.QVBoxLayout()
      self.vbox3.addWidget(self.gbox)
      self.vbox3.setAlignment(self.gbox,QtCore.Qt.AlignTop)
      self.vbox3.addStretch(1)

      self.vbox1= QtGui.QVBoxLayout()
      font_size=PILCONFIG.get("pyilper","directorycharsize")
      self.lifdir=cls_LifDirWidget(self,10,FONT,font_size)
      self.vbox1.addWidget(self.lifdir)

      self.hbox2= QtGui.QHBoxLayout()
      self.hbox2.addLayout(self.vbox1)
      self.hbox2.addLayout(self.vbox3)
      self.hbox2.setAlignment(self.gbox,QtCore.Qt.AlignRight)
      self.hbox2.setContentsMargins(10,3,10,3)

      self.hbox3= QtGui.QHBoxLayout()
      self.hbox3.addWidget(self.cbActive)
      self.hbox3.setAlignment(self.cbActive,QtCore.Qt.AlignLeft)
      self.hbox3.setContentsMargins(10,3,10,3)
#
#     Initialize file management tool bar
#
      self.tBar= QtGui.QToolBar()
      self.tBut= QtGui.QToolButton(self.tBar)
      self.menu= QtGui.QMenu(self.tBut)
      self.tBut.setMenu(self.menu)
      self.tBut.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
      self.actPack= self.menu.addAction("Pack")
      self.actImport= self.menu.addAction("Import")
      self.actLabel=self.menu.addAction("Label")
      self.tBut.setText("Tools")
      self.tBut.setEnabled(False)
      self.hbox3.addWidget(self.tBut)
#
#     Initialize charset combo box
#
      self.lbltxtc=QtGui.QLabel("Charset ")
      self.comboCharset=QtGui.QComboBox()
      for txt in charsets:
         self.comboCharset.addItem(txt)
      self.hbox3.addWidget(self.lbltxtc)
      self.hbox3.addWidget(self.comboCharset)
      self.comboCharset.setEnabled(False)

      self.hbox3.setAlignment(self.tBar,QtCore.Qt.AlignLeft)
      self.hbox3.addStretch(1)

      self.vbox= QtGui.QVBoxLayout()
      self.vbox.addLayout(self.hbox1)
      self.vbox.setAlignment(self.hbox1,QtCore.Qt.AlignTop)
      self.vbox.addLayout(self.hbox2)
      self.vbox.setAlignment(self.hbox2,QtCore.Qt.AlignTop)
      self.vbox.addLayout(self.hbox3)
      self.vbox.setAlignment(self.hbox2,QtCore.Qt.AlignTop)
      self.setLayout(self.vbox)
#
#     basic initialization
#
      self.lblFilename.setText(self.filename)
      self.butFilename.setEnabled(False)
      self.setDrivetypeChecked()
      for w in self.gbox_buttonlist:
         w.setEnabled(False)
      self.lblFilename.setText(self.filename)
      self.lifdir.setFileName(self.filename)
      self.comboCharset.setCurrentIndex(self.charset)

#
#     connect actions
#   
      self.radbutCass.clicked.connect(self.do_drivetypeChanged)
      self.radbutDisk.clicked.connect(self.do_drivetypeChanged)
      self.radbutHdrive1.clicked.connect(self.do_drivetypeChanged)
      self.butFilename.clicked.connect(self.do_filenameChanged)
      self.actPack.triggered.connect(self.do_pack)
      self.actImport.triggered.connect(self.do_import)
      self.actLabel.triggered.connect(self.do_label)
      self.comboCharset.activated[str].connect(self.do_changeCharset)

#
#     refresh timer
#
      self.timer=QtCore.QTimer()
      self.timer.timeout.connect(self.update_hdrive)
      self.update_pending= False
#
#     enable/disable GUI elements
#
      self.toggle_controls()

#
#     enable/disable
#
   def enable(self):
      super().enable()
      self.pildevice= cls_drive(isWINDOWS())
      self.parent.commobject.register(self.pildevice,self.name)
      self.pildevice.setactive(PILCONFIG.get(self.name,"active"))
      did,aid= self.deviceinfo[self.drivetype]
      self.pildevice.setdevice(did,aid)
      status, tracks, surfaces, blocks= self.lifMediumCheck(self.filename,True)
      if not status:
         self.filename=""
         PILCONFIG.put(self.name,'filename',self.filename)
         try:
            PILCONFIG.save()
         except PilConfigError as e:
            reply=QtGui.QMessageBox.critical(self.parent.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      self.pildevice.sethdisk(self.filename,tracks,surfaces,blocks)
      self.lblFilename.setText(self.filename)
      self.lifdir.setFileName(self.filename)

   def disable(self):
      super().disable()
      self.timer.stop()
      self.pildevice= None
#
#  enable/disable lif image file controls:
#  - change drive type
#  - change drive type
#  - tools teardown menu

   def toggle_active(self):
      self.toggle_controls()

   def toggle_controls(self):
      self.butFilename.setEnabled(True)
      for w in self.gbox_buttonlist:
         w.setEnabled(True)
      if self.active:
         self.tBut.setEnabled(False)
         self.comboCharset.setEnabled(False)
         self.tBut.setToolTip("To use this menu, please disable the device first")
      else:
         self.tBut.setToolTip("")
         if self.filename != "" and self.parent.ui.lifutils_installed:
            self.tBut.setEnabled(True)
            self.comboCharset.setEnabled(True)
#
#  set drive type checked
#
   def setDrivetypeChecked(self):
      i=0
      for w in self.gbox_buttonlist:
         if i == self.drivetype:
            w.setChecked(True)
         else:
            w.setChecked(False)
         i+=1
#
#  becomes visible, activate update timer
#
   def becomes_visible(self):
      self.timer.start(REFRESH_RATE)
      return
#
#  becomes invisible, deactivate update timer
#
   def becomes_invisible(self):
      self.timer.stop()
      return
#
#  Callbacks
#
   def do_changeCharset(self,text):
      self.charset=self.comboCharset.findText(text)
      PILCONFIG.put(self.name,'charset',self.charset)

   def do_filenameChanged(self):
      flist= self.get_lifFilename()
      if flist == None:
         return
      status, tracks, surfaces, blocks= self.lifMediumCheck(flist[0],False)
      if status:
         self.filename=flist[0]
      else:
         self.filename=""
      PILCONFIG.put(self.name,'filename',self.filename)
      try:
         PILCONFIG.save()
      except PilConfigError as e:
         reply=QtGui.QMessageBox.critical(self.parent.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)

      if self.pildevice is not None:
         self.pildevice.setlocked(True)
         self.pildevice.sethdisk(self.filename,tracks,surfaces,blocks)
         self.pildevice.setlocked(False)
      self.lblFilename.setText(self.filename)
      self.lifdir.setFileName(self.filename)
      if self.filename=="":
         self.lifdir.clear()
      else:
         self.lifdir.refresh()
      self.toggle_controls()

   def do_drivetypeChanged(self):
      i=0
      for w in self.gbox_buttonlist:
         if w.isChecked():
            self.drivetype=i
            break
         i+=1
      PILCONFIG.put(self.name,'drivetype', self.drivetype)
#
#     remove filename
#
      if self.filename != "":
         self.filename=""
         PILCONFIG.put(self.name,'filename',self.filename)
         self.lblFilename.setText(self.filename)
         self.lifdir.clear()
         reply=QtGui.QMessageBox.warning(self.parent.ui,'Warning',"Drive type changed. You have to reopen the LIF image file",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      did,aid= self.deviceinfo[self.drivetype]
      try:
         PILCONFIG.save()
      except PilConfigError as e:
         reply=QtGui.QMessageBox.critical(self.parent.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      if self.pildevice is not None:
         self.pildevice.setlocked(True)
         self.pildevice.setdevice(did,aid)
         self.pildevice.setlocked(False)
      self.toggle_controls()

   def do_pack(self):
      cls_lifpack.exec(self.filename)
      self.lifdir.refresh()

   def do_import(self):
      workdir=PILCONFIG.get('pyilper','workdir')
      cls_lifimport.exec(self.filename, workdir)
      self.lifdir.refresh()

   def do_label(self):
      oldlabel=self.lifdir.getLabel()
      cls_liflabel.exec(self.filename, oldlabel)
      self.lifdir.refresh()

#
#  Drive tab: refresh directory listing of medium
#
   def update_hdrive(self):
      if self.filename=="":
         return
      if self.pildevice is None:
         return
      tm=time.time()
      modified, timestamp= self.pildevice.ismodified()
      self.update_pending= self.update_pending or modified
      if self.update_pending:
         if tm - timestamp > NOT_TALKER_SPAN:
            self.refreshDirList()
            self.update_pending= False

   def refreshDirList(self):
      if self.filename=="":
         return
      self.pildevice.acquireaccesslock()
      self.lifdir.refresh()
      self.pildevice.releaseaccesslock()
#
#  enter lif filename
#
   def get_lifFilename(self):
      dialog=QtGui.QFileDialog()
      dialog.setWindowTitle("Select LIF Image File")
      dialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtGui.QFileDialog.AnyFile)
      dialog.setNameFilters( ["LIF Image File (*.dat *.DAT *.lif *.LIF)", "All Files (*)"] )
      dialog.setOptions(QtGui.QFileDialog.DontUseNativeDialog)
#     dialog.setDirectory(PILCONFIG.get('pyilper','workdir'))
      if dialog.exec():
         return dialog.selectedFiles() 
#
#  Check lif image file, returns status, tracks, surfaces, blocks 
#  If valid LIF1 medium and medium is compatible to device:
#     return True, tracks, surfaces, blocks of medium
#  else:
#     return False and default layout of device
#
   def lifMediumCheck(self,filename,quiet):
      defaultmedium= self.getDefaultMedium(self.drivetype)
      def_name, def_tracks, def_surfaces, def_blocks= self.mediainfo[defaultmedium]
      status, tracks, surfaces, blocks= self.getMediumInfo(filename)
      if status ==0: # medium info found
         return [True, tracks, surfaces, blocks]
      elif status==1: # file dos not exist or cannot be opened
            return [True, def_tracks, def_surfaces, def_blocks]
      elif status==2:
         if not quiet:
            reply=QtGui.QMessageBox.critical(self.parent.ui,'Error',"File does not contain a LIF type 1 medium.",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return [False, def_tracks, def_surfaces, def_blocks]
      elif status==3:
         if not quiet:
            reply=QtGui.QMessageBox.warning(self.parent.ui,'Warning',"File does not contain a LIF type 1 medium with valid layout information. Using default layout of current drive type.",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return [True, def_tracks, def_surfaces, def_blocks]
#
# get media info from lif header
#
   def getMediumInfo(self,filename):

#
#     read lif file header
#
      try:
         if isWINDOWS():
            fd= os.open(filename,os.O_RDONLY | os.O_BINARY)
         else:
            fd= os.open(filename,os.O_RDONLY)
         b=os.read(fd,256)
      except OSError:
         return [1,0,0,0]   # file does not exist or cannot be opened
      if len(b) < 256:
         return [2,0,0,0]   # not lif type 1 file
#
#     do we have a LIF type 1 file
#
      lifmagic= getLifInt(b,0,2)
      dirstart=getLifInt(b,8,4)
#     if not(lifmagic == 0x8000 and dirstart == 2):
      if not(lifmagic == 0x8000):
         return [2,0,0,0] #  no lif type 1 file
#
#     get medium layout
#
      tracks= getLifInt(b,24,4)
      surfaces= getLifInt(b,28,4)
      blocks= getLifInt(b,32,4)
      if (tracks == surfaces) and (surfaces == blocks) :
         return [3,0,0,0] # no valid media layout information
      return [0, tracks, surfaces, blocks]


   def getDefaultMedium(self,device):
      if device== self.DEV_CASS:
         return self.MEDIUM_CASS
      if device== self.DEV_DISK:
         return self.MEDIUM_DISK
      if device== self.DEV_HDRIVE1:
         return self.MEDIUM_HDRIVE1
#
# LifDir Widget -----------------------------------------------------------
#
class TableModel(QtGui.QStandardItemModel):
    _sort_order = QtCore.Qt.AscendingOrder

    def sortOrder(self):
        return self._sort_order

    def sort(self, column, order):
         self._sort_order = order
         super().sort(column, order)

class DirTableView(QtGui.QTableView):

    def __init__(self,parent):
        super().__init__(parent)
        self.parent=parent
#
#       context menu
#
    def contextMenuEvent(self, event):
        if self.parent.parent.active:
           event.accept()
           return
        if not self.parent.parent.parent.ui.lifutils_installed:
           event.accept()
           return
        if self.selectionModel().selection().indexes():
            for i in self.selectionModel().selection().indexes():
                row, column = i.row(), i.column()
            model=self.parent.getModel()
            imagefile= self.parent.getFilename()
            liffilename=model.item(row,0).text()
            liffiletype=model.item(row,1).text()
            menu = QtGui.QMenu()
            exportAction = menu.addAction("Export")
            purgeAction = menu.addAction("Purge")
            renameAction = menu.addAction("Rename")
            ft=get_finfo_name(liffiletype)
            if ft is not None:
               if get_finfo_type(ft)[1] != "":
                  viewAction= menu.addAction("View")
            else:
               viewAction= None
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action== None:
               event.accept()
               return
            workdir=PILCONFIG.get('pyilper','workdir')
            charset=self.parent.parent.charset
            if action ==exportAction:
                cls_lifexport.exec(imagefile,liffilename,liffiletype,workdir)
            elif action== purgeAction:
                cls_lifpurge.exec(imagefile,liffilename)
                self.parent.refresh()
            elif action== renameAction:
                cls_lifrename.exec(imagefile,liffilename)
                self.parent.refresh()
            elif action== viewAction:
                cls_lifview.exec(imagefile, liffilename, liffiletype,workdir, charset)
            event.accept()

class cls_LifDirWidget(QtGui.QWidget):

    def __init__(self,parent,rows,font_name, font_size):
        super().__init__(parent)
        self.parent=parent
        self.__font_name__= font_name
        self.__font_size__= font_size
        self.__table__ = DirTableView(self)  # Table view for dir
        self.__table__.setSortingEnabled(False)  # no sorting
        self.__table__.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
#
#       switch off grid, no focus, no row selection
#
        self.__table__.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.__table__.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__table__.setShowGrid(False)
        self.__columns__=6     # 5 rows for directory listing
        self.__rowcount__=0    # number of rows in table
        self.__filename__=""   # LIF filename
        self.__label__=""      # Label of lif file
        self.__model__ = TableModel(rows, self.__columns__, self.__table__)
#
#       populate header , set column size
#
        self.__model__.setHeaderData(0,QtCore.Qt.Horizontal,"File")
        self.__model__.setHeaderData(1,QtCore.Qt.Horizontal,"Type")
        self.__model__.setHeaderData(2,QtCore.Qt.Horizontal,"Size")
        self.__model__.setHeaderData(3,QtCore.Qt.Horizontal,"Space")
        self.__model__.setHeaderData(4,QtCore.Qt.Horizontal,"Date")
        self.__model__.setHeaderData(5,QtCore.Qt.Horizontal,"Time")
        self.__table__.setModel(self.__model__)
        self.__table__.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
#
#       handle click to header -> sorting
#
        self.__table__.horizontalHeader().sectionClicked.connect(
            self.handleSectionClicked)
#
#       no vertical header
#
        self.__table__.verticalHeader().setVisible(False)
        self.__table__.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
#
#       set font for directory listing, adjust row height
#
#       self.__font__= QtGui.QFont(self.__font_name__)
        self.__font__= QtGui.QFont()
        self.__font__.setPixelSize(self.__font_size__)
        metrics= QtGui.QFontMetrics(self.__font__)
        self.__table__.verticalHeader().setDefaultSectionSize(metrics.height()+1)
#
#       add labels for text information (label, medium, directory)
#
        layout = QtGui.QVBoxLayout(self)
        self.__labelMedium__= QtGui.QLabel()
        self.__labelMedium__.setText("")
        layout.addWidget(self.__labelMedium__)
        self.__labelDir__= QtGui.QLabel()
        self.__labelDir__.setText("")
        layout.addWidget(self.__labelDir__)
        layout.addWidget(self.__table__)

    def getModel(self):
        return(self.__model__)

    def getFilename(self):
        return(self.__filename__)

    def getLabel(self):
        return(self.__label__)

#
#   connect lif data file 
#
    def setFileName(self,filename):
        self.__filename__= filename
        self.refresh()

#
#   clear info
#
    def clear(self):
        self.__labelMedium__.setText("")
        self.__labelDir__.setText("")
        if self.__rowcount__==0:
           return
        self.__model__.removeRows(0, self.__rowcount__)
        self.__rowcount__=0
        return

#
#   read and display directory
#
    def refresh(self):
        if self.__filename__== "":
           return
        self.clear()
        try:
           lif=cls_LifFile()
           lif.set_filename(self.__filename__)
           lif.lifopen()
        except LifError:
           return
        lifdir= cls_LifDir(lif)
        lifdir.open()
        lifdir.rewind()
        dir_start, dir_length, no_tracks, no_surfaces, no_blocks, label, initdatetime=lif.getLifHeader()
        self.__label__= label
        totalblocks=no_tracks* no_surfaces* no_blocks
        totalbytes= totalblocks* 256
#
#       handle invalid values
#
        if no_tracks> 125 or no_surfaces>8 or no_blocks > 256 or \
           no_tracks==0   or no_surfaces==0 or no_blocks ==0:

           self.__labelMedium__.setText("Medium Layout: (invalid). Label: {:6s}, formatted: {:s}".format(label, initdatetime))
        else:
           self.__labelMedium__.setText("Medium Layout: ({}/{}/{}), Size: {} blocks ({} bytes). Label: {:6s}, formatted: {:s}".format(no_tracks,no_surfaces,no_blocks,totalblocks, totalbytes, label, initdatetime))
        self.__labelDir__.setText("Directory size: {} entries ({} used). Last block used: {}".format(dir_length*8, lifdir.num_entries, lifdir.lastblock))

#
#       populate directory listing
#
        while True:
            r= lifdir.getNextEntry()
            if r == []:
              break
            name, ftype_num, start_block, alloc_blocks, datetime, ftype, length= r
            x=[name,ftype ,"{:-8d}".format(length),"{:-8d}".format(alloc_blocks*256),datetime.split(sep=' ')[0],datetime.split(sep=' ')[1]]
            for column in range(self.__columns__):
                item = QtGui.QStandardItem(x[column])
                item.setFont(self.__font__)
                item.setTextAlignment(QtCore.Qt.AlignLeft)
                self.__model__.setItem(self.__rowcount__, column, item)
            self.__rowcount__+=1
        lif.lifclose()
#
#       go to end of scroll area
#
        self.__table__.verticalScrollBar().setRange(0,10000)
        self.__table__.verticalScrollBar().setValue(10000)

#
#   handle click to header field and sort column
#
    def handleSectionClicked(self, index):
        if index >=4:  # not for date/time
           return
        if not self.__table__.isSortingEnabled():
           self.__table__.setSortingEnabled(True)
        self.__table__.sortByColumn(index,self.__model__.sortOrder())
        self.__table__.horizontalHeader().setSortIndicator(
                index, self.__table__.model().sortOrder())
        self.__table__.verticalScrollBar().setValue(0)

#
# Help Dialog class ----------------------------------------------------------
#
class cls_HelpWindow(QtGui.QDialog):

   def __init__(self,parent=None):
#
      super().__init__()
      self.setWindowTitle('pyILPER Manual')
 
      self.vlayout = QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)
      if HAS_WEBKIT:
         self.view = QtWebKit.QWebView()
      if HAS_WEBENGINE:
         self.view = QtWebEngineWidgets.QWebEngineView()
      self.view.setMinimumWidth(600)
      self.vlayout.addWidget(self.view)
      self.buttonExit = QtGui.QPushButton('Exit')
      self.buttonExit.setFixedWidth(60)
      self.buttonExit.clicked.connect(self.do_exit)
      self.buttonBack = QtGui.QPushButton('<')
      self.buttonBack.setFixedWidth(60)
      self.buttonForward = QtGui.QPushButton('>')
      self.buttonForward.setFixedWidth(60)
      self.hlayout = QtGui.QHBoxLayout()
      self.hlayout.addWidget(self.buttonBack)
      self.hlayout.addWidget(self.buttonExit)
      self.hlayout.addWidget(self.buttonForward)
      self.vlayout.addLayout(self.hlayout)
      if HAS_WEBKIT or HAS_WEBENGINE:
         self.buttonBack.clicked.connect(self.do_back)
         self.buttonForward.clicked.connect(self.do_forward)

   def do_exit(self):
      self.hide()

   def do_back(self):
      self.view.back()

   def do_forward(self):
      self.view.forward()

   def loadDocument(self,subdir,document):
      if subdir=="":
         docpath=os.path.join(os.path.dirname(pyilper.__file__),"Manual",document)
      else:
         docpath=os.path.join(os.path.dirname(pyilper.__file__),"Manual",subdir,document)
      docpath=re.sub("//","/",docpath,1)
      self.view.load(QtCore.QUrl.fromLocalFile(docpath))
#
# Release Info Dialog class --------------------------------------------------------
#
class cls_ReleaseWindow(QtGui.QDialog):

   def __init__(self,version):
      super().__init__()
      self.setWindowTitle('Release Information for pyILPER '+version)
      self.vlayout = QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)
      self.view = QtGui.QLabel()
      self.view.setFixedWidth(500)
      self.view.setWordWrap(True)
      self.view.setText("Release Info Text")
      self.button = QtGui.QPushButton('OK')
      self.button.setFixedWidth(60)
      self.button.clicked.connect(self.do_exit)
      self.vlayout.addWidget(self.view)
      self.hlayout = QtGui.QHBoxLayout()
      self.hlayout.addWidget(self.button)
      self.vlayout.addLayout(self.hlayout)

   def do_exit(self):
      self.hide()

#
#
# About Dialog class --------------------------------------------------------
#
class cls_AboutWindow(QtGui.QDialog):

   def __init__(self,version):
      super().__init__()
      self.qtversion=QtCore.QT_VERSION_STR
      self.pyversion=str(sys.version_info.major)+"."+str(sys.version_info.minor)+"."+str(sys.version_info.micro)
      self.setWindowTitle('pyILPER About ...')
      self.vlayout = QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)
      self.view = QtGui.QLabel()
      self.view.setFixedWidth(300)
      self.view.setWordWrap(True)
      self.view.setText("pyILPER "+version+ "\n\nAn emulator for virtual HP-IL devices for the PIL-Box derived from ILPER 1.4.5 for Windows\n\nCopyright (c) 2008-2013   Jean-Francois Garnier\nC++ version (c) 2015 Christoph Gießelink\nTerminal emulator code Henning Schröder\nPython Version (c) 2015-2016 Joachim Siebold\n\nGNU General Public License Version 2\n\nYou run Python "+self.pyversion+" and Qt "+self.qtversion+"\n")


      self.button = QtGui.QPushButton('OK')
      self.button.setFixedWidth(60)
      self.button.clicked.connect(self.do_exit)
      self.vlayout.addWidget(self.view)
      self.hlayout = QtGui.QHBoxLayout()
      self.hlayout.addWidget(self.button)
      self.vlayout.addLayout(self.hlayout)

   def do_exit(self):
      self.hide()

#
# Get TTy  Dialog class -------------------------------------------------------
#

class cls_TtyWindow(QtGui.QDialog):

   def __init__(self, parent=None):
      super().__init__()

      self.setWindowTitle("Select serial device")
      self.vlayout= QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.label= QtGui.QLabel()
      self.label.setText("Select or enter serial port")
      self.label.setAlignment(QtCore.Qt.AlignCenter)

      self.__ComboBox__ = QtGui.QComboBox() 
      self.__ComboBox__.setEditable(True)

      if isWINDOWS():
#
#        Windows COM ports from registry
#
         try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"Hardware\DeviceMap\SerialComm",0,winreg.KEY_QUERY_VALUE|winreg.KEY_ENUMERATE_SUB_KEYS) as key:
               for i in range (0, winreg.QueryInfoKey(key)[1]):
                  port = winreg.EnumValue(key, i)[1]
                  self.__ComboBox__.addItem( port, port )
         except FileNotFoundError:
            pass
      elif isLINUX():
#
#        Linux /dev/ttyUSB?
#
         devlist=glob.glob("/dev/ttyUSB*")
         for port in devlist:
            self.__ComboBox__.addItem( port, port )
#
#        Mac OS X /dev/tty.usbserial-*
#
      elif isMACOS():
         devlist=glob.glob("/dev/tty.usbserial-*")
         for port in devlist:
            self.__ComboBox__.addItem( port, port )

      else:
#
#        Other
#
         devlist=glob.glob("/dev/tty*")
         for port in devlist:
            self.__ComboBox__.addItem( port, port )

      self.connect(self.__ComboBox__, QtCore.SIGNAL('activated(QString)'), self.combobox_choosen)
      self.__ComboBox__.editTextChanged.connect(self.combobox_textchanged)
      self.buttonBox = QtGui.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.label)
      self.vlayout.addWidget(self.__ComboBox__)
      self.hlayout = QtGui.QHBoxLayout()
      self.hlayout.addWidget(self.buttonBox)
      self.vlayout.addWidget(self.buttonBox)
      self.__device__= ""

   def do_ok(self):
      if self.__device__=="":
         self.__device__= self.__ComboBox__.currentText()
         if self.__device__=="":
            return
      super().accept()

   def do_cancel(self):
      self.__device__==""
      super().reject()


   def combobox_textchanged(self, device):
      self.__device__= device

   def combobox_choosen(self, device):
      self.__device__= device

   def getDevice(self):
      return self.__device__

   @staticmethod
   def getTtyDevice(parent=None):
      dialog= cls_TtyWindow(parent)
      dialog.resize(200,100)
      result= dialog.exec_()
      if result== QtGui.QDialog.Accepted:
         return dialog.getDevice()
      else:
         return ""

class cls_PilConfigWindow(QtGui.QDialog):

   def __init__(self,parent): 
      super().__init__()
      self.__name__=parent.name
      self.__parent__= parent
      self.__mode__=  PILCONFIG.get(self.__name__,"mode")
      self.__tty__= PILCONFIG.get(self.__name__,"tty")
      self.__ttyspeed__= PILCONFIG.get(self.__name__,"ttyspeed")
      self.__port__= PILCONFIG.get(self.__name__,"port")
      self.__idyframe__= PILCONFIG.get(self.__name__,"idyframe")
      self.__remotehost__= PILCONFIG.get(self.__name__,"remotehost")
      self.__remoteport__= PILCONFIG.get(self.__name__,"remoteport")
      self.__inpipename__= PILCONFIG.get(self.__name__,"inpipename")
      self.__outpipename__= PILCONFIG.get(self.__name__,"outpipename")
      self.__workdir__=  PILCONFIG.get(self.__name__,"workdir")
      self.__termsize__= PILCONFIG.get(self.__name__,"terminalsize")
      self.__scrollupbuffersize__= PILCONFIG.get(self.__name__,"scrollupbuffersize")
      self.__colorscheme__= PILCONFIG.get(self.__name__,"colorscheme")
      self.__termcharsize__=PILCONFIG.get(self.__name__,"terminalcharsize")
      self.__dircharsize__=PILCONFIG.get(self.__name__,"directorycharsize")
 

      self.setWindowTitle("pyILPER configuration")
      self.vbox0= QtGui.QVBoxLayout()
      self.setLayout(self.vbox0)

#
#     Group box with radio buttons for communication typ
#
 
      self.gbox = QtGui.QGroupBox()
      self.gbox.setFlat(True)
      self.gbox.setTitle("Communication configuration")
      self.vboxgbox= QtGui.QVBoxLayout()
      self.gbox.setLayout(self.vboxgbox)
#
#     Section PIL-Box
#
      self.radbutPIL = QtGui.QRadioButton(self.gbox)
      self.radbutPIL.setText("PIL-Box")
      self.radbutPIL.clicked.connect(self.setCheckBoxes)
      self.vboxgbox.addWidget(self.radbutPIL)
#
#     serial device
#
      self.hboxtty= QtGui.QHBoxLayout()
      self.lbltxt1=QtGui.QLabel("Serial Device: ")
      self.hboxtty.addWidget(self.lbltxt1)
      self.hboxtty.setAlignment(self.lbltxt1,QtCore.Qt.AlignLeft)
      self.lblTty=QtGui.QLabel()
      self.lblTty.setText(self.__tty__)
      self.hboxtty.addWidget(self.lblTty)
      self.hboxtty.setAlignment(self.lblTty,QtCore.Qt.AlignLeft)
      self.hboxtty.addStretch(1)
      self.butTty=QtGui.QPushButton()
      self.butTty.setText("change")
      self.butTty.pressed.connect(self.do_config_Interface)
      self.hboxtty.addWidget(self.butTty)
      self.hboxtty.setAlignment(self.butTty,QtCore.Qt.AlignRight)
      self.vboxgbox.addLayout(self.hboxtty)
#
#     tty speed combo box
#
      self.hboxbaud= QtGui.QHBoxLayout()
      self.lbltxt2=QtGui.QLabel("Baud rate ")
      self.hboxbaud.addWidget(self.lbltxt2)
      self.hboxbaud.setAlignment(self.lbltxt2,QtCore.Qt.AlignLeft)
      self.comboBaud=QtGui.QComboBox()
      i=0
      for baud in BAUDRATES:
         self.comboBaud.addItem(baud[0])
         if self.__ttyspeed__== baud[1]:
            self.comboBaud.setCurrentIndex(i)
         i+=1
 
      self.hboxbaud.addWidget(self.comboBaud)
      self.hboxbaud.addStretch(1)
      self.vboxgbox.addLayout(self.hboxbaud)

#
#     idy frames
#
      self.cbIdyFrame= QtGui.QCheckBox('Enable IDY frames')
      self.cbIdyFrame.setChecked(self.__idyframe__)
      self.cbIdyFrame.setEnabled(True)
      self.cbIdyFrame.stateChanged.connect(self.do_cbIdyFrame)
      self.vboxgbox.addWidget(self.cbIdyFrame)
#
#     section TCP/IP communication
#
      self.radbutTCPIP = QtGui.QRadioButton(self.gbox)
      self.radbutTCPIP.setText("TCP/IP")
      self.radbutTCPIP.clicked.connect(self.setCheckBoxes)
      self.vboxgbox.addWidget(self.radbutTCPIP)
#
#     TCP/IP Parameter input (port, remote host, remote port)
#
      self.intvalidator= QtGui.QIntValidator()
      self.glayout=QtGui.QGridLayout()
      self.lbltxt3=QtGui.QLabel("Port:")
      self.glayout.addWidget(self.lbltxt3,0,0)
      self.lbltxt4=QtGui.QLabel("Remote host:")
      self.glayout.addWidget(self.lbltxt4,1,0)
      self.lbltxt5=QtGui.QLabel("Remote port:")
      self.glayout.addWidget(self.lbltxt5,2,0)
      self.edtPort= QtGui.QLineEdit()
      self.glayout.addWidget(self.edtPort,0,1)
      self.edtPort.setText(str(self.__port__))
      self.edtPort.setValidator(self.intvalidator)
      self.edtRemoteHost= QtGui.QLineEdit()
      self.glayout.addWidget(self.edtRemoteHost,1,1)
      self.edtRemoteHost.setText(self.__remotehost__)
      self.edtRemotePort= QtGui.QLineEdit()
      self.glayout.addWidget(self.edtRemotePort,2,1)
      self.edtRemotePort.setText(str(self.__remoteport__))
      self.edtRemotePort.setValidator(self.intvalidator)
      self.vboxgbox.addLayout(self.glayout)
      self.vbox0.addWidget(self.gbox)
#
#     Section Pipes
#
      if isLINUX() or isMACOS():
         self.radbutPipe = QtGui.QRadioButton(self.gbox)
         self.radbutPipe.setText("Pipes")
         self.radbutPipe.clicked.connect(self.setCheckBoxes)
         self.vboxgbox.addWidget(self.radbutPipe)
         self.playout=QtGui.QGridLayout()
         self.playout.addWidget(QtGui.QLabel("Input pipe:"),0,0)
         self.edtInpipe=QtGui.QLineEdit()
         self.edtInpipe.setText(self.__inpipename__)
         self.playout.addWidget(self.edtInpipe,0,1)
         self.playout.addWidget(QtGui.QLabel("Output pipe:"),1,0)
         self.playout.addWidget(self.edtInpipe,0,1)
         self.edtOutpipe=QtGui.QLineEdit()
         self.playout.addWidget(self.edtOutpipe,1,1)
         self.edtOutpipe.setText(self.__outpipename__)
         self.vboxgbox.addLayout(self.playout)

#
#     Init radio buttons
#
      if self.__mode__==0:
         self.radbutPIL.setChecked(True)
      elif self.__mode__==1:
         self.radbutTCPIP.setChecked(True)
      else:
         self.radbutPipe.setChecked(True)
      self.setCheckBoxes()
#
#     Section Working Directory
#
      self.gboxw = QtGui.QGroupBox()
      self.gboxw.setFlat(True)
      self.gboxw.setTitle("Working directory")
      self.vboxgboxw= QtGui.QVBoxLayout()
      self.gboxw.setLayout(self.vboxgboxw)
      self.hboxwdir= QtGui.QHBoxLayout()
      self.lbltxt6=QtGui.QLabel("Directory: ")
      self.hboxwdir.addWidget(self.lbltxt6)
      self.hboxwdir.setAlignment(self.lbltxt6,QtCore.Qt.AlignLeft)
      self.lblwdir=QtGui.QLabel()
      self.lblwdir.setText(self.__workdir__)
      self.hboxwdir.addWidget(self.lblwdir)
      self.hboxwdir.setAlignment(self.lblwdir,QtCore.Qt.AlignLeft)
      self.hboxwdir.addStretch(1)
      self.butwdir=QtGui.QPushButton()
      self.butwdir.setText("change")
      self.butwdir.pressed.connect(self.do_config_Workdir)
      self.hboxwdir.addWidget(self.butwdir)
      self.hboxwdir.setAlignment(self.butwdir,QtCore.Qt.AlignRight)
      self.vboxgboxw.addLayout(self.hboxwdir)
      self.vbox0.addWidget(self.gboxw)
#
#     Section Terminal configuration: size, scroll up buffer, color scheme, font size
#
      self.gboxt= QtGui.QGroupBox()
      self.gboxt.setFlat(True)
      self.gboxt.setTitle("Terminal Settings (restart required)")
      self.gridt= QtGui.QGridLayout()
      self.gridt.setSpacing(3)
      self.gridt.addWidget(QtGui.QLabel("Termial size"),1,0)
      self.gridt.addWidget(QtGui.QLabel("Scroll up buffer size"),2,0)
      self.gridt.addWidget(QtGui.QLabel("Color Scheme"),3,0)
      self.gridt.addWidget(QtGui.QLabel("Font Size"),4,0)

      self.comboRes=QtGui.QComboBox()
      self.comboRes.addItem("80x24")
      self.comboRes.addItem("80x40")
      self.comboRes.addItem("120x25") 
      self.gridt.addWidget(self.comboRes,1,1)
      self.comboRes.setCurrentIndex(self.comboRes.findText(self.__termsize__))

      self.spinScrollBufferSize=QtGui.QSpinBox()
      self.spinScrollBufferSize.setMinimum(0)
      self.spinScrollBufferSize.setMaximum(9999)
      self.spinScrollBufferSize.setValue(self.__scrollupbuffersize__)
      self.gridt.addWidget(self.spinScrollBufferSize,2,1)

      self.comboCol=QtGui.QComboBox()
      self.comboCol.addItem("white")
      self.comboCol.addItem("amber")
      self.comboCol.addItem("green") 
      self.gridt.addWidget(self.comboCol,3,1)
      self.comboCol.setCurrentIndex(self.comboCol.findText(self.__colorscheme__))

      self.spinTermCharsize=QtGui.QSpinBox()
      self.spinTermCharsize.setMinimum(15)
      self.spinTermCharsize.setMaximum(20)
      self.spinTermCharsize.setValue(self.__termcharsize__)
      self.gridt.addWidget(self.spinTermCharsize,4,1)

      self.gboxt.setLayout(self.gridt)
      self.vbox0.addWidget(self.gboxt)
#
#     Section Directory listing configuration: font size
#
      self.gboxd= QtGui.QGroupBox()
      self.gboxd.setFlat(True)
      self.gboxd.setTitle("Directory Listing Settings (restart required)")
      self.gridd= QtGui.QGridLayout()
      self.gridd.setSpacing(3)
      self.gridd.addWidget(QtGui.QLabel("Font Size"),0,0)
      self.spinDirCharsize=QtGui.QSpinBox()
      self.spinDirCharsize.setMinimum(13)
      self.spinDirCharsize.setMaximum(18)
      self.spinDirCharsize.setValue(self.__dircharsize__)
      self.gridd.addWidget(self.spinDirCharsize,0,1)

      self.gboxd.setLayout(self.gridd)
      self.vbox0.addWidget(self.gboxd)
#
#     add ok/cancel buttons
#
      self.gbox_buttonlist=[self.radbutPIL, self.radbutTCPIP]

      self.buttonBox = QtGui.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.hlayout = QtGui.QHBoxLayout()
      self.hlayout.addWidget(self.buttonBox)
      self.vbox0.addLayout(self.hlayout)

   def setCheckBoxes(self):
      if self.radbutPIL.isChecked():
         self.__mode__=0
         self.butTty.setEnabled(True)
         self.edtPort.setEnabled(False)
         self.edtRemoteHost.setEnabled(False)
         self.edtRemotePort.setEnabled(False)
         self.cbIdyFrame.setEnabled(True)
      elif self.radbutTCPIP.isChecked():
         self.__mode__=1
         self.butTty.setEnabled(False)
         self.edtPort.setEnabled(True)
         self.edtRemoteHost.setEnabled(True)
         self.edtRemotePort.setEnabled(True)
         self.cbIdyFrame.setEnabled(True)
      elif self.radbutPipe.isChecked():
         self.__mode__=2
         self.butTty.setEnabled(False)
         self.edtPort.setEnabled(True)
         self.edtRemoteHost.setEnabled(False)
         self.edtRemotePort.setEnabled(False)
         self.cbIdyFrame.setEnabled(False)

   def do_config_Interface(self):
      interface= cls_TtyWindow.getTtyDevice()
      if interface == "" :
         return
      self.__tty__= interface
      self.lblTty.setText(self.__tty__)

   def getWorkDirName(self):
      dialog=QtGui.QFileDialog()
      dialog.setWindowTitle("Select pyILPER working directory")
      dialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtGui.QFileDialog.DirectoryOnly)
#     dialog.setDirectory(os.path.expanduser('~'))
      if dialog.exec():
         return dialog.selectedFiles() 

   def do_cbIdyFrame(self):
      self.__idyframe__= self.cbIdyFrame.isChecked()

   def do_config_Workdir(self):
      flist=self.getWorkDirName()
      if flist== None:
         return
      self.__workdir__= flist[0]
      self.lblwdir.setText(self.__workdir__)


   def do_ok(self):
      PILCONFIG.put(self.__name__,"mode",self.__mode__)
      PILCONFIG.put(self.__name__,"tty", self.lblTty.text())
      PILCONFIG.put(self.__name__,"ttyspeed", BAUDRATES[self.comboBaud.currentIndex()][1])
      PILCONFIG.put(self.__name__,"idyframe",self.__idyframe__)
      PILCONFIG.put(self.__name__,"port", int(self.edtPort.text()))
      PILCONFIG.put(self.__name__,"remotehost", self.edtRemoteHost.text())
      PILCONFIG.put(self.__name__,"remoteport", int(self.edtRemotePort.text()))
      PILCONFIG.put(self.__name__,"workdir", self.lblwdir.text())
      PILCONFIG.put(self.__name__,"terminalsize", self.comboRes.currentText())
      PILCONFIG.put(self.__name__,"scrollupbuffersize", self.spinScrollBufferSize.value())
      PILCONFIG.put(self.__name__,"colorscheme", self.comboCol.currentText())
      PILCONFIG.put(self.__name__,"terminalcharsize",self.spinTermCharsize.value())
      PILCONFIG.put(self.__name__,"directorycharsize",self.spinDirCharsize.value())
      if isLINUX() or isMACOS():
         PILCONFIG.put(self.__name__,"inpipename", self.edtInpipe.text())
         PILCONFIG.put(self.__name__,"outpipename", self.edtOutpipe.text())
      super().accept()

   def do_cancel(self):
      super().reject()


   @staticmethod
   def getPilConfig(parent):
      dialog= cls_PilConfigWindow(parent)
      result= dialog.exec_()
      if result== QtGui.QDialog.Accepted:
         return True
      else:
         return False

#
# Plotter pen table mode class --------------------------------------------
#
class PenTableModel(QtCore.QAbstractTableModel):
   def __init__(self, datain, parent = None):
      super().__init__()
      self.arraydata = datain

   def rowCount(self, parent):
      return len(self.arraydata)

   def columnCount(self, parent):
      return len(self.arraydata[0])

   def data(self, index, role):
      if not index.isValid():
          return None
      elif role != QtCore.Qt.DisplayRole:
          return None
      return (self.arraydata[index.row()][index.column()])

   def setData(self, index, value,role):
      self.arraydata[index.row()][index.column()] = value
      self.dataChanged.emit(index,index) # this updates the edited cell
      return True

   def flags(self, index):
      return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

   def headerData(self,section,orientation,role):
      if role != QtCore.Qt.DisplayRole:
         return None
      if (orientation == QtCore.Qt.Horizontal):
         if section==0:
            return("Description")
         elif section==1:
            return("R")
         elif section==2:
            return("G")
         elif section==3:
            return("B")
         elif section==3:
            return("A")
         elif section==4:
            return("Alpha")
         elif section==5:
            return("Width")
         else:
            return("")

   def getTable(self):
      return self.arraydata

   def setAll(self,penconfig):
      self.arraydata=penconfig
      self.layoutChanged.emit() # this updates all cells
         
#
# Custom class with input validators ---------------------------------------
#
class PenDelegate(QtGui.QItemDelegate):

   def createEditor(self, parent, option, index):
      editor= super(PenDelegate,self).createEditor(parent,option,index)
      if index.column() > 0 and index.column()< 5:
         editor.setValidator(QtGui.QIntValidator(0,255))
      elif index.column() == 5:
         editor.setValidator(QtGui.QDoubleValidator(0.0,5.0,1))
      return(editor)

   def setEditorData(self, editor, index):
      # Gets display text if edit data hasn't been set.
      text = index.data(QtCore.Qt.EditRole) or index.data(QtCore.Qt.DisplayRole)
      editor.setText(str(text))         

#
# Plotter pen  configuration class -----------------------------------
#
class cls_PenConfigWindow(QtGui.QDialog):

   def __init__(self): 
      super().__init__()
      self.setWindowTitle('Plotter pen config')
      self.vlayout = QtGui.QVBoxLayout()
#
#     table widget
#
      self.tablemodel=PenTableModel(PENCONFIG.get_all())
      self.tableview= QtGui.QTableView()
      self.tableview.setModel(self.tablemodel)
      self.tableview.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
      self.tableview.verticalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
      self.delegate= PenDelegate()
      self.tableview.setItemDelegate(self.delegate)
      self.vlayout.addWidget(self.tableview)
#
#     ok/cancel button box
#    
      self.buttonBox = QtGui.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Reset| QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.buttonBox.button(QtGui.QDialogButtonBox.Reset).clicked.connect(self.do_reset)
      self.vlayout.addWidget(self.buttonBox)
      self.setLayout(self.vlayout)

   def do_ok(self):
      PENCONFIG.set_all(self.tablemodel.getTable())
      super().accept()

   def do_cancel(self):
      super().reject()
#
#     reset populates table with the default configuration
#
   def do_reset(self):
      self.tablemodel.setAll(PENCONFIG.default_config())

   @staticmethod
   def getPenConfig():
      dialog= cls_PenConfigWindow()
      dialog.resize(650,600)
      result= dialog.exec_()
      if result== QtGui.QDialog.Accepted:
         return True
      else:
         return False
#
# HP-IL virtual device  configuration class -----------------------------------
#

class cls_DeviceConfigWindow(QtGui.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.parent=parent
      self.setWindowTitle('Virtual HP-IL device config')
      self.vlayout = QtGui.QVBoxLayout()
#
#     item list and up/down buttons
#
      self.hlayout = QtGui.QHBoxLayout()
      self.devList = QtGui.QListWidget()
      self.hlayout.addWidget(self.devList)
      self.vlayout2= QtGui.QVBoxLayout()
      self.buttonUp= QtGui.QPushButton("^")
      self.vlayout2.addWidget(self.buttonUp)
      self.buttonDown= QtGui.QPushButton("v")
      self.vlayout2.addWidget(self.buttonDown)
      self.buttonAdd= QtGui.QPushButton("Add")
      self.vlayout2.addWidget(self.buttonAdd)
      self.buttonRemove= QtGui.QPushButton("Remove")
      self.vlayout2.addWidget(self.buttonRemove)
      self.hlayout.addLayout(self.vlayout2)
      self.vlayout.addLayout(self.hlayout)
      self.buttonUp.clicked.connect(self.do_itemUp)
      self.buttonDown.clicked.connect(self.do_itemDown)
      self.buttonAdd.clicked.connect(self.do_itemAdd)
      self.buttonRemove.clicked.connect(self.do_itemRemove)
#
#     ok/cancel button box
#    
      self.buttonBox = QtGui.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.buttonBox)
      self.setLayout(self.vlayout)
#
#     fill list widget
#
      self.tabList=PILCONFIG.get(self.parent.name,"tabconfig")
      for tab in self.tabList:
         typ= tab[0]
         name=tab[1]
         self.devList.addItem(name+" ("+ TAB_NAMES[typ]+ ")")
      self.devList.setCurrentRow(0)

   def do_ok(self):
      PILCONFIG.put(self.parent.name,"tabconfig",self.tabList)
      super().accept()

   def do_cancel(self):
      super().reject()

   def do_itemUp(self):
      num_rows=self.devList.count()
      if num_rows == 0:
         return
      row=self.devList.currentRow()
      if row == 0:
          return
      item= self.devList.takeItem(row)
      self.devList.insertItem(row-1,item)
      item= None
      self.devList.setCurrentRow(row-1)
      temp=self.tabList[row]
      self.tabList[row]= self.tabList[row-1]
      self.tabList[row-1]=temp
      return


   def do_itemDown(self):
      num_rows=self.devList.count()
      if num_rows == 0:
         return
      row=self.devList.currentRow()
      if row+1 == num_rows:
         return
      item= self.devList.takeItem(row)
      self.devList.insertItem(row+1,item)
      item= None
      self.devList.setCurrentRow(row+1)
      temp=self.tabList[row]
      self.tabList[row]= self.tabList[row+1]
      self.tabList[row+1]=temp
      return

   def do_itemRemove(self):
      row=self.devList.currentRow()
      del(self.tabList[row])
      item=self.devList.takeItem(row)
      item= None

   def do_itemAdd(self):
      retval=cls_AddDeviceWindow.getAddDevice(self)
      if retval== "":
         return
      typ=retval[0]
      name=retval[1]
      self.devList.addItem(name+" ("+ TAB_NAMES[typ]+ ")")
      self.tabList.append([typ,name])

   @staticmethod
   def getDeviceConfig(parent):
      dialog= cls_DeviceConfigWindow(parent)
      dialog.resize(350,100)
      result= dialog.exec_()
      if result== QtGui.QDialog.Accepted:
         return True
      else:
         return False
#
# validator checks for valid device name
#
class cls_Device_validator(QtGui.QValidator):

   def validate(self,string,pos):
      self.regexp = QtCore.QRegExp('[A-Za-z][A-Za-z0-9]*')
      self.validator = QtGui.QRegExpValidator(self.regexp)
      result=self.validator.validate(string,pos)
      return result[0], result[1], result[2]
#
# Add virtual device dialog class ---------------------------------------------
#
class cls_AddDeviceWindow(QtGui.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.typ= None
      self.name=None
      self.tabList=parent.tabList
      self.setWindowTitle('New Virtual HP-IL device')
#
#     Device name, allow only letter followed by letters or digits
#
      self.vlayout = QtGui.QVBoxLayout()
      self.leditName= QtGui.QLineEdit(self)
      self.leditName.setText("")
      self.leditName.setMaxLength(10)
      self.leditName.textChanged.connect(self.do_checkdup)
      self.validator=cls_Device_validator()
      self.leditName.setValidator(self.validator)
      self.vlayout.addWidget(self.leditName)
#
#     Combobox, omit the scope!
#
      self.comboTyp=QtGui.QComboBox()
      for i in range(1,len(TAB_NAMES)):
         self.comboTyp.addItem(TAB_NAMES[i])
      self.vlayout.addWidget(self.comboTyp)

      self.buttonBox = QtGui.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.buttonBox)
      self.setLayout(self.vlayout)
#
#  validate if name is not empty and unique
#
   def do_checkdup(self):
      self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
      tst=self.leditName.text()
      if tst=="":
         return
      for tab in self.tabList:
         if tst== tab[1]:
            return
      self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)
#
#  return results
#
   def getResult(self):
      return([self.typ,self.name])

#
#  only enabled if name is not empty and unique
#
   def do_ok(self):
      self.name= self.leditName.text()
      self.typ= self.comboTyp.currentIndex()+1
      super().accept()

   def do_cancel(self):
      super().reject()

   @staticmethod
   def getAddDevice(parent):
      dialog= cls_AddDeviceWindow(parent)
      dialog.resize(250,100)
      result= dialog.exec_()
      if result== QtGui.QDialog.Accepted:
         return dialog.getResult()
      else:
         return ""
#
# HP-IL device Status Dialog class ---------------------------------------------
#

class cls_DevStatusWindow(QtGui.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.parent=parent
      self.setWindowTitle('Virtual HP-IL device status')
      self.vlayout = QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)
      self.__timer__=QtCore.QTimer()
      self.__timer__.timeout.connect(self.do_refresh)
      self.rows=len(parent.tabobjects)-1
      self.cols=6
      self.__table__ = QtGui.QTableWidget(self.rows,self.cols)  # Table view for dir
      self.__table__.setSortingEnabled(False)  # no sorting
#
#     switch off grid, no focus, no row selection
#
      self.__table__.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
      self.__table__.setFocusPolicy(QtCore.Qt.NoFocus)
      self.__table__.setShowGrid(False)
      h1= QtGui.QTableWidgetItem()
      h1.setText("Device")
      self.__table__.setHorizontalHeaderItem(0,h1)
      h2= QtGui.QTableWidgetItem()
      h2.setText("DID")
      self.__table__.setHorizontalHeaderItem(1,h2)
      h3= QtGui.QTableWidgetItem()
      h3.setText("AID")
      self.__table__.setHorizontalHeaderItem(2,h3)
      h4= QtGui.QTableWidgetItem()
      h4.setText("Addr.")
      self.__table__.setHorizontalHeaderItem(3,h4)
      h5= QtGui.QTableWidgetItem()
      h5.setText("2nd. Addr.")
      self.__table__.setHorizontalHeaderItem(4,h5)
      h6= QtGui.QTableWidgetItem()
      h6.setText("HP-IL Status")
      self.__table__.setHorizontalHeaderItem(5,h6)
      self.__table__.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
      self.__table__.resizeColumnsToContents()
#
#     no vertical header
#
      self.__table__.verticalHeader().setVisible(False)
      self.__table__.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
      self.__table__.verticalHeader().setDefaultSectionSize(16)
#
#     populate
#
      self.__items__= { }
      for row in range(self.rows):
         for col in range(self.cols):
            self.__items__[row,col]= QtGui.QTableWidgetItem()
            if col > 1:
               self.__items__[row,col].setTextAlignment(QtCore.Qt.AlignHCenter)
            self.__items__[row,col].setText(" ")
            self.__table__.setItem(row,col,self.__items__[row,col])

      self.__table__.resizeRowsToContents()
      self.vlayout.addWidget(self.__table__)
      self.button = QtGui.QPushButton('OK')
      self.button.setFixedWidth(60)
      self.button.clicked.connect(self.do_exit)
      self.hlayout = QtGui.QHBoxLayout()
      self.hlayout.addWidget(self.button)
      self.vlayout.addLayout(self.hlayout)
      self.resize(600,self.sizeHint().height())
      self.do_refresh()

   def hideEvent(self,event):
      self.__timer__.stop()

   def showEvent(self,event):
      self.__timer__.start(500)
      
   def do_exit(self):
      super().accept()

   def do_refresh(self):
      devices=self.parent.commobject.getDevices()
      i=1
      for row in range(self.rows):
         pildevice= devices[i][0]
         name=devices[i][1]
         i+=1
         self.__items__[row,0].setText(name)
         for col in range (1,self.cols):
            self.__items__[row,col].setText("")
         if pildevice== None:
            continue
         (active, did, aid, addr, addr2nd, hpilstatus)= pildevice.getstatus()
         if not active:
            continue
         self.__items__[row,1].setText(did)
         self.__items__[row,2].setText("{0:x}".format(aid))
         self.__items__[row,3].setText("{0:x}".format(addr& 0xF))
         self.__items__[row,4].setText("{0:x}".format(addr2nd &0xF))
         self.__items__[row,5].setText("{0:s}".format(hpilstatus))
# 
# Error message Dialog Class --------------------------------------------------
#
class cls_PilMessageBox(QtGui.QMessageBox):
   def __init__(self):
      super().__init__()
      self.setSizeGripEnabled(True)

   def event(self, e):
      result = QtGui.QMessageBox.event(self, e)

      self.setMinimumHeight(0)
      self.setMaximumHeight(16777215)
      self.setMinimumWidth(0)
      self.setMaximumWidth(16777215)
      self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

      textEdit = self.findChild(QtGui.QTextEdit)
      if textEdit != None :
         textEdit.setMinimumHeight(0)
         textEdit.setMaximumHeight(16777215)
         textEdit.setMinimumWidth(0)
         textEdit.setMaximumWidth(16777215)
         textEdit.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
      return result

#
# Main Window user interface -----------------------------------------------
#
class cls_ui(QtGui.QMainWindow):

   def __init__(self,parent,version,instance):
      super().__init__()
      if instance == "":
         self.setWindowTitle("pyILPER "+version)
      else:
         self.setWindowTitle("pyILPER "+version+" Instance: "+instance)
#
#     check if lifutils are installed
#
      self.lifutils_installed= check_lifutils()[0]
#
#     signals
#
      self.sig_crash= parent.sig_crash
      self.sig_quit= parent.sig_quit
      self.sig_show_message= parent.sig_show_message

#
#     Menu
#
      self.menubar = self.menuBar()
      self.menubar.setNativeMenuBar(False)
      self.menuFile= self.menubar.addMenu('File')
      self.menuUtil= self.menubar.addMenu('Utilities')
      self.menuHelp= self.menubar.addMenu('Help')

      self.actionConfig=self.menuFile.addAction("pyILPER configuration")
      self.actionDevConfig=self.menuFile.addAction("Virtual HP-IL device configuration")
      self.actionPenConfig=self.menuFile.addAction("Plotter pen configuration")
      self.actionReconnect=self.menuFile.addAction("Reconnect")
      self.actionExit=self.menuFile.addAction("Quit")

      self.actionInit=self.menuUtil.addAction("Initialize LIF image file")
      self.actionFix=self.menuUtil.addAction("Fix Header of LIF image file")
      self.actionDevStatus=self.menuUtil.addAction("Virtual HP-IL device status")
      self.actionCopyPilimage=self.menuUtil.addAction("Copy PILIMAGE.DAT to workdir")
      self.actionInstallCheck=self.menuUtil.addAction("Check LIFUTILS installation")
      if not self.lifutils_installed:
         self.actionInit.setEnabled(False)
         self.actionFix.setEnabled(False)

      self.actionAbout=self.menuHelp.addAction("About")
      self.actionHelp=self.menuHelp.addAction("Manual")
#
#     Central widget (tabs only)
#
      self.centralwidget= QtGui.QWidget()
      self.setCentralWidget(self.centralwidget)

      self.tabs=QtGui.QTabWidget()
      self.vbox= QtGui.QVBoxLayout()
      self.vbox.addWidget(self.tabs,1)
      self.centralwidget.setLayout(self.vbox)
#
#     Status bar
#
      self.statusbar=self.statusBar()
#
#     Size policy
#
      self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

#
#  queued emit of the signal to update the message text
#
   def emit_message(self,s):
      self.sig_show_message.emit(s)
#
#  queued emit of the signal to indicate crash
#
   def emit_crash(self):
      self.sig_crash.emit()
#
#  catch close event
#
   def closeEvent(self,evnt):
      evnt.accept()
      self.sig_quit.emit()
