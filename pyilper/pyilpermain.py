#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pyILPER 1.2.4 for Linux
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
# pyILPER main program -----------------------------------------------------
#
# Changelog
# 05.10.2015 jsi:
# - new style signal/slot handling for quit, crash and show_message
# - adjust super statements to python3+ syntax
# 11.10.2015 jsi:
# - bump version number to 1.2.2
# 24.10.2015 jsi
# - raise gui (OS X issue)
# 28.10.2015 jsi
# - introduced separate version number for config file layout
# 08.11.2015 jsi
# - bump version number to 1.2.3
# 14.11.2015 jsi
# - bump version number to 1.3.0
# 29.11.2015 jsi
# - removed pause and resume pil loop
# 30.11.2015 jsi
# - introduced idyframe option
# - bump version number to 1.3.1
# 18.12.2015 jsi
# - bump version number to 1.3.2
# 26.12.2015 cg
# -fixed misspelling
# 10.1.2016 jsi
# - store last windows position as proposed by cg
# 11.1.2016 jsi
# - corrected error im my implementation of determining the windows position
# 22.1.2016 jsi
# - corrected typo in Message box if HP-IL device config was changed, hint by cg
# 01.02.2016 jsi
# - added InstallCheck menu entry
# 16.02.2016 jsi
# - bump version number to 1.3.3 (Development)
# 20.02.2016 jsi
# - dump stacks introduced
# 21.02.2016 jsi
# - dump stacks disabled for windows
# 02.03.2016 jsi
# - added generic terminal configuration
# 05.03.2016 jsi
# - renmoved dead code
# 22.02.2016 jsi
# - modified call of cls_ui
# 01.04.2016 jsi
# - added copy function of PILIMAGE.DAT to the utility menu
# 03.04.2016 jsi
# - 1.3.3 productio
# 05.04.2016 jsi
# - bump version number to 1.3.4 (Development)
# 07.04.2016 cg
# - added 230400 baud to supported baudrates
# 14.04.2016 jsi
# - store coordinate list of position in config instead of QPoint Object
# - set config file version to 2
# 21.04.2016 jsi
# - development version uses other config file than the production version. This 
#   is controlled by the PRODUCTION constant
# 26.04.2016 jsi
# - IDY frame processing now enabled by default
# - remove baudrate config parameter
# - TypeError in open tty device now handled in pilbox.py
# - show error if no serial device was configured.
# 28.04.2016 jsi
# - call post_enable to register outbound scope device
# 07.05.2016 jsi
# - introduce parameter for scroll up buffer size
# 08.05.2016 jsi
# - refactoring, make autobaud/baud rate setting configurable again (ttyspeed parameter)
# 03.07.2016 jsi
# - refactoring import reorganized
# 08.07.2016 jsi
# - refactoring, use constant for configuration
# - refactoring, move constants to pilcore.py
# - refactoring, use platform functions from pilcore.py
# 27.08.2016 jsi
# - tab configuration rewritten
# 18.09.2016 jsi
# - multiple instances capability added
# 13.10.2016 jsi
# - device configuration rewritten (add, remove and change position of devices)
# 19.10.2016 jsi
# - added pen config menu entry (merged)
# 19.11.2016 jsi
# - pipes thread added
# 11.12.2016 jsi
# - default configuration now includes the plotter
# 07.01.2016 jsi
# - store pyILPER version in config file
# - show "first run" information, if started unconfigures
# - show release information if a new pyILPER version was started the first time
# - show tty device unconfigured message in status bar instead in pop up window
# 19.02.2017 jsi:
# - directorycharsize parameter introduced
# 11.03.2017 jsi:
# - change document names of release notes and change log
# 16.03.2017 jsi:
# - catch exception if neither QtWebKitWidgets or QtWebEngineWidgets are found
# 17.03.2017 jsi:
# - do not load initial document, if online manual is re-opened
# 01.08.2017 jsi
# - HP82162A added
# 07.08.2017 jsi
# - papersize parameter now global
# - refactoring of tab classes
# - minimum display position is 50,50 - otherwise some display manager hide
#   the menu bar (e.g. RASPBIAN)
# - error in exception handling of reading the config file fixed
# 23.08.2017 jsi:
# - used pilsocket instead of pilpipes
# 30.08.2017 jsi:
# - save and restore main window size
# 31.08.2017 jsi:
# - config parameter terminalsize changed to terminalwidth
# 04.09.2017 jsi:
# - refactoring of thread classes
# 20.09.2017 jsi:
# - configuration of tab parameters at runtime
# 28.10.2017 jsi:
# - detection of lifutils now in cls_pyilper
# 12.11.2017 jsi:
# - removed configuration parameters: winpipename and socketname
# - introduced configuration parameter: serverport
# - remove MODE_PIPE communication
# 17.11.2017 jsi:
# - put drive tabs at the end in the default configuration
# 05.12.2017 jsi
# - initialized parameter hp82162a_pixelsize
# 27.12.2017 jsi
# - changes because of new cls_Tabs widget
# 17.01.2018 jsi
# - remove global parameters for terminal width and color scheme which
#   are now tab specific. 
# - remove scrollupbuffersize as global parameter
# 05.02.2018 jsi
# - usebom config variable introduced
# 12.02.2018 jsi
# - added --clean startup option
# 01.03.2018 jsi
# - check minimum python version
# 10.08.2018 jsi
# - cls_PenConfigWindow moved to penconfig.py
# 11.08.2018 jsi
# - terminal custom shortcut config added
# 18.12.2018 jsi
# - added HP2225B tab
# 06.01.2018 jsi
# - added HP2225B screenwidth global parameter
# 30.11.2019 jsi
# - improved help text for command line parameters
# 26.11.2020 jsi
# - fix: disable filemanagement controls, if lifutils are not installed
# 15.11.2021 jsi
# - raw drive tab added to TAB_CLASSES dict
# 12.12.2021 jsi
# - copy config runtime option added
# - check if the configuration are from a newer pyILPER version
# 18.12.2021 jsi
# - copy config: display versions
# 19.12.2021 jsi
# - copy config: error processing added
# 04.05.2022 jsi
# - PySide6 migration
#
import os
import sys
import signal
import traceback
import shutil
import pyilper
import re
import argparse
import time
from .pilcore import *
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtWidgets
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtWidgets
from .pilwidgets import cls_ui, cls_AboutWindow, cls_HelpWindow, HelpError, cls_DeviceConfigWindow, cls_DevStatusWindow, cls_PilConfigWindow
from .pilconfig import  PilConfigError, PILCONFIG, cls_pilconfig
from .penconfig import  PenConfigError, PENCONFIG, cls_PenConfigWindow
from .shortcutconfig import  ShortcutConfigError, SHORTCUTCONFIG, cls_ShortcutConfigWindow
from .pilthreads import cls_PilBoxThread, cls_PilTcpIpThread, cls_PilSocketThread, PilThreadError
from .lifexec import cls_lifinit, cls_liffix, cls_installcheck, check_lifutils
from .pilhp82162a import cls_tabhp82162a
from .pilplotter import cls_tabplotter
from .pildrive import cls_tabdrive,cls_tabrawdrive
from .pilscope import cls_tabscope
from .pilprinter import cls_tabprinter
from .pilterminal import cls_tabterminal
from .pilhp2225b import cls_tabhp2225b

