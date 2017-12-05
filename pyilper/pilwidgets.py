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
# 30.11.2015 jsi
# - introduced idy frame option
# 22.12.2015 jsi
# - added navigation buttons to the help window 
# - make help window resizeable
# 28.12.2015 jsi
# - do_cbActive: check for method toggle_active fixed
# 06.01.2016 jsi
# - initialize charset properly at program start
# - use utf-8-sig as charset for logging
# 29.01.2016 jsi
# - improve os detection
# 30.01.2016 jsi
# - use font metrics to determine terminal window size
# - removed experimental mark from TCP/IP configuration
# 01.02.2016 jsi
# - added InstallCheck menu callback
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
# - webkit/webengine handling added (experimental)
# 24.10.2016 jsi
# - show python and qt version in the About window
# 04.12.2016 jsi
# - allow LIF directories not starting at record 2
# 11.12.2016 jsi
# - extend configuration regarding pipes (Linux and Mac OS only)
# 07.01.2016 jsi
# - extended cls_HelpWindow to load arbitrary html files
# 16.03.2017 jsi
# - catch exception if neither QtWebKitWidgets or QtWebEngineWidgets are found
# 01.08.2017 jsi
# - add HP82162A tab
# - refactoring: tab classes moved to pilxxxx.py 
# 23.08.2017 jsi
# - socket config replaced by unix domain socket config
# 31.08.2017 jsi
# - changed config param terminalsize to terminalwidth
# 03.09.2017 jsi
# - getDevices is now method of commthread
# 07.09.2017 jsi
# - bugfixes: moved pen config classes to pilplotter, remove double addLayout in
#   config window
# 08.09.2017 jsi
# - renamed paper format from US to Letter
# 14.04.2017 jsi
# - refactoring of cls_tabtermgeneric
# 20.09.2017 jsi
# - changes of the pyILPER configuration dialog. Determine which changes need a
#   restart of the communication and wich need a restart of the application.
#   Issue appropriate messages. 
# 30.10.2017 jsi
# - added configuration of lifutils path
# - removed deprecated constant QFileDialog.DirectoryOnly
# 12.11.2017 jsi
# - removed editing of parameters winpipe and socketname
# - added editing of parameter serverport
# - two column layout of config window
# 17.11.2017 jsi
# - added missing reconfigure method to cls_tabtermgeneric
# 22.11.2017 jsi
# - renamed header of socket server configuration
# 01.12.2017 jsi
# - added HP82162A thermal printer display pixelsize configuration
#
import os
import glob
import datetime
import re
import sys
import pyilper
from PyQt5 import QtCore, QtGui, QtWidgets
HAS_WEBKIT=False
HAS_WEBENGINE=False
try:
   from PyQt5 import QtWebKitWidgets
   HAS_WEBKIT= True
except:
   pass
try:
   from PyQt5 import QtWebEngineWidgets
   HAS_WEBENGINE=True
except:
   pass
if HAS_WEBKIT and HAS_WEBENGINE:
   HAS_WEBENGINE=False
from .pilqterm import QScrolledTerminalWidget
from .pilcharconv import CHARSET_HP71, charsets
from .pilconfig import PILCONFIG
from .pilcore import *
if isWINDOWS():
   import winreg

