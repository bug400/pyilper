#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pyILPER 1.341 for Linux
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
# plotter tab classes   ----------------------------------------------------
#
# Changelog
# 17.10.2016 jsi:
# - initial version


from __future__ import print_function
import os
import re
import sys
import subprocess
import time
import sys
import queue
import base64
import threading
import pyilper
from PyQt4 import QtCore, QtGui
from .pilcore import UPDATE_TIMER, FONT
from .pilconfig import PilConfigError, PILCONFIG
from .penconfig import PenConfigError, PENCONFIG


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

MODE_DIGI=0
MODE_P1=1
MODE_P2=2
MODE_NONE=3

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

#
# Custom class LED widget -------------------------------------------------
#
class cls_LedWidget(QtGui.QWidget):

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
# custom class mark for digitized points -------------------------------------------
#

class cls_DigitizedMark(QtGui.QGraphicsItem):

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
# custom class mark for Scaling points --------------------------------------------
#
class cls_P1P2Mark(QtGui.QGraphicsTextItem):

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
# custom class graphics scene with digitizing capabilities ----------------------------
#
class cls_mygraphicsscene(QtGui.QGraphicsScene):

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
# custom class graphics view  with digitizing capabilities ----------------------------
#
class cls_mygraphicsview(QtGui.QGraphicsView):

   def __init__(self,parent):
      super().__init__()
      self.restorecursor=None
      self.digitize=False
      self.parent=parent
#
#  start digitizing, switch to crosshair cursor
#
   def digi_start(self):
      self.restorecursor=self.viewport().cursor()
      self.viewport().setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
      self.digitize= True
#
#  finish digitizing, restore old cursor
#
   def digi_clear(self):
      self.viewport().setCursor(self.restorecursor)
      self.digitize= False
#
#  Mouse click event, convert coordinates first to scene coordinates and then to
#  plotter coordinates. Store the coordinates (in plotter units) in the coordinate
#  line edit of the GUI.
#
   def mousePressEvent(self, event):
      if self.digitize:
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

#
# Plotter widget class - GUI component of the plotter emulator ---------------------------
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
class cls_PlotterWidget(QtGui.QWidget):

   def __init__(self,parent,name):
      super().__init__()
      self.name=name
      self.parent=parent
#
#     get configuration for the virtual plotter
#     1. pen indices
#
      self.penconfig1=PILCONFIG.get(self.name,"penconfig1",0)
      self.penconfig2=PILCONFIG.get(self.name,"penconfig2",1)
#
#     create pen, do not assign color or width
      self.pen=QtGui.QPen()
      self.pen.setCapStyle(QtCore.Qt.RoundCap)
      self.pen.setJoinStyle(QtCore.Qt.RoundJoin)
#
#     get papersize, set width and height of graphics scene according to papersize
#
      self.papersize=PILCONFIG.get(self.name,"papersize",0)
      self.width= 650
      self.lastx=-1
      self.lasty=-1
      if self.papersize ==0:    # A4
         self.height= int(self.width/1.425)
      else:                     # US
         self.height= int(self.width/1.346)
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
#     status window and external view window
#
      self.viewwin= None
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
#     create user interface
#
      self.hbox=QtGui.QHBoxLayout()
#
#     plot graphics view
#
      self.plotview= cls_mygraphicsview(self)
      self.hbox.addWidget(self.plotview)
      self.hbox.setAlignment(self.plotview,QtCore.Qt.AlignLeft)
      self.vbox=QtGui.QVBoxLayout()
#
#     push buttons "Config" - starts configuration window
#
      self.configButton= QtGui.QPushButton("Config")
      self.vbox.addWidget(self.configButton)
      self.vbox.setAlignment(self.configButton,QtCore.Qt.AlignTop)
      self.configButton.clicked.connect(self.do_config)
#
#     push buttons "View" - opens external view window
#
      self.viewButton= QtGui.QPushButton("View")
      self.vbox.addWidget(self.viewButton)
      self.vbox.setAlignment(self.viewButton,QtCore.Qt.AlignTop)
      self.viewButton.clicked.connect(self.do_view)
#
#     push buttons "Enter" - digitize: this button is only enabled in digitizing mode
#
      self.digiButton= QtGui.QPushButton("Enter")
      self.vbox.addWidget(self.digiButton)
      self.vbox.setAlignment(self.digiButton,QtCore.Qt.AlignTop)
      self.digiButton.clicked.connect(self.do_enter)
      self.digiButton.setEnabled(False)