STAT_DISABLED = 0     # Application in cold state:  not running
STAT_ENABLED = 1      # Application in warm state:  running

COMMTHREAD_CLASSES={MODE_PILBOX:cls_PilBoxThread,MODE_TCPIP:cls_PilTcpIpThread,MODE_SOCKET:cls_PilSocketThread}

TAB_CLASSES={TAB_SCOPE:cls_tabscope,TAB_PRINTER:cls_tabprinter,TAB_DRIVE:cls_tabdrive,TAB_TERMINAL:cls_tabterminal,TAB_PLOTTER:cls_tabplotter,TAB_HP82162A:cls_tabhp82162a,TAB_HP2225B: cls_tabhp2225b, TAB_RAWDRIVE: cls_tabrawdrive}

#
# Main application ------------------------------------------------------ 
#

class cls_pyilper(QtCore.QObject):

   if QTBINDINGS=="PySide6":
       sig_show_message=QtCore.Signal(str)
       sig_crash=QtCore.Signal()
       sig_quit=QtCore.Signal()
   if QTBINDINGS=="PyQt5":
       sig_show_message=QtCore.pyqtSignal(str)
       sig_crash=QtCore.pyqtSignal()
       sig_quit=QtCore.pyqtSignal()

   def __init__(self,args):
 
      super().__init__()
      self.name="pyilper"
      self.instance=""
      self.clean=False
      if args.instance:
         if args.instance.isalnum():
            self.instance=args.instance
      if args.clean:
         self.clean=True
      self.status= STAT_DISABLED
      self.pilwidgets= [ ]
      self.commobject=None
      self.commthread= None
      self.helpwin= None
      self.aboutwin=None
      self.devstatuswin=None
      self.lifutils_installed= False
      self.message=""
      self.msgTimer=QtCore.QTimer()
      self.msgTimer.timeout.connect(self.show_refresh_message)
