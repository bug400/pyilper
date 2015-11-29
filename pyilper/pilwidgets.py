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
#
# 20.10.2015 jsi
# - fix leading // for docpath (OSX)
#
# 24.10.2015 jsi
# - use non native menus only (OSX issues)
# - removed ) from date of medium formatted
#
# 21.11.2015 jsi
# - introduced show IDY frames option in scope tab
#
# 29.11.2015 jsi
# - working directory is default when opening lif files
# - do not check lif medium version
# - invalid layout if all media information are zero
#
import os
import glob
import datetime
import time
import platform
import re
import pyilper
from PyQt4 import QtCore, QtGui, QtWebKit
from .lifutils import cls_LifFile,cls_LifDir,LifError, getLifInt
from .pilqterm import QTerminalWidget,HPTerminal
from .pilscope import cls_scope
from .pilprinter import cls_printer
from .pilterminal import cls_terminal
from .pildrive import cls_drive
from .pilcharconv import charconv, CHARSET_HP71, CHARSET_HP41, CHARSET_ROMAN8, charsets
from .pilconfig import PilConfigError
#
# Constants
#
UPDATE_TIMER=100      # Refresh timer (ms) for terminal window content
REFRESH_RATE=5000     # refresh rate for lif directory

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
         self.log=open(self.filename,"a")
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
#
# abstract class
#
class cls_tabgeneric(QtGui.QWidget):

   def __init__(self,parent,name):

      super().__init__()
      self.name= name
      self.active= parent.config.get(self.name,"active",False)
      self.parent=parent
      self.font_name=""
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
      self.parent.config.put(self.name,"active",self.active)
      self.pildevice.setactive(self.active)
      return

   def __set_termconfig__(self,rows,cols):
      if platform.dist()[0] != "":
#
#        Linux
#
          self.font_name="Monospace"
          self.font_size=15
          self.font_width=9
          self.font_height=18
      else:
#
#        all other
#
          self.font_name="Courier New"
          self.font_size=15
          self.font_width=9
#         self.font_height=17.28
          self.font_height=17
      self.width= self.font_width*cols
      self.height= int(self.font_height* rows)

#
# generic terminal widget ----------------------------------------------------
#
class cls_tabtermgeneric(cls_tabgeneric):

   def __init__(self,parent,name,cblog,cbcharset):
      super().__init__(parent,name)
      self.cblog= cblog
      self.cbcharset= cbcharset
#
#     Set default values
#
      if self.cblog:
         self.logging= parent.config.get(self.name,"logging",False)
      if self.cbcharset:
         self.charset= parent.config.get(self.name,"charset",CHARSET_HP71)

      self.rows=24
      self.cols=80
#
#     Build GUI 
#
      super().__set_termconfig__(self.rows,self.cols)
      self.qterminal=QTerminalWidget(None,self.font_name, self.font_size, self.width, self.height)
      self.hbox1= QtGui.QHBoxLayout()
      self.hbox1.addWidget(self.qterminal)
      self.hbox1.setAlignment(self.qterminal,QtCore.Qt.AlignHCenter)
      self.hbox1.setContentsMargins(20,20,20,20)
      self.hbox2= QtGui.QHBoxLayout()
      self.hbox2.addWidget(self.cbActive)
      self.hbox2.setAlignment(self.cbActive,QtCore.Qt.AlignLeft)
      if self.cblog:
         self.cbLogging= LogCheckboxWidget("Log "+self.name,self.name+".log")
         self.hbox2.addWidget(self.cbLogging)
         self.hbox2.setAlignment(self.cbLogging,QtCore.Qt.AlignLeft)
      if self.cbcharset:
         self.lbltxtc=QtGui.QLabel("Charset ")
         self.lbltxtc.setFixedHeight(10)
         self.lbltxtc.setFixedWidth(50)
#        self.hbox2.addWidget(self.lbltxtc)
#        self.hbox2.setAlignment(self.lbltxtc,QtCore.Qt.AlignLeft)
         self.comboCharset=QtGui.QComboBox()
         for txt in charsets:
            self.comboCharset.addItem(txt)
         self.hbox2.addWidget(self.comboCharset)
