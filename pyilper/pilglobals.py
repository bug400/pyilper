#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pilconfig for pyILPER
#
# (c) 2026 Joachim Siebold
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
# pilglobals class -------------------------------------------
#
# Changelog
# 16.03.2026 jsi
# - initial version
# 21.03.2026 jsi
# - autoreconnect for no network devices
# - pluggable interfaces and tabs
# 24.03.2026 jsi
# - make autoreconnect configurable
# 28.03.2026 jsi
# - added standard configuration directory name parameter StandardConfigDir
# 31.03.2026 jsi
# - Diagnostics variable added (argument)
# 05.04.2026 jsi
# - Version and production status now defined in __init__.py
# - renamed Config_Version to ConfigVersion
# 18.04.2026 jsi
# - added SerialDevicePlugDelay
# - pySerial version check
# - pyQt5 and PySide6 version check
# 19.04.2026 jsi
# - checkVersion fix
# 25.04.26 jsi
# - parameter "nohelp renamed to useSystemBrowser"
#
import os
import platform
import sys

from pyilper import __version__ , __isProduction__

def checkVersion(package,version,requiredMajor,requiredMinor):
   splitVersion=version.split(".")
   major=int(splitVersion[0])
   minor=int(splitVersion[1])
   if major >= requiredMajor:
      if minor >= requiredMinor:
         return
   print(f"{package} {requiredMajor}.{requiredMinor} required. Found {version}. Cannot start pyILPER")
   sys.exit(1)


class cls_pilglobals:
#
#  initialize: create instance
#
   def __init__(self):
      self.Production=__isProduction__  # Production/Development Version
      self.FullVersion=__version__      # pyILPER full package version
      self.ConfigVersion="2"            # Version number of pyILPER config file, must be string
      self.Instance=""                  # Python config instance
      self.Clean=False                  # Start with clean config
      self.Diagnostics=False            # do not output diagnostic messages
#
#     Base version number
#
      temp=self.FullVersion.split(".")
      self.Version= temp[0]+"."+temp[1]+"."+temp[2]
#
#     Python minimum version
#
      self.PythonRequiredMajor=3
      self.PythonRequiredMinor=7
#
#     pySerial minimum version
#
      self.PyserialRequiredMajor=3
      self.PyserialRequiredMinor=2
#
#     pyQt5 minimum version
#
      self.Pyqt5RequiredMajor=5
      self.Pyqt5RequiredMinor=15
#
#     PySide6 minimum version
#
      self.PysideRequiredMajor=6
      self.PysideRequiredMinor=3
#
#     Thread crash reasons
#
      self.Crash_Reason_Unknown=0
      self.Crash_Reason_No_Device=1
#
#     Interface ids, default is Pil-Box (id=0)
#
      self.Interface_Pilbox=0
      self.Interface_Tcpip=1
      self.Interface_Socket=2
#
#     Interface hardware classes
#
      self.Interface_HW_Class_Serial=0
      self.Interface_HW_Class_Network=1
      self.Interface_HW_Class_Usb=2
#
#     Interface Modules
#
      self.InterfaceModules= ["pilbox","piltcpip","pilsocket"]
      self.ModeDefault=self.Interface_Pilbox
      self.AutoreconnectInterval= 1000 # reconnect timer interval
#
#     Device check return values
#
      self.CheckDeviceUnconfigured=0
      self.CheckDeviceExists=1
      self.CheckDeviceNonexistent=2
#
#     Time delay for an USB serial device to become ready or to disappear from the system
#
      self.SerialDevicePlugDelay=1
#
#     PIL-Box communication
#
      self.Tmout_Cmd=1            # time out for PIL-Box commands
      self.Tmout_Frm=0.05         # time out for HP-IL frames
#
#     predefined baudrates
#     the list controlles the baudrates that are supported by the application:
#     - the first list element sets the text in the combobox
#     - the second list element is the baud rate, a value of 0 means auto baud detection
#     the baudrates must be defined in ascending order
      self.Baudrates= [ ["Auto", 0], ["9600", 9600 ] , [ "115200", 115200 ], ["230400", 230400]]