#
#     create user interface instance
#
      self.ui= cls_ui(self,VERSION,self.instance)
#
#     check minimum python version
#
      if sys.version_info < ( PYTHON_REQUIRED_MAJOR, PYTHON_REQUIRED_MINOR):
         required_version= str(PYTHON_REQUIRED_MAJOR)+"."+str(PYTHON_REQUIRED_MINOR)
         found_version=str(sys.version_info.major)+"."+str(sys.version_info.minor)+"."+str(sys.version_info.micro)
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error','pyILPER requires at least Python version '+required_version+". You rund Python version "+found_version,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         sys.exit(1)

#
#     Initialize Main Window, connect callbacks
#
      self.ui.actionConfig.triggered.connect(self.do_pyilperConfig)
      self.ui.actionDevConfig.triggered.connect(self.do_DevConfig)
      self.ui.actionPenConfig.triggered.connect(self.do_PenConfig)
      self.ui.actionShortcutConfig.triggered.connect(self.do_ShortcutConfig)
      self.ui.actionDevStatus.triggered.connect(self.do_DevStatus)
      self.ui.actionReconnect.triggered.connect(self.do_Reconnect)
      self.ui.actionExit.triggered.connect(self.do_Exit)
      self.ui.actionInit.triggered.connect(self.do_Init)
      self.ui.actionFix.triggered.connect(self.do_Fix)
      self.ui.actionCopyPilimage.triggered.connect(self.do_CopyPilimage)
      self.ui.actionInstallCheck.triggered.connect(self.do_InstallCheck)
      self.ui.actionAbout.triggered.connect(self.do_About)
      self.ui.actionHelp.triggered.connect(self.do_Help)

#
#     queued signal to show a status message. This is the only update of
#     the user interface that is issued by the thread process and must
#     be issued as a queued connection
#
      self.sig_show_message.connect(self.show_message, QtCore.Qt.QueuedConnection)
      self.sig_crash.connect(self.do_crash_cleanup, QtCore.Qt.QueuedConnection)
      self.sig_quit.connect(self.do_Exit, QtCore.Qt.QueuedConnection)

