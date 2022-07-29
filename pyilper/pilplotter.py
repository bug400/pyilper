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
# Plotter tab object classes ---------------------------------------------------
#
# Changelog
# 17.10.2016 jsi:
# - initial version
# 23.10.2016 jsi:
# - check required version of emu7470
# - terminate subprocess on ipc input/output error
# 24.10.2016 jsi:
# - show emu7470 version in status window
# 03.11.2016 cg:
# - bugfix in process HP-GL command, stdin flush was missing
# - added workaround for creating a subprocess without console window under Windows
# 04.11.2016 cg:
# - changed pdf filename dialog to AcceptSave and added "pdf" as default suffix
# 01.02.2017 jsi
# - fixed crash in do_finishX, finishY if either of the lineEdits is already empty
# 05.02.2017 jsi
# - update pen configuration before each draw command
# 07.08.2017 jsi
# - papersize is now a global configuration parameter
# 19.08.2017 jsi
# - fixed refactoring bug: plotter HP-IL device was accidently disabled
#   permanently when the disable method was called
# 22.08.2017 jsi
# - disable gui elements if not active
# 24.08.2017 jsi
# - error in logging fixed
# 28.08.2017 jsi
# - remove alignments from GUI
# - get papersize config parameter in constructor of tab widget
# - full responsive design of plotter tab
# 01.09.2017 jsi
# - get open pdf file dialog from cls_pdfprinter
# 03.09.2017 jsi
# - register pildevice is now method of commobject
# - missing classes of pen config window moved from pilwidgets
# 08.09.2017 jsi
# - fixed crash when letter format
# - fixed crash when using user defined pen configurations
# 19.09.2017 jsi
# - fixed call if setInvalid
# 27.09.2017 jsi
# - renamed putOutput to putDataToHPIL
# - code to output data to HP-IL rewritten
# 28.09.2017 jsi
# - block multiple calls of start_digi
# 02.10.2017 jsi
# - fixed crash on cursor restore if digitizing mode was stopped twice
# 30.10.2017 jsi
# - LIFUTILS path handling added
# 28.12.2017 jsi
# - fixed bug in parse utility - needless comma removed
# 04.01.2018 jsi
# - reconfigure log checkbox
# - flush log buffer
# 16.01.2018 jsi
# - adapt to cls_tabgeneric, implemented cascading config menus
# 20.01.2018 jsi
# - removed the external plot view window. Since the plotter tab can be
#   undocked now it is no needed any more
# 29.01.2018 jsi
# - removed external view references
# - clear digitize mode when "IN" received
# - set pushbutton autodefault property to false
# 10.08.2018 jsi
# - cls_PenConfigWindow moved to penconfig.py
# 25.02.2020 jsi
# - cleanup status byte access
# 26.02.2020 jsi
# - cleanup status byte access fix
# 02.03.2021 jsi
# - Enter button is deactivated in digi mode until a point was digitized or 
#   entered (hint by cgh)
# 18.04.2022 jsi
# - assure that the return value of heightForWidth is an integer
# - assure that argument for pen.setWidth is int in update_PenDef
# - improve shutdown of the plotter subprocess
# 04.05.2022 jsi
# - PySide6 migration

import sys
import subprocess
import queue
import threading
import array
from .pilcore import *
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtGui, QtPrintSupport, QtWidgets
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtGui, QtPrintSupport, QtWidgets

from .pilconfig import PilConfigError, PILCONFIG
from .penconfig import PENCONFIG
from .pildevbase import cls_pildevbase
from .pilwidgets import cls_tabgeneric, LogCheckboxWidget, T_STRING
from .pilpdf import cls_pdfprinter
from .lifcore import add_path

#
# constants --------------------------------------------------------------
#
CMD_CLEAR=0
CMD_MOVE_TO=1
CMD_DRAW_TO=2
CMD_PLOT_AT=3
CMD_SET_PEN=4
CMD_OUTPUT=5
CMD_STATUS=6
CMD_ERRMSG=7
CMD_DIGI_START=8
CMD_DIGI_CLEAR=9
CMD_P1P2=10
CMD_EOF=11
CMD_OFF_ERROR=12
CMD_ON_ERROR_YELLOW=13
CMD_ON_ERROR_RED=14
CMD_EMU_VERSION=15
CMD_EXT_ERROR=16
CMD_SET_STATUS=17
CMD_LOG=18

MODE_DIGI=0
MODE_P1=1
MODE_P2=2
MODE_NONE=3

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
#
# plotter widget ----------------------------------------------------------
#
class cls_tabplotter(cls_tabgeneric):

   def __init__(self,parent,name):
      super().__init__(parent,name)
      self.name=name
#
#     this parameter is global
#
      self.papersize=PILCONFIG.get("pyilper","papersize")
#
#     init config parameters
#
      self.loglevel= PILCONFIG.get(self.name,"loglevel",0)
#
#     Create Plotter GUI object
#
      self.guiobject=cls_PlotterWidget(self,self.name,self.papersize)
#
#     add gui object to tab
#
      self.add_guiobject(self.guiobject)
#
#     add cascading config menu
#
      self.add_configwidget()
#
#     add logging control widget
#
      self.add_logging()
#
#     add local config options to cascading config menu
#
      self.cBut.add_option("Log level","loglevel",T_STRING, ["HP-GL","HP-GL+Status","HP-GL+Status+Commands"])
#
#     create IL-Interface object, notify plotter processor object
#
      self.pildevice= cls_pilplotter(self.guiobject,self.papersize)
      self.guiobject.set_pildevice(self.pildevice)
      self.cBut.config_changed_signal.connect(self.do_tabconfig_changed)
#
#  handle changes of tab config options
#
   def do_tabconfig_changed(self):
      self.loglevel= PILCONFIG.get(self.name,"loglevel")
      super().do_tabconfig_changed()
#
#  enable pildevice and gui object
#
   def enable(self):
      super().enable()
      self.parent.commthread.register(self.pildevice,self.name)
      self.pildevice.setactive(self.active)
      self.pildevice.enable()
      self.guiobject.enable()
#
#  disable pildevice and gui object
#
   def disable(self):
      self.pildevice.disable()
      self.guiobject.disable()
      super().disable()
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
#
#  toggle active/inactive
#
   def toggle_active(self):
      super().toggle_active()
      self.guiobject.toggle_active()
      return
#
# Custom class LED widget -------------------------------------------------
#
class cls_LedWidget(QtWidgets.QWidget):

   def __init__(self):
      super().__init__()
      self.ledSize=20
      self.ledColor= QtGui.QColor(0xff,0xff,0xff,0xff)
      self.ledPattern= QtCore.Qt.SolidPattern
      self.setFixedSize(self.ledSize, self.ledSize)

   def paintEvent(self,event):
      p=QtGui.QPainter(self)
      p.setBrush(QtGui.QBrush(self.ledColor,self.ledPattern))
      p.setPen(QtGui.QColor(0x00,0x00,0x00,0xff))
      p.drawEllipse(0,0,self.ledSize-1,self.ledSize-1)

   def setColor(self,color):
      self.ledColor=color
      self.repaint()

   def setSize(self,size):
      self.ledSize=size
      self.setFixedSize(size,size)
      self.repaint()