#
# Logging check box
#
class LogCheckboxWidget(QtWidgets.QCheckBox):
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
         reply=QtWidgets.QMessageBox.critical(self,'Error',"Cannot open log file: "+ e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)

   def logClose(self):
      try:
         self.log.write("\nEnd log "+self.filename+" at ")
         self.log.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
         self.log.write("\n")
         self.log.close()
         self.log= None
      except OSError as e:
         reply=QtWidgets.QMessageBox.critical(self,'Error',"Cannot close log file: "+ e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)

   def logWrite(self,line):
      if self.log is None:
         return
      try:
         self.log.write(line)
      except OSError as e:
         reply=QtWidgets.QMessageBox.critical(self,'Error',"Cannot write to log file: "+ e.strerror+". Logging disabled",QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
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
         reply=QtWidgets.QMessageBox.critical(self,'Error',"Cannot write to log file: "+ e.strerror+". Logging disabled",QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         try:
            self.log.close()
         except OSError:
            pass
         self.log = None

#
# abstract class
#
class cls_tabgeneric(QtWidgets.QWidget):

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

      self.cbActive= QtWidgets.QCheckBox('Device enabled')
      self.cbActive.setChecked(self.active)
      self.cbActive.setEnabled(False)
      self.cbActive.stateChanged.connect(self.do_cbActive)

   def disable(self):
      self.cbActive.setEnabled(False)

   def enable(self):
      self.cbActive.setEnabled(True)

   def toggle_active(self):
      return

   def do_cbActive(self):
      self.active= self.cbActive.isChecked()
      PILCONFIG.put(self.name,"active",self.active)
      self.pildevice.setactive(self.active)
      self.toggle_active()

   def reconfigure(self):
      return
#
# generic terminal tab widget --------------------------------------------------
#
class cls_tabtermgeneric(cls_tabgeneric):

   def __init__(self,parent,name,cblog,cbcharset):
      super().__init__(parent,name)
      self.cblog= cblog
      self.cbcharset= cbcharset
      self.kbd_delay=False

      if self.cblog:
         self.logging= PILCONFIG.get(self.name,"logging",False)
      if self.cbcharset:
         self.charset= PILCONFIG.get(self.name,"charset",CHARSET_HP71)

#
#     Build GUI 
#
      self.guiobject=QScrolledTerminalWidget(self)

      self.hbox1= QtWidgets.QHBoxLayout()
      self.hbox1.addStretch(1)
      self.hbox1.addWidget(self.guiobject)
      self.hbox1.setContentsMargins(10,10,10,10)
      self.hbox1.addStretch(1)
      self.hbox2= QtWidgets.QHBoxLayout()
      self.hbox2.addWidget(self.cbActive)
      if self.cblog:
         self.cbLogging= LogCheckboxWidget("Log "+self.name,self.name+".log")
         self.hbox2.addWidget(self.cbLogging)
      if self.cbcharset:
         self.lbltxtc=QtWidgets.QLabel("Charset ")
         self.comboCharset=QtWidgets.QComboBox()
         for txt in charsets:
            self.comboCharset.addItem(txt)
         self.hbox2.addWidget(self.lbltxtc)
         self.hbox2.addWidget(self.comboCharset)
      self.hbox2.setContentsMargins(10,3,10,3)
      self.hbox2.addStretch(1)
      self.vbox= QtWidgets.QVBoxLayout()
      self.vbox.addLayout(self.hbox1)
      self.vbox.addLayout(self.hbox2)
      self.setLayout(self.vbox)
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
         self.guiobject.set_charset(self.charset)
#
#     catch resize event to redraw the terminal window
#
   def resizeEvent(self,event):
      self.guiobject.redraw()


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
      self.guiobject.set_charset(self.charset)
      self.pildevice.setlocked(False)

   def enable(self):
      super().enable()
      if self.cblog:
         self.cbLogging.setEnabled(True)
         if self.logging:
            self.cbLogging.logOpen()
      if self.cbcharset:
         self.comboCharset.setEnabled(True)
      self.guiobject.enable()

   def disable(self):
      super().disable()
      self.guiobject.disable()
      if self.cblog:
         if self.logging:
            self.cbLogging.logClose()
         self.cbLogging.setEnabled(False)
      if self.cbcharset:
         self.comboCharset.setEnabled(False)
#
#  becomes visible, refresh content, activate update and blink
#
   def becomes_visible(self):
      self.guiobject.becomes_visible()
      return
#
#  becomes invisible, deactivate update and blink
#
   def becomes_invisible(self):
      self.guiobject.becomes_invisible()
      return

#     reconfigure
#
   def reconfigure(self):
      self.guiobject.reconfigure()

#
# Help Dialog class ----------------------------------------------------------
#
class HelpError(Exception):
   def __init__(self,value):
      self.value=value

   def __str__(self):
      return repr(self.value)


class cls_HelpWindow(QtWidgets.QDialog):

   def __init__(self,parent=None):
#
      super().__init__()
      self.setWindowTitle('pyILPER Manual')
 
      self.vlayout = QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)
      if HAS_WEBKIT:
         self.view = QtWebKitWidgets.QWebView()
      if HAS_WEBENGINE:
         self.view = QtWebEngineWidgets.QWebEngineView()
      if not HAS_WEBENGINE and not HAS_WEBKIT:
         raise HelpError("The Python bindings for QtWebKit and QtWebEngine are missing. Can not display manual")
      self.view.setMinimumWidth(600)
      self.vlayout.addWidget(self.view)
      self.buttonExit = QtWidgets.QPushButton('Exit')
      self.buttonExit.setFixedWidth(60)
      self.buttonExit.clicked.connect(self.do_exit)
      self.buttonBack = QtWidgets.QPushButton('<')
      self.buttonBack.setFixedWidth(60)
      self.buttonForward = QtWidgets.QPushButton('>')
      self.buttonForward.setFixedWidth(60)
      self.hlayout = QtWidgets.QHBoxLayout()
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
class cls_ReleaseWindow(QtWidgets.QDialog):

   def __init__(self,version):
      super().__init__()
      self.setWindowTitle('Release Information for pyILPER '+version)
      self.vlayout = QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)
      self.view = QtWidgets.QLabel()
      self.view.setFixedWidth(500)
      self.view.setWordWrap(True)
      self.view.setText("Release Info Text")
      self.button = QtWidgets.QPushButton('OK')
      self.button.setFixedWidth(60)
      self.button.clicked.connect(self.do_exit)
      self.vlayout.addWidget(self.view)
      self.hlayout = QtWidgets.QHBoxLayout()
      self.hlayout.addWidget(self.button)
      self.vlayout.addLayout(self.hlayout)

   def do_exit(self):
      self.hide()

