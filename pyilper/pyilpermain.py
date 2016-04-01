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
#
import os
import sys
import platform
import signal
import threading
import traceback
import shutil
import pyilper
import re
from PyQt4 import QtCore, QtGui
from pyilper import cls_pilbox,PilBoxError,cls_piltcpip, TcpIpError,cls_pilconfig, PilConfigError, cls_ui,cls_tabscope, cls_PilBoxThread, cls_PilTcpIpThread, cls_PilMessageBox, cls_AboutWindow, cls_HelpWindow, cls_tabprinter, cls_tabterminal, cls_tabdrive, cls_TabConfigWindow, cls_DevStatusWindow, cls_PilConfigWindow, cls_lifinit, cls_liffix, cls_installcheck

#
# Program constants --------------------------------------------------
#
VERSION="1.3.3 (Development)"       # pyILPR version number
CONFIG_VERSION="1"    # Version number of pyILPER config file, must be string
STAT_DISABLED = 0     # Application in cold state:  not running
STAT_ENABLED = 1      # Application in warm state:  running
MODE_PILBOX=0         # connect to PIL-Box
MODE_TCPIP=1          # connect to virtual HP-IL over TCP/IP
USE8BITS= True        # use 8 bit data transfer to PIL-Box
BAUD_9600=0
BAUD_115200=1

BAUDRATES=[ 9600, 115200] # supported baud rates

#
# Main application ------------------------------------------------------ 
#

class cls_pyilper(QtCore.QObject):

   sig_show_message=QtCore.pyqtSignal(str)
   sig_crash=QtCore.pyqtSignal()
   sig_quit=QtCore.pyqtSignal()


   def __init__(self):
 
      super().__init__()
      self.name="pyilper"
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
      self.ui= cls_ui(self,VERSION)
      self.ui.actionConfig.triggered.connect(self.do_pyilperConfig)
      self.ui.actionDevConfig.triggered.connect(self.do_DevConfig)
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
#
      try:
         self.config=cls_pilconfig(CONFIG_VERSION)
         self.config.get(self.name,"active_tab",0)
         self.config.get(self.name,"tabconfig",[1,2,1,1])
         self.config.get(self.name,"tabconfigchanged",False)
         self.config.get(self.name,"tty","/dev/ttyUSB0")
         self.config.get(self.name,"baudrate",BAUD_115200)
         self.config.get(self.name,"idyframe",False)
         self.config.get(self.name,"port",60001)
         self.config.get(self.name,"remotehost","localhost")
         self.config.get(self.name,"remoteport",60000)
         self.config.get(self.name,"mode",MODE_PILBOX)
         self.config.get(self.name,"workdir",os.path.expanduser('~'))
         self.config.get(self.name,"position","")
         self.config.get(self.name,"terminalsize","80x24")
         self.config.get(self.name,"colorscheme","white")
         self.config.get(self.name,"terminalcharsize",15)
         self.config.save()
      except PilConfigError as e:
         reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         QtGui.qApp.quit()
#
#     create tab objects
#
      self.tabconfig=self.config.get(self.name,"tabconfig")
      self.registerTab(cls_tabscope,"Scope")
#     self.registerTab(cls_tabscope,"Scope1")
      for i in range (self.tabconfig[1]):
         devname="Drive"+str(int(i+1))
         self.registerTab(cls_tabdrive,devname)
      for i in range (self.tabconfig[2]):
         devname="Printer"+str(int(i+1))
         self.registerTab(cls_tabprinter,devname)
      if self.tabconfig[3] ==1:
         self.registerTab(cls_tabterminal,"Terminal")
#     self.registerTab(cls_tabscope,"Scope2")
#
#     remove config of non existing tabs
#
      if self.config.get(self.name,"tabconfigchanged"):
         self.config.put(self.name,"tabconfigchanged",False)
         self.config.put(self.name,"active_tab",0)
         names= [self.name]
         for obj in self.tabobjects:
            names.append(obj.name)
         removekeys=[]
         for key in self.config.getkeys():
            prefix=key.split(sep="_")[0]
            if not prefix in names:
               removekeys.append(key)
         for key in removekeys:
            self.config.remove(key)
      else:
#
#     go to last active tab (if tabconfig did not change)
#
         self.ui.tabs.setCurrentIndex(self.config.get(self.name,"active_tab"))
#
#     connect callback for tab change to update only the visible tab
#  
      self.ui.tabs.currentChanged[int].connect(self.tab_current_changed)
#
#  move window to last position
#
      position=self.config.get(self.name,"position")
      if position !="":
         self.ui.move(position)
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
#  start application into warm state
#
   def enable(self):
      if self.status== STAT_ENABLED:
         return