#
# custom class mark for digitized points --------------------------------------
#

class cls_DigitizedMark(QtWidgets.QGraphicsItem):

    def __init__(self):
        super().__init__()
        self.rect = QtCore.QRectF(0,0, 10, 10)

    def boundingRect(self):
        return self.rect

    def setPos(self,x,y):
       super().setPos(x-5,y-5)

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setWidth(2)
        painter.setPen(pen)
        pen.setColor(QtCore.Qt.blue)
        painter.drawLine(0,0,10,10)
        painter.drawLine(0,10,10,0)

#
# custom class mark for Scaling points ----------------------------------------
#
class cls_P1P2Mark(QtWidgets.QGraphicsTextItem):

    def __init__(self,string):
        super().__init__(string)
        self.font=QtGui.QFont(FONT)
        self.font.setPixelSize(10)

    def setPos(self,x,y):
       super().setPos(x-3,y-5)

    def paint(self, painter, option, widget):
        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setWidth(2)
        pen.setColor(QtCore.Qt.red)
        painter.setPen(pen)
        painter.drawLine(-2,5,8,5)
        painter.drawLine(3,0,3,10)
        super().paint(painter, option, widget)

#
# custom class graphics scene with digitizing capabilities ---------------------
#
class cls_mygraphicsscene(QtWidgets.QGraphicsScene):

   def __init__(self):
      super().__init__()
      self.mark_digi= None
      self.mark_p1=None
      self.mark_p2=None
      self.mark_added= False
      self.mode= MODE_NONE
      return
#
#  start digitizing in mode:
#  MODE_DIGI: mark is an x cross, mark appears after the first click
#  MODE_P1: mark P1, mark appears at the current position of scaling point P1
#  MODE_P2: mark P2, mark appears at the current position of scaling point P2
#
   def digi_mode(self,mode):
      self.mode=mode
      return
#
#  set position of mark, in MODE_DIGI the mark is added to the scene at the first click
#
   def setMark(self,x,y):
      if self.mode== MODE_DIGI:
         if not self.mark_added:
            self.mark_digi= cls_DigitizedMark()
            self.addItem(self.mark_digi)
            self.mark_added= True
         self.mark_digi.setPos(x,y) 
      elif self.mode== MODE_P1:
         self.mark_p1.setPos(x,y) 
      elif self.mode== MODE_P2:
         self.mark_p2.setPos(x,y) 
#
#   add the marks of the scaling points P1 and P2 to the scene and place them at 
#   their original position
#
   def setMarkp1p2(self,x1,y1,x2,y2):
      self.mark_p1= cls_P1P2Mark("P1")
      self.addItem(self.mark_p1)
      self.mark_p1.setPos(x1,y1) 
      self.mark_p2= cls_P1P2Mark("P2")
      self.addItem(self.mark_p2)
      self.mark_p2.setPos(x2,y2) 
#
#  clear digitizing, remove marks from scene
#
   def digi_clear(self):
      if self.mode==MODE_DIGI:
         if self.mark_added:
            self.removeItem(self.mark_digi)
            self.mark_digi=None
            self.mark_added= False
      if self.mode==MODE_P1 or self.mode== MODE_P2:
         self.removeItem(self.mark_p1)
         self.removeItem(self.mark_p2)
         self.mark_p1=None
         self.mark_p2=None
      self.mark_added=False
#
# custom layout class, only valid for one item. Ensures that the
# item keeps its aspect ratio on resize
#
class cls_AspectLayout(QtWidgets.QLayout):
    def __init__(self, aspect_ratio,parent=None):
        super(cls_AspectLayout, self).__init__(parent)
        self.aspect_ratio=aspect_ratio
        self.setSpacing(-1)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(3))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