#
#
# About Dialog class --------------------------------------------------------
#
class cls_AboutWindow(QtWidgets.QDialog):

   def __init__(self,version):
      super().__init__()
      self.qtversion=QtCore.QT_VERSION_STR
      self.pyversion=str(sys.version_info.major)+"."+str(sys.version_info.minor)+"."+str(sys.version_info.micro)
      self.setWindowTitle('pyILPER About ...')
      self.vlayout = QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)
      self.view = QtWidgets.QLabel()
      self.view.setFixedWidth(300)
      self.view.setWordWrap(True)
      self.view.setText("pyILPER "+version+ "\n\nAn emulator for virtual HP-IL devices for the PIL-Box derived from ILPER 1.4.5 for Windows\n\nCopyright (c) 2008-2013   Jean-Francois Garnier\nC++ version (c) 2017 Christoph Gießelink\nTerminal emulator code Henning Schröder\nPython Version (c) 2015-2017 Joachim Siebold\n\nGNU General Public License Version 2\n\nYou run Python "+self.pyversion+" and Qt "+self.qtversion+"\n")


      self.button = QtWidgets.QPushButton('OK')
      self.button.setFixedWidth(60)
      self.button.clicked.connect(self.do_exit)
      self.vlayout.addWidget(self.view)
      self.hlayout = QtWidgets.QHBoxLayout()
      self.hlayout.addWidget(self.button)
      self.vlayout.addLayout(self.hlayout)

   def do_exit(self):
      self.hide()

#
# Get TTy  Dialog class -------------------------------------------------------
#

class cls_TtyWindow(QtWidgets.QDialog):

   def __init__(self, parent=None):
      super().__init__()

      self.setWindowTitle("Select serial device")
      self.vlayout= QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.label= QtWidgets.QLabel()
      self.label.setText("Select or enter serial port")
#     self.label.setAlignment(QtCore.Qt.AlignCenter)

      self.__ComboBox__ = QtWidgets.QComboBox() 
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

      self.__ComboBox__.activated['QString'].connect(self.combobox_choosen)
      self.__ComboBox__.editTextChanged.connect(self.combobox_textchanged)
      self.buttonBox = QtWidgets.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.label)
      self.vlayout.addWidget(self.__ComboBox__)
      self.hlayout = QtWidgets.QHBoxLayout()
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
      if result== QtWidgets.QDialog.Accepted:
         return dialog.getDevice()
      else:
         return ""

class cls_PilConfigWindow(QtWidgets.QDialog):

   def __init__(self,parent): 
      super().__init__()
      self.__needs_reconnect__= False
      self.__needs_reconfigure__= False
      self.__needs_restart__= False
      self.__name__=parent.name
      self.__parent__= parent
      self.__mode__=  PILCONFIG.get(self.__name__,"mode")
      self.__tty__= PILCONFIG.get(self.__name__,"tty")
      self.__ttyspeed__= PILCONFIG.get(self.__name__,"ttyspeed")
      self.__port__= PILCONFIG.get(self.__name__,"port")
      self.__idyframe__= PILCONFIG.get(self.__name__,"idyframe")
      self.__remotehost__= PILCONFIG.get(self.__name__,"remotehost")
      self.__remoteport__= PILCONFIG.get(self.__name__,"remoteport")
      self.__serverport__= PILCONFIG.get(self.__name__,"serverport")
      self.__workdir__=  PILCONFIG.get(self.__name__,"workdir")
      self.__termsize__= PILCONFIG.get(self.__name__,"terminalwidth")
      self.__scrollupbuffersize__= PILCONFIG.get(self.__name__,"scrollupbuffersize")
      self.__colorscheme__= PILCONFIG.get(self.__name__,"colorscheme")
      self.__termcharsize__=PILCONFIG.get(self.__name__,"terminalcharsize")
      self.__dircharsize__=PILCONFIG.get(self.__name__,"directorycharsize")
      self.__papersize__=PILCONFIG.get(self.__name__,"papersize")
      self.__lifutilspath__=PILCONFIG.get(self.__name__,"lifutilspath")
      self.__hp82162a_pixelsize__=PILCONFIG.get(self.__name__,"hp82162a_pixelsize")

      self.setWindowTitle("pyILPER configuration")
      self.vbox0= QtWidgets.QVBoxLayout()
      self.setLayout(self.vbox0)
      self.hbox0= QtWidgets.QHBoxLayout()
      self.vbox0.addLayout(self.hbox0)
      self.vbox1= QtWidgets.QVBoxLayout()
      self.vbox2= QtWidgets.QVBoxLayout()
      self.hbox0.addLayout(self.vbox1)
      self.hbox0.addLayout(self.vbox2)

#
#     Group box with radio buttons for communication typ
#
 
      self.gbox = QtWidgets.QGroupBox()
      self.gbox.setFlat(True)
      self.gbox.setTitle("Communication configuration")
      self.vboxgbox= QtWidgets.QVBoxLayout()
      self.gbox.setLayout(self.vboxgbox)
#
#     Section PIL-Box
#
      self.radbutPIL = QtWidgets.QRadioButton(self.gbox)
      self.radbutPIL.setText("PIL-Box")
      self.radbutPIL.clicked.connect(self.setCheckBoxes)
      self.vboxgbox.addWidget(self.radbutPIL)
#
#     serial device
#
      self.hboxtty= QtWidgets.QHBoxLayout()
      self.lbltxt1=QtWidgets.QLabel("Serial Device: ")
      self.hboxtty.addWidget(self.lbltxt1)
      self.lblTty=QtWidgets.QLabel()
      self.lblTty.setText(self.__tty__)
      self.hboxtty.addWidget(self.lblTty)
      self.hboxtty.addStretch(1)
      self.butTty=QtWidgets.QPushButton()
      self.butTty.setText("change")
      self.butTty.pressed.connect(self.do_config_Interface)
      self.hboxtty.addWidget(self.butTty)
      self.vboxgbox.addLayout(self.hboxtty)
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
         if self.__ttyspeed__== baud[1]:
            self.comboBaud.setCurrentIndex(i)
         i+=1
 
      self.hboxbaud.addWidget(self.comboBaud)
      self.hboxbaud.addStretch(1)
      self.vboxgbox.addLayout(self.hboxbaud)