#     self.hbox2.addStretch(1)
      self.hbox2.setContentsMargins(10,3,10,3)
      self.vbox= QtGui.QVBoxLayout()
      self.vbox.addLayout(self.hbox1)
      self.vbox.addLayout(self.hbox2)
      self.setLayout(self.vbox)
      self.hpterm=HPTerminal(self.cols,self.rows,self.qterminal)
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

   def do_cbLogging(self):
      self.cbLogging.setEnabled(False)
      self.logging= self.cbLogging.isChecked()
      self.parent.pause_pil_loop()
      if self.logging:
         self.cbLogging.logOpen()
      else:
         self.cbLogging.logClose()
      self.parent.config.put(self.name,"logging",self.logging)
      self.parent.resume_pil_loop()
      self.cbLogging.setEnabled(True)

   def do_changeCharset(self,text):
      self.charset=self.comboCharset.findText(text)
      self.parent.config.put(self.name,'charset',self.charset)
      self.parent.pause_pil_loop()
      self.hpterm.set_charset(self.charset)
      self.parent.resume_pil_loop()

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
#  becomes visible, activate update timer
#
   def becomes_visible(self):
      self.hpterm.refresh()
      self.hpterm.start_update(UPDATE_TIMER)
#
#  becomes invisible, deactivate update timer
#
   def becomes_invisible(self):
      self.hpterm.start_update(UPDATE_TIMER*50)
#
# tabscope widget ----------------------------------------------------
#
class cls_tabscope(cls_tabtermgeneric):

   def __init__(self,parent,name):
      super().__init__(parent,name,True,False)
      self.showIdy= parent.config.get(self.name,"showidy",False)
      self.cbShowIdy= QtGui.QCheckBox("Show IDY frames")
      self.cbShowIdy.setChecked(self.showIdy)
      self.cbShowIdy.setEnabled(False)
      self.cbShowIdy.stateChanged.connect(self.do_show_idy)
      self.hbox2.addWidget(self.cbShowIdy)
      self.hbox2.setAlignment(self.cbShowIdy,QtCore.Qt.AlignLeft)
      self.hbox2.addStretch(1)
      self.scope_charpos=0

   def enable(self):
      super().enable()
      self.pildevice= cls_scope()
      self.parent.commobject.register(self.pildevice)
      self.pildevice.setactive(self.parent.config.get(self.name,"active"))
      self.pildevice.register_callback_dispchar(self.out_scope)
      self.cbShowIdy.setEnabled(True)
      self.pildevice.set_show_idy(self.showIdy)

   def disable(self):
      super().disable()
      self.cbShowIdy.setEnabled(False)


   def do_show_idy(self):
      self.cbShowIdy.setEnabled(False)
      self.showIdy= self.cbShowIdy.isChecked()
      self.parent.pause_pil_loop()
      self.parent.config.put(self.name,"showidy",self.showIdy)
      self.pildevice.set_show_idy(self.showIdy)
      self.parent.resume_pil_loop()
      self.cbShowIdy.setEnabled(True)
#
#  callback output char to console
#
   def out_scope(self,s):
      self.scope_charpos+=len(s)
      if self.scope_charpos>self.cols :
         self.hpterm.putchar("\x0D")
         self.hpterm.putchar("\x0A")
         self.cbLogging.logWrite("\n")
         self.scope_charpos=0
      for i in range(0,len(s)-1):
         self.hpterm.putchar(s[i])
      self.cbLogging.logWrite(s)
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
      self.parent.commobject.register(self.pildevice)
      self.pildevice.setactive(self.parent.config.get(self.name,"active"))
      self.pildevice.register_callback_printchar(self.out_printer)
      self.pildevice.register_callback_clprint(self.hpterm.reset)

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
#
#     Set default values
#
      self.termsize=parent.config.get(self.name,"terminalsize","80x24")
      self.cols=int(self.termsize.split(sep="x")[0])
      self.rows=int(self.termsize.split(sep="x")[1])
#
#     Build GUI 
#
      super().__set_termconfig__(self.rows,self.cols)
#
#     add Combobox for terminal size
#
      self.lbltxt1=QtGui.QLabel("Terminal size ")
      self.lbltxt1.setFixedHeight(10)
      self.lbltxt1.setFixedWidth(50)
      self.comboRes=QtGui.QComboBox()
      self.comboRes.addItem("80x24")
      self.comboRes.addItem("80x40")
      self.comboRes.addItem("120x25")
      self.hbox2.addWidget(self.comboRes)
      self.hbox2.setAlignment(self.comboRes,QtCore.Qt.AlignLeft)