#
#     TCP/IP communication
#
      self.Com_Tmout_Read=0.1      # time out for read
      self.Com_Tmout_Ack=1
      self.Com_Tmout_Write=1

#
#     Tab ids
#
      self.Tab_Scope=0
      self.Tab_Printer=1
      self.Tab_Drive=2
      self.Tab_Terminal=3
      self.Tab_Plotter=4
      self.Tab_HP82162A=5
      self.Tab_HP2225B=6
      self.Tab_Rawdrive=7
#
#     self.Tab_Names={self.Tab_Scope:'Scope',self.Tab_Printer:'Generic Printer',self.Tab_Drive:'Drive',self.Tab_Terminal:'Terminal',self.Tab_Plotter:'HP7470A',self.Tab_HP82162A:'HP82162A', self.Tab_HP2225B: 'HP2225B', self.Tab_Rawdrive: 'Raw Drive'}
#
#     Tab modules
#
      self.TabModules=["pilscope","pilprinter","pilterminal","pildrive","pilplotter","pilhp82162a","pilhp2225b"]

# 
#     Drive tab - directory listing
# 
      self.Refresh_Rate=1000     # period to check whether a drive was altered and is idle
      self.Not_Talker_Span=3     # time (s) a drive must be inactive to be concidered as idle

#
#     Drive tab - predefined xroms
#
      self.Application_Xroms=[["Advantage","advantage"],["Aviation","aviation"],["CopyConfigD","ccd"],["Circuit Analysis","circuit"],["Clinical Lab","clinical"],["Data Acquisition","dataacq"],["Financial Decisions","finance"],["Home Management","homemgmt"],["Machine Design","machine"],["Math","math"],["MELROM","melrom"],["Navigation","navigation"],["Petroleum","petroleum"],["PPC","ppc"],["Real Estate","realestate"],["Standard Pac","standard"],["Statistics","statistics"],["Stress Analysis","stress"],["Structural Analysis","struct"],["Surveying","surveying"],["Thermal Science","thermal"]]

      self.Device_Xroms=[["Card Reader","cardrdr"],["HP-IL Development","devil"],["HEPAX","hepax"],["HP-IL","hpil"],["Plotter","plotter"],["Printer","Thermal Printer","printer"],["Time Module (Cx)","timecx"],["Time Module","time"],["Wand","wand"],["X-Functions (CX)","xfncx"],["X-Functions","xfn"],["Extended I/O","xio"]]

      self.ALLDEVICE_XROM=["All HP Devices","hpdevices"]
#
#     Terminal tab
#
      self.Update_Timer=25                 # Poll timer (ms) for terminal output queue
      self.Cursor_Blink=500                # 500 ms cursor blink rate
      self.Cursor_Blink_INTERVAL= self.Cursor_Blink / self.Update_Timer
      self.Autoscroll_Rate=100             # 500 ms cursor blink rate
      self.Terminal_Minimum_Rows=24        # can't get beyond that
      self.Keyboard_Delay=500              # autorepeat delay to prevent too fast kbd input
#
#     Plotter tab, required version of emu7470
#
      self.EMU7470_Version=900
#
#     Thermal printer tab
#
      self.HP82162A_Linebuffersize=2000
#
#     PDF Constants in 1/10 mm
#
      self.PDF_Margin=100
      self.PDF_Format_A4=0
      self.PDF_Format_Letter=1
      self.PDF_Orientation_Portrait=0
      self.PDF_Orientation_Landscape=1
#
#     Barcode Constants in 1/10 mm
#
      self.Barcode_Height=100
      self.Barcode_Narrow_W= 5
      self.Barcode_Wide_W= 10
      self.Barcode_Spacing= 5