#
#     set working directory
#
      try:
         os.chdir(self.config.get(self.name,'workdir'))
      except OSError as e:
         reply=QtGui.QMessageBox.critical(self.ui,'Error',"Cannot change to working directory: "+e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return
      except TypeError as e:
         reply=QtGui.QMessageBox.critical(self.ui,'Error',"Cannot change to working directory",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return
#
#     connect to HP-IL
#
      if self.config.get(self.name,"mode")== MODE_PILBOX:
#
#        create PIL-Box object, connect to PIL-Box
#
         try:
            self.commobject= cls_pilbox(self.config.get(self.name,'tty'),BAUDRATES[self.config.get(self.name,'baudrate')],self.config.get(self.name,'idyframe'),USE8BITS)
            self.commobject.open()
            self.commthread= cls_PilBoxThread(self.ui,self.commobject)
         except PilBoxError as e:
            reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+": "+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
            return
         except TypeError as e:
            reply=QtGui.QMessageBox.critical(self.ui,'Error',"Cannot connect to PIL-Box: communication error",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
            return
      else:
#
#        create TCP-IP-object, connect to network
#
         try:
            self.commobject= cls_piltcpip(self.config.get(self.name,"port"),self.config.get(self.name,"remotehost"),self.config.get(self.name,"remoteport"))
            self.commobject.open()
            self.commthread= cls_PilTcpIpThread(self.ui,self.commobject)
         except TcpIpError as e:
            self.commobject.close()
            self.commobject=None
            reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
            return
#
#     enable all registered tab objects
#
      for obj in self.tabobjects:
         obj.enable()
#
#     start emulator thread
#
      self.commthread.start()
      self.status= STAT_ENABLED
#
#     trigger visible tab to enable refreshs
#
      tab= self.ui.tabs.widget(self.config.get(self.name,"active_tab"))
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
      oldtab= self.config.get(self.name,"active_tab")
      if oldtab != idx:
         self.ui.tabs.widget(oldtab).becomes_invisible()
         self.ui.tabs.widget(idx).becomes_visible()
         self.config.put(self.name,"active_tab",idx)

#
#  callback pyilper configuration
#
   def do_pyilperConfig(self):
      mode=  self.config.get(self.name,"mode")
      tty= self.config.get(self.name,"tty")
      baudrate= self.config.get(self.name,"baudrate")
      port= self.config.get(self.name,"port")
      idyframe= self.config.get(self.name,"idyframe")
      remotehost= self.config.get(self.name,"remotehost")
      remoteport= self.config.get(self.name,"remoteport")
      workdir=  self.config.get(self.name,"workdir")
      terminalsize= self.config.get(self.name,"terminalsize")
      colorscheme= self.config.get(self.name,"colorscheme")
      terminalcharsize=self.config.get(self.name,"terminalcharsize")
      
      config=cls_PilConfigWindow.getPilConfig(mode,tty,baudrate,idyframe,port,remotehost,remoteport,workdir,terminalsize,colorscheme,terminalcharsize)
      if config is None: 
         return
      self.config.put(self.name,"mode",config[0])
      self.config.put(self.name,"tty",config[1])
      self.config.put(self.name,"baudrate",config[2])
      self.config.put(self.name,"idyframe",config[3])
      self.config.put(self.name,"port",config[4])
      self.config.put(self.name,"remotehost",config[5])
      self.config.put(self.name,"remoteport",config[6])
      self.config.put(self.name,"workdir",config[7])
      self.config.put(self.name,"terminalsize",config[8])
      self.config.put(self.name,"colorscheme",config[9])
      self.config.put(self.name,"terminalcharsize",config[10])
      self.disable()
      try:
         self.config.save()
      except PilConfigError as e:
         reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return
      self.enable()
#
#  callback HP-IL device config
#
   def do_DevConfig(self):
      config=cls_TabConfigWindow.getTabConfig(self.tabconfig)
      if config is None:
         return
      self.config.put(self.name,"tabconfig",config)
      self.config.put(self.name,"tabconfigchanged",True)
      try:
         self.config.save()
      except PilConfigError as e:
         reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return
      reply=QtGui.QMessageBox.information(self.ui,"Restart required","HP-IL Device configuration changed. Restart Application.",QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      
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
      position=self.ui.pos()
      try:
         self.config.put(self.name,"position",position)
         self.config.save()
      except PilConfigError as e:
         reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      QtGui.qApp.quit()
#
#  callback initialize LIF medium
#
   def do_Init(self):
      workdir=  self.config.get(self.name,"workdir")
      cls_lifinit.exec(workdir)

#
#  callback fix LIF Medium
#
   def do_Fix(self):
      workdir=  self.config.get(self.name,"workdir")
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
      dstpath=self.config.get(self.name,"workdir")
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
      self.helpwin.raise_()

def dumpstacks(signal, frame):
  for threadId, stack in sys._current_frames().items():
    print("Thread ID %x" % threadId)
    traceback.print_stack(f=stack)

def main():
   if platform.system() != "Windows":
      signal.signal(signal.SIGQUIT, dumpstacks)
   app = QtGui.QApplication(sys.argv)
   pyilper= cls_pyilper()
   sys.exit(app.exec_())


if __name__ == '__main__':

   main()