#
#     idy frames
#
      self.cbIdyFrame= QtWidgets.QCheckBox('Enable IDY frames')
      self.cbIdyFrame.setChecked(self.__idyframe__)
      self.cbIdyFrame.setEnabled(True)
      self.cbIdyFrame.stateChanged.connect(self.do_cbIdyFrame)
      self.vboxgbox.addWidget(self.cbIdyFrame)
#
#     section TCP/IP communication
#
      self.radbutTCPIP = QtWidgets.QRadioButton(self.gbox)
      self.radbutTCPIP.setText("HP-IL over TCP/IP")
      self.radbutTCPIP.clicked.connect(self.setCheckBoxes)
      self.vboxgbox.addWidget(self.radbutTCPIP)
#
#     TCP/IP Parameter input (port, remote host, remote port)
#
      self.intvalidator= QtGui.QIntValidator()
      self.glayout=QtWidgets.QGridLayout()
      self.lbltxt3=QtWidgets.QLabel("Port:")
      self.glayout.addWidget(self.lbltxt3,0,0)
      self.lbltxt4=QtWidgets.QLabel("Remote host:")
      self.glayout.addWidget(self.lbltxt4,1,0)
      self.lbltxt5=QtWidgets.QLabel("Remote port:")
      self.glayout.addWidget(self.lbltxt5,2,0)
      self.edtPort= QtWidgets.QLineEdit()
      self.glayout.addWidget(self.edtPort,0,1)
      self.edtPort.setText(str(self.__port__))
      self.edtPort.setValidator(self.intvalidator)
      self.edtRemoteHost= QtWidgets.QLineEdit()
      self.glayout.addWidget(self.edtRemoteHost,1,1)
      self.edtRemoteHost.setText(self.__remotehost__)
      self.edtRemotePort= QtWidgets.QLineEdit()
      self.glayout.addWidget(self.edtRemotePort,2,1)
      self.edtRemotePort.setText(str(self.__remoteport__))
      self.edtRemotePort.setValidator(self.intvalidator)
      self.vboxgbox.addLayout(self.glayout)
      self.vbox1.addWidget(self.gbox)
#
#     Section TCP/IP server port
#
      self.radbutServerport = QtWidgets.QRadioButton(self.gbox)
      self.radbutServerport.setText("TCP/IP socket Server (PIL-Box emulator)")
      self.radbutServerport.clicked.connect(self.setCheckBoxes)
      self.vboxgbox.addWidget(self.radbutServerport)
      self.splayout=QtWidgets.QGridLayout()
      self.splayout.addWidget(QtWidgets.QLabel("Server port:"),0,0)
      self.edtServerport=QtWidgets.QLineEdit()
      self.edtServerport.setValidator(self.intvalidator)
      self.splayout.addWidget(self.edtServerport,0,1)
      self.edtServerport.setText(str(self.__serverport__))
      self.vboxgbox.addLayout(self.splayout)

#
#     Init radio buttons
#
      if self.__mode__==0:
         self.radbutPIL.setChecked(True)
      elif self.__mode__==1:
         self.radbutTCPIP.setChecked(True)
      else:
         self.radbutServerport.setChecked(True)
      self.setCheckBoxes()
#
#     Section Working Directory
#
      self.gboxw = QtWidgets.QGroupBox()
      self.gboxw.setFlat(True)
      self.gboxw.setTitle("Working directory")
      self.vboxgboxw= QtWidgets.QVBoxLayout()
      self.gboxw.setLayout(self.vboxgboxw)
      self.hboxwdir= QtWidgets.QHBoxLayout()
      self.lbltxt6=QtWidgets.QLabel("Directory: ")
      self.hboxwdir.addWidget(self.lbltxt6)
      self.lblwdir=QtWidgets.QLabel()
      self.lblwdir.setText(self.__workdir__)
      self.hboxwdir.addWidget(self.lblwdir)
      self.hboxwdir.addStretch(1)
      self.butwdir=QtWidgets.QPushButton()
      self.butwdir.setText("change")
      self.butwdir.pressed.connect(self.do_config_Workdir)
      self.hboxwdir.addWidget(self.butwdir)
      self.vboxgboxw.addLayout(self.hboxwdir)
      self.vbox1.addWidget(self.gboxw)
      self.vbox1.addStretch(1)