#       fixed DEPRECATED use of float argument for int parameter
        height = int(width// self.aspect_ratio)
        return height

    def setGeometry(self, rect):
        super(cls_AspectLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        w = rect.width()
        h = rect.height()
        if int(w / self.aspect_ratio) > h:
           item_w= int(h* self.aspect_ratio)
           item_h= h
        else:
           item_w= w
           item_h= int(w / self.aspect_ratio)
        

        for item in self.itemList:
           item.setGeometry(QtCore.QRect(x,y,item_w,item_h))
        return 
#
# custom class graphics view  with digitizing capabilities ---------------------
#
class cls_mygraphicsview(QtWidgets.QGraphicsView):

   def __init__(self,parent,aspect_ratio):
      super().__init__()
      self.parent=parent
      self.aspect_ratio= aspect_ratio
      self.restorecursor=None
      self.digitize=False
#
#  start digitizing, switch to crosshair cursor
#
   def digi_start(self):
      if self.digitize:
         return
      if self.restorecursor is None:
         self.restorecursor=self.viewport().cursor()
         self.viewport().setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
      self.digitize= True
#
#  finish digitizing, restore old cursor
#
   def digi_clear(self):
      if not self.digitize:
         return
      self.viewport().setCursor(self.restorecursor)
      self.restorecursor=None
      self.digitize= False
#
#  Mouse click event, convert coordinates first to scene coordinates and then to
#  plotter coordinates. Store the coordinates (in plotter units) in the coordinate
#  line edit of the GUI.
#
   def mousePressEvent(self, event):
      if self.digitize:
#DEPRECATED
         x=event.pos()
         p=self.mapToScene(x)
         x=p.x()
         y=p.y()
         if x < 0 or x > self.parent.width or y < 0 or y > self.parent.height:
            return
         self.scene().setMark(x,y)
         x=int(round(x/self.parent.factor))
         y=int(round(self.parent.height -y)/self.parent.factor)
         self.parent.setKoord(x,y)

   def resizeEvent(self,event):
      self.fitInView(self.parent.plotscene.sceneRect(),QtCore.Qt.KeepAspectRatio)


#
# Plotter widget class - GUI component of the plotter emulator ------------------
#
# The GUI is driven by:
# User-Input and actions
# Commands from the thread component. The thread components stores commands in the
# GUI command queue (draw graphics, update status and error information switch and clear
# digitize mode).
#
# The GUI component can send commands asynchronly to HP-GL command queue of the
# thread component. These are: initialize, papersize changed, digitized coordinates,
# digitized P1/P2.
#
# The GUI is also responsible for the plotter pen management. In the configuration
# dialogue the HP7470A pens number 1 and 2 can be each assigned to one of 16
# predefined pens in the pyILPER pen configuration file. These predefined pens
# can be configures in the pyILPER main menu.
#
class cls_PlotterWidget(QtWidgets.QWidget):

   def __init__(self,parent,name,papersize):
      super().__init__()
      self.name=name
      self.parent=parent
      self.papersize= papersize
      self.pildevice= None
#
#     get configuration for the virtual plotter
#     1. pen indices
#
      self.pen_number=1
      self.penconfig1=PILCONFIG.get(self.name,"penconfig1",0)
      self.penconfig2=PILCONFIG.get(self.name,"penconfig2",1)
#
#     create pen, do not assign color or width
#
      self.pen=QtGui.QPen()
      self.pen.setCapStyle(QtCore.Qt.RoundCap)
      self.pen.setJoinStyle(QtCore.Qt.RoundJoin)
#
#     get papersize, set width and height of graphics scene according to papersize
#
      self.width= 650
      self.lastx=-1
      self.lasty=-1
      if self.papersize ==0:    # A4
         self.aspect_ratio= 1.425
         self.height= int(self.width/self.aspect_ratio)
      else:                     # US
         self.aspect_ratio= 1.346
         self.height= int(self.width/self.aspect_ratio)
      self.factor=self.height/ 7650
#
#     initialize variables for plotter status information: status, error, error message
#     and the incorrect command
#
      self.error=0
      self.illcmd=""
      self.errmsg=""
      self.status=0
#
#     status window 
#
      self.statuswin= None
#
#     initialize digitize mode and digitzed coordinates (-1 means none)
#
      self.digi_mode= MODE_NONE
      self.digi_x=-1
      self.digi_y=-1
#
#     initial scaling point position
#   
      self.p1x=250
      self.p1y=279
      self.p2x=10250
      self.p2y=7479
#
#     emu7470 version
#
      self.emu_version=0
#
#     create user interface
#
      self.hbox=QtWidgets.QHBoxLayout()
#
#     plot graphics view
#
      self.plotview= cls_mygraphicsview(self,self.aspect_ratio)
      self.plotlayout=cls_AspectLayout(self.aspect_ratio)
      self.plotlayout.addWidget(self.plotview)
     
      self.hbox.addLayout(self.plotlayout,1)
      self.vbox=QtWidgets.QVBoxLayout()
#
#     push buttons "Config" - starts configuration window
#
      self.configButton= QtWidgets.QPushButton("Pens")
      self.configButton.setEnabled(False)
      self.configButton.setAutoDefault(False)
      self.vbox.addWidget(self.configButton)
      self.configButton.clicked.connect(self.do_config)
#
#     push buttons "Enter" - digitize: this button is only enabled in 
#     digitizing mode
#
      self.digiButton= QtWidgets.QPushButton("Enter")
      self.digiButton.setEnabled(False)
      self.digiButton.setAutoDefault(False)
      self.vbox.addWidget(self.digiButton)
      self.digiButton.clicked.connect(self.do_enter)
      self.digibutton_state= self.digiButton.isEnabled()
#
#     push buttons "P1/P2" - show or alter P1/P2
#
      self.p1p2Button= QtWidgets.QPushButton("P1/P2")
      self.p1p2Button.setEnabled(False)
      self.p1p2Button.setAutoDefault(False)
      self.vbox.addWidget(self.p1p2Button)
      self.p1p2Button.clicked.connect(self.do_p1p2)
#
#     push buttons "Clear" - in digitizing mode this clears that mode, otherwise it
#     clears the graphics scene and issues an "IN" command to the plotter emulator
#
      self.clearButton= QtWidgets.QPushButton("Clear")
      self.clearButton.setEnabled(False)
      self.clearButton.setAutoDefault(False)
      self.vbox.addWidget(self.clearButton)
      self.clearButton.clicked.connect(self.do_clear)
#
#     push buttons "Generate PDF"
#
      self.printButton= QtWidgets.QPushButton("PDF")
      self.printButton.setEnabled(False)
      self.printButton.setAutoDefault(False)
      self.vbox.addWidget(self.printButton)
      self.printButton.clicked.connect(self.do_print)
#
#     push buttons "Show Status": shows status window with status and error information
#
      self.statusButton= QtWidgets.QPushButton("Status")
      self.statusButton.setEnabled(False)
      self.statusButton.setAutoDefault(False)
      self.vbox.addWidget(self.statusButton)
      self.statusButton.clicked.connect(self.do_status)
#
#     error LED: yellow: an error had occured, red: the emulator subprocess
#     crashed
#
      self.hbox2=QtWidgets.QHBoxLayout()
      self.led=cls_LedWidget()
      self.hbox2.addWidget(self.led)
      self.led.setSize(15)
      self.label=QtWidgets.QLabel("Error")
      self.hbox2.addWidget(self.label)
      self.hbox2.addStretch(1)
      self.vbox.addLayout(self.hbox2)
#
# line edit of digitized coordinates. They are only enabled in digitizing mode. Digitizing
# can also be performed by entering coordinates manually
#
      if self.papersize==0: 
         self.intvalidatorX=QtGui.QIntValidator(0,10900)
      else:
         self.intvalidatorX=QtGui.QIntValidator(0,10300)

      self.intvalidatorY=QtGui.QIntValidator(0,7650)
      self.hbox3=QtWidgets.QHBoxLayout()
      self.labelX=QtWidgets.QLabel("X")
      self.hbox3.addWidget(self.labelX)
      self.lineEditX= QtWidgets.QLineEdit()
      self.lineEditX.setValidator(self.intvalidatorX)
      self.lineEditX.setText("")
      self.lineEditX.setEnabled(False)
      self.lineEditX.editingFinished.connect(self.do_finishX)
      self.lineEditX.textChanged.connect(self.checkEnableEnter)
      self.hbox3.addWidget(self.lineEditX)
      self.vbox.addLayout(self.hbox3)

      self.hbox4=QtWidgets.QHBoxLayout()
      self.labelY=QtWidgets.QLabel("Y")
      self.hbox4.addWidget(self.labelY)
      self.lineEditY= QtWidgets.QLineEdit()
      self.lineEditY.setValidator(self.intvalidatorY)
      self.lineEditY.setText("")
      self.lineEditY.setEnabled(False)
      self.lineEditY.editingFinished.connect(self.do_finishY)
      self.lineEditY.textChanged.connect(self.checkEnableEnter)
      self.hbox4.addWidget(self.lineEditY)
      self.vbox.addLayout(self.hbox4)

      self.vbox.addStretch(1)
      self.hbox.addLayout(self.vbox)
      self.setLayout(self.hbox)
#
#     configure plotview and scene
#
#     app= QtWidgets.QApplication.instance()
#     scrollbar_width=app.style().pixelMetric(QtWidgets.QStyle.PM_ScrollBarExtent)
      self.plotscene=cls_mygraphicsscene()
      self.plotscene.setSceneRect(0,0,self.width,self.height)
      self.plotview.setScene(self.plotscene)
      self.plotview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
      self.plotview.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
      self.plotview.setSceneRect(self.plotscene.sceneRect())
#     self.plotview.ensureVisible(0,0,self.width,self.height,0,0)
#
#     initialize GUI command queue and lock
#
      self.gui_queue= queue.Queue()
      self.gui_queue_lock= threading.Lock()
#
#     initialize refresh timer
#
      self.UpdateTimer= QtCore.QTimer()
      self.UpdateTimer.setSingleShot(True)
      self.UpdateTimer.timeout.connect(self.process_queue)
#
#     set HP-IL device object
#
   def set_pildevice(self,pildevice):
      self.pildevice=pildevice
#
#     enable: start timer
#
   def enable(self):
      self.UpdateTimer.start(UPDATE_TIMER)
      self.toggle_active()
      return
#
#     disable: reset LED, clear the GUI command queue, stop the timer
#
   def disable(self):
      self.gui_queue_lock.acquire()
      while True:
         try:
            self.gui_queue.get_nowait()
            self.gui_queue.task_done()
         except queue.Empty:
            break
      self.gui_queue_lock.release()
      self.led.setColor(QtGui.QColor(0xff,0xff,0xff,0xff))
      self.UpdateTimer.stop()
      return
#
#     becomes visible, do nothing
#
   def becomes_visible(self):
      pass
#
#     becomes invisible, do nothing
#
   def becomes_invisible(self):
      pass

#     active/inactive: enable/disable GUI controls
#
   def toggle_active(self):
      if self.parent.active:
         self.configButton.setEnabled(True)
         self.digiButton.setEnabled(self.digibutton_state)
         self.p1p2Button.setEnabled(True)
         self.clearButton.setEnabled(True)
         self.printButton.setEnabled(True)
         self.statusButton.setEnabled(True)
      else:
         self.configButton.setEnabled(False)
         self.digibutton_state= self.digiButton.isEnabled()
         self.digiButton.setEnabled(False)
         self.p1p2Button.setEnabled(False)
         self.clearButton.setEnabled(False)
         self.printButton.setEnabled(False)
         self.statusButton.setEnabled(False)
#
#     action: clear button
#     if in digitize mode: leave digitize mode
#     if not in digitize mode: clear plotter view, send "IN" command to plotter, clear LED
#
   def do_clear(self):
      if self.digi_mode != MODE_NONE:
         self.digi_clear()
      else:
         self.plotscene.clear()
         self.led.setColor(QtGui.QColor(0xff,0xff,0xff,0xff))
         self.send_initialize()
         self.p1x=250
         self.p1y=279
         self.p2x=10250
         self.p2y=7479
#
#     action: print pdf file
#
   def do_print(self):
      flist= cls_pdfprinter.get_pdfFilename()
      if flist is None:
         return
      printer = QtPrintSupport.QPrinter (QtPrintSupport.QPrinter.HighResolution)
      if self.papersize==0:
         printer.setPageSize(QT_FORM_A4)
      else:
         printer.setPageSize(QT_FORM_LETTER)

      printer.setPageOrientation(QtGui.QPageLayout.Landscape)
      printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
      printer.setOutputFileName(flist[0])
      p = QtGui.QPainter(printer)
      self.plotscene.render(p)
      p.end()
#
#     action configure plotter, show config window. A modified papersize is sent to
#     to the plotter emulator
#
   def do_config(self):
      if cls_PlotterConfigWindow.getPlotterConfig(self):
         try:
            PILCONFIG.save()
         except PilConfigError as e:
            reply=QtWidgets.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
            return
         self.penconfig1=PILCONFIG.get(self.name,"penconfig1")
         self.penconfig2=PILCONFIG.get(self.name,"penconfig2")
#
#     action: show status window
#
   def do_status(self):
      if self.statuswin is None:
         self.statuswin= cls_statusWindow(self)
      self.statuswin.show()
      self.statuswin.raise_()
#
#     action: check if lineEditX and lineEditY have text so that we
#     can enable the Enter key. The textChanged signal is also emitted
#     if the text was changed programmatically. Thus we also catch a digitized
#     coordinate 
#
   def checkEnableEnter(self):
      if self.lineEditX.text() != "" and self.lineEditY.text()!= "":
         self.digiButton.setEnabled(True)
#
#     action: process digitized point
#
   def do_enter(self):
#
#     get coordinates from GUI line edit. If they are empty then "Enter" was pressed 
#     without digitizing a point
      xs=self.lineEditX.text()
      ys=self.lineEditY.text()
      if xs !="" and ys != "":
         x=int(xs)
         y=int(ys)
#
#        we have x,y in plotter coordinates, if MODE_DIGI send digitized coordinates to
#        plotter emulator and clear digitizing mode
#
         if self.digi_mode== MODE_DIGI:
            self.send_digitize(x,y)
            self.digi_clear()
#
#        we are in MODE_P!: notice the digitized coordinate, clear digitizing mode
#        in both views, set mode to MODE_P2 and restart digitizing 
         elif self.digi_mode== MODE_P1:
            self.p1x=x
            self.p1y=y
            self.plotview.digi_clear()
            self.digi_mode= MODE_P2
            self.plotscene.digi_mode(self.digi_mode)
            self.plotview.digi_start()
            self.lineEditX.setText(str(self.p2x))
            self.lineEditY.setText(str(self.p2y))
#
#        we are in MODE_P2: send digitized coordinates of P1 and P2 to plotter emulator
#        and clear digitizing mode
#
         elif self.digi_mode== MODE_P2:
            self.p2x=x
            self.p2y=y
            self.send_p1p2(self.p1x,self.p1y,self.p2x,self.p2y)
            self.digi_clear()
      else:
         self.digi_clear()
#
#  start digitizing in both views and the scene, enable Enter Button and coordinate
#  line edit, disable P1/P2 button. Called by GUI command queue processing
#
   def digi_start(self):
      if self.digi_mode== MODE_DIGI:
         return
      self.p1p2Button.setEnabled(False)
      self.lineEditX.setEnabled(True)
      self.lineEditY.setEnabled(True)
      self.digi_mode= MODE_DIGI
      self.plotscene.digi_mode(self.digi_mode)
      self.plotview.digi_start()
#
#  stop digitizing in both views and the scene, disable Enter button, enable P1/p2 button
#
   def digi_clear(self):
      self.digiButton.setEnabled(False)
      self.p1p2Button.setEnabled(True)
      self.lineEditX.setText("")
      self.lineEditY.setText("")
      self.lineEditX.setEnabled(False)
      self.lineEditY.setEnabled(False)
      self.digi_mode= MODE_NONE
      self.plotscene.digi_clear()
      self.plotview.digi_clear()
      return
#
#     Action: digitize P1/P2
#
   def do_p1p2(self):
#
#     enable "Enter", disable P1/P2, enable digitizing mode in scene and view,
#     enable coordinate line edit
#
      self.digiButton.setEnabled(True)
      self.p1p2Button.setEnabled(False)
      self.lineEditX.setEnabled(True)
      self.lineEditY.setEnabled(True)
      self.digi_mode= MODE_P1
      self.plotscene.digi_mode(self.digi_mode)
      self.plotview.digi_start()
#
#     set marks according to the original postion of P1, P2
#
      x1=int(round(self.p1x)*self.factor)
      y1=int(round(((self.height/self.factor) -self.p1y)*self.factor))
      x2=int(round(self.p2x)*self.factor)
      y2=int(round(((self.height/self.factor) -self.p2y)*self.factor))
      self.plotscene.setMarkp1p2(x1,y1,x2,y2)
      self.lineEditX.setText(str(self.p1x))
      self.lineEditY.setText(str(self.p1y))
#
#    handle editing finished of coordinate input in line edits. Transform plotter 
#    coordinates to scene coordinates and move mark
#
   def do_finishX(self):
      if self.lineEditX.isModified():
         if(self.lineEditY.text()!=""):
            x=int(self.lineEditX.text())
            y=int(self.lineEditY.text())
            x1=int(round(x)*self.factor)
            y1=int(round(((self.height/self.factor) -y)*self.factor))
            self.plotscene.setMark(x1,y1)
      self.lineEditX.setModified(False)

   def do_finishY(self):
      if self.lineEditY.isModified():
         if(self.lineEditX.text()!=""):
            x=int(self.lineEditX.text())
            y=int(self.lineEditY.text())
            x1=int(round(x)*self.factor)
            y1=int(round(((self.height/self.factor) -y)*self.factor))
            self.plotscene.setMark(x1,y1)
      self.lineEditY.setModified(False)
#
#    put digitized coordinates into the line edits
#
   def setKoord(self,x,y):
      self.lineEditX.setText(str(x))
      self.lineEditY.setText(str(y))
#
#  send digitized coordinates to plotter emulator
#
   def send_digitize(self,x,y):
      self.pildevice.put_cmd("ZY %d %d" % (x,y))
      return
#
#  send initialize command to plotter emulator
#
   def send_initialize(self):
      self.pildevice.put_cmd("IN")
      return
#
# send IP command to plotter emulator
#
   def send_p1p2(self,xp1,yp1,xp2,yp2):
      self.pildevice.put_cmd("IP%d,%d,%d,%d;" % (xp1,yp1,xp2,yp2))
      return
#
#  put command into the GUI-command queue, this is called by the thread component
#
   def put_cmd(self,item):
       self.gui_queue_lock.acquire()
       self.gui_queue.put(item)
       self.gui_queue_lock.release()
#
# update pen definition
#
   def update_PenDef(self):
      pendef = [0xff, 0xff, 0xff, 0x00, 0x01]
      if self.pen_number==0:
         pendef=[0xff,0xff,0xff,0x00,0x01]    
      elif self.pen_number==1:
         pendef= PENCONFIG.get_pen(self.penconfig1)
      elif self.pen_number==2:
         pendef= PENCONFIG.get_pen(self.penconfig2)
      self.pen.setColor(QtGui.QColor(pendef[0],pendef[1],pendef[2],pendef[3]))
#     fixed DEPRECATED use of float argument for int parameter
      self.pen.setWidth(round(pendef[4]))

#
#  process commands in the GUI command queue, this is called by a timer event
#
   def process_queue(self):
       items=[]
       self.gui_queue_lock.acquire()
       while True:
          try:
             i=self.gui_queue.get_nowait()
             items.append(i)
             self.gui_queue.task_done()
          except queue.Empty:
             break
       self.gui_queue_lock.release()
       if len(items):
          for c in items:
             self.process(c)
       self.plotview.update() 
       self.UpdateTimer.start(UPDATE_TIMER)
       return
#
#  GUI command processing
#
   def process(self,item):
      cmd= item[0]
#
#     clear graphhics views (issued by in IN command)
#
      if cmd==  CMD_CLEAR:
         if self.digi_mode != MODE_NONE:
            self.digi_clear()
         self.plotscene.clear()
#
#     end of commands
#
      elif cmd== CMD_EOF:
         pass
#
#     set pen, pen 0 is transparent white. Set color and width of pen 1 and pen 2
#     according to the entries in the pen condiguration
#
      elif cmd== CMD_SET_PEN:
         self.pen_number= item[1]

#
#     move to new location, graphic command generated by plotter emulator
#
      elif cmd== CMD_MOVE_TO:
         self.lastx= item[1] * self.factor
         self.lasty= self.height- (item[2] * self.factor)
#
#     draw to new location, graphic command generated by plotter emulator
#
      elif cmd== CMD_DRAW_TO:
         self.update_PenDef()
         x= item[1] * self.factor
         y= self.height- (item[2] * self.factor)
         self.plotscene.addLine(self.lastx,self.lasty,x,y,pen=self.pen)
         self.lastx=x
         self.lasty=y
#
#     draw dot at location, graphic command generated by plotter emulator
#
      elif cmd== CMD_PLOT_AT:
         self.update_PenDef()
         x= item[1] * self.factor
         y= self.height- (item[2] * self.factor)
         rad=self.pen.width()/2.0
         x1=x-rad
         y1=y-rad
         self.plotscene.addEllipse(x1,y1,2*rad,2*rad,self.pen)
#
#     set LED color to red 
#
      elif cmd== CMD_ON_ERROR_RED:
         self.led.setColor(QtGui.QColor(0xff,0x00,0x00,0xff))
#
#     set LED color to yellow
#
      elif cmd== CMD_ON_ERROR_YELLOW:
         self.led.setColor(QtGui.QColor(0xff,0xff,0x00,0xff))
#
#     set LED color to transparent
#
      elif cmd== CMD_OFF_ERROR:
         self.led.setColor(QtGui.QColor(0xff,0xff,0xff,0xff))
#
#     start digitize mode (issued by a DP command)

      elif cmd== CMD_DIGI_START:
         self.digi_start()
#
#     terminate digitize mode (issued by a DC command)
#
      elif cmd== CMD_DIGI_CLEAR:
         self.digi_clear()
#
#     P1/P2 changed (issued by an IN or IP command)
#
      elif cmd== CMD_P1P2:
         self.p1x=int(item[1])
         self.p1y=int(item[2])
         self.p2x=int(item[3])
         self.p2y=int(item[4])
#
#     Get version of emu7470
#
      elif cmd== CMD_EMU_VERSION:
         self.emu_version=item[1]
#
#     extended Error Message
#
      elif cmd== CMD_EXT_ERROR:
         self.error=item[1]
         self.illcmd=item[2]
         self.errmsg= item[3]
#
#    set status
#
      elif cmd== CMD_SET_STATUS:
         self.status= item[1]
#
#    logging
#
      elif cmd== CMD_LOG:
         if self.parent.loglevel >= item[1]:
            self.parent.cbLogging.logWrite(item[2])
            self.parent.cbLogging.logFlush()
     
#
# status window class --------------------------------------------------------
#
# Display status byte, error code, error message and illegal HP-GL command
# The window may remain open and the content of the window will be updated
#
class cls_statusWindow(QtWidgets.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.parent=parent
      self.setWindowTitle("Plotter error status")
      self.__timer__=QtCore.QTimer()
      self.__timer__.timeout.connect(self.do_refresh)
      
      self.vbox=QtWidgets.QVBoxLayout()
      self.grid=QtWidgets.QGridLayout()
      self.grid.setSpacing(3)
      self.grid.addWidget(QtWidgets.QLabel("emu7470 version:"),1,0)
      self.grid.addWidget(QtWidgets.QLabel("Status:"),2,0)
      self.grid.addWidget(QtWidgets.QLabel("Error code:"),3,0)
      self.grid.addWidget(QtWidgets.QLabel("HP-GL command:"),4,0)
      self.grid.addWidget(QtWidgets.QLabel("Error message:"),5,0)
      self.lblVersion=QtWidgets.QLabel(decode_version(self.parent.emu_version))
      self.lblStatus=QtWidgets.QLabel("")
      self.lblError=QtWidgets.QLabel("")
      self.lblIllCmd=QtWidgets.QLabel("")
      self.lblErrMsg=QtWidgets.QLabel("")
      self.grid.addWidget(self.lblVersion,1,1)
      self.grid.addWidget(self.lblStatus,2,1)
      self.grid.addWidget(self.lblError,3,1)
      self.grid.addWidget(self.lblIllCmd,4,1)
      self.grid.addWidget(self.lblErrMsg,5,1)
      self.vbox.addLayout(self.grid)
      self.vbox.addStretch(1)

      self.hlayout=QtWidgets.QHBoxLayout()
      self.button = QtWidgets.QPushButton('OK')
      self.button.setFixedWidth(60)
      self.button.clicked.connect(self.do_exit)
      self.hlayout.addWidget(self.button)
      self.vbox.addLayout(self.hlayout)
      self.setLayout(self.vbox)
      self.resize(300,180)
      self.do_refresh()

   def hideEvent(self,event):
      self.__timer__.stop()

   def showEvent(self,event):
      self.__timer__.start(500)

   def do_exit(self):
      super().accept()
#
#  timer event function, refresh output
#
   def do_refresh(self):
      self.lblStatus.setText("{0:b}".format(self.parent.parent.pildevice.getPlotterStatus()))
      self.lblError.setText(str(self.parent.error))
      self.lblIllCmd.setText(self.parent.illcmd)
      self.lblErrMsg.setText(self.parent.errmsg)

#
# Plotter configuration window class ------------------------------------------------
#
class cls_PlotterConfigWindow(QtWidgets.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.__name__=parent.name
      self.__penconfig1__= PILCONFIG.get(self.__name__,"penconfig1")
      self.__penconfig2__= PILCONFIG.get(self.__name__,"penconfig2")
      self.setWindowTitle("Plotter configuration")
      self.vbox= QtWidgets.QVBoxLayout()
      self.grid=QtWidgets.QGridLayout()
      self.grid.setSpacing(3)


#
#     Pen1 combo box
#
      self.grid.addWidget(QtWidgets.QLabel("Pen1:"),2,0)
      self.combopen1=QtWidgets.QComboBox()
      for pen_desc in PENCONFIG.get_penlist():
         self.combopen1.addItem(pen_desc)
      self.combopen1.setCurrentIndex(self.__penconfig1__)
      self.grid.addWidget(self.combopen1,2,1)
#
#     Pen2 combo box
#
      self.grid.addWidget(QtWidgets.QLabel("Pen2:"),3,0)
      self.combopen2=QtWidgets.QComboBox()
      for pen_desc in PENCONFIG.get_penlist():
         self.combopen2.addItem(pen_desc)
      self.combopen2.setCurrentIndex(self.__penconfig2__)
      self.grid.addWidget(self.combopen2,3,1)

      self.vbox.addLayout(self.grid)
#
#     OK, Cancel
#
      self.buttonBox = QtWidgets.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.hlayout = QtWidgets.QHBoxLayout()
      self.hlayout.addWidget(self.buttonBox)
      self.vbox.addLayout(self.hlayout)

      self.setLayout(self.vbox)


   def do_ok(self):
      PILCONFIG.put(self.__name__,"penconfig1",self.combopen1.currentIndex())
      PILCONFIG.put(self.__name__,"penconfig2",self.combopen2.currentIndex())
      super().accept()

    
   def do_cancel(self):
      super().reject()


   @staticmethod
   def getPlotterConfig(parent):
      dialog= cls_PlotterConfigWindow(parent)
      result= dialog.exec()
      if result== QtWidgets.QDialog.Accepted:
         return True
      else:
         return False

#
# Plotter emulator (thrad component) -----------------------------------------------
#
# This is the thread component of the plotter emulator.
# The thread part is called from the  __indata__ method. Incoming bytes from the
# HP-IL loop are preparsed until a complete HP-GL statement was received.
# The the commands in the HP-GL commmand queue (asynchronously sent by the GUI) part are
# processed first.
# The HP-GL commands are sent to the em7470 subprocess. The subprocess returns a number
# of commands and data which are prreprocessed by the thread component and put into
# the plotquee buffer. These commands are processed by a timer event of the GUI
# component.
#
class cls_HP7470(QtCore.QObject):

   def __init__(self,parent,guiobject,papersize):
      super().__init__()
      self.parent=parent
      self.guiobject= guiobject
      self.papersize= papersize
      self.cmdbuf=[]
      self.parse_state=0
      self.termchar= chr(3)
      self.proc=None
      self.pendown=False
      self.x=0
      self.y=0
      self.status=0
      self.error=0
      self.errmsg=""
      self.illcmd=""
      self.inparam=False
      self.separator=False
      self.numparam=0
      self.invalid=True
#
#  handle emulator not found or crashed
#
   def setInvalid(self, errno, errmsg):
      self.invalid=True
      self.error=errno
      self.illcmd=""
      self.errmsg=errmsg
      self.guiobject.put_cmd([CMD_EXT_ERROR,self.error,self.illcmd,self.errmsg])
#
#     send to GUI: switch LED to red
#
      self.guiobject.put_cmd([CMD_ON_ERROR_RED])
#
#     disable HP-IL device permanently
#
      self.parent.disable_permanently()
#
#  start the subprocess of the plotter emulator, check required version,
#  set papeersize according to  config 
#
   def enable(self):
#     progpath=os.path.join(os.path.dirname(pyilper.__file__),"emu7470","emu7470")
#     progpath=re.sub("//","/",progpath,1)
      progpath=add_path("emu7470")

      try:
         if isWINDOWS():
            creationflags=0x08000000 # CREATE_NO_WINDOW
         else:
            creationflags=0
         self.proc=subprocess.Popen([progpath], bufsize=1, universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=creationflags)
         line=self.proc.stdout.readline()
      except OSError as e:
         self.setInvalid(100,"emu7470 not found")
         return
#
#     close if version does not match
#
      try:
         version=int(line)
      except ValueError:
         version=0
      if version < EMU7470_VERSION:
         self.proc.stdin.close()
         self.proc.stdout.close()
         self.proc.kill()
         self.proc.wait()
         self.setInvalid(101,"incompatible version of emu7470")
         return
      self.cmdbuf.clear()
      self.guiobject.put_cmd([CMD_EMU_VERSION,line])
      self.parse_state=0
      self.invalid=False
      self.parent.put_cmd("ZZ%d" % self.papersize)
#
#  stop the subprocess of the plotter emulator
#
   def disable(self):
      if not self.invalid:
         self.proc.stdin.close()
         self.proc.stdout.close()
         self.proc.kill()
         self.proc.wait()
#
#  send a HP-GL command to the emu7470 subprocess and process the results:
#  - plotter status, current termchar,
#  - error code and errof message (if any)
#  - output of "O." commands 
#  - clear plotter
#  - geometry generated by emu7470 with the following commands:
#      - select pen (pen number)
#      - move to (coordinate)
#      - draw to (coordinate)
#      - plot at (coordinate)
#
#  since we are not allowed to draw to the graphics window from the thread
#  process all commands that affect the user interface are sent to the GUI
#  command queue.
#
   def process(self,command):
#
#     send HP-GL command to plotter as base16 encoded string, since the string
#     may contain control sequences and we communicate th emu7470 with text i/o.
#
      log_line=""
      try:
#
#     send status
#
         self.proc.stdin.write("%2.2x " % self.status )
#
#     send command
#
         for c in command:
            i=ord(c)
            x="%2.2x" % i
            self.proc.stdin.write(x)
            if i == 0x0A or i== 0x0D:
               log_line+="("+x+")"
            else:
               log_line+=c
         self.proc.stdin.write("\n")
         self.proc.stdin.flush()
         log_line+="\n"
         self.guiobject.put_cmd([CMD_LOG,0,log_line])
      except OSError as e:
         self.proc.stdin.close()
         self.setInvalid(102,"ipc input/output error")
         return
      except AttributeError as e:
         self.proc.stdin.close()
         self.setInvalid(103,"ipc input/output error")
         return
#
#     read processed results from plotter
#
      while True:
         try:
            line=self.proc.stdout.readline()
         except OSError as e:
            self.proc.stdin.close()
            self.setInvalid(104,"ipc input/output error")
            return
         if line =="":
            self.proc.stdin.close()
            self.proc.stdin.close()
            self.setInvalid(104,"ipc input/output error")
            return
         ret=line.split()
         cmd= int(ret[0])
#
#        end of output of a command
#
         if cmd== CMD_EOF: 
            self.guiobject.put_cmd([CMD_EOF])
            self.guiobject.put_cmd([CMD_EXT_ERROR,self.error,self.illcmd,self.errmsg])
            self.guiobject.put_cmd([CMD_SET_STATUS,self.status])
            break
#
#        clear
#
         elif cmd== CMD_CLEAR:
            self.guiobject.put_cmd([CMD_CLEAR])
            self.parent.clear_outbuf()
#
#        set pen 
#
         elif cmd== CMD_SET_PEN:
            self.guiobject.put_cmd([CMD_SET_PEN, int(ret[1])])
            self.guiobject.put_cmd([CMD_LOG,2,"Set Pen %s\n" % ret[1]])
#
#        move
#
         elif cmd== CMD_MOVE_TO:
            self.x= float(ret[1])
            self.y= float(ret[2])
            self.guiobject.put_cmd([CMD_MOVE_TO,self.x,self.y])
            self.guiobject.put_cmd([CMD_LOG,2,"Move To %d %d\n" % (self.x,self.y)])
#
#        draw
#
         elif cmd== CMD_DRAW_TO:
            self.x= float(ret[1])
            self.y= float(ret[2])
            self.guiobject.put_cmd([CMD_DRAW_TO,self.x,self.y])
            self.guiobject.put_cmd([CMD_LOG,2,"Draw To %d %d\n" % (self.x,self.y)])
#
#        draw dot
#
         elif cmd== CMD_PLOT_AT:
            self.x= float(ret[1])
            self.y= float(ret[2])
            self.guiobject.put_cmd([CMD_PLOT_AT, self.x,self.y])
            self.guiobject.put_cmd([CMD_LOG,2,"Plot At %d %d\n" % (self.x,self.y)])
#
#        output from plotter to HP-IL, use the cls_pilplotter putDataToHPIL 
#        method. This puts the data to an output data buffer of pilotter
#
         elif cmd== CMD_OUTPUT:
            result=ret[1]+chr(0x0D)+chr(0x0A)
            self.parent.putDataToHPIL(result)
            self.guiobject.put_cmd([CMD_LOG,1,"Plotter to HP-IL: %s\n" % ret[1]])
#
#        status, error, termchar
#
         elif cmd== CMD_STATUS:
            self.status=int(ret[1])
            self.error=int(ret[2])
            self.termchar= chr(int(ret[3]))
#
#           error bit set?
#
            if self.status & 0x20:
               self.guiobject.put_cmd([CMD_ON_ERROR_YELLOW])
            else:
               self.errmsg=""
               self.illcmd=""
               self.guiobject.put_cmd([CMD_OFF_ERROR])
            self.guiobject.put_cmd([CMD_LOG,1,"Status %x, Error %d\n" % (self.status,self.error)])
#
#        extended error message
#
         elif cmd== CMD_ERRMSG:
            self.errmsg= line[2:-1]
            self.illcmd="".join(self.cmdbuf)
            self.guiobject.put_cmd([CMD_LOG,1,"Error message %s\n" % (self.errmsg)])
#
#        enter digitizing mode, status bit is handled by emu7470
#
         elif cmd== CMD_DIGI_START:
            self.guiobject.put_cmd([CMD_DIGI_START])
#
#        clear digitizing mode, status bit is handled by emu7470
#
         elif cmd== CMD_DIGI_CLEAR:
            self.guiobject.put_cmd([CMD_DIGI_CLEAR])
#
#        P1, P2 set
#
         elif cmd== CMD_P1P2:
            x1= float(ret[1])
            y1= float(ret[2])
            x2= float(ret[3])
            y2= float(ret[4])
            self.guiobject.put_cmd([CMD_P1P2,x1,y1,x2,y2])
         else:
            eprint("Unknown command %s" % ret)
#
#  HP-IL device clear; clear command buffer
#
   def reset(self):
      self.cmdbuf.clear()
      self.parse_state=0
#
#  process_char is called py the cls_pilplotter __indata__ method (registered)
#  process single characters obtained from the interface loop, store
#  complete HPGL-commands in and process them. This ugly parser ensures that
#  emu7470 gets HPGL-Commands with a more strict HPGL-syntax
#
   def process_char(self,c):
      if self.parse_state==0:
#
#        get the first character of command
#
         if c.isalpha():
            self.cmdbuf.append(c.upper())
            self.parse_state=1
      elif self.parse_state==1:
#
#        get the second character of command, skip blanks first
#
         if c == " ":
            return
         if c.isalpha():
            self.cmdbuf.append(c.upper())
            self.parse_state=2
            if self.cmdbuf[0]== "L" and self.cmdbuf[1]=="B":
              self.parse_state=3
            if self.cmdbuf[0]== "D" and self.cmdbuf[1]=="T":
              self.parse_state=4
            if self.cmdbuf[0]== "S" and self.cmdbuf[1]=="M":
              self.parse_state=4
         else:
            self.cmdbuf.clear()
            self.parse_state=0
      elif self.parse_state==2:
#
#        get parameters, remove all blanks, allow , as separator only
#
         if c.isdigit() or c=="." or c=="+" or c=="-":
            if not self.inparam:
               self.inparam= True
               if not self.separator:
                  if self.numparam>0:
                     self.cmdbuf.append(",")
                  self.numparam+=1
            self.cmdbuf.append(c)
            return
         if c == " " :
            self.inparam= False
#           self.separator=False
            return
         if c ==",":
            self.separator=True
            self.inparam= False
            self.cmdbuf.append(c)
            return
         self.inparam= False
         self.numparam=0
         self.separator=False
         self.parent.put_cmd("".join(self.cmdbuf))
         if c.isalpha():
            self.cmdbuf.clear()
            self.cmdbuf.append(c)
            self.parse_state=1
         else:
            self.cmdbuf.clear()
            self.parse_state=0
      elif self.parse_state==3:
#
#        process label string
#
         if c == self.termchar:
            self.cmdbuf.append(self.termchar)
            self.parent.put_cmd("".join(self.cmdbuf))
            self.cmdbuf.clear()
            self.parse_state=0
         else:
            self.cmdbuf.append(c)
      elif self.parse_state==4:
#
#        process single character of DT or SM command
#
         self.cmdbuf.append(c)
         self.parent.put_cmd("".join(self.cmdbuf))
         self.cmdbuf.clear()
         self.parse_state=0
#
# HP-IL plotter class ---------------------------------------------------------
#

class cls_pilplotter(cls_pildevbase):

   def __init__(self,guiobject,papersize):
      super().__init__()
      self.__guiobject__= guiobject
      self.__papersize__= papersize
#
#     overloaded variable initialization
#
      self.__aid__ = 0x60         # accessory id 
      self.__defaddr__ = 5        # default address alter AAU
      self.__did__ = "HP7470A"    # device id
#
#     object specific variables
#
      self.__disabled__=False     # flag to disable device permanently
#
#     initialize remote command queue and lock
#
      self.__plot_queue__= queue.Queue()
      self.__plot_queue_lock__= threading.Lock()
#
#     plotter processor
#
      self.__plotter__=cls_HP7470(self,self.__guiobject__,self.__papersize__)
#
#     initialize HP-IL outdata buffer
#
      self.__outbuf__= array.array('i')
      self.__oc__=0
#
# public (overloaded) --------
#
#  enable: reset
#
   def enable(self):
      self.__plotter__.enable()
      return
#
#  disable: clear the remote HP-GL command queue
#
   def disable(self):
      self.__plot_queue_lock__.acquire()
      while True:
         try:
            self.__plot_queue__.get_nowait()
            self.__plot_queue__.task_done()
         except queue.Empty:
            break
      self.__plot_queue_lock__.release()
      self.__plotter__.disable()
      self.clear_outbuf()
#
#  clear output buffer
#
   def clear_outbuf(self):
      self.__status_lock__.acquire()
      self.__oc__=0
      self.__outbuf__= array.array('i')
      self.__status__= self.__status__ & 0xEF # clear ready for data
      self.__status_lock__.release()

#
#  process frames 
#
   def process(self,frame):

      if self.__isactive__:
         self.process_plot_queue()
      frame= super().process(frame)
      return frame
#
#  process the remote HPGL command queue
#
   def process_plot_queue(self):
       items=[]
       self.__plot_queue_lock__.acquire()
       while True:
          try:
             i=self.__plot_queue__.get_nowait()
             items.append(i)
             self.__plot_queue__.task_done()
          except queue.Empty:
             break
       self.__plot_queue_lock__.release()
       if len(items):
          for c in items:
             self.__plotter__.process(c)
       return
#
#  put remote HP-GL command into the plot-command queue
#
   def put_cmd(self,item):
       self.__plot_queue_lock__.acquire()
       self.__plot_queue__.put(item)
       self.__plot_queue_lock__.release()
#
# public --------
#
#  put data to the HP-IL outdata buffer, called by the plotter processor
#
   def putDataToHPIL(self,s):
      self.__status_lock__.acquire()
      self.__oc__=0
      for c in s:
         self.__outbuf__.insert(0,ord(c))
         self.__oc__+=1
      self.__status__ = self.__status__ | 0x10 # set ready for data bit
      self.__status_lock__.release()

#
#  disable permanently, if emu7470 is not available
#
   def disable_permanently(self):
      self.__disabled__= True
      self.setactive(False)
#
#  get status
#
   def getPlotterStatus(self):
      return(self.__getstatus__())
#
# public (overloaded)
#
   def setactive(self,active):
      if not self.__disabled__:
         super().setactive(active)
      else:
         super().setactive(False)

#
# private (overloaded) --------
#
#
#  forward data coming from HP-IL to the plotter processor
#
   def __indata__(self,frame):

      self.__access_lock__.acquire()
      locked= self.__islocked__
      self.__access_lock__.release()
      if not locked:
         self.__plotter__.process_char(chr(frame & 0xFF))
#
#  clear device: empty HP-IL outdata buffer and reset plotter
#
   def __clear_device__(self):
      super().__clear_device__()
      self.clear_outbuf()
#
#     clear plotter queue
#
      self.__plot_queue_lock__.acquire()
      while True:
         try:
            self.__plot_queue__.get_nowait()
            self.__plot_queue__.task_done()
         except queue.Empty:
            break
      self.__plot_queue_lock__.release()
#
#     reset device 
#
      self.__plotter__.reset()
      return
#
#  send data from HP-IL outdata buffer to the loop
#
   def __outdata__(self,frame):
      self.__status_lock__.acquire()
      if self.__oc__== 0:
         frame= 0x540 # EOT
      else:
         frame= self.__outbuf__.pop()
         self.__oc__-=1
         if self.__oc__== 0:
            self.__status__= self.__status__ & 0xEF # clear ready for data bit
      self.__status_lock__.release()
      return(frame)