#
#     Set up configuration subsystem
#     1. pyILPER config
#
      try:
         PILCONFIG.open(self.name,CONFIG_VERSION,self.instance,PRODUCTION,self.clean)
         PILCONFIG.get(self.name,"active_tab",0)
         PILCONFIG.get(self.name,"tabconfigchanged",False)
         PILCONFIG.get(self.name,"tty","")
         PILCONFIG.get(self.name,"ttyspeed",0)
         PILCONFIG.get(self.name,"idyframe",True)
         PILCONFIG.get(self.name,"port",60001)
         PILCONFIG.get(self.name,"remotehost","localhost")
         PILCONFIG.get(self.name,"remoteport",60000)
         PILCONFIG.get(self.name,"mode",MODE_PILBOX)
         PILCONFIG.get(self.name,"workdir",os.path.expanduser('~'))
         PILCONFIG.get(self.name,"position","")
         PILCONFIG.get(self.name,"serverport",59999)
         PILCONFIG.get(self.name,"tabconfig",[[TAB_PRINTER,"Printer1"],[TAB_TERMINAL,"Terminal1"],[TAB_PLOTTER,"Plotter1"],[TAB_DRIVE,"Drive1"],[TAB_DRIVE,"Drive2"]])
         PILCONFIG.get(self.name,"version","0.0.0")
         PILCONFIG.get(self.name,"helpposition","")
         PILCONFIG.get(self.name,"papersize",0)
         PILCONFIG.get(self.name,"lifutilspath","")
         PILCONFIG.get(self.name,"terminalcharsize",15)
         PILCONFIG.get(self.name,"directorycharsize",13)
         PILCONFIG.get(self.name,"hp82162a_pixelsize",1)
         PILCONFIG.get(self.name,"hp2225b_screenwidth",640)
         PILCONFIG.get(self.name,"usebom",False)

         PILCONFIG.save()
      except PilConfigError as e:
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         sys.exit(1)
#
#     2. pen configuration
#
      try:
         PENCONFIG.open(self.name,CONFIG_VERSION,self.instance,PRODUCTION,self.clean)
      except PenConfigError as e:
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         sys.exit(1)
#
#     3. terminal keyboard shortcuts
#
      try:
         SHORTCUTCONFIG.open(self.name,CONFIG_VERSION,self.instance,PRODUCTION,self.clean)
      except ShortcutConfigError as e:
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         sys.exit(1)
#
#     check lifutils
#
      self.lifutils_installed= check_lifutils()[0]
      if self.lifutils_installed:
         self.ui.enableLIFControls()
#
#     version check, warn user if the configuration files are of a newer
#     version
#
      oldversion=decode_pyILPERVersion(PILCONFIG.get(self.name,"version"))
      thisversion=decode_pyILPERVersion(VERSION)
      if thisversion < oldversion:
         reply=QtWidgets.QMessageBox.warning(self.ui,'Warning',"Your configuration files are of pyILPER version "+PILCONFIG.get(self.name,"version")+" which is newer than the version you are running. The program might crash or mishehave. Do you want to continue?",QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Cancel)
         if reply== QtWidgets.QMessageBox.Cancel:
            sys.exit(1) 
      PILCONFIG.put(self.name,"version",VERSION)
#
#     create tab objects, scope is fixed all others are configured by tabconfig
#
      active_tab=PILCONFIG.get(self.name,"active_tab")
      self.registerTab(cls_tabscope,"Scope")
      for t in PILCONFIG.get(self.name,"tabconfig"):
         self.registerTab(TAB_CLASSES[t[0]],t[1])
#
#     remove config of non existing tabs
#
      if PILCONFIG.get(self.name,"tabconfigchanged"):
         PILCONFIG.put(self.name,"tabconfigchanged",False)
         PILCONFIG.put(self.name,"active_tab",0)
         names= [self.name]
         for obj in self.pilwidgets:
            names.append(obj.name)
         removekeys=[]
         for key in PILCONFIG.getkeys():
            prefix=key.split(sep="_")[0]
            if not prefix in names:
               removekeys.append(key)
         for key in removekeys:
            PILCONFIG.remove(key)
      else:
#
#     go to last active tab (if tabconfig did not change)
#
         self.ui.tabs.setCurrentIndex(active_tab)