#
#     section lifutils path
#
      self.gboxlifpath = QtWidgets.QGroupBox()
      self.gboxlifpath.setFlat(True)
      self.gboxlifpath.setTitle("Custom LIFUTILS location")
      self.vboxgboxlifpath= QtWidgets.QVBoxLayout()
      self.gboxlifpath.setLayout(self.vboxgboxlifpath)
      self.hboxlifpath= QtWidgets.QHBoxLayout()
      self.lbltxt7=QtWidgets.QLabel("Path to lifversion program: ")
      self.hboxlifpath.addWidget(self.lbltxt7)
      self.lbllifpath=QtWidgets.QLabel()
      self.lbllifpath.setText(self.__lifutilspath__)
      self.hboxlifpath.addWidget(self.lbllifpath)
      self.hboxlifpath.addStretch(1)

      self.vboxlifbut= QtWidgets.QVBoxLayout()
      self.butlifpathchange=QtWidgets.QPushButton()
      self.butlifpathchange.setText("change")
      self.butlifpathchange.pressed.connect(self.do_config_lifutilspath_change)
      self.butlifpathclear=QtWidgets.QPushButton()
      self.butlifpathclear.setText("clear")
      self.butlifpathclear.pressed.connect(self.do_config_lifutilspath_clear)
      self.vboxlifbut.addWidget(self.butlifpathchange)
      self.vboxlifbut.addWidget(self.butlifpathclear)

      self.hboxlifpath.addLayout(self.vboxlifbut)
      self.vboxgboxlifpath.addLayout(self.hboxlifpath)
      self.vbox2.addWidget(self.gboxlifpath)
#
#     Section Terminal configuration: size, scroll up buffer, color scheme, 
#     font size
#
      self.gboxt= QtWidgets.QGroupBox()
      self.gboxt.setFlat(True)
      self.gboxt.setTitle("Terminal Settings")
      self.gridt= QtWidgets.QGridLayout()
      self.gridt.setSpacing(3)
      self.gridt.addWidget(QtWidgets.QLabel("Terminal width"),1,0)
      self.gridt.addWidget(QtWidgets.QLabel("Scroll up buffer size"),2,0)
      self.gridt.addWidget(QtWidgets.QLabel("Color Scheme"),3,0)
      self.gridt.addWidget(QtWidgets.QLabel("Font Size"),4,0)

      self.comboTerminalWidth=QtWidgets.QComboBox()
      self.comboTerminalWidth.addItem("80")
      self.comboTerminalWidth.addItem("120") 
      self.gridt.addWidget(self.comboTerminalWidth,1,1)
      self.comboTerminalWidth.setCurrentIndex(self.comboTerminalWidth.findText(str(self.__termsize__)))

      self.spinScrollBufferSize=QtWidgets.QSpinBox()
      self.spinScrollBufferSize.setMinimum(TERMINAL_MINIMUM_ROWS)
      self.spinScrollBufferSize.setMaximum(9999)
      self.spinScrollBufferSize.setValue(self.__scrollupbuffersize__)
      self.gridt.addWidget(self.spinScrollBufferSize,2,1)

      self.comboCol=QtWidgets.QComboBox()
      self.comboCol.addItem("white")
      self.comboCol.addItem("amber")
      self.comboCol.addItem("green") 
      self.gridt.addWidget(self.comboCol,3,1)
      self.comboCol.setCurrentIndex(self.comboCol.findText(self.__colorscheme__))

      self.spinTermCharsize=QtWidgets.QSpinBox()
      self.spinTermCharsize.setMinimum(15)
      self.spinTermCharsize.setMaximum(20)
      self.spinTermCharsize.setValue(self.__termcharsize__)
      self.gridt.addWidget(self.spinTermCharsize,4,1)

      self.gboxt.setLayout(self.gridt)
      self.vbox2.addWidget(self.gboxt)
#
#     HP82162A thermal printer settings
#
      self.gbox82162a= QtWidgets.QGroupBox()
      self.gbox82162a.setFlat(True)
      self.gbox82162a.setTitle("HP82162A Settings")
      self.grid82162a= QtWidgets.QGridLayout()
      self.grid82162a.setSpacing(3)
      self.grid82162a.addWidget(QtWidgets.QLabel("Pixel size"),0,0)

      self.spinHP82162APixelsize=QtWidgets.QSpinBox()
      self.spinHP82162APixelsize.setMinimum(1)
      self.spinHP82162APixelsize.setMaximum(2)
      self.spinHP82162APixelsize.setValue(self.__hp82162a_pixelsize__)
      self.grid82162a.addWidget(self.spinHP82162APixelsize,0,1)

      self.gbox82162a.setLayout(self.grid82162a)
      self.vbox2.addWidget(self.gbox82162a)
#
#     Section Directory listing configuration: font size
#
      self.gboxd= QtWidgets.QGroupBox()
      self.gboxd.setFlat(True)
      self.gboxd.setTitle("Directory Listing Settings")
      self.gridd= QtWidgets.QGridLayout()
      self.gridd.setSpacing(3)
      self.gridd.addWidget(QtWidgets.QLabel("Font Size"),0,0)
      self.spinDirCharsize=QtWidgets.QSpinBox()
      self.spinDirCharsize.setMinimum(13)
      self.spinDirCharsize.setMaximum(18)
      self.spinDirCharsize.setValue(self.__dircharsize__)
      self.gridd.addWidget(self.spinDirCharsize,0,1)

      self.gboxd.setLayout(self.gridd)
      self.vbox2.addWidget(self.gboxd)
#
#     Section Papersize
#
      self.gboxps= QtWidgets.QGroupBox()
      self.gboxps.setFlat(True)
      self.gboxps.setTitle("Papersize (Plotter and PDF output)")
      self.gridps=QtWidgets.QGridLayout()
      self.gridps.setSpacing(3)

      self.gridps.addWidget(QtWidgets.QLabel("Papersize:"),1,0)
      self.combops=QtWidgets.QComboBox()
      self.combops.addItem("A4")
      self.combops.addItem("Letter")
      self.combops.setCurrentIndex(self.__papersize__)
      self.gridps.addWidget(self.combops,1,1)
      self.gboxps.setLayout(self.gridps)
      self.vbox2.addWidget(self.gboxps)
      self.vbox2.addStretch(1)
