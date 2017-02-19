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
# - development version uses other config file than the production version. This is
#   controlled by the PRODUCTION constant
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
#
import os
import sys
import signal
import threading
import traceback
import shutil
import pyilper
import re
import argparse
from PyQt4 import QtCore, QtGui
from .pilwidgets import cls_ui, cls_tabscope, cls_tabdrive, cls_tabprinter, cls_tabterminal, cls_PilMessageBox, cls_AboutWindow, cls_HelpWindow,cls_DeviceConfigWindow, cls_DevStatusWindow, cls_PilConfigWindow, cls_tabplotter, cls_PenConfigWindow
from .pilcore import *
from .pilconfig import cls_pilconfig, PilConfigError, PILCONFIG
from .penconfig import cls_penconfig, PenConfigError, PENCONFIG
from .pilbox import cls_pilbox, PilBoxError
from .pilboxthread import cls_PilBoxThread
from .piltcpip import cls_piltcpip, TcpIpError
from .piltcpipthread import cls_PilTcpIpThread
from .pilpipes import cls_pilpipes, PipesError
from .pilpipesthread import cls_PilPipesThread
from .lifexec import cls_lifinit, cls_liffix, cls_installcheck

STAT_DISABLED = 0     # Application in cold state:  not running
STAT_ENABLED = 1      # Application in warm state:  running
MODE_PILBOX=0         # connect to PIL-Box
MODE_TCPIP=1          # connect to virtual HP-IL over TCP/IP
MODE_PIPES=2          # conect via named pipes

TAB_CLASSES={TAB_SCOPE:cls_tabscope,TAB_PRINTER:cls_tabprinter,TAB_DRIVE:cls_tabdrive,TAB_TERMINAL:cls_tabterminal,TAB_PLOTTER:cls_tabplotter}


#
# Main application ------------------------------------------------------ 
#

class cls_pyilper(QtCore.QObject):

   sig_show_message=QtCore.pyqtSignal(str)
   sig_crash=QtCore.pyqtSignal()
   sig_quit=QtCore.pyqtSignal()


   def __init__(self,args):
 
      super().__init__()
      self.name="pyilper"
      self.instance=""
      if args.instance:
         if args.instance.isalnum():
            self.instance=args.instance
      self.status= STAT_DISABLED
      self.tabobjects= [ ]
      self.commobject=None
      self.commthread= None
      self.helpwin= None
      self.aboutwin=None
      self.devstatuswin=None
      self.message=""
      self.msgTimer=QtCore.QTimer()
      self.msgTimer.timeout.connect(self.show_refresh_message)

#
#     Initialize Main Window, connect callbacks
#
      self.ui= cls_ui(self,VERSION,self.instance)
      self.ui.actionConfig.triggered.connect(self.do_pyilperConfig)
      self.ui.actionDevConfig.triggered.connect(self.do_DevConfig)
      self.ui.actionPenConfig.triggered.connect(self.do_PenConfig)
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
         PILCONFIG.open(self.name,CONFIG_VERSION,self.instance)
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
         PILCONFIG.get(self.name,"terminalsize","80x24")
         PILCONFIG.get(self.name,"colorscheme","white")
         PILCONFIG.get(self.name,"terminalcharsize",15)
         PILCONFIG.get(self.name,"directorycharsize",13)
         PILCONFIG.get(self.name,"scrollupbuffersize",1000)
         PILCONFIG.get(self.name,"inpipename","/tmp/pilinpipe")
         PILCONFIG.get(self.name,"outpipename","/tmp/piloutpipe")
         PILCONFIG.get(self.name,"tabconfig",[[TAB_PRINTER,"Printer1"],[TAB_DRIVE,"Drive1"],[TAB_DRIVE,"Drive2"],[TAB_TERMINAL,"Terminal1"],[TAB_PLOTTER,"Plotter1"]])
         PILCONFIG.get(self.name,"version","0.0.0")
         PILCONFIG.save()
      except PilConfigError as e:
         reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         QtGui.qApp.quit()