#
#  move window to last position
#
      position=PILCONFIG.get(self.name,"position")
      if position !="":
         self.ui.move(QtCore.QPoint(position[0],position[1]))
         if len(position)==4:
            self.ui.resize(position[2],position[3])
#
#  show and raise gui
#
      self.ui.show()
      self.ui.raise_()
#
#     start application into warm state
#
      self.enable()
      self.msgTimer.start(500)
#
#     if we run pyILPER for the first time (oldversion =0.0.0), show startup info
#
      if PILCONFIG.get(self.name,"position")=="":
         self.show_StartupInfo()
      else:
#
#     if we run a new version for the first time, show release notes
#
         if thisversion > oldversion:
            self.show_ReleaseInfo(VERSION)
#
#  start application into warm state
#
   def enable(self):
      if self.status== STAT_ENABLED:
         return
#
#     set working directory
#
      try:
         os.chdir(PILCONFIG.get(self.name,'workdir'))
      except OSError as e:
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error',"Cannot change to working directory: "+e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         return
#
#     create and enable thread
#
      mode=PILCONFIG.get(self.name,"mode")
      try:
         commthread_class= COMMTHREAD_CLASSES[mode]
         self.commthread= commthread_class(self.ui)
         self.commthread.enable()
      except PilThreadError as e:
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error',e.msg+": "+e.add_msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         return
#
#     enable all registered tab objects
#
      for obj in self.pilwidgets:
         obj.enable()
#
#     register outbound scope
#
      self.pilwidgets[0].post_enable()
#
#     start emulator thread
#
      self.commthread.start()
      self.status= STAT_ENABLED
#
#     trigger visible virtual device widget to enable refreshs
#
      pilwidget= self.ui.tabs.pilWidget(PILCONFIG.get(self.name,"active_tab"))
      pilwidget.becomes_visible()

#
#  shut down application to cold state
#
   def disable(self):
      if self.status== STAT_DISABLED:
         return
#
#     stop emulator thread
#
      if self.commthread is not None:
         if self.commthread.isRunning:
            self.commthread.finish()
#
#     disable all registered tab objects
#
      for obj in self.pilwidgets:
         obj.disable()

#
#     close commobject/tcpip connection
#
      if self.commthread is not None:
         self.commthread.disable()
      self.status= STAT_DISABLED
      self.commthread= None
#
#  clean up from thread crash
#
   def do_crash_cleanup(self):
      time.sleep(1)
      self.disable()

#
#  show status message
#
   def show_message(self,message):
      self.message=message
      self.ui.statusbar.showMessage(self.message)

#
#  refresh status message
#
   def show_refresh_message(self):
      self.ui.statusbar.showMessage(self.message)

   def registerTab(self,classname,name):
      tab= classname(self,name)
      self.ui.tabs.addTab(tab,name)
      self.pilwidgets.append(tab)
#
#  callback pyilper configuration, reset the communication only if needed
#
   def do_pyilperConfig(self):
      (accept, needs_reconnect, needs_reconfigure)= cls_PilConfigWindow.getPilConfig(self)
      if accept:
         if needs_reconnect:
            self.disable()
         try:
            PILCONFIG.save()
         except PilConfigError as e:
            reply=QtWidgets.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
            return
         if needs_reconnect:
            self.enable()
#
#        reconfigure the tabs while the thread is stopped
#
         if needs_reconfigure:
            if self.status== STAT_ENABLED:
               if self.commthread is not None:
                  if self.commthread.isRunning():
                     self.commthread.halt()
            for obj in self.pilwidgets:
               obj.reconfigure()
            if self.status== STAT_ENABLED:
               if self.commthread is not None:
                  self.commthread.resume()