#
#     add ok/cancel buttons
#
      self.gbox_buttonlist=[self.radbutPIL, self.radbutTCPIP]

      self.buttonBox = QtWidgets.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.hlayout = QtWidgets.QHBoxLayout()
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
         self.edtServerport.setEnabled(False)
         self.comboBaud.setEnabled(True)
      elif self.radbutTCPIP.isChecked():
         self.__mode__=1
         self.butTty.setEnabled(False)
         self.edtPort.setEnabled(True)
         self.edtRemoteHost.setEnabled(True)
         self.edtRemotePort.setEnabled(True)
         self.cbIdyFrame.setEnabled(True)
         self.edtServerport.setEnabled(False)
         self.comboBaud.setEnabled(False)
      elif self.radbutServerport.isChecked():
         self.__mode__=2
         self.butTty.setEnabled(False)
         self.edtPort.setEnabled(False)
         self.edtRemoteHost.setEnabled(False)
         self.edtRemotePort.setEnabled(False)
         self.cbIdyFrame.setEnabled(False)
         self.edtServerport.setEnabled(True)
         self.comboBaud.setEnabled(False)

   def do_config_Interface(self):
      interface= cls_TtyWindow.getTtyDevice()
      if interface == "" :
         return
      self.__tty__= interface
      self.lblTty.setText(self.__tty__)

   def getWorkDirName(self):
      dialog=QtWidgets.QFileDialog()
      dialog.setWindowTitle("Select pyILPER working directory")
      dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtWidgets.QFileDialog.Directory)
      dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly,True)
      if dialog.exec():
         return dialog.selectedFiles() 

   def do_cbIdyFrame(self):
      self.__idyframe__= self.cbIdyFrame.isChecked()

   def do_config_Workdir(self):
      flist=self.getWorkDirName()
      if flist is None:
         return
      self.__workdir__= flist[0]
      self.lblwdir.setText(self.__workdir__)

   def getLifutilsDirName(self):
      dialog=QtWidgets.QFileDialog()
      dialog.setWindowTitle("Select Path to lifversion executable")
      dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
      if dialog.exec():
         return dialog.selectedFiles() 

   def do_config_lifutilspath_clear(self):
      self.__lifutilspath__= ""
      self.lbllifpath.setText(self.__lifutilspath__)

   def do_config_lifutilspath_change(self):
      flist=self.getLifutilsDirName()
      if flist is None:
         return
      self.__lifutilspath__= flist[0]
      self.lbllifpath.setText(self.__lifutilspath__)
#
#     check if configuration parameter was changed
#
   def check_param(self,param,value):
      oldvalue= PILCONFIG.get(self.__name__,param,value)
      return (value!= oldvalue)

#
#  OK button pressed
#
   def do_ok(self):
#
#     check if we need to restart the pyILPER communication
#
      self.__needs_reconnect__= False
      self.__needs_reconnect__ |= self.check_param("mode",self.__mode__)
      self.__needs_reconnect__ |= self.check_param("tty", self.lblTty.text())
      self.__needs_reconnect__ |= self.check_param("ttyspeed", BAUDRATES[self.comboBaud.currentIndex()][1])
      self.__needs_reconnect__ |= self.check_param("idyframe",self.__idyframe__)
      self.__needs_reconnect__ |= self.check_param("port", int(self.edtPort.text()))
      self.__needs_reconnect__ |= self.check_param("remotehost", self.edtRemoteHost.text())
      self.__needs_reconnect__ |= self.check_param("serverport", int(self.edtServerport.text()))
      self.__needs_reconnect__ |= self.check_param("workdir", self.lblwdir.text())
#
#     we need to reconnect, so get confirmation
#
      if self.__needs_reconnect__ and PILCONFIG.get("pyilper","show_msg_commparams_changed",True):
         msgbox= QtWidgets.QMessageBox()
         msgbox.setText("The changes of communication parameters or the working directory require a disconnect and reconnect of the pyILPER communication. Continue?")
         msgbox.setIcon(QtWidgets.QMessageBox.Warning)
         msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
         msgbox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
         cb=QtWidgets.QCheckBox("Do not show this message again")
         msgbox.setCheckBox(cb)
         msgbox.setWindowTitle("Warning")
         reply=msgbox.exec()
         PILCONFIG.put("pyilper","show_msg_commparams_changed",cb.checkState()!=QtCore.Qt.Checked)
#
#    not confirmed, cancel everything
#
         if reply == QtWidgets.QMessageBox.Cancel:
            super().reject
#
#     store parameters
#
      PILCONFIG.put(self.__name__,"mode",self.__mode__)
      PILCONFIG.put(self.__name__,"tty", self.lblTty.text())
      PILCONFIG.put(self.__name__,"ttyspeed", BAUDRATES[self.comboBaud.currentIndex()][1])
      PILCONFIG.put(self.__name__,"idyframe",self.__idyframe__)
      PILCONFIG.put(self.__name__,"port", int(self.edtPort.text()))
      PILCONFIG.put(self.__name__,"remotehost", self.edtRemoteHost.text())
      PILCONFIG.put(self.__name__,"remoteport", int(self.edtRemotePort.text()))
      PILCONFIG.put(self.__name__,"serverport", int(self.edtServerport.text()))
      PILCONFIG.put(self.__name__,"workdir", self.lblwdir.text())