#
#     add insert/replace indicator
#
      self.lblTermstatus=QtGui.QLabel()
      self.lblTermstatus.setText("Replace")
      self.lblTermstatus.setFixedWidth(50)
      self.lblTermstatus.setFixedHeight(10)
      self.hbox2.addStretch(1)
      self.hbox2.addWidget(self.lblTermstatus)
      self.hbox2.setAlignment(self.lblTermstatus,QtCore.Qt.AlignRight)

      self.comboRes.activated[str].connect(self.do_changeRes)
      self.comboRes.setCurrentIndex(self.comboRes.findText(self.termsize))
      self.comboRes.setEnabled(False)
      self.do_changeRes(self.termsize)
#
#     enable/disable
#
   def enable(self):
      super().enable()
      self.pildevice= cls_terminal()
      self.parent.commobject.register(self.pildevice)
      self.pildevice.setactive(self.parent.config.get(self.name,"active"))
      self.pildevice.register_callback_dispchar(self.out_terminal)
      self.pildevice.register_callback_cldisp(self.hpterm.reset)
      self.hpterm.set_kbdfunc(self.pildevice.queueOutput)
      self.hpterm.set_irindicfunc(self.do_irindic)
      self.comboRes.setEnabled(True)

   def disable(self):
      super().disable()
      self.comboRes.setEnabled(False)
#
#  callback to output character to teminal
#
   def out_terminal(self,s):
      self.hpterm.putchar(s)
#
#  callback update Insert/Replace indicator
#
   def do_irindic(self,insert):
      if insert:
         self.lblTermstatus.setText("Insert")
      else:
         self.lblTermstatus.setText("Replace")
#
#  callback change resolutiom
#
   def do_changeRes(self,text):
      self.termsize=text
      self.parent.config.put(self.name,'terminalsize',self.termsize)
      cols=int(text.split(sep="x")[0])
      rows=int(text.split(sep="x")[1])
      d_cols= cols- self.cols
      d_rows= rows- self.rows
      self.cols=cols
      self.rows=rows
#
#     Resize terminal
#
      self.width= self.font_width*self.cols
      self.height= int(self.font_height* self.rows)
      self.qterminal.hide()
      self.qterminal.setSize(self.width,self.height)
      self.hpterm.set_size(self.cols,self.rows)
      self.hpterm.refresh()
      self.qterminal.show()
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
      self.filename= parent.config.get(self.name,"filename","")
      self.drivetype= parent.config.get(self.name,"drivetype",self.DEV_HDRIVE1)
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
      self.lifdir=cls_LifDirWidget(None,10)
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
#
#     connect actions
#   
      self.radbutCass.clicked.connect(self.do_drivetypeChanged)
      self.radbutDisk.clicked.connect(self.do_drivetypeChanged)
      self.radbutHdrive1.clicked.connect(self.do_drivetypeChanged)
      self.butFilename.clicked.connect(self.do_filenameChanged)
#
#     refresh timer
#
      self.timer=QtCore.QTimer()
      self.timer.timeout.connect(self.update_hdrive)