#
#     OS types
#
      self.isLinux=platform.system()=="Linux"
      self.isWindows=platform.system()=="Windows"
      self.isMacos=platform.system()=="Darwin"
# 
#     Standard Font
#     Note: It would be more elegant to use "Andale Mono" on Macos and "Consolas" on
#     Windows. "Consolas" is not available on XP and older Windows versions.
# 
      if self.isLinux:
         self.Font="Monospace"
      else:
         self.Font="Courier New"
#
#     Standard configuration directory
#
      if self.isWindows:
         self.StandardConfigDir="pyilper_config"
      else:
         self.StandardConfigDir="pyilper"
#
#     Check Python interpreter version
#
      self.PythonVersion=str(sys.version_info.major)+"."+str(sys.version_info.minor)+"."+str(sys.version_info.micro)
      checkVersion("Python",self.PythonVersion,self.PythonRequiredMajor,self.PythonRequiredMinor)
#
#     Check PyQt5, PySide6 availability and version
#
      self.QT_Bindings="None"
      self.Has_Webengine=False
      self.Has_Webkit=False
      # already loaded
      for _b in('PyQt5','PySide6'):
         if _b+'.QtCore' in sys.modules:
            self.QT_Bindings=_b
            break
      else:
         try:
            if "PYILPER_FORCE_QT5" in os.environ:
               import xyz
            import PySide6.QtCore
            self.QtVersion=PySide6.QtCore.__version__
            checkVersion("PySide6",self.QtVersion,self.PysideRequiredMajor,self.PysideRequiredMinor)
         except ImportError:
            if "PySide6" in sys.modules:
               del sys.modules["Pyside6"]
            try:
               import PyQt5.QtCore
               self.QtVersion=PyQt5.QtCore.QT_VERSION_STR
               checkVersion("pyQt5",self.QtVersion,self.Pyqt5RequiredMajor,self.Pyqt5RequiredMinor)
            except ImportError:
               if "PyQt5" in sys.modules:
                  del sys.modules["PyQt5"]
               print("No Qt bindings found, exit program")
               sys.exit(1)
            else:
               self.QT_Bindings="PyQt5"
               from PyQt5 import QtPrintSupport
               self.QT_Form_A4=QtPrintSupport.QPrinter.A4
               self.QT_Form_Letter=QtPrintSupport.QPrinter.Letter
               try:
                  from PyQt5 import QtWebKitWidgets
                  self.Has_Webkit=True
               except:
                  pass
               try:
                  from PyQt5 import QtWebEngineWidgets
                  self.Has_Webengine=True
               except:
                  pass
               if self.Has_Webkit and self.Has_Webengine:
                 self.Has_Webengine=False
         else:
            self.QT_Bindings="PySide6"
            from PySide6 import QtGui
            self.QT_Form_A4=QtGui.QPageSize.A4
            self.QT_Form_Letter=QtGui.QPageSize.Letter
            try:
               from PySide6 import QtWebEngineWidgets
               self.Has_Webengine=True
            except:
               pass

#
#     check pySerial
#
      try:
         from serial import __version__ as serial__version__
      except ImportError:
         print("No pySerial module found, exit program")
         sys.exit(1)
      self.PyserialVersion= serial__version__
      checkVersion("pySerial",self.PyserialVersion,self.PyserialRequiredMajor,self.PyserialRequiredMinor)
#
#     If Development Version append string to Version and "d" to config file name
#
      if not self.Production:
         self.Version=self.Version+" (Development)"
      return
#
#     add command line args
#
   def setArgs(self,args):
      if args.instance.isalnum():
         self.Instance=args.instance
      self.Clean=args.clean
      if args.useSystemBrowser:
         self.Has_Webkit=False
         self.Has_Webengine=False  
      self.Diagnostics=args.diag

#
#  set/clear 8bit PILBox format
#
   def set8Bits(self,flag):
      self.Use_8Bits= flag
      return

#
#  create instance
#
PILGLOBALS=  cls_pilglobals()