#
#     these parameters require a reconfiguration 
#
      self.__needs_reconfigure__= False
      self.__needs_reconfigure__ |= self.check_param("terminalwidth", int(self.comboTerminalWidth.currentText()))
      self.__needs_reconfigure__ |= self.check_param("colorscheme", self.comboCol.currentText())
      self.__needs_reconfigure__ |= self.check_param("terminalcharsize",self.spinTermCharsize.value())
      self.__needs_reconfigure__ |= self.check_param("directorycharsize",self.spinDirCharsize.value())
      self.__needs_reconfigure__ |= self.check_param("hp82162a_pixelsize",self.spinHP82162APixelsize.value())
#
#     These parameters need a restart, display message
#
      self.__needs_restart__= False
      self.__needs_restart__ |= self.check_param("papersize",self.combops.currentIndex())
      self.__needs_restart__ |= self.check_param("scrollupbuffersize", self.spinScrollBufferSize.value())
      self.__needs_restart__ |= self.check_param("lifutilspath",self.lbllifpath.text())
#
#     some parameters need a restart of the application, inform user
#
      if self.__needs_restart__ and PILCONFIG.get("pyilper","show_msg_restartparams_changed",True):
         msgbox= QtWidgets.QMessageBox()
         msgbox.setText("Changes of the papersize, the scrollup buffer size or the lifutils path require a restart of pyILPER for take the changes to effect.")
         msgbox.setIcon(QtWidgets.QMessageBox.Information)
         msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
         msgbox.setDefaultButton(QtWidgets.QMessageBox.Ok)
         cb=QtWidgets.QCheckBox("Do not show this message again")
         msgbox.setCheckBox(cb)
         msgbox.setWindowTitle("Information")
         reply=msgbox.exec()
         PILCONFIG.put("pyilper","show_msg_restartparams_changed",cb.checkState()!=QtCore.Qt.Checked)
#
#     store parameters
#
      PILCONFIG.put(self.__name__,"terminalwidth", int(self.comboTerminalWidth.currentText()))
      PILCONFIG.put(self.__name__,"scrollupbuffersize", self.spinScrollBufferSize.value())
      PILCONFIG.put(self.__name__,"colorscheme", self.comboCol.currentText())
      PILCONFIG.put(self.__name__,"terminalcharsize",self.spinTermCharsize.value())
      PILCONFIG.put(self.__name__,"directorycharsize",self.spinDirCharsize.value())
      PILCONFIG.put(self.__name__,"papersize",self.combops.currentIndex())
      PILCONFIG.put(self.__name__,"lifutilspath",self.lbllifpath.text())
      PILCONFIG.put(self.__name__,"hp82162a_pixelsize",self.spinHP82162APixelsize.value())
      super().accept()

   def do_cancel(self):
      super().reject()

   def get_status(self):
      return (self.__needs_reconnect__, self.__needs_reconfigure__)


   @staticmethod
   def getPilConfig(parent):
      dialog= cls_PilConfigWindow(parent)
      result= dialog.exec_()
      (reconnect,reconfigure)= dialog.get_status()
      if result== QtWidgets.QDialog.Accepted:
         return True, reconnect, reconfigure
      else:
         return False, False, False

#
# HP-IL virtual device  configuration class -----------------------------------
#