#
#     push buttons "P1/p2" - show or alter P1/P2
#
      self.p1p2Button= QtGui.QPushButton("P1/P2")
      self.vbox.addWidget(self.p1p2Button)
      self.vbox.setAlignment(self.p1p2Button,QtCore.Qt.AlignTop)
      self.p1p2Button.clicked.connect(self.do_p1p2)
#
#     push buttons "Clear" - in digitizing mode this clears that mode, otherwise it
#     clears the graphics scene and issues an "IN" command to the plotter emulator
#
      self.clearButton= QtGui.QPushButton("Clear")
      self.vbox.addWidget(self.clearButton)
      self.vbox.setAlignment(self.clearButton,QtCore.Qt.AlignTop)
      self.clearButton.clicked.connect(self.do_clear)
#
#     push buttons "Generate PDF"
#
      self.printButton= QtGui.QPushButton("PDF")
      self.vbox.addWidget(self.printButton)
      self.vbox.setAlignment(self.printButton,QtCore.Qt.AlignTop)
      self.printButton.clicked.connect(self.do_print)
#
#     push buttons "Show Status": shows status window with status and error information
#
      self.statusButton= QtGui.QPushButton("Status")
      self.vbox.addWidget(self.statusButton)
      self.vbox.setAlignment(self.statusButton,QtCore.Qt.AlignTop)
      self.statusButton.clicked.connect(self.do_status)
#
#     error LED: yellow: an error had occured, red: the emulator subprocess
#     crashed
#
      self.hbox2=QtGui.QHBoxLayout()
      self.led=cls_LedWidget()
      self.hbox2.addWidget(self.led)
      self.hbox2.setAlignment(self.led,QtCore.Qt.AlignLeft)
      self.led.setSize(15)
      self.label=QtGui.QLabel("Error")
      self.hbox2.addWidget(self.label)
      self.hbox2.setAlignment(self.label,QtCore.Qt.AlignLeft)
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
      self.hbox3=QtGui.QHBoxLayout()
      self.labelX=QtGui.QLabel("X")
      self.hbox3.addWidget(self.labelX)
      self.hbox3.setAlignment(self.labelX,QtCore.Qt.AlignLeft)
      self.lineEditX= QtGui.QLineEdit()
      self.lineEditX.setValidator(self.intvalidatorX)
      self.lineEditX.setText("")
      self.lineEditX.setEnabled(False)
      self.lineEditX.editingFinished.connect(self.do_finishX)
      self.hbox3.addWidget(self.lineEditX)
      self.hbox3.setAlignment(self.lineEditX,QtCore.Qt.AlignLeft)
      self.vbox.addLayout(self.hbox3)

      self.hbox4=QtGui.QHBoxLayout()
      self.labelY=QtGui.QLabel("Y")
      self.hbox4.addWidget(self.labelY)
      self.hbox4.setAlignment(self.labelY,QtCore.Qt.AlignLeft)
      self.lineEditY= QtGui.QLineEdit()
      self.lineEditY.setValidator(self.intvalidatorY)
      self.lineEditY.setText("")
      self.lineEditY.setEnabled(False)
      self.lineEditY.editingFinished.connect(self.do_finishY)
      self.hbox4.addWidget(self.lineEditY)
      self.hbox4.setAlignment(self.lineEditY,QtCore.Qt.AlignLeft)
      self.vbox.addLayout(self.hbox4)

      self.vbox.addStretch(1)
      self.hbox.addLayout(self.vbox)
#
#     configure plotview and scene
#
      app= QtGui.QApplication.instance()
      scrollbar_width=app.style().pixelMetric(QtGui.QStyle.PM_ScrollBarExtent)
      self.plotview.setFixedWidth(self.width+scrollbar_width)
      self.plotview.setFixedHeight(self.height+scrollbar_width)
      self.setLayout(self.hbox)
      self.plotscene=cls_mygraphicsscene()
      self.plotscene.setSceneRect(0,0,self.width,self.height)
      self.plotview.setScene(self.plotscene)
      self.plotview.setSceneRect(self.plotscene.sceneRect())
      self.plotview.ensureVisible(0,0,self.width,self.height,0,0)
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
#     enable: start timer
#
   def enable(self):
      self.UpdateTimer.start(UPDATE_TIMER)
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
         self.parent.plotter.send_initialize()
         self.p1x=250
         self.p1y=279
         self.p2x=10250
         self.p2y=7479