#
#     enable/disable
#
   def enable(self):
      super().enable()
      self.pildevice= cls_drive()
      self.parent.commobject.register(self.pildevice)
      self.pildevice.setactive(self.parent.config.get(self.name,"active"))
      did,aid= self.deviceinfo[self.drivetype]
      self.pildevice.setdevice(did,aid)
      status, tracks, surfaces, blocks= self.lifMediumCheck(self.filename)
      if not status:
         self.filename=""
         self.parent.config.put(self.name,'filename',self.filename)
         try:
            self.parent.config.save()
         except PilConfigError as e:
            reply=QtGui.QMessageBox.critical(self.parent.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      self.pildevice.sethdisk(self.filename,tracks,surfaces,blocks)
      self.lblFilename.setText(self.filename)
      self.lifdir.setFileName(self.filename)
      self.butFilename.setEnabled(True)
      for w in self.gbox_buttonlist:
         w.setEnabled(True)
      self.lifdir.refresh()
      self.timer.start(REFRESH_RATE)

   def disable(self):
      super().disable()
      self.timer.stop()
      self.butFilename.setEnabled(False)
      for w in self.gbox_buttonlist:
         w.setEnabled(False)
      self.pildevice= None
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
   def do_filenameChanged(self):
      flist= self.get_lifFilename()
      if flist == None:
         return
      self.parent.pause_pil_loop()
      status, tracks, surfaces, blocks= self.lifMediumCheck(flist[0])
      if status:
         self.filename=flist[0]
      else:
         self.filename=""
      self.pildevice.sethdisk(self.filename,tracks,surfaces,blocks)
      self.lblFilename.setText(self.filename)
      self.lifdir.setFileName(self.filename)
      self.lifdir.refresh()
      self.parent.config.put(self.name,'filename',self.filename)
      try:
         self.parent.config.save()
      except PilConfigError as e:
         reply=QtGui.QMessageBox.critical(self.parent.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      self.parent.resume_pil_loop()

   def do_drivetypeChanged(self):
      i=0
      for w in self.gbox_buttonlist:
         if w.isChecked():
            self.drivetype=i
            break
         i+=1
      self.parent.pause_pil_loop()
      self.parent.config.put(self.name,'drivetype', self.drivetype)
#
#     remove filename
#
      if self.filename != "":
         self.filename=""
         self.parent.config.put(self.name,'filename',self.filename)
         self.lblFilename.setText(self.filename)
         self.lifdir.clear()
         reply=QtGui.QMessageBox.warning(self.parent.ui,'Warning',"Drive type changed. You have to reopen the LIF image file",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      did,aid= self.deviceinfo[self.drivetype]
      self.pildevice.setdevice(did,aid)
      try:
         self.parent.config.save()
      except PilConfigError as e:
         reply=QtGui.QMessageBox.critical(self.parent.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      self.parent.resume_pil_loop()

#
#  Drive tab: refresh directory listing of medium
#
   def update_hdrive(self):
      if self.filename=="":
         return
      if self.pildevice is None:
         return
      tm=time.time()
      if tm - self.parent.commobject.gettimestamp() > 3:
         if self.pildevice.ismodified():
            self.refreshDirList()

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
      dialog.setNameFilters( ["LIF Image File (*.dat *.DAT *.lif *.LIF)", "All Files (*.*)"] )
      dialog.setOptions(QtGui.QFileDialog.DontUseNativeDialog)
      dialog.setDirectory(self.parent.config.get('pyilper','workdir'))
      if dialog.exec():
         return dialog.selectedFiles() 
#
#  Check lif image file, returns status, tracks, surfaces, blocks 
#  If valid LIF1 medium and medium is compatible to device:
#     return True, tracks, surfaces, blocks of medium
#  else:
#     return False and default layout of device
#
   def lifMediumCheck(self,filename):
      defaultmedium= self.getDefaultMedium(self.drivetype)
      def_name, def_tracks, def_surfaces, def_blocks= self.mediainfo[defaultmedium]
      status, tracks, surfaces, blocks= self.getMediumInfo(filename)
      if status ==0: # medium info found
         medium=self.getMediumInfobyLayout(tracks,surfaces,blocks)
         if medium== self.MEDIUM_UNKNOWN:
            reply=QtGui.QMessageBox.critical(self.parent.ui,'Error',"LIF layout not supported.",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
            return [False, def_tracks, def_surfaces, def_blocks]
         if not self.isMediumCompatible(medium, self.drivetype):
            reply=QtGui.QMessageBox.critical(self.parent.ui,'Error',"LIF layout not supported for this device.",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
            return [False, def_tracks, def_surfaces, def_blocks]
         return [True, tracks, surfaces, blocks]
      elif status==1: # file dos not exist or cannot be opened
            return [True, def_tracks, def_surfaces, def_blocks]
      elif status==2:
         reply=QtGui.QMessageBox.critical(self.parent.ui,'Error',"File does not contain a LIF type 1 medium.",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return [False, def_tracks, def_surfaces, def_blocks]
      elif status==3:
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
         if platform.win32_ver()[0] != "":
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
#     liftype= getLifInt(b,20,2)
      dirstart=getLifInt(b,8,4)
#     if not(lifmagic == 0x8000 and liftype == 1 and dirstart == 2):
      if not(lifmagic == 0x8000 and dirstart == 2):
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


   def getMediumInfobyLayout(self,tracks,surfaces,blocks):
      for i in self.mediainfo.keys():
         t=self.mediainfo[i]
         if t[1]== tracks and t[2]== surfaces and t[3]== blocks:
            return i
      return self.MEDIUM_UNKNOWN

   def isMediumCompatible(self,media_type,device_type):
      if device_type == self.DEV_CASS and media_type != self.MEDIUM_CASS:
         return False
      if device_type == self.DEV_DISK and media_type != self.MEDIUM_DISK:
         return False
      return True

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

class cls_LifDirWidget(QtGui.QWidget):


    def __init__(self,parent,rows):
        super().__init__(parent)
        self.__table__ = QtGui.QTableView(self)  # Table view for dir
        self.__table__.setSortingEnabled(False)  # no sorting
#
#       switch off grid, no focus, no row selection
#
        self.__table__.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.__table__.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__table__.setShowGrid(False)
        self.__columns__=6     # 5 rows for directory listing
        self.__rowcount__=0    # number of rows in table
        self.__filename__=""   # LIF filename
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
        self.__table__.verticalHeader().setDefaultSectionSize(16)

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
        while True:
            r= lifdir.getNextEntry()
            if r == []:
              break
            name, ftype_num, start_block, alloc_blocks, datetime, ftype, length= r
            x=[name,ftype ,"{:-8d}".format(length),"{:-8d}".format(alloc_blocks*256),datetime.split(sep=' ')[0],datetime.split(sep=' ')[1]]
            for column in range(self.__columns__):
                item = QtGui.QStandardItem(x[column])
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
        self.__table__.sortByColumn(index)
        self.__table__.horizontalHeader().setSortIndicator(
                index, self.__table__.model().sortOrder())
        self.__table__.verticalScrollBar().setValue(0)

#
# Help Dialog class ----------------------------------------------------------
#
class cls_HelpWindow(QtGui.QDialog):

   def __init__(self,parent=None):
      docpath=os.path.join(os.path.dirname(pyilper.__file__),"Manual","index.html")
#
#     fix leading //  (OSX)
#
      docpath=re.sub("//","/",docpath,1)
      super().__init__()
      self.setWindowTitle('pyILPER Help')
 
      self.vlayout = QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)
      self.view = QtWebKit.QWebView()
      self.view.setFixedWidth(600)
      self.view.load(QtCore.QUrl.fromLocalFile(docpath))
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
# About Dialog class --------------------------------------------------------
#
class cls_AboutWindow(QtGui.QDialog):

   def __init__(self,version):
      super().__init__()
      self.setWindowTitle('pyILPER About ...')
      self.vlayout = QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)
      self.view = QtGui.QLabel()
      self.view.setFixedWidth(300)
      self.view.setWordWrap(True)
      self.view.setText("pyILPER "+version+ "\n\nAn emulator for virtual HP-IL devices for the PIL-Box derived from ILPER 1.4.5 for Windows\n\nCopyright (c) 2008-2013   Jean-Francois Garnier\nC++ version (c) 2015 Christoph Gießelink\nTerminal emulator code Henning Schröder\nPython Version (c) 2015 Joachim Siebold\n\nGNU General Public License Version 2\n")

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

      self.win = QtGui.QWidget()
      self.win.setWindowTitle("Select serial device")
      self.vlayout= QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.label= QtGui.QLabel()
      self.label.setText("Select or enter serial port")
      self.label.setAlignment(QtCore.Qt.AlignCenter)

      self.__ComboBox__ = QtGui.QComboBox() 
      self.__ComboBox__.setEditable(True)

      if platform.win32_ver()[0] != "":
#
#        Windows COM1 .. COM4
#
         for i in range (1,5):
            port="COM"+str(i)
            self.__ComboBox__.addItem( port, port )
      elif platform.dist()[0] != "":
#
#        Linux /dev/ttyUSB?
#
         devlist=glob.glob("/dev/ttyUSB*")
         for port in devlist:
            self.__ComboBox__.addItem( port, port )
#
#        Mac OS X /dev/*serial*
#
      elif platform.mac_ver()[0] != "":
         devlist=glob.glob("/dev/*FTD*")
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
      self.close()

   def do_cancel(self):
      self.__device__==""
      self.close()


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
      device= dialog.getDevice()
      return device

class cls_PilConfigWindow(QtGui.QDialog):

   def __init__(self, mode,tty, baudrate,port,remotehost,remoteport,workdir):
      super().__init__()
      self.__mode__= mode
      self.__tty__= tty
      self.__baudrate__=baudrate
      self.__port__= port
      self.__remotehost__= remotehost
      self.__remoteport__= remoteport
      self.__workdir__= workdir
      self.__config__= None
      

      self.win = QtGui.QWidget()
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
#     baud rate combo box
#
      self.hboxbaud= QtGui.QHBoxLayout()
      self.lbltxt2=QtGui.QLabel("Baud rate ")
      self.hboxbaud.addWidget(self.lbltxt2)
      self.hboxbaud.setAlignment(self.lbltxt2,QtCore.Qt.AlignLeft)
      self.comboBaud=QtGui.QComboBox()
      self.comboBaud.addItem("9600")
      self.comboBaud.addItem("115200")
      self.comboBaud.setCurrentIndex(self.__baudrate__)
      self.hboxbaud.addWidget(self.comboBaud)
      self.hboxbaud.addStretch(1)
      self.vboxgbox.addLayout(self.hboxbaud)
#
#     section TCP/IP communication
#
      self.radbutTCPIP = QtGui.QRadioButton(self.gbox)
      self.radbutTCPIP.setText("TCP/IP (experimental)")
      self.radbutTCPIP.clicked.connect(self.setCheckBoxes)
      self.vboxgbox.addWidget(self.radbutTCPIP)
#
#     Parameter input
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
      if self.__mode__==0:
         self.radbutPIL.setChecked(True)
      else:
         self.radbutTCPIP.setChecked(True)
      self.setCheckBoxes()
      self.vbox0.addWidget(self.gbox)
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
         self.comboBaud.setEnabled(True)
         self.butTty.setEnabled(True)
         self.edtPort.setEnabled(False)
         self.edtRemoteHost.setEnabled(False)
         self.edtRemotePort.setEnabled(False)
      else:
         self.__mode__=1
         self.comboBaud.setEnabled(False)
         self.butTty.setEnabled(False)
         self.edtPort.setEnabled(True)
         self.edtRemoteHost.setEnabled(True)
         self.edtRemotePort.setEnabled(True)

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
      dialog.setDirectory(os.path.expanduser('~'))
      if dialog.exec():
         return dialog.selectedFiles() 

   def do_config_Workdir(self):
      flist=self.getWorkDirName()
      if flist== None:
         return
      self.__workdir__= flist[0]
      self.lblwdir.setText(self.__workdir__)


   def do_ok(self):
      self.__baudrate__= self.comboBaud.currentIndex()
      self.__port__= int(self.edtPort.text())
      self.__remotehost__= self.edtRemoteHost.text()
      self.__remoteport__= int(self.edtRemotePort.text())
      self.__tty__= self.lblTty.text()
      self.__workdir__= self.lblwdir.text()
      self.__config__=[self.__mode__, self.__tty__, self.__baudrate__, 
         self.__port__, self.__remotehost__, self.__remoteport__, self.__workdir__]
      self.close()

   def do_cancel(self):
      self.__config__= None
      self.close()

   def getConfig(self):
      return self.__config__

   @staticmethod
   def getPilConfig(mode,tty,baudrate,port,remotehost,remoteport,workdir):
      dialog= cls_PilConfigWindow(mode,tty,baudrate,port,remotehost,remoteport,workdir)
      dialog.resize(200,100)
      result= dialog.exec_()
      config= dialog.getConfig()
      return config
#
# Get Tab Config Dialog class ------------------------------------------------
#

class cls_TabConfigWindow(QtGui.QDialog):

   def __init__(self, config):
      super().__init__()
      self.__config__= config

      self.win = QtGui.QWidget()
      self.win.setWindowTitle("Configure virtual HP-IL devices")
      self.vlayout= QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.label= QtGui.QLabel()
      self.label.setText("Configure virtual devices")
      self.label.setAlignment(QtCore.Qt.AlignCenter)
      self.vlayout.addWidget(self.label)
      self.glayout=QtGui.QGridLayout()
      self.spinScope=QtGui.QSpinBox()
      self.spinScope.setMinimum(1)
      self.spinScope.setMaximum(1)
      self.spinScope.setFixedWidth(35)
      self.spinScope.setEnabled(False)
      self.glayout.addWidget(self.spinScope,0,0)
      self.glayout.addWidget(QtGui.QLabel("Scopes"),0,2)
      self.spinDrive=QtGui.QSpinBox()
      self.spinDrive.setMinimum(0)
      self.spinDrive.setMaximum(5)
      self.spinDrive.setFixedWidth(35)
      self.glayout.addWidget(self.spinDrive,1,0)
      self.glayout.addWidget(QtGui.QLabel("Drives"),1,2)
      self.spinPrinter=QtGui.QSpinBox()
      self.spinPrinter.setMinimum(0)
      self.spinPrinter.setMaximum(3)
      self.spinPrinter.setFixedWidth(35)
      self.glayout.addWidget(self.spinPrinter,2,0)
      self.glayout.addWidget(QtGui.QLabel("Printers"),2,2)
      self.spinTerminal=QtGui.QSpinBox()
      self.spinTerminal.setMinimum(0)
      self.spinTerminal.setMaximum(1)
      self.spinTerminal.setFixedWidth(35)
      self.glayout.addWidget(self.spinTerminal,3,0)
      self.glayout.addWidget(QtGui.QLabel("Terminals"),3,2)
      self.glayout.setColumnMinimumWidth(1,10)
      self.vlayout.addLayout(self.glayout)
      self.buttonBox = QtGui.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.hlayout = QtGui.QHBoxLayout()
      self.hlayout.addWidget(self.buttonBox)
      self.vlayout.addWidget(self.buttonBox)

      self.spinScope.setValue(self.__config__[0])
      self.spinDrive.setValue(self.__config__[1])
      self.spinPrinter.setValue(self.__config__[2])
      self.spinTerminal.setValue(self.__config__[3])

   def do_ok(self):
      self.__config__= [self.spinScope.value(), self.spinDrive.value(),
       self.spinPrinter.value(),self.spinTerminal.value() ]
      self.close()

   def do_cancel(self):
      self.__config__= None
      self.close()

   def getConfig(self):
      return self.__config__

   @staticmethod
   def getTabConfig(config):
      dialog= cls_TabConfigWindow(config)
      dialog.resize(200,100)
      result= dialog.exec_()
      config= dialog.getConfig()
      return config

#
# HP-IL device Status Dialog class ---------------------------------------------
#

class cls_DevStatusWindow(QtGui.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.parent=parent
      self.setWindowTitle('HP-IL device status')
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

      self.__table__.resizeColumnsToContents()
      self.__table__.resizeRowsToContents()
      self.vlayout.addWidget(self.__table__)
      self.button = QtGui.QPushButton('OK')
      self.button.setFixedWidth(60)
      self.button.clicked.connect(self.do_exit)
      self.hlayout = QtGui.QHBoxLayout()
      self.hlayout.addWidget(self.button)
      self.vlayout.addLayout(self.hlayout)
      self.resize(500,120+16*self.rows)
      self.do_refresh()

   def hideEvent(self,event):
      self.__timer__.stop()

   def showEvent(self,event):
      self.__timer__.start(500)
      
   def do_exit(self):
      self.close()

   def do_refresh(self):
      i=1
      for row in range(self.rows):
         tabobject=self.parent.tabobjects[i]
         i+=1
         name= tabobject.name
         self.__items__[row,0].setText(name)
         for col in range (1,self.cols):
            self.__items__[row,col].setText("")
         if tabobject.pildevice== None:
            continue
         (active, did, aid, addr, addr2nd, hpilstatus)= tabobject.pildevice.getstatus()
         if not active:
            continue
         self.__items__[row,1].setText(did)
         self.__items__[row,2].setText("{0:x}".format(aid))
         self.__items__[row,3].setText("{0:x}".format(addr& 0xF))
         self.__items__[row,4].setText("{0:x}".format(addr2nd &0xF))
         self.__items__[row,5].setText("{0:b}".format(hpilstatus))
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

   def __init__(self,parent,version,width,height):
      super().__init__()
      self.setWindowTitle("pyILPER "+version)
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
      self.menuHelp= self.menubar.addMenu('Help')

      self.actionConfig=self.menuFile.addAction("pyILPER configuration")
      self.actionDevConfig=self.menuFile.addAction("HP-IL device configuration")
      self.actionDevStatus=self.menuFile.addAction("HP-IL device status")
      self.actionReconnect=self.menuFile.addAction("Reconnect")
      self.actionExit=self.menuFile.addAction("Quit")

      self.actionAbout=self.menuHelp.addAction("About")
      self.actionHelp=self.menuHelp.addAction("Help")
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