class cls_DeviceConfigWindow(QtWidgets.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.parent=parent
      self.setWindowTitle('Virtual HP-IL device config')
      self.vlayout = QtWidgets.QVBoxLayout()
#
#     item list and up/down buttons
#
      self.hlayout = QtWidgets.QHBoxLayout()
      self.devList = QtWidgets.QListWidget()
      self.hlayout.addWidget(self.devList)
      self.vlayout2= QtWidgets.QVBoxLayout()
      self.buttonUp= QtWidgets.QPushButton("^")
      self.vlayout2.addWidget(self.buttonUp)
      self.buttonDown= QtWidgets.QPushButton("v")
      self.vlayout2.addWidget(self.buttonDown)
      self.buttonAdd= QtWidgets.QPushButton("Add")
      self.vlayout2.addWidget(self.buttonAdd)
      self.buttonRemove= QtWidgets.QPushButton("Remove")
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
      self.buttonBox = QtWidgets.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
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
      if result== QtWidgets.QDialog.Accepted:
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
class cls_AddDeviceWindow(QtWidgets.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.typ= None
      self.name=None
      self.tabList=parent.tabList
      self.setWindowTitle('New Virtual HP-IL device')
#
#     Device name, allow only letter followed by letters or digits
#
      self.vlayout = QtWidgets.QVBoxLayout()
      self.leditName= QtWidgets.QLineEdit(self)
      self.leditName.setText("")
      self.leditName.setMaxLength(10)
      self.leditName.textChanged.connect(self.do_checkdup)
      self.validator=cls_Device_validator()
      self.leditName.setValidator(self.validator)
      self.vlayout.addWidget(self.leditName)
#
#     Combobox, omit the scope!
#
      self.comboTyp=QtWidgets.QComboBox()
      for i in range(1,len(TAB_NAMES)):
         self.comboTyp.addItem(TAB_NAMES[i])
      self.vlayout.addWidget(self.comboTyp)

      self.buttonBox = QtWidgets.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.buttonBox)
      self.setLayout(self.vlayout)
#
#  validate if name is not empty and unique
#
   def do_checkdup(self):
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      tst=self.leditName.text()
      if tst=="":
         return
      for tab in self.tabList:
         if tst== tab[1]:
            return
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
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
      if result== QtWidgets.QDialog.Accepted:
         return dialog.getResult()
      else:
         return ""
#
# HP-IL device Status Dialog class ---------------------------------------------
#

class cls_DevStatusWindow(QtWidgets.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.parent=parent
      self.setWindowTitle('Virtual HP-IL device status')
      self.vlayout = QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)
      self.__timer__=QtCore.QTimer()
      self.__timer__.timeout.connect(self.do_refresh)
      self.rows=len(parent.tabobjects)-1
      self.cols=6
      self.__table__ = QtWidgets.QTableWidget(self.rows,self.cols)  # Table view for dir
      self.__table__.setSortingEnabled(False)  # no sorting
#
#     switch off grid, no focus, no row selection
#
      self.__table__.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
      self.__table__.setFocusPolicy(QtCore.Qt.NoFocus)
      self.__table__.setShowGrid(False)
      h1= QtWidgets.QTableWidgetItem()
      h1.setText("Device")
      self.__table__.setHorizontalHeaderItem(0,h1)
      h2= QtWidgets.QTableWidgetItem()
      h2.setText("DID")
      self.__table__.setHorizontalHeaderItem(1,h2)
      h3= QtWidgets.QTableWidgetItem()
      h3.setText("AID")
      self.__table__.setHorizontalHeaderItem(2,h3)
      h4= QtWidgets.QTableWidgetItem()
      h4.setText("Addr.")
      self.__table__.setHorizontalHeaderItem(3,h4)
      h5= QtWidgets.QTableWidgetItem()
      h5.setText("2nd. Addr.")
      self.__table__.setHorizontalHeaderItem(4,h5)
      h6= QtWidgets.QTableWidgetItem()
      h6.setText("HP-IL Status")
      self.__table__.setHorizontalHeaderItem(5,h6)
      self.__table__.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
      self.__table__.resizeColumnsToContents()
#
#     no vertical header
#
      self.__table__.verticalHeader().setVisible(False)
      self.__table__.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
      self.__table__.verticalHeader().setDefaultSectionSize(16)
#
#     populate
#
      self.__items__= { }
      for row in range(self.rows):
         for col in range(self.cols):
            self.__items__[row,col]= QtWidgets.QTableWidgetItem()
            if col > 1:
               self.__items__[row,col].setTextAlignment(QtCore.Qt.AlignHCenter)
            self.__items__[row,col].setText(" ")
            self.__table__.setItem(row,col,self.__items__[row,col])

      self.__table__.resizeRowsToContents()
      self.vlayout.addWidget(self.__table__)
      self.button = QtWidgets.QPushButton('OK')
      self.button.setFixedWidth(60)
      self.button.clicked.connect(self.do_exit)
      self.hlayout = QtWidgets.QHBoxLayout()
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
      devices=self.parent.commthread.getDevices()
      i=1
      for row in range(self.rows):
         pildevice= devices[i][0]
         name=devices[i][1]
         i+=1
         self.__items__[row,0].setText(name)
         for col in range (1,self.cols):
            self.__items__[row,col].setText("")
         if pildevice is None:
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
class cls_PilMessageBox(QtWidgets.QMessageBox):
   def __init__(self):
      super().__init__()
      self.setSizeGripEnabled(True)

   def event(self, e):
      result = QtWidgets.QMessageBox.event(self, e)

      self.setMinimumHeight(0)
      self.setMaximumHeight(16777215)
      self.setMinimumWidth(0)
      self.setMaximumWidth(16777215)
      self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

      textEdit = self.findChild(QtWidgets.QTextEdit)
      if textEdit is not None:
         textEdit.setMinimumHeight(0)
         textEdit.setMaximumHeight(16777215)
         textEdit.setMinimumWidth(0)
         textEdit.setMaximumWidth(16777215)
         textEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
      return result

#
# Main Window user interface -----------------------------------------------
#
class cls_ui(QtWidgets.QMainWindow):

   def __init__(self,parent,version,instance):
      super().__init__()
      if instance == "":
         self.setWindowTitle("pyILPER "+version)
      else:
         self.setWindowTitle("pyILPER "+version+" Instance: "+instance)
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
      self.actionInit.setEnabled(False)
      self.actionFix.setEnabled(False)

      self.actionAbout=self.menuHelp.addAction("About")
      self.actionHelp=self.menuHelp.addAction("Manual")
#
#     Central widget (tabs only)
#
      self.centralwidget= QtWidgets.QWidget()
      self.setCentralWidget(self.centralwidget)

      self.tabs=QtWidgets.QTabWidget()
      self.vbox= QtWidgets.QVBoxLayout()
      self.vbox.addWidget(self.tabs)
      self.centralwidget.setLayout(self.vbox)
#
#     Status bar
#
      self.statusbar=self.statusBar()
#
#     Size policy
#
      self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

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
#
# enable controls that require lifutils
#
   def enableLIFControls(self):
      self.actionInit.setEnabled(True)
      self.actionFix.setEnabled(True)