#
#     action: show external view window, restore size and position
#
   def do_view(self):
      viewposition=PILCONFIG.get(self.name,"viewposition",[10,10,self.width,self.height])
      if self.viewwin== None:
         self.viewwin= cls_plotViewWindow(self)
      if self.digi_mode != MODE_NONE:
         self.viewwin.plotview.digi_start()
      self.viewwin.show()
      self.viewwin.move(QtCore.QPoint(viewposition[0],viewposition[1]))
      self.viewwin.resize(viewposition[2],viewposition[3])
      self.viewwin.raise_()
#
#     file name input dialogue for pdf print file
#
   def get_pdfFilename(self):
      dialog=QtGui.QFileDialog()
      dialog.setWindowTitle("Enter PDF file name")
      dialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtGui.QFileDialog.AnyFile)
      dialog.setNameFilters( ["PDF (*.pdf )", "All Files (*)"] )
      dialog.setOptions(QtGui.QFileDialog.DontUseNativeDialog)
      if dialog.exec():
         return dialog.selectedFiles()
#
#     action: print pdf file
#
   def do_print(self):
      flist= self.get_pdfFilename()
      if flist==None:
         return
      printer = QtGui.QPrinter (QtGui.QPrinter.HighResolution)
      if self.papersize==0:
         printer.setPageSize(QtGui.QPrinter.A4)
      else:
         printer.setPageSize(QtGui.QPrinter.Letter)

      printer.setOrientation(QtGui.QPrinter.Portrait)
      printer.setOutputFormat(QtGui.QPrinter.PdfFormat)
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
            reply=QtGui.QMessageBox.critical(self.ui,'Error',e.msg+': '+e.add_msg,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
            return
         self.penconfig1=PILCONFIG.get(self.name,"penconfig1")
         self.penconfig2=PILCONFIG.get(self.name,"penconfig2")
         self.papersize=PILCONFIG.get(self.name,"papersize")
         self.parent.plotter.send_papersize(self.papersize)
#
#     action: show status window
#
   def do_status(self):
      if self.statuswin== None:
         self.statuswin= cls_statusWindow(self)
      self.statuswin.show()
      self.statuswin.raise_()
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
            self.parent.plotter.send_digitize(x,y)
            self.digi_clear()
#
#        wen are in MODE_P!: notice the digitized coordinate, clear digitizing mode
#        in both views, set mode to MODE_P2 and restart digitizing 
         elif self.digi_mode== MODE_P1:
            self.p1x=x
            self.p1y=y
            self.plotview.digi_clear()
            if self.viewwin != None:
               self.viewwin.plotview.digi_clear()
            self.digi_mode= MODE_P2
            self.plotscene.digi_mode(self.digi_mode)
            self.plotview.digi_start()
            if self.viewwin != None:
               self.viewwin.plotview.digi_start()
            self.lineEditX.setText(str(self.p2x))
            self.lineEditY.setText(str(self.p2y))
#
#        we are in MODE_P2: send digitized coordinates of P1 and P2 to plotter emulator
#        and clear digitizing mode
#
         elif self.digi_mode== MODE_P2:
            self.p2x=x
            self.p2y=y
            self.parent.plotter.send_p1p2(self.p1x,self.p1y,self.p2x,self.p2y)
            self.digi_clear()
      else:
         self.digi_clear()
#
#  start digitizing in both views and the scene, enable Enter Button and coordinate
#  line edit, disable P1/P2 button. Called by GUI command queue processing
#
   def digi_start(self):
      self.digiButton.setEnabled(True)
      self.p1p2Button.setEnabled(False)
      self.lineEditX.setEnabled(True)
      self.lineEditY.setEnabled(True)
      self.digi_mode= MODE_DIGI
      self.plotscene.digi_mode(self.digi_mode)
      self.plotview.digi_start()
      if self.viewwin != None:
         self.viewwin.plotview.digi_start()
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
      if self.viewwin != None:
         self.viewwin.plotview.digi_clear()
      return
#
#     Action: digitize P1/P2
#
   def do_p1p2(self):
#
#     enable "Enter", disable P1/P2, enable digitizing mode in scene and both views,
#     enable coordinate line edit
#
      self.digiButton.setEnabled(True)
      self.p1p2Button.setEnabled(False)
      self.lineEditX.setEnabled(True)
      self.lineEditY.setEnabled(True)
      self.digi_mode= MODE_P1
      self.plotscene.digi_mode(self.digi_mode)
      self.plotview.digi_start()
      if self.viewwin != None:
         self.viewwin.plotview.digi_start()
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
         x=int(self.lineEditX.text())
         y=int(self.lineEditY.text())
         x1=int(round(x)*self.factor)
         y1=int(round(((self.height/self.factor) -y)*self.factor))
         self.plotscene.setMark(x1,y1)
      self.lineEditX.setModified(False)

   def do_finishY(self):
      if self.lineEditY.isModified():
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
#    set error information. Called by GUI command queue processing.
#
   def setError(self,error,illcmd,errmsg):
      self.error=error
      self.illcmd=illcmd
      self.errmsg= errmsg
#
#    set status information. Called by GUI command queue processing.
#
   def setStatus(self,status):
      self.status=status
#
#  put command into the GUI-command queue, this is called by the thread component
#
   def put(self,item):
       self.gui_queue_lock.acquire()
       self.gui_queue.put(item)
       self.gui_queue_lock.release()

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
         if item[1]==0:
            pendef=[0xff,0xff,0xff,0x00,0x01]    
         elif item[1]==1:
            pendef= PENCONFIG.get_pen(self.penconfig1)
         elif item[1]==2:
            pendef= PENCONFIG.get_pen(self.penconfig2)
         self.pen.setColor(QtGui.QColor(pendef[0],pendef[1],pendef[2],pendef[3]))
         self.pen.setWidth(pendef[4])
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
         x= item[1] * self.factor
         y= self.height- (item[2] * self.factor)
         self.plotscene.addLine(self.lastx,self.lasty,x,y,pen=self.pen)
         self.lastx=x
         self.lasty=y
#
#     draw dot at location, graphic command generated by plotter emulator
#
      elif cmd== CMD_PLOT_AT:
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
# external lot view window class ------------------------------------------------------
#
class cls_plotViewWindow(QtGui.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.parent=parent
      self.setWindowTitle(self.parent.name+" view")
      self.vbox=QtGui.QVBoxLayout()
      self.plotview= cls_mygraphicsview(self.parent)
      self.vbox.addWidget(self.plotview)
      self.setLayout(self.vbox)

      self.plotview.setScene(self.parent.plotscene)
#     self.plotview.setSceneRect(self.parent.plotscene.sceneRect())
#     self.plotview.fitInView(self.parent.plotscene.sceneRect(),QtCore.Qt.KeepAspectRatio)
#     self.plotview.scale(self.width/self.parent.width,self.height/self.parent.height)
#     self.plotview.setSceneRect(self.parent.plotscene.sceneRect())
#     self.plotview.fitInView(self.parent.plotscene.sceneRect(),QtCore.Qt.KeepAspectRatio)
#     self.plotview.ensureVisible(0,0,self.width,self.height,0,0)

#
#  store geometry and position whenever changed
#
   def resizeEvent(self,event):
      self.plotview.fitInView(self.parent.plotscene.sceneRect(),QtCore.Qt.KeepAspectRatio)
      self.update_position()

   def moveEvent(self,event):
      self.update_position()

   def update_position(self):
      PILCONFIG.put(self.parent.name,"viewposition",[self.pos().x(),self.pos().y(),self.plotview.width(),self.plotview.height()])
   
#
# status window class -------------------------------------------------------------
#
# Display status byte, error code, error message and illegal HP-GL command
# The window may remain open and the content of the window will be updated
#
class cls_statusWindow(QtGui.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.parent=parent
      self.setWindowTitle("Plotter error status")
      self.__timer__=QtCore.QTimer()
      self.__timer__.timeout.connect(self.do_refresh)
      
      self.vbox=QtGui.QVBoxLayout()
      self.grid=QtGui.QGridLayout()
      self.grid.setSpacing(3)
      self.grid.addWidget(QtGui.QLabel("Status:"),1,0)
      self.grid.addWidget(QtGui.QLabel("Error code:"),2,0)
      self.grid.addWidget(QtGui.QLabel("HP-GL command:"),3,0)
      self.grid.addWidget(QtGui.QLabel("Error message:"),4,0)
      self.lblStatus=QtGui.QLabel("")
      self.lblError=QtGui.QLabel("")
      self.lblIllCmd=QtGui.QLabel("")
      self.lblErrMsg=QtGui.QLabel("")
      self.grid.addWidget(self.lblStatus,1,1)
      self.grid.addWidget(self.lblError,2,1)
      self.grid.addWidget(self.lblIllCmd,3,1)
      self.grid.addWidget(self.lblErrMsg,4,1)
      self.vbox.addLayout(self.grid)

      self.hlayout=QtGui.QHBoxLayout()
      self.button = QtGui.QPushButton('OK')
      self.button.setFixedWidth(60)
      self.button.clicked.connect(self.do_exit)
      self.hlayout.addWidget(self.button)
      self.vbox.addLayout(self.hlayout)
      self.setLayout(self.vbox)
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
      self.lblStatus.setText("{0:b}".format(self.parent.parent.pildevice.get_status()))
      self.lblError.setText(str(self.parent.error))
      self.lblIllCmd.setText(self.parent.illcmd)
      self.lblErrMsg.setText(self.parent.errmsg)

#
# Plotter configuration window class ------------------------------------------------
#
class cls_PlotterConfigWindow(QtGui.QDialog):

   def __init__(self,parent):
      super().__init__()
      self.__name__=parent.name
      self.__papersize__= PILCONFIG.get(self.__name__,"papersize")
      self.__penconfig1__= PILCONFIG.get(self.__name__,"penconfig1")
      self.__penconfig2__= PILCONFIG.get(self.__name__,"penconfig2")
      self.setWindowTitle("Plotter configuration")
      self.vbox= QtGui.QVBoxLayout()
#
#     Papersize combo box
#
      self.grid=QtGui.QGridLayout()
      self.grid.setSpacing(3)

      self.grid.addWidget(QtGui.QLabel("Papersize:"),1,0)
      self.combops=QtGui.QComboBox()
      self.combops.addItem("A4")
      self.combops.addItem("US")
      self.combops.setCurrentIndex(self.__papersize__)
      self.grid.addWidget(self.combops,1,1)
#
#     Pen1 combo box
#
      self.grid.addWidget(QtGui.QLabel("Pen1:"),2,0)
      self.combopen1=QtGui.QComboBox()
      for pen_desc in PENCONFIG.get_penlist():
         self.combopen1.addItem(pen_desc)
      self.combopen1.setCurrentIndex(self.__penconfig1__)
      self.grid.addWidget(self.combopen1,2,1)
#
#     Pen2 combo box
#
      self.grid.addWidget(QtGui.QLabel("Pen2:"),3,0)
      self.combopen2=QtGui.QComboBox()
      for pen_desc in PENCONFIG.get_penlist():
         self.combopen2.addItem(pen_desc)
      self.combopen2.setCurrentIndex(self.__penconfig2__)
      self.grid.addWidget(self.combopen2,3,1)

      self.vbox.addLayout(self.grid)
#
#     OK, Cancel
#
      self.buttonBox = QtGui.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.hlayout = QtGui.QHBoxLayout()
      self.hlayout.addWidget(self.buttonBox)
      self.vbox.addLayout(self.hlayout)

      self.setLayout(self.vbox)


   def do_ok(self):
      PILCONFIG.put(self.__name__,"papersize",self.combops.currentIndex())
      PILCONFIG.put(self.__name__,"penconfig1",self.combopen1.currentIndex())
      PILCONFIG.put(self.__name__,"penconfig2",self.combopen2.currentIndex())
      super().accept()

    
   def do_cancel(self):
      super().reject()


   @staticmethod
   def getPlotterConfig(parent):
      dialog= cls_PlotterConfigWindow(parent)
      result= dialog.exec_()
      if result== QtGui.QDialog.Accepted:
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

   def __init__(self,parent,name):
      super().__init__()
      self.cmdbuf=[]
      self.parse_state=0
      self.termchar= chr(3)
      self.proc=None
      self.parent=parent
      self.qplotter=parent.qplotter
      self.name=name
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
      self.outfunc=None
      self.invalid=True
#
#     initialize HP-GL command queue and lock
#
      self.hpgl_queue= queue.Queue()
      self.hpgl_queue_lock= threading.Lock()
#
#     initialize refresh timer
#
      self.UpdateTimer= QtCore.QTimer()
      self.UpdateTimer.setSingleShot(True)
      self.UpdateTimer.timeout.connect(self.process_hpgl_queue)
#
#  handle emulator not found or crashed
#
   def setInvalid(self):
#     self.UpdateTimer.stop()
      self.invalid=True
      self.error=99
      self.illcmd=""
      self.errmsg="emu7470 subprocess not running"
      self.qplotter.setError(self.error,self.illcmd,self.errmsg)
#
#     send to GUI: switch LED to red
#
      self.qplotter.put([CMD_ON_ERROR_RED])
#
#     disable HP-IL device permanently
#
      self.parent.pildevice.disable()
#
#  start the subprocess of the plotter emulator, set papeersize according to
#  config and send an "IN" command to the HP-GL command queue
#
   def enable(self):
#     progpath=os.path.join(os.path.dirname(pyilper.__file__),"emu7470","emu7470")
#     progpath=re.sub("//","/",progpath,1)
      progpath="emu7470"

      try:
         self.proc= subprocess.Popen([progpath], bufsize=1, universal_newlines=True, stdin=subprocess.PIPE,stdout=subprocess.PIPE)
      except OSError as e:
         self.setInvalid()
         return
      self.cmdbuf.clear()
      self.parse_state=0
      self.invalid=False
      papersize=PILCONFIG.get(self.name,"papersize")
      self.put_cmd("ZZ%d" % papersize)
#
#  stop the subprocess of the plotter emulator, clear the HP-GL command queue
#
   def disable(self):
      self.hpgl_queue_lock.acquire()
      while True:
         try:
            self.hpgl_queue.get_nowait()
            self.hpgl_queue.task_done()
         except queue.Empty:
            break
      self.hpgl_queue_lock.release()
      if not self.invalid:
         self.proc.stdin.close()
#
#  process the HP-GL command queue
#
   def process_hpgl_queue(self):
       items=[]
       self.hpgl_queue_lock.acquire()
       while True:
          try:
             i=self.hpgl_queue.get_nowait()
             items.append(i)
             self.hpgl_queue.task_done()
          except queue.Empty:
             break
       self.hpgl_queue_lock.release()
       if len(items):
          for c in items:
             self.process(c)
       return
#
#  put command into the HPGL-command queue
#
   def put_cmd(self,item):
       self.hpgl_queue_lock.acquire()
       self.hpgl_queue.put(item)
       self.hpgl_queue_lock.release()
#
#  send digitized coordinates to plotter emulator
#
   def send_digitize(self,x,y):
      self.put_cmd("ZY %d %d" % (x,y))
      return
#
#  send initialize command to plotter emulator
#
   def send_initialize(self):
      self.put_cmd("IN")
      return
#
# send IP command to plotter emulator
#
   def send_p1p2(self,xp1,yp1,xp2,yp2):
      self.put_cmd("IP%d,%d,%d,%d;" % (xp1,yp1,xp2,yp2))
      return
#
# send papersize to plotter emulator
#
   def send_papersize(self,papersize):
      self.put_cmd("ZZ%d" % papersize)
      return
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
      if self.parent.loglevel>0:
         self.parent.cbLogging.logWrite("HPGL: ")
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
               self.parent.cbLogging.logWrite("("+x+")")
            else:
               self.parent.cbLogging.logWrite(c)
         self.parent.cbLogging.logWrite("\n")
         self.proc.stdin.write("\n")
      except OSError as e:
         self.setInvalid()
         return
      except AttributeError as e:
         self.setInvalid()
         return
#
#     read processed results from plotter
#
      while True:
         try:
            line=self.proc.stdout.readline()
         except OSError as e:
            self.setInvalid()
            return
         if line =="":
            self.setInvalid()
            return
         ret=line.split()
         cmd= int(ret[0])
#
#        end of output of a command
#
         if cmd== CMD_EOF: 
            self.qplotter.put([CMD_EOF])
            self.qplotter.setError(self.error,self.illcmd,self.errmsg)
            self.qplotter.setStatus(self.status)
            break
#
#        clear
#
         elif cmd== CMD_CLEAR:
            self.qplotter.put([CMD_CLEAR])
#
#        set pen 
#
         elif cmd== CMD_SET_PEN:
            self.qplotter.put([CMD_SET_PEN, int(ret[1])])
            if self.parent.loglevel>1:
               self.parent.cbLogging.logWrite("Set Pen %s\n" % ret[1])
#
#        move
#
         elif cmd== CMD_MOVE_TO:
            self.x= float(ret[1])
            self.y= float(ret[2])
            self.qplotter.put([CMD_MOVE_TO,self.x,self.y])
            if self.parent.loglevel>1:
               self.parent.cbLogging.logWrite("Move To %d %d\n" % (self.x,self.y))
#
#        draw
#
         elif cmd== CMD_DRAW_TO:
            self.x= float(ret[1])
            self.y= float(ret[2])
            self.qplotter.put([CMD_DRAW_TO,self.x,self.y])
            if self.parent.loglevel>1:
               self.parent.cbLogging.logWrite("Draw To %d %d\n" % (self.x,self.y))
#
#        draw dot
#
         elif cmd== CMD_PLOT_AT:
            self.x= float(ret[1])
            self.y= float(ret[2])
            self.qplotter.put([CMD_PLOT_AT, self.x,self.y])
            if self.parent.loglevel>1:
               self.parent.cbLogging.logWrite("Plot At %d %d\n" % (self.x,self.y))

#
#        output from plotter to HP-IL, use the cls_pilplotter setOutput 
#        method (registered). This puts the data to an output data queue of pilotter
#
         elif cmd== CMD_OUTPUT:
            result=ret[1]+chr(0x0D)+chr(0x0A)
            self.outfunc(result)
            if self.parent.loglevel>0:
               self.parent.cbLogging.logWrite("Plotter to HP-IL: %s\n" % ret[1])
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
               self.qplotter.put([CMD_ON_ERROR_YELLOW])
            else:
               self.errmsg=""
               self.illcmd=""
               self.qplotter.put([CMD_OFF_ERROR])
            if self.parent.loglevel>0:
               self.parent.cbLogging.logWrite("Status %x, Error %d\n" % (self.status,self.error))
#
#        extended error message
#
         elif cmd== CMD_ERRMSG:
            self.errmsg= line[2:-1]
            self.illcmd="".join(self.cmdbuf)
            if self.parent.loglevel>0:
               self.parent.cbLogging.logWrite("Error message %s\n" % (self.errmsg))
#
#        enter digitizing mode, status bit is handled by emu7470
#
         elif cmd== CMD_DIGI_START:
            self.qplotter.put([CMD_DIGI_START])
#
#        clear digitizing mode, status bit is handled by emu7470
#
         elif cmd== CMD_DIGI_CLEAR:
            self.qplotter.put([CMD_DIGI_CLEAR])
#
#        P1, P2 set
#
         elif cmd== CMD_P1P2:
            x1= float(ret[1])
            y1= float(ret[2])
            x2= float(ret[3])
            y2= float(ret[4])
            self.qplotter.put([CMD_P1P2,x1,y1,x2,y2])
         else:
            eprint("Unknown command %s" % ret)
#
#  HP-IL device clear; clear command buffer
#
   def reset(self):
      self.cmdbuf.clear()
      self.parse_state=0
#
#  register function to send output from plotter to HP-IL
#
   def set_outfunc(self,func):
      self.outfunc=func
#
#  register functio to update the status byte of the HP-IL device
#
   def set_statfunc(self,func):
      self.statfunc=func

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
            self.separator=False
            return
         if c ==",":
            self.separator=True
            self.inparam= False
            self.cmdbuf.append(c)
            return
         self.inparam= False
         self.numparam=0
         self.separator=False
         self.put_cmd("".join(self.cmdbuf))
         self.process_hpgl_queue()
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
            self.put_cmd("".join(self.cmdbuf))
            self.process_hpgl_queue()
            self.cmdbuf.clear()
            self.parse_state=0
         else:
            self.cmdbuf.append(c)
      elif self.parse_state==4:
#
#        process single character of DT or SM command
#
         self.cmdbuf.append(c)
         self.put_cmd("".join(self.cmdbuf))
         self.process_hpgl_queue()
         self.cmdbuf.clear()
         self.parse_state=0