#
#     2. pen configuration
      try:
         PENCONFIG.open(self.name,CONFIG_VERSION,self.instance)
      except PenConfigError as e:
         reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         QtGui.qApp.quit()
#
#     determine if we run a new version of pyILPER (or for the first time)
#
      oldversion=encode_version(PILCONFIG.get(self.name,"version"))
      thisversion=encode_version(VERSION)
      PILCONFIG.put(self.name,"version",VERSION)
#
#     create tab objects, scope is fixed all others are configured by tabconfig
#
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
         for obj in self.tabobjects:
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
         self.ui.tabs.setCurrentIndex(PILCONFIG.get(self.name,"active_tab"))
#
#     connect callback for tab change to update only the visible tab
#  
      self.ui.tabs.currentChanged[int].connect(self.tab_current_changed)
#
#  move window to last position
#
      position=PILCONFIG.get(self.name,"position")
      if position !="":
         self.ui.move(QtCore.QPoint(position[0],position[1]))
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
         reply=QtGui.QMessageBox.critical(self.ui,'Error',"Cannot change to working directory: "+e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return
#
#     connect to HP-IL
#

      mode=PILCONFIG.get(self.name,"mode")
      if mode == MODE_PILBOX:
#
#        create PIL-Box object, connect to PIL-Box. Return if not configured
#
         if PILCONFIG.get(self.name,'tty') =="":
            self.ui.emit_message("Serial device not confgured. Run pyILPER configuration")
            return

         try:
            self.commobject= cls_pilbox(PILCONFIG.get(self.name,'tty'),PILCONFIG.get(self.name,'ttyspeed'),PILCONFIG.get(self.name,'idyframe'),USE8BITS)
            self.commobject.open()
            self.commthread= cls_PilBoxThread(self.ui,self.commobject)
         except PilBoxError as e:
            reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+": "+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
            return
      elif mode== MODE_TCPIP:
#
#        create TCP-IP-object, connect to network
#
         try:
            self.commobject= cls_piltcpip(PILCONFIG.get(self.name,"port"),PILCONFIG.get(self.name,"remotehost"),PILCONFIG.get(self.name,"remoteport"))
            self.commobject.open()
            self.commthread= cls_PilTcpIpThread(self.ui,self.commobject)
         except TcpIpError as e:
            self.commobject.close()
            self.commobject=None
            reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+": "+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
            return
      else:
         self.commobject= cls_pilpipes(PILCONFIG.get(self.name,"inpipename"),PILCONFIG.get(self.name,"outpipename"))
         try:
            self.commobject.open()
            self.commthread= cls_PilPipesThread(self.ui,self.commobject)
         except PipesError as e:
            self.commobject.close()
            self.commobject=None
            reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+": "+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
            return
#
#     enable all registered tab objects
#
      for obj in self.tabobjects:
         obj.enable()
#
#     register outbound scope
#
      self.tabobjects[0].post_enable()
#
#     start emulator thread
#
      self.commthread.start()
      self.status= STAT_ENABLED
#
#     trigger visible tab to enable refreshs
#
      tab= self.ui.tabs.widget(PILCONFIG.get(self.name,"active_tab"))
      tab.becomes_visible()

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
      for obj in self.tabobjects:
         obj.disable()

#
#     close commobject/tcpip connection
#
      if self.commobject != None:
         try:
            self.commobject.close()
         except:
            pass
      self.commobject=None
      self.status= STAT_DISABLED
#
#  clean up from thread crash
#
   def do_crash_cleanup(self):
      self.commthread= None
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
      self.tabobjects.append(tab)
#
#  callback tab changed
#
   def tab_current_changed(self,idx):
      oldtab= PILCONFIG.get(self.name,"active_tab")
      if oldtab != idx:
         self.ui.tabs.widget(oldtab).becomes_invisible()
         self.ui.tabs.widget(idx).becomes_visible()
         PILCONFIG.put(self.name,"active_tab",idx)

#
#  callback pyilper configuration
#
   def do_pyilperConfig(self):
      
      if cls_PilConfigWindow.getPilConfig(self):
         self.disable()
         try:
            PILCONFIG.save()
         except PilConfigError as e:
            reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
            return
         self.enable()
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
         reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return
      reply=QtGui.QMessageBox.information(self.ui,"Restart required","HP-IL Device configuration changed. Restart Application.",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      
#
# callback plotter pen configuration
#
   def do_PenConfig(self):
      if not cls_PenConfigWindow.getPenConfig():
         return
      try:
         PENCONFIG.save()
      except PenConfigError as e:
         reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return

#
#  callback show hp-il device status
#
   def do_DevStatus(self):
      if self.devstatuswin== None:
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
#  callback exit
#
   def do_Exit(self):
      self.disable()
      position=[self.ui.pos().x(),self.ui.pos().y()]
      try:
         PILCONFIG.put(self.name,"position",position)
         PILCONFIG.save()
      except PilConfigError as e:
         reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      QtGui.qApp.quit()
#
#  callback initialize LIF medium
#
   def do_Init(self):
      workdir=  PILCONFIG.get(self.name,"workdir")
      cls_lifinit.exec(workdir)

#
#  callback fix LIF Medium
#
   def do_Fix(self):
      workdir=  PILCONFIG.get(self.name,"workdir")
      cls_liffix.exec(workdir)
#
#  callback check LIFUTILS installation
#
   def do_InstallCheck(self):
      cls_installcheck.exec()

#
#  callback copy PILIMAGE.DAT to working directory
#
   def do_CopyPilimage(self):

      srcfile=os.path.join(os.path.dirname(pyilper.__file__),"lifimage","PILIMAGE.DAT")
      srcfile= re.sub("//","/",srcfile,1)
      dstpath=PILCONFIG.get(self.name,"workdir")
      if os.access(os.path.join(dstpath,"PILIMAGE.DAT"),os.W_OK):
         reply=QtGui.QMessageBox.warning(self.ui,'Warning',"File PILIMAGE.DAT already exists. Do you really want to overwrite that file?",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Cancel)
         if reply== QtGui.QMessageBox.Cancel:
            return
      try:
         shutil.copy(srcfile,dstpath)
      except OSError as e:
         reply=QtGui.QMessageBox.critical(self.ui,'Error',"Cannot copy file: "+e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return

#
#  callback show about window
#
   def do_About(self):
      if self.aboutwin== None:
         self.aboutwin= cls_AboutWindow(VERSION)
      self.aboutwin.show()
      self.aboutwin.raise_()
#
#  callback show help window
#
   def do_Help(self):
      if self.helpwin == None:
         self.helpwin= cls_HelpWindow()
      self.helpwin.show()
      self.helpwin.loadDocument("","index.html")
      self.helpwin.raise_()
#
#  show release information window
#
   def show_ReleaseInfo(self, version):
      if self.helpwin == None:
         self.helpwin= cls_HelpWindow()
      self.helpwin.show()
      self.helpwin.loadDocument("Misc","Releasenotes.html")
      self.helpwin.raise_()
#
#  show startup info
#
   def show_StartupInfo(self):
      if self.helpwin == None:
         self.helpwin= cls_HelpWindow()
      self.helpwin.show()
      self.helpwin.loadDocument("Introduction","Startup.html")
      self.helpwin.raise_()

def dumpstacks(signal, frame):
  for threadId, stack in sys._current_frames().items():
    print("Thread ID %x" % threadId)
    traceback.print_stack(f=stack)

def main():
   parser=argparse.ArgumentParser(description='pyILPER startup script')
   parser.add_argument('--instance', '-instance', default="", help="Start a pyILPER instance INSTANCE")
   args=parser.parse_args()

   if not isWINDOWS():
      signal.signal(signal.SIGQUIT, dumpstacks)
   app = QtGui.QApplication(sys.argv)
   pyilper= cls_pyilper(args)
   sys.exit(app.exec_())


if __name__ == '__main__':

   main()