#
#  callback HP-IL device config
#
   def do_DevConfig(self):
      if not cls_DeviceConfigWindow.getDeviceConfig(self):
         return
      PILCONFIG.put(self.name,"tabconfigchanged",True)
      try:
         PILCONFIG.save()
      except PilConfigError as e:
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         return
      reply=QtWidgets.QMessageBox.information(self.ui,"Restart required","HP-IL Device configuration changed. Restart Application.",QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
      
#
# callback plotter pen configuration
#
   def do_PenConfig(self):
      if not cls_PenConfigWindow.getPenConfig():
         return
      try:
         PENCONFIG.save()
      except PenConfigError as e:
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         return

#
# callback terminal keyboard shortcut configuration
#
   def do_ShortcutConfig(self):
      if not cls_ShortcutConfigWindow.getShortcutConfig():
         return
      try:
         SHORTCUTCONFIG.save()
      except ShortcutConfigError as e:
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         return

#
#  callback show hp-il device status
#
   def do_DevStatus(self):
      if self.devstatuswin is None:
         self.devstatuswin= cls_DevStatusWindow(self)
      self.devstatuswin.show()
      self.devstatuswin.raise_()
#
#  callback reconnect
#
   def do_Reconnect(self):
      self.disable()
      self.enable()
#
#  callback exit, store windows position and size, close floating windows
#
   def do_Exit(self):
      self.disable()
      pos_x=self.ui.pos().x()
      pos_y=self.ui.pos().y()
      if pos_x < 50:
         pos_x=50
      if pos_y < 50:
         pos_y=50
      width= self.ui.width()
      height= self.ui.height()

      position=[pos_x, pos_y, width, height]

      PILCONFIG.put(self.name,"position",position)
      if self.helpwin is not None:
         helpposition=[self.helpwin.pos().x(),self.helpwin.pos().y(),self.helpwin.width(),self.helpwin.height()]
         PILCONFIG.put(self.name,"helpposition",helpposition)
      self.ui.tabs.closeFloatingWindows()
      try:
         PILCONFIG.save()
      except PilConfigError as e:
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
      QtWidgets.QApplication.quit()
#     print(os.times())
#
#  callback initialize LIF medium
#
   def do_Init(self):
      workdir=  PILCONFIG.get(self.name,"workdir")
      cls_lifinit.execute(workdir)

#
#  callback fix LIF Medium
#
   def do_Fix(self):
      workdir=  PILCONFIG.get(self.name,"workdir")
      cls_liffix.execute(workdir)
#
#  callback check LIFUTILS installation
#
   def do_InstallCheck(self):
      cls_installcheck.execute()

#
#  callback copy PILIMAGE.DAT to working directory
#
   def do_CopyPilimage(self):

      srcfile=os.path.join(os.path.dirname(pyilper.__file__),"lifimage","PILIMAGE.DAT")
      srcfile= re.sub("//","/",srcfile,1)
      dstpath=PILCONFIG.get(self.name,"workdir")
      if os.access(os.path.join(dstpath,"PILIMAGE.DAT"),os.W_OK):
         reply=QtWidgets.QMessageBox.warning(self.ui,'Warning',"File PILIMAGE.DAT already exists. Do you really want to overwrite that file?",QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Cancel)
         if reply== QtWidgets.QMessageBox.Cancel:
            return
      try:
         shutil.copy(srcfile,dstpath)
      except OSError as e:
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error',"Cannot copy file: "+e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         return
      except shutil.SameFileError:
         reply=QtWidgets.QMessageBox.critical(self.ui,'Error',"Source and destination file are identical",QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         return

#
#  callback show about window
#
   def do_About(self):
      if self.aboutwin is None:
         self.aboutwin= cls_AboutWindow(VERSION)
      self.aboutwin.show()
      self.aboutwin.raise_()
#
#  callback show help window
#
   def do_Help(self):
      self.show_Help("","index.html")
#
#  show release information window
#
   def show_ReleaseInfo(self, version):
      self.show_Help("","releasenotes.html")
#
#  show startup info
#
   def show_StartupInfo(self):
      self.show_Help("","startup.html")
#
#  show help windows for a certain document
#
   def show_Help(self,path,document):
      if self.helpwin is None:
         try:
            self.helpwin= cls_HelpWindow()
            self.helpwin.loadDocument(path,document)
         except HelpError as e:
            reply=QtWidgets.QMessageBox.critical(self.ui,'Error',e.value,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
            return
         helpposition=PILCONFIG.get(self.name,"helpposition")
         if helpposition!= "":
            self.helpwin.move(QtCore.QPoint(helpposition[0],helpposition[1]))
            self.helpwin.resize(helpposition[2],helpposition[3])
         else:
            self.helpwin.resize(720,700)
      self.helpwin.show()
      self.helpwin.raise_()
#
# copy configuration data from devel to production and vice versa
# - a development/beta version of pyILPER copies the files of the
#   production version
# - a production version of pyILPER copies the files of the development/beta
#   version
#
def copy_config(args):
   count=0
#
#  get version numbers
#
   from_config=cls_pilconfig()
   to_config=cls_pilconfig()
   try:
      from_config.open("pyilper",CONFIG_VERSION,args.instance, not PRODUCTION,False)
      from_version=from_config.get("pyilper","version","0.0.0")
      to_config.open("pyilper",CONFIG_VERSION,args.instance, PRODUCTION,False)
      to_version=to_config.get("pyilper","version","0.0.0")
   except PilConfigError as e:
      print(e.msg+': '+e.add_msg)
      return
   if from_version == "0.0.0":
      print("There are no configuration files to copy")
      return
#
#  ask for confirmation
#
   print("\nW A R N I N G!")
   print("This overwrites the configuration files")
   if PRODUCTION:
      print("of the production version: ", to_version)
   else:
      print("of the development/beta version: ", to_version)
   print("with the configuration files")
   if PRODUCTION:
      print("of the development/beta version: ",from_version)
   else:
      print("of the production version: ",from_version)
   inp= input("Continue? (enter 'YES' uppercase): ")
   if inp !="YES":
      print("cancelled")
      return
#
#  now copy configuration files
#
   for name in ['pyilper','penconfig','shortcutconfig']:
      from_filename=buildconfigfilename("pyilper",name,CONFIG_VERSION,args.instance,not PRODUCTION)[0]
      if not os.path.isfile(from_filename):
         continue
      to_filename=buildconfigfilename("pyilper",name,CONFIG_VERSION,args.instance, PRODUCTION)[0]
      try:
         shutil.copy(from_filename,to_filename)
      except OSError as e:
         print("Error copying file "+from_filename+": "+e.strerror)
         return
      except  SameFileError as e:
         print("Error copying file "+from_filename+" "+"source and destination file are identical")
         return
      print(from_filename)
      print("copied to:")
      print(to_filename)
      count+=1
   print(count,"files copied. Restart pyILPER without the 'cc' option now")

#
# dump stack if signalled externally (for debugging)
#
def dumpstacks(signal, frame):
  for threadId, stack in sys._current_frames().items():
    print("Thread ID %x" % threadId)
    traceback.print_stack(f=stack)

def main():
   parser=argparse.ArgumentParser(description='pyILPER command line invocation')
   parser.add_argument('--instance', '-instance', default="", help="Start a pyILPER instance INSTANCE. This instance has an own configuration file.")
   parser.add_argument('--clean','-clean',action='store_true',help="Start pyILPER with a config file which is reset to defaults")
   parser.add_argument('--cc','-cc',action='store_true',help="Copy configuration from development to production version and vice versa")
   args=parser.parse_args()
   if args.cc:
      copy_config(args)
      sys.exit(1)

   if not isWINDOWS():
      signal.signal(signal.SIGQUIT, dumpstacks)
   app = QtWidgets.QApplication(sys.argv)
   pyilper= cls_pyilper(args)
   sys.exit(app.exec())


if __name__ == '__main__':

   main()
