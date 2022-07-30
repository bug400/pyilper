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
# HP2225B virtual device classes  ---------------------------------------------
#
# Changelog
# 30.12.2018 jsi:
# - initial version
# 02.01.2018 jsi:
# - added support for ^N and ^O for bold mode on and off
# - allow ESC&kS in addition to ESC&k0S to switch to normal character pitch
# 04.01.2018 jsi:
# - support zero length graphics chunks
# - switchable print color
# 04.05.2022 jsi:
# - PySide6 migration
# 04.05.2022 jsi
# - force background of printer to be always white (dark mode!)
# 30.07.2022 jsi
# - user cls_pdfprinter.get_pdfFilename method to get pdf file name
#
import copy
import queue
import threading
import re
from math import floor
from .pilcore import *
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtGui, QtWidgets,QtPrintSupport
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtGui, QtWidgets,QtPrintSupport

from .pilconfig import PILCONFIG
from .pilcharconv import charconv, barrconv, CHARSET_HP2225
from .pildevbase import cls_pildevbase
from .pilwidgets import cls_tabgeneric, LogCheckboxWidget, T_INTEGER, O_DEFAULT, T_STRING
from .pilpdf import cls_pdfprinter

#
# constants --------------------------------------------------------------
#

PDF_LINES=70           # number of lines in pdf output
PDF_MARGINS=50         # margins (top,bot,left,right) of pdf output
PDF_MAX_COLS=3         # max number of columns in pdf output
PDF_COLUMN_SPACING=80  # spacing between columns
PDF_LINE_SPACING=0     # linespacing in (relative) pixel

# GUI commands
CMD_LF_PRESSED=     0
CMD_LF_RELEASED=    1
CMD_FF_PRESSED=     2
CMD_CLEAR=          3

# HPIL-Thread commands
REMOTECMD_CLEAR=0      # clear device
REMOTECMD_LOG=1        # log something
REMOTECMD_STATUS=2     # printer status information: 
REMOTECMD_TEXT=3       # print characters according to current status
REMOTECMD_GRAPHICS=4   # print graphics according to current status
REMOTECMD_CR=5         # carriage return
REMOTECMD_LF=6         # line feed
REMOTECMD_HLF=7        # half line feed
REMOTECMD_BS=8         # backspace
REMOTECMD_FF=9         # form feed
REMOTECMD_TERMGRAPHICS=10 # end of graphics

ELEMENT_FF=0
ELEMENT_TEXT=1
ELEMENT_GRAPHICS=2

# Printer constants
BUFFER_LINE_H=2             # number of dots for a buffer line height
PRINTER_WIDTH_HIGH= 1280    # width in dots for high resolution
PRINTER_WIDTH_LOW= 640      # width in dots for low resolution
HP2225B_FONT_PIXELSIZE=28   # pixel size of the font used
HP2225B_MAX_LINES= 69       # maximum number of lines for a page

# Font widths
# Print mode norm                 : 80 chars/line, character width 16 dots
# Print mode expand               : 40 chars/line, character width 32 dots
# Print mode compressed           : 142 chars/line, character width 9 dots
# Print mode expand/compressed    : 71 chars/line, character width 18 dots
FONT_WIDTH= [16, 32, 9, 18 ]
#
# this is a hack because Qt on Macos does not display expanded fonts correctly
#
if isMACOS():
   FONT_STRETCH= [100, 110, 56, 110]
else:
   FONT_STRETCH= [100, 200, 56, 113]

BUFFER_SIZE_NAMES=["5 Pages", "10 Pages","20 Pages","50 Pages"]
BUFFER_SIZE_VALUES=[2500, 5000, 10000, 25000]
#
# Print colors
#
HP2225_COLOR_BLACK=0
HP2225_COLOR_RED=1
HP2225_COLOR_BLUE=2
HP2225_COLOR_GREEN=3
COLOR_NAMES= [ "black", "red", "blue", "green" ]
HP2225_COLORS=[QtCore.Qt.black, QtCore.Qt.red, QtCore.Qt.blue, QtCore.Qt.green]

#
# HP2225B tab widget ---------------------------------------------------------
#
class cls_tabhp2225b(cls_tabgeneric):


   def __init__(self,parent,name):
      super().__init__(parent,name)
      self.name=name
#
#     this parameter is global
#
      self.papersize=PILCONFIG.get("pyilper","papersize")
#
#     init local parameter
#
      self.screenwidth=PILCONFIG.get(self.name,"hp2225b_screenwidth",-1)
      self.scrollupbuffersize=PILCONFIG.get(self.name,"hp2225b_scrollupbuffersize",1)
      self.printcolor=PILCONFIG.get(self.name,"hp2225b_printcolor",HP2225_COLOR_BLACK)
#
#     create Printer GUI object
#
      self.guiobject=cls_hp2225bWidget(self,self.name,self.papersize)
#
#     add gui object 
#
      self.add_guiobject(self.guiobject)
#
#     add cascading config menu
#
      self.add_configwidget()
#
#     add local config option
#
      self.cBut.add_option("Screen width","hp2225b_screenwidth",T_INTEGER,[O_DEFAULT,640,960,1280])
      self.cBut.add_option("Buffer size","hp2225b_scrollupbuffersize",T_STRING,BUFFER_SIZE_NAMES)
      self.cBut.add_option("Print color","hp2225b_printcolor",T_STRING,COLOR_NAMES)
#
#     add logging control widget
#
      self.add_logging()
#
#     create IL-Interface object, notify printer processor object
#
      self.pildevice= cls_pilhp2225b(self.guiobject)
      self.guiobject.set_pildevice(self.pildevice)
      self.cBut.config_changed_signal.connect(self.do_tabconfig_changed)
#
#  handle changes of tab config options
#
   def do_tabconfig_changed(self):
      self.loglevel= PILCONFIG.get(self.name,"loglevel",0)
      self.guiobject.reconfigure()
      super().do_tabconfig_changed()
#
#  reconfigure: reconfigure the gui object
#
   def reconfigure(self):
      self.guiobject.reconfigure()
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
#  active/inactive: enable/disable GUI controls
#
   def toggle_active(self):
      super().toggle_active()
      self.guiobject.toggle_active()
#
#  becomes visible, refresh content, activate update
#
   def becomes_visible(self):
      self.guiobject.becomes_visible()
      return
#
#  becomes invisible, deactivate update
#
   def becomes_invisible(self):
      self.guiobject.becomes_invisible()
      return
#
#
# hp2225b widget classes - GUI component of the HP2225B HP-IL printer
#
class cls_hp2225bWidget(QtWidgets.QWidget):

   def __init__(self,parent,name,papersize):
      super().__init__()
      self.name= name
      self.parent= parent
      self.papersize= papersize
      self.pildevice= None
#
#     printer status that controls the appearance of the printer output 
#
      self.pdf_rows=480           # text length in rows
      self.char_attr=0            # character pitch
      self.char_bold=False        # bold mode
      self.char_underline=False   # underline mode
      self.hiRes=False            # high resolution of graphics output
      self.lpi6=True              # lines/inch
      self.wrapEOL=False          # EOL wrap
#
#     line coordinates
#
      self.pos_y=0                # in 4 dots (1280dpi) steps
      self.pos_x=0                # in 1280dpi steps

      self.graphics_counter=0     # number of graphics lines 
#
#     create user interface of printer widget
#
      self.hbox=QtWidgets.QHBoxLayout()
      self.hbox.addStretch(1)
#
#     scrolled printer view
#
      self.printview=cls_ScrolledHp2225bView(self,self.name,self.papersize)
      self.hbox.addWidget(self.printview)
      self.vbox=QtWidgets.QVBoxLayout()
#
#     Clear Button
#
      self.clearButton= QtWidgets.QPushButton("Clear")
      self.clearButton.setEnabled(False)
      self.clearButton.setAutoDefault(False)
      self.vbox.addWidget(self.clearButton)
      self.clearButton.clicked.connect(self.do_clear)
#
#     LF Button
#
      self.LFButton= QtWidgets.QPushButton("LF")
      self.LFButton.setEnabled(False)
      self.LFButton.setAutoDefault(False)
      self.vbox.addWidget(self.LFButton)
      self.LFButton.pressed.connect(self.do_LF_pressed)
      self.LFButton.released.connect(self.do_LF_released)
#
#     FF Button
#
      self.FFButton= QtWidgets.QPushButton("FF")
      self.FFButton.setEnabled(False)
      self.FFButton.setAutoDefault(False)
      self.vbox.addWidget(self.FFButton)
      self.FFButton.pressed.connect(self.do_FF_pressed)
#
#     PDF Button
#
      self.pdfButton= QtWidgets.QPushButton("PDF")
      self.pdfButton.setEnabled(False)
      self.pdfButton.setAutoDefault(False)
      self.vbox.addWidget(self.pdfButton)
      self.pdfButton.clicked.connect(self.do_pdf)

      self.vbox.addStretch(1)
      self.hbox.addLayout(self.vbox)
      self.hbox.addStretch(1)
      self.setLayout(self.hbox)
#
#     initialize GUI command queue and lock
#
      self.gui_queue= queue.Queue()
      self.gui_queue_lock= threading.Lock()
#
#     initialize refresh timer
#
      self.UpdateTimer=QtCore.QTimer()
      self.UpdateTimer.setSingleShot(True)
      self.UpdateTimer.timeout.connect(self.process_queue)
#
#     initialize timer for the repeated pressed LF action
#
      self.repeatedLFpressedTimer=QtCore.QTimer()
      self.repeatedLFpressedTimer.timeout.connect(self.repeated_LFpressed)
      self.repeatedLFpressedTimer.setInterval(1500)
#
#     set HP-IL device object
#
   def set_pildevice(self,pildevice):
      self.pildevice=pildevice
#
#     enable: start timer, send mode to virtual device, update check boxes
#
   def enable(self):
      self.UpdateTimer.start(UPDATE_TIMER)
      self.toggle_active()
      return
#
#     disable, clear the GUI queue, stop the timer
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
      self.UpdateTimer.stop()
      return
#
#     becomes visible
#
   def becomes_visible(self):
      self.printview.becomes_visible()
#
#     becomes invisible, do nothing
#
   def becomes_invisible(self):
      pass
#
#     active/inactive: enable/disable GUI controls
#
   def toggle_active(self):
      if self.parent.active:
         self.clearButton.setEnabled(True)
         self.LFButton.setEnabled(True)
         self.FFButton.setEnabled(True)
         self.pdfButton.setEnabled(True)
      else:
         self.clearButton.setEnabled(False)
         self.LFButton.setEnabled(False)
         self.FFButton.setEnabled(False)
         self.pdfButton.setEnabled(False)
#
#     reconfigure
#
   def reconfigure(self):
      self.printview.reconfigure()
      return
#
#     action scripts
#
   def do_clear(self):
      self.printview.reset()
      self.pildevice.put_cmd(CMD_CLEAR)
      return

   def do_FF_pressed(self):
      self.put_cmd([REMOTECMD_FF])
      return

   def do_LF_pressed(self):
      self.repeatedLFpressedTimer.start()
      self.put_cmd([REMOTECMD_LF])
      return

   def do_LF_released(self):
      self.repeatedLFpressedTimer.stop()
      return

   def do_pdf(self):
      flist=cls_pdfprinter.get_pdfFilename()
      if flist is None:
         return
      self.printview.pdf(flist[0],self.pdf_rows)
      return
#
#  put command into the GUI-command queue, this is called by the thread component
#
   def put_cmd(self,item):
       self.gui_queue_lock.acquire()
       self.gui_queue.put(item)
       self.gui_queue_lock.release()
#
#  repeated LF pressed action
#
   def repeated_LFpressed(self):
      self.put_cmd([REMOTECMD_LF])
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
       self.UpdateTimer.start(UPDATE_TIMER)
       return
#
#  GUI command processing, commands issued by the HP-IL thread
#
# Printer coordinate system
#
# The internal scene coordinate systems of this program is dots at
# a resolution of 192 dpi.  The HP2225B operates
# either at 96x96dpi or 96x192dpi resolution. Thus we have always even
# values for the y coordinate. 
#
# Constants for movement and positioning
# Dots per line: 1280
# Print mode norm                 : 80 chars/line, character width 16 dots
# Print mode expand               : 40 chars/line, character width 32 dots
# Print mode compressed           : 142 chars/line, character width 9 dots
# Print mode expand/compressed    : 71 chars/line, character width 18 dots
# Character height always 16 dots
# Line spacing 8 dots at 8 lines/inch, 16 dots at 6 lines/inch
# Line feed is 24 dots at 8 lines/inch, 32 dots at 6 lines/inc
# Half line feed is 12 dots at 8 lines/inch and 16 dots at 6 lines/inch
# Graphics line: 16 dots height, 1280 dots width
# A graphics dot is 2x2 dots at low res an 2x1 dot at high res
# Graphics data is 80 bytes at low res and 160 bytes at high res
#
# Here we use the following coordinate system:
# x= 1 dot (resolution 1280)
# y= 4 dots (resolution 1280)
#    LF= 6 / 8 , half LF= 3 / 4
# 
   def process(self,item):
      cmd= item[0]
#
#     clear graphhics views 
#
      if cmd==  REMOTECMD_CLEAR:
         self.printview.reset()
         self.pos_x=0
#        print("GUI: reset")
         self.graphics_counter=0
#
#     carriage return go to beginning of the current line
#
      elif cmd== REMOTECMD_CR:
#        print("GUI: cr")
         self.pos_x=0
         self.graphics_counter=0
#
#     line feed advance according to line spacing
#
      elif cmd== REMOTECMD_LF:
#        print("GUI: lf")
         if self.lpi6:
             self.printview.advance(8)
         else:
             self.printview.advance(6)
         self.graphics_counter=0
#
#     Form feed, we need that for the PDF output later
#
      elif cmd== REMOTECMD_FF:
#        print("GUI: ff")
         if self.lpi6:
             self.printview.advance(8)
         else:
             self.printview.advance(6)
         self.graphics_counter=0
         self.printview.add([ELEMENT_FF])
#
#     advance one half line feed
#
      elif cmd== REMOTECMD_HLF:
#        print("GUI: half lf")
         self.graphics_counter=0
         if self.lpi6:
             self.printview.advance(4)
         else:
             self.printview.advance(3)
#
#     Backspace, go back one character, use current font width
#
      elif cmd== REMOTECMD_BS:
#        print("GUI: bs")
         self.graphics_counter=0
         l= FONT_WIDTH[self.char_attr]
         self.pos_x-=l
         if self.pos_x < 0:
             self.pos_x=0
#
#     update configuration triggered by an escape sequence
#
      elif cmd== REMOTECMD_STATUS:
#        print("GUI status", item[1])
         self.pdf_rows=item[1][0] 
         self.char_attr=item[1][1]
         self.char_bold=item[1][2]
         self.char_underline=item[1][3]
         self.hiRes=item[1][4]
         self.lpi6=item[1][5]
         self.wrapEOL=item[1][6]
#
#     text element, we do not support EOL wrap at the moment and ignore any text
#     that exceeds a sinlge line
#
      elif cmd== REMOTECMD_TEXT:
         self.graphics_counter=0
#        print("GUI text", self.pos_x, item[1])
         txt_list= item[1]

         while txt_list is not None:
#
#           new length of row 
#
            newlen=self.pos_x+len(txt_list)*FONT_WIDTH[self.char_attr]
#
#           exceeds row
#
            if newlen> PRINTER_WIDTH_HIGH:
               fit_in_row=len(txt_list)- round((newlen-PRINTER_WIDTH_HIGH)/
                       FONT_WIDTH[self.char_attr])
#
#              txt contains the characters that fit in the current row
#
               txt=bytearray(txt_list[:fit_in_row])
#
#              if eolWrap is off we throw away the remaining content, otherwise
#              keep it
#
               if self.wrapEOL:
                   txt_list= txt_list[fit_in_row:]
               else:
                   txt_list= None
            else:
#
#              text fits into current row
#
               fit_in_row= len(txt_list)
               txt=bytearray(txt_list)
               txt_list= None
#
#              add it to the current line in the view
#
            self.printview.add([ELEMENT_TEXT,self.pos_x,self.char_attr,
                self.char_bold,self.char_underline,barrconv(txt,CHARSET_HP2225)])
            self.pos_x+= fit_in_row* FONT_WIDTH[self.char_attr]
#
#           if we have remaining text in txt_list then do a cr/lf
#
            if txt_list is not None:
               if self.lpi6:
                  self.printview.advance(8)
               else:
                  self.printview.advance(6)
               self.graphics_counter=0
               self.pos_x=0
#
#     graphics, we can have only 2 graphics lines at a single printer rows
#
      elif cmd== REMOTECMD_GRAPHICS:
         self.pos_x=0
#        print("GUI: graphics",self.graphics_counter, item[1])
         self.printview.add([ELEMENT_GRAPHICS,self.graphics_counter,self.hiRes,item[1]])
         self.graphics_counter+=1
         if self.graphics_counter == 2:
             self.graphics_counter=0
             self.printview.advance(1)
#
#     terminate graphics, advance 4 dots
#
      elif cmd== REMOTECMD_TERMGRAPHICS:
          self.graphics_counter=0
          self.printview.advance(1)
#
#     log line
#
      elif cmd== REMOTECMD_LOG:
         self.parent.cbLogging.logWrite(item[1])
         self.parent.cbLogging.logFlush()
#
# custom class for scrolled hp2225b output widget ----------------------------
#
class cls_ScrolledHp2225bView(QtWidgets.QWidget):

   def __init__(self,parent,name,papersize):
      super().__init__(parent)
      self.parent=parent
      self.name=name
#     
#     create window and scrollbars
#
      self.hbox= QtWidgets.QHBoxLayout()
      self.scrollbar= QtWidgets.QScrollBar()
      self.hp2225bwidget= cls_hp2225bView(self,self.name,papersize)
      self.hp2225bwidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
      self.hp2225bwidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
      self.hbox.addWidget(self.hp2225bwidget)
      self.hbox.addWidget(self.scrollbar)
      self.setLayout(self.hbox)
#
#     Initialize scrollbar
#
      self.scrollbar.valueChanged.connect(self.do_scrollbar)
      self.scrollbar.setEnabled(True)
      self.reset()
#
#   scrollbar value changed action
#
   def do_scrollbar(self):
      self.hp2225bwidget.do_scroll(self.scrollbar.value())
#
#   reset output window
#
   def reset(self):
      self.hp2225bwidget.reset()
      self.scrollbar.setMinimum(0)
      self.scrollbar.setMaximum(0)
      self.scrollbar.setSingleStep(1)
#
#   generate pdf output
#
   def pdf(self,filename,pdf_rows):
      self.hp2225bwidget.pdf(filename,pdf_rows)
#
#  becomes visible/invisible: nothing to do
#
   def becomes_visible(self):
      return

   def becomes_invisible(self):
      return
#
#  reconfigure
#
   def reconfigure(self):
      self.hp2225bwidget.reconfigure()
      return
#
#  add elements
#
   def add(self,element):
      self.hp2225bwidget.add(element)
#
#  advance
#
   def advance(self,n):
      self.hp2225bwidget.advance(n)
      
#
# custom class for hp2225b output  -----------------------------------------
#
class cls_hp2225bView(QtWidgets.QGraphicsView):

   def __init__(self,parent,name,papersize):
      super().__init__()
      self.parent=parent
      self.name= name
      self.screenwidth= -1
      self.printcolor= QtCore.Qt.black
#
#     background of print area is always white
#
      self.setAutoFillBackground(True)
      p=self.palette()
      p.setColor(self.backgroundRole(),QtCore.Qt.white)
      self.setPalette(p)
      self.w=-1
      self.h=-1
      self.rows= 0

      self.linebuffersize= -1
      self.papersize= papersize
#
#     set the font and font size
 
      self.font=QtGui.QFont(FONT)

      self.font.setPixelSize(HP2225B_FONT_PIXELSIZE)
      metrics=QtGui.QFontMetrics(self.font)
#
#     Initialize line bitmap buffer
#
      self.lb= [ ]
      self.lb_current= 0
      self.lb_anz=0
      self.lb_position=0

      self.printscene=None
      self.reconfigure()
      return


   def reconfigure(self):
#
#     re/configure the printview widget
#
      tmp=BUFFER_SIZE_VALUES[PILCONFIG.get(self.name,"hp2225b_scrollupbuffersize")]
      if tmp != self.linebuffersize:
         self.linebuffersize=tmp
         if self.printscene is not None:
             self.printscene.reset()
         self.lb= [None]* self.linebuffersize
         self.lb_current= 0
         self.lb_anz=0
         self.lb_position=0

      tmp=PILCONFIG.get_dual(self.name,"hp2225b_screenwidth")
      if tmp != self.screenwidth:
         self.screenwidth=tmp
         self.w=self.screenwidth
#
#        set fixed width
#
         self.setFixedWidth(self.w)
#
#        reconfigure scene if it exists
#
         if self.printscene is not None:
            self.printscene.reconfigure(self.screenwidth,self.printcolor)
            self.do_resize()
#
#     print color
#
      tmp=HP2225_COLORS[PILCONFIG.get(self.name,"hp2225b_printcolor")]
      if tmp != self.printcolor:
          self.printcolor=tmp
          if self.printscene is not None:
             self.printscene.reconfigure(self.screenwidth,self.printcolor)
             self.do_resize()
#
#     initialize scene if it does not exist
#
      if  self.printscene is None:
         self.printscene= cls_hp2225b_scene(self,self.font, self.screenwidth,self.printcolor)
         self.setScene(self.printscene)
         self.reset()
      return
#
#      reset output window
#
   def reset(self):
      for i in range(0,self.linebuffersize):
         if self.lb[i] is not None:
            self.lb[i]= None
      self.lb_current= 0
      self.lb_anz=0
      self.lb_position=0
      self.printscene.reset()
#
#  resize event, adjust the scene size, reposition everything and redraw
#
   def resizeEvent(self,event):
      self.do_resize()

   def do_resize(self):
      h=self.height()
#
#     compute the number of rows that will fit into the current window size
#
      self.rows= floor(h /BUFFER_LINE_H /2 * PRINTER_WIDTH_HIGH /self.screenwidth)

#     print("resize view dimensions ",self.screenwidth,h);
#     print("resize view rows: ",self.rows)
#     print("resize view: fit in view", PRINTER_WIDTH_HIGH, self.rows*2*BUFFER_LINE_H))
#
#     adjust the size of the print scene
#
      self.printscene.set_scenesize(self.rows)
#
#     now transform the scene into the current view, force transformation
#     to identity if we use a screen width of 1280
#
      if self.screenwidth != PRINTER_WIDTH_HIGH:
         self.fitInView(0,0,PRINTER_WIDTH_HIGH,self.rows*2*BUFFER_LINE_H) 
      else:
         self.resetTransform()
#
#     now adjust the scroll bar parameters
#
      scroll_max=self.lb_current- self.rows
      if scroll_max < 0:
         scroll_max=0
#     print("scrollbar adjustment: ", self.lb_current,scroll_max)
#     print("---")
      self.parent.scrollbar.setMaximum(scroll_max)
      self.parent.scrollbar.setPageStep(self.rows)
      self.printscene.update_scene()
      return
#
#  PDF output. Text length configuration is not supported at the moment
#
   def pdf(self,filename,pdf_rows):

      self.printer=QtPrintSupport.QPrinter (QtPrintSupport.QPrinter.HighResolution)
      self.printer.setPageOrientation(QtGui.QPageLayout.Portrait)
      self.printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
      self.pdfscene=QtWidgets.QGraphicsScene()
#
#     page set up, we use 192 dpi dots as scene units and set the left
#     and right margins so that we get a print width of 6.7 inches
#     The height of 60 lines is 10 inches
#     DINA4:  0,79 inches= 151 dots
#     Letter: 0.9 inches = 173 dots
#
#
#     A4 format is 8,27 inches x 11,7 inches
#
      if self.papersize== PDF_FORMAT_A4:
         self.printer.setPageSize(QT_FORM_A4)
         lmargin= 151
         tmargin= 163 
         scene_w= 1280 + lmargin*2
         scene_h= 1920 + tmargin*2
         self.pdfscene.setSceneRect(0,0,scene_w,scene_h)
      else:
#
#     Letter format is 8.5 inches x 11 inches
#
         self.printer.setPageSize(QT_FORM_LETTER)
         lmargin= 173
         tmargin= 96 
         scene_w= 1280 + lmargin*2
         scene_h= 1920 + tmargin*2
         self.pdfscene.setSceneRect(0,0,scene_w,scene_h)

      self.painter= QtGui.QPainter()

      self.printer.setOutputFileName(filename)
      self.painter.begin(self.printer)

      pdfitems=[]
      anzitems=0
      delta= BUFFER_LINE_H*2
      horizontal_margin=floor((480-pdf_rows)/2)*delta

      rowcount=0
      y=tmargin + horizontal_margin
#
#     print all items to pdf
#
      for i in range(0,self.lb_anz):
          s= self.lb[i]
#
#         we have a form feed element, issue new page
#
          if s is not None:
              if s[0][0]== ELEMENT_FF:
#                print("FF ",rowcount, pdf_rows)
                 self.pdfscene.render(self.painter)
                 self.printer.newPage()
                 for l in reversed(range(anzitems)):
                    self.pdfscene.removeItem(pdfitems[l])
                    del pdfitems[-1]
                 anzitems=0
                 y=tmargin + horizontal_margin
                 rowcount=0
#                print("reset y to ",y,tmargin,horizontal_margin)
              item=cls_hp2225b_line(s,self.font,self.printcolor)
              pdfitems.append(item)
              self.pdfscene.addItem(item)
              item.setPos(lmargin,y)
#             print("pdf item added ",rowcount,y,s)
              anzitems+=1
#         else:
#             print("none element")
          rowcount+=1
          y+= delta
#
#         does the next line fit into the page, if not issue page break
#         The character height is always 16px.
#
          if rowcount > pdf_rows:
#             print("page break ",rowcount, pdf_rows)
              self.pdfscene.render(self.painter)
              self.printer.newPage()
              for l in reversed(range(anzitems)):
                  self.pdfscene.removeItem(pdfitems[l])
                  del pdfitems[-1]
              anzitems=0
              rowcount=0
              y=tmargin + horizontal_margin
#             print("reset y to ",y,tmargin,horizontal_margin)
#
#     output remaining data and terminate printing
#
      if anzitems > 0:
          self.pdfscene.render(self.painter)
          for l in reversed(range(anzitems)):
              self.pdfscene.removeItem(pdfitems[l])
              del pdfitems[-1]
      self.painter.end()
#
#
#  Mouse wheel event
#
   def wheelEvent(self,event):
       numDegrees= event.angleDelta()/8
       delta=0
       step= round (8 *  self.w / PRINTER_WIDTH_HIGH)
       if numDegrees.y() is not None:
          if numDegrees.y() < 0:
             delta=step
          if numDegrees.y() > 0:
             delta=-step
       event.accept()
       if self.lb_current < self.rows:
          return
       if self.lb_position+delta < 0:
           delta=-self.lb_position
       if self.lb_position+delta+self.rows > self.lb_current:
           delta=self.lb_current-(self.lb_position + self.rows )
       self.lb_position+=delta
       self.parent.scrollbar.setValue(self.lb_position)
       self.printscene.update_scene()
       return
#
#  external methods
#
#     add element
#
   def add(self,elem):
#     print("View add element: ",self.lb_current,elem)
      if self.lb[self.lb_current] is None:
          self.lb[self.lb_current]= [ ]
      self.lb[self.lb_current].append(elem)
      self.printscene.update_scene()
      return
#
#  advance
#
   def advance(self,n):
      if self.lb_anz+n < self.linebuffersize:
          self.lb_anz+=n
          self.lb_current+=n
      else:
          self.lb=self.lb[n:] + self.lb[:n]
          for i in range (0,n):
              self.lb[i-n]=None

      self.lb_position= self.lb_current- (self.rows) 
      if self.lb_position < 0:
          self.lb_position=0
#     print("View advance: ",n,self.lb_current, self.lb_position)
      self.parent.scrollbar.setMaximum(self.lb_position)
      self.parent.scrollbar.setValue(self.lb_position)
      self.printscene.update_scene()
      return
#
#     scroll bar action
#
   def do_scroll(self,value):
      self.lb_position=value
      self.printscene.update_scene()
#
#     pdf output
#
   def do_pdf(self,filename):
      return
#
# custom class for HP2225B graphics scene
#
class cls_hp2225b_scene(QtWidgets.QGraphicsScene):

   def __init__(self,parent,font,screenwidth,printcolor):
      super().__init__()
      self.rows= 0
      self.w=0
      self.h=0
      self.parent=parent
      self.si= None
      self.font=font
      self.reconfigure(screenwidth,printcolor)
      return
#
#  re/configure graphics scene
#
   def reconfigure(self,screenwidth,printcolor):
      self.screenwidth=screenwidth
      self.w= PRINTER_WIDTH_HIGH
      self.h= BUFFER_LINE_H *2
      self.printcolor=printcolor
      return
#
#  set or change the size of the scene
#
   def set_scenesize(self,rows):
      self.reset()
      self.rows= rows
      self.si= [None] * rows
      self.setSceneRect(0,0,self.w,(self.h*(self.rows)))
#     print("Scene size ",self.w,self.h*self.rows)
#
#  clear window and reset
#
   def reset(self):
      for i in range(0,self.rows):
         if self.si[i] is not None:
            self.removeItem(self.si[i])
            self.si[i]=None
#
#  update graphics scene
#
   def update_scene(self):
      for i in range(0,self.rows):
         if self.si[i] is not None:
            self.removeItem(self.si[i])
            self.si[i]=None
      start= self.parent.lb_position
      end= start+self.rows
      if end >= self.parent.lb_anz:
         end=self.parent.lb_anz
      y=0
      j=0
      for i in range(start,end):
         self.si[j]=self.parent.lb[i]
         if self.parent.lb[i] is not None:
            self.si[j]=cls_hp2225b_line(self.parent.lb[i], self.font,self.printcolor)
            self.addItem(self.si[j])
            self.si[j].setPos(0,y)
         y+=self.h
         j+=1
#     print("Scene updated: ",start,end)

#
# custum class HP2225 print line
#
class cls_hp2225b_line(QtWidgets.QGraphicsItem):

    def __init__(self,itemlist, font, color):
        super().__init__()
        self.itemlist= itemlist
        self.font=font
        self.color=color
        metrics=QtGui.QFontMetrics(self.font)
        self.font_height=metrics.height()
        self.rect= QtCore.QRectF(0,0,PRINTER_WIDTH_HIGH,self.font_height)
#       self.flags=QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop | QtCore.Qt.TextDontClip
#       self.flags=QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop 


    def setPos(self,x,y):
        super().setPos(x,y)

    def boundingRect(self):
        return self.rect
#
#   paint elements
#
    def paint(self,painter,option,widget):

        posx=0
        for item in self.itemlist:
#
#       Ignore element form feed
#
            if item[0]== ELEMENT_FF:
                continue
#
#       Paint text, align each character so that we get exactly the
#       number of characters per row as the original printer
#
            elif item[0]== ELEMENT_TEXT:
                painter.setPen(self.color)
                posx=item[1]
                self.font.setBold(item[3])
                self.font.setUnderline(item[4])
                self.font.setStretch(FONT_STRETCH[item[2]])
                posy=self.font_height-12

                painter.setFont(self.font)
                for c in item[5]:
                    painter.drawText(posx,posy,c)
#                   bounding_rect= QtCore.QRect(posx,0,posx+ (FONT_WIDTH[item[2]]),self.font_height)
#                   painter.drawText(bounding_rect, self.flags, c)
                    posx+= FONT_WIDTH[item[2]]
                continue
#
#       Paint raster graphics elements. They always begin at column 0
#       We have at most two graphics row elements. The y resolution
#       is always 96dpi and the x resolution may bei either 96 or 192
#       dpi according to the hiRes mode
#
            elif item[0]==ELEMENT_GRAPHICS:
                painter.setPen(self.color)
                posy=item[1]*2
                hiRes=item[2]
                posx=0
                for i in item[3]:
                    mask=0x80
                    if posx>=PRINTER_WIDTH_HIGH:
                        break
                    for j in range (0,8):
                       if hiRes:
                          if i & mask:
                             painter.fillRect(posx,posy,1,2,self.color)
                          posx+=1
                       else:
                          if i & mask:
                             painter.fillRect(posx,posy,2,2,self.color)
                          posx+=2
                       mask= mask >> 1
        return

#
# HP2225B emulator (thread component) --------------------------------------
#

class cls_hp2225b(QtCore.QObject):

   BUF_EMPTY=0
   BUF_TEXT=1
   BUF_GRAPHICS=2

   def __init__(self,parent,guiobject):
      super().__init__()
      self.pildevice=parent
      self.guiobject= guiobject

      self.esc= False             # escape mode
      self.esc_seq=""             # escape sequence
      self.esc_prefix=""          # prefix of combined esc sequences
      self.num_graphics=-1        # number of graphics bytes
      self.ignore_crlf=False      # flag to ignore cr/lf between graphics chunks
      self.apgot=False            # flag avoid printing graphics over text
#
#     printer status that controls the appearance of the printer output and
#     is therefore handled in the GUI component
#
      self.text_legnth= 60        # text length given in lines
      self.char_attr=0            # character pitch
      self.char_bold=False        # bold mode
      self.char_underline=False   # underline mode
      self.hiRes=False            # high resolution of graphics output
      self.lpi6=False             # lines/inch
      self.pdf_rows=480           # number of rows for pdf output
      self.wrapEOL=False          # EOL wrap
      self.empty_line=False       # detect empty text lines, this disables
                                  # ignoring cr/lf.
#
#     printer status which is handled here
#
      self.ltermMode=0           # line termination mode
      self.altMode= False         # alternate control mode
      self.displayFunctions=False # display functions mode
#
#     buffer for accumulated text and graphics data b e t w e e n control 
#     characters or escape sequences
#
      self.buf_status=self.BUF_EMPTY   # buffer status
      self.buf_data= [ ]
      self.log_line=""
      self.reset()
#
#
   def reset(self):
#
#     reset variables to default
#
      self.esc= False
      self.esc_seq=""
      self.esc_prefix=""
      self.num_graphics=-1
      self.ignore_crlf=False
      self.apgot=False
      self.text_length=60
      self.pdf_rows=480
      self.char_attr=0
      self.char_bold= False
      self.char_underline=False
      self.ltermMode=0
      self.hiRes=False
      self.lpi6=True
      self.wrapEOL=False

      self.displayFunctions=False
      self.log_line=""
      self.empty_line=False
      self.buf_clear()

#
#     send clear command to GUI
#
      self.guiobject.put_cmd([REMOTECMD_CLEAR])
      self.put_status()
      return
#
#     clear data buffer
#
   def buf_clear(self):
       self.buf_status= self.BUF_EMPTY
       self.buf_data= [ ]
#
#      flush buffer, send data to printer
#
   def buf_flush(self):
       if self.buf_status == self.BUF_EMPTY:
           return
       data_copy= copy.deepcopy(self.buf_data)
       if self.buf_status == self.BUF_TEXT:
           self.guiobject.put_cmd([REMOTECMD_TEXT,data_copy])
#          print("put cmd text",data_copy)
       else:
           self.guiobject.put_cmd([REMOTECMD_GRAPHICS,data_copy])
#          print("put cmd graphics",data_copy)
       self.buf_clear()
# 
#  send status
#
   def put_status(self):
#
#      if we have data in the buffer, clear it first
#
       self.buf_flush()
#
#      send printer status to GUI
#
       self.guiobject.put_cmd([REMOTECMD_STATUS,[self.pdf_rows,self.char_attr,self.char_bold,self.char_underline,self.hiRes,self.lpi6,self.wrapEOL]])

#
#  set/clear alternate control mode (has no effect)
#
   def setAltMode(self,mode):
       self.altMode= mode
       if self.altMode:
           print("hp2225: entering ESC/P command mode. This mode is not supported and the emulator will ignore all data.")
       else:
           print("hp2225: returning to PCL command mode.")
       return
#
#  process escaape sequences HP command set
#
   def process_esc_hp(self):
#
#     normal width
#
      if self.esc_seq=="&k0S" or self.esc_seq=="&kS":
         self.char_attr= (self.char_attr & 0x0C) 
         self.put_status()
         return
#
#     expanded width
#
      elif self.esc_seq=="&k1S":
         self.char_attr= (self.char_attr & 0x0C) | 0x01
         self.put_status()
         return
#
#     compressed width
#
      elif self.esc_seq=="&k2S":
         self.char_attr= (self.char_attr & 0x0C) | 0x02
         self.put_status()
         return
#
#     expanded-compressed width
#
      elif self.esc_seq=="&k3S":
         self.char_attr= (self.char_attr & 0x0C) | 0x03
         self.put_status()
         return
#
#     bold mode on
#
      elif self.esc_seq=="(s1B":
         self.char_bold= True
         self.put_status()
         return
#
#     bold mode off
#
      elif self.esc_seq=="(s0B":
         self.char_bold=False
         self.put_status()
         return
#
#     underline mode on
#
      elif self.esc_seq=="&dD":
         self.char_underline=True
         self.put_status()
         return
#
#     underline mode off
#
      elif self.esc_seq=="&d@":
         self.char_underline=False
         self.put_status()
         return
#
#     6 lines/inch
#
      elif self.esc_seq=="&l6D":
         self.lpi6=True
         self.put_status()
         return
#
#     8 lines/inch
#
      elif self.esc_seq=="&l8D":
         self.lpi6=False
         self.put_status()
         return
#
#     perforation skip on (has no effect)
#
      elif self.esc_seq=="&l1L":
         return
#
#     perforation skip off (has no effect)
#
      elif self.esc_seq=="&l0L":
         return
#
#     EOL wrap on
#
      elif self.esc_seq=="&s0C":
         self.wrapEOL=True
         self.put_status()
         return
#
#     EOL wrap off
#
      elif self.esc_seq=="&s1C":
         self.wrapEOL=False
         self.put_status()
         return
#
#     display functions on
#
      elif self.esc_seq=="Y":
         self.displayFunctions=True
         return
#
#     display functions off
#
      elif self.esc_seq=="Z":
         self.displayFunctions=False
         return
#
#     unidirectional printing (has no effect)
#
      elif self.esc_seq=="&k0W":
         return
#
#     biidirectional printing (has no effect)
#
      elif self.esc_seq=="&k1W":
         return
#
#     half line feed
#
      elif self.esc_seq=="=":
         self.half_lf()
         return
#
#     avoid printing graphics over text
#
      elif self.esc_seq=="*rA":
         self.apgot= True
         return
#
#     terminate graphics
#
      elif self.esc_seq=="*rB":
         self.ignore_crlf= False
         self.guiobject.put_cmd([REMOTECMD_TERMGRAPHICS])
         return
#
#     line termination mode 0
#
      elif self.esc_seq=="&k0G":
         self.ltermMode=0
         return
#
#     line termination mode 1
#
      elif self.esc_seq=="&k1G":
         self.ltermMode=1
         return
#
#     line termination mode 2
#
      elif self.esc_seq=="&k2G":
         self.ltermMode=2
         return
#
#     line termination mode 3
#
      elif self.esc_seq=="&k3G":
         self.ltermMode=3
         return
#
#     self test (has no effect)
#
      elif self.esc_seq=="z":
         return
#
#     reset printer
#
      elif self.esc_seq=="E":
         self.reset()
         return
#
#     Graphics dot row
#
      elif self.esc_seq.startswith("*b") and self.esc_seq.endswith("W"):
         ret=re.findall(r"\d+",self.esc_seq)
         if ret== []:
            return
         try:
            n=int(ret[0])
         except ValueError:
            return
         if n<0 or n> 255:
            return
         self.num_graphics=n
         self.begin_graphics()
         return
#
#     graphics resolution
#
      elif self.esc_seq.startswith("*r") and self.esc_seq.endswith("S"):
         ret=re.findall(r"\d+",self.esc_seq)
         if ret== []:
            return
         try:
            n=int(ret[0])
         except ValueError:
            return
         if n<=640:
            self.hiRes=False
         else:
            self.hiRes=True
         self.put_status()
         return
#
#     page length (has no effect)
#
      elif self.esc_seq.startswith("&l") and self.esc_seq.endswith("P"):
         return
#
#    Text length
#
      elif self.esc_seq.startswith("&l") and self.esc_seq.endswith("F"):
         ret=re.findall(r"\d+",self.esc_seq)
         if ret== []:
            return
         try:
            n=int(ret[0])
         except ValueError:
            return
         self.text_length=n
#
#        the text length can not exceed 80 lines at 8lpi or 60 lines at
#        6lpi. The maximum print area is limited to 10 inches in this
#        emulator. We now compute the numbes of rows the new text length
#        will occupy in the pdf file
#
         if self.text_length < 1:
             self.text_length=1
         if self.lpi6:
             if self.text_length> 60:
                 self.text_length=60
             self.pdf_rows= self.text_length* 8
         else:
             if self.text_length> 80:
                 self.text_length=80
             self.pdf_rows= self.text_length * 6
         self.pdf_rows-=1
         self.put_status()
         return
      else:
          print("hp2225: illegal escape sequence ignored: ", self.esc_seq)
      return
#
#  begin graphics
#
   def begin_graphics(self):
#
#     flush any pending text and go to BOL
#
#     print("begin new graphics ",self.num_graphics)
      if self.buf_status== self.BUF_TEXT:
         self.cr()
#
#  if the avoid printing graphics over text command was issued do a linefeed
#
         if self.apgot:
            self.lf()
      self.apgot= False
      self.ignore_crlf= True
      self.buf_status= self.BUF_GRAPHICS
      self.empty_line= False
      return

#
#  printer data processor HP command set
#
   def process_char_hp(self,ch):
#
#     if there are graphics data, append it to buffer and return
#
      if self.num_graphics > 0:
         self.num_graphics-=1
         self.buf_data.append(ch)
         return
#
#     last byte of graphics received, flush buffer and proceed
#
      if self.num_graphics==0:
         self.buf_flush()
#        print("graphics flushed ", self.buf_status)
         self.num_graphics= -1
#
#     process ESC sequences
#
      if (self.esc== False) and (ch== 0x1B):
         self.esc= True
         self.esc_seq=""
         self.esc_prefix=""
         self.empty_line=False
         return
      if self.esc:
#
#        ESC | or escape sequence terminated with capital letter
#
#        if ch == 0x7c or (ch >= 0x41 and ch <= 0x5A):
         self.empty_line=False
         if chr(ch) in "SBD@LPFCYZW=AGzE":
            self.esc_seq+= chr(ch)
            if self.esc_prefix!="":
               self.esc_seq= self.esc_prefix+self.esc_seq
            self.process_esc_hp()
            self.esc= False
            self.esc_seq=""
            self.esc_prefix=""
            return
#
#        repeated escape sequence terminated with lowercase letter
#
         if chr(ch) in "sdlpfcwabg" and len(self.esc_seq)>2:
            if self.esc_prefix == "":
               self.esc_prefix= self.esc_seq[:2]
               self.esc_seq= self.esc_seq[2:]
            self.esc_seq= self.esc_prefix+self.esc_seq+chr(ch).upper()
            self.process_esc_hp()
            self.esc_seq=""
            return
#
#        still in escape sequence, accumulate characters
#            
         self.esc_seq+= chr(ch)
         return
#
#     not in escape sequence, process control and data characters
#
#     Backspace:
#
      if (ch == 0x08):
          if self.ignore_crlf:
              return
          self.buf_flush()
          self.guiobject.put_cmd([REMOTECMD_BS])
#
#     CR
#
      elif (ch == 0x0D):
          if self.ignore_crlf:
              return
          self.cr()
          if self.ltermMode & 0x01:
              self.lf()
#
#     LF
#
      elif (ch == 0x0A):
          if self.empty_line:
              if self.ignore_crlf:
                  self.ignore_crlf= False
          self.empty_line= True 
          if self.ignore_crlf:
              return
          if self.ltermMode & 0x02:
              self.cr()
          self.lf()
#
#     FF
#
      elif (ch == 0x0C):
          if self.ltermMode & 0x02 or self.ltermMode & 0x03:
              self.cr()
          self.ff()
#
#     bold mode on ^N
#
      elif (ch == 0x0E):
          self.empty_line= False
          self.char_bold=True
          self.put_status()
#
#     bold mode off ^O
#
      elif (ch == 0x0F):
          self.empty_line= False
          self.char_bold=False
          self.put_status()
#
#     normal character
#
      else:
          self.empty_line= False
          self.ignore_crlf=False
          if ((ch >=0x20 and ch < 127) or (ch > 159 and ch< 255)):
              self.buf_status= self.BUF_TEXT
              assert self.buf_status== self.BUF_EMPTY or self.buf_status== self.BUF_TEXT
              self.buf_data.append(ch)
              self.log_line+= charconv(chr(ch), CHARSET_HP2225)
#
#  process printer data for display functions mode
#
   def process_char_df(self,ch):
      if self.esc:
         self.esc= False
         if ch== 0x5A:             # ESC Z terminates display functions mode
            self.displayFunctions= False
      if ch == 0x1B:
         self.esc=True
      self.buf_status= self.BUF_TEXT
      self.buf_data.append(ch)
      self.log_line+= charconv(chr(ch), CHARSET_HP2225)
      if (ch == 0x0A):
          self.cr()
          self.lf()
      return
#
# process printer data for the alternate control mode (not implemented!)
#
   def process_char_alt(self,ch):
       return
#
#  process printer data 
#
   def process_char(self,ch):
      if self.altMode:
         self.process_char_alt(ch)
      else:
         if self.displayFunctions:
            self.process_char_df(ch)
         else:
            self.process_char_hp(ch)
         return
#
#  line positioning: cr, lf, ff
#
   def cr(self):
       self.buf_flush()
       self.guiobject.put_cmd([REMOTECMD_CR])
       return

   def lf(self):
       self.buf_flush()
       self.guiobject.put_cmd([REMOTECMD_LF])
       if self.log_line != "":
           self.log_line+="\n"
           self.guiobject.put_cmd([REMOTECMD_LOG,self.log_line])
           self.log_line=""
       return

   def half_lf(self):
       self.buf_flush()
       self.guiobject.put_cmd([REMOTECMD_HLF])
       return


   def ff(self):
       self.buf_flush()
       self.guiobject.put_cmd([REMOTECMD_FF])
       if self.log_line != "":
           self.log_line+="\n"
           self.guiobject.put_cmd([REMOTECMD_LOG,self.log_line])
           self.log_line=""
       return
#
# process commands sent from the GUI
#
   def process(self,command):

      if command== CMD_CLEAR:
         self.reset()
         return

#
# HP-IL virtual HP2225B object class ---------------------------------------
#


class cls_pilhp2225b(cls_pildevbase):

   def __init__(self,guiobject):
      super().__init__()

#
#     overloaded variable initialization
#
      self.__aid__ = 0x23         # accessory id 
      self.__defaddr__ = 5        # default address alter AAU
      self.__did__ = "HP2225B"    # device id
      self.__status_len__=2       # device status is 2 bytes
#
#     private vars
#
      self.__ddlcmd__=False       # ddl command was sent
#
#     object specific variables
#
      self.__guiobject__= guiobject
#
#     initialize remote command queue and lock
#
      self.__print_queue__= queue.Queue()
      self.__print_queue_lock__= threading.Lock()
#
#     printer processor
#
      self.__printer__=cls_hp2225b(self,self.__guiobject__)
#
#     the printer status is a l w a y s:
#     - first byte : 0xA1   (everything is fine, no service request)
#     - second byte: 0x04   (buffer empty)
#
      self.set_status(0x04A1)

#
# public (overloaded) --------
#
#  enable: reset
#
   def enable(self):
      self.__ddlcmd__= False
      self.__printer__.reset()
      return
#
#  disable: clear the printer command queue
#
   def disable(self):
      self.__print_queue_lock__.acquire()
      while True:
         try:
            self.__print_queue__.get_nowait()
            self.__print_queue__.task_done()
         except queue.Empty:
            break
      self.__print_queue_lock__.release()
#
#  process frames 
#
   def process(self,frame):

      if self.__isactive__:
         self.process_print_queue()
      frame= super().process(frame)
      return frame
#
#  process the printer command queue
#
   def process_print_queue(self):
       items=[]
       self.__print_queue_lock__.acquire()
       while True:
          try:
             i=self.__print_queue__.get_nowait()
             items.append(i)
             self.__print_queue__.task_done()
          except queue.Empty:
             break
       self.__print_queue_lock__.release()
       if len(items):
          for c in items:
             self.__printer__.process(c)
       return

#
#  put command into the print-command queue
#
   def put_cmd(self,item):
       self.__print_queue_lock__.acquire()
       self.__print_queue__.put(item)
       self.__print_queue_lock__.release()
#
#  set status (2 byte status information)
#
   def set_status(self,s):
      self.__setstatus__(s)
      return s
#
#  get status byte (2 byte status information)
#
   def get_status(self):
      s=self.__getstatus__()
      return s

#
# private (overloaded) --------
#
#
#  output character to HP2225B
#
   def __indata__(self,frame):
      n= frame & 0xFF
#
      if self.__ddlcmd__:
          if n== 18:
              self.__printer__.setAltMode(True)
          if n==0:
              self.__printer__.setAltMode(False)
          self.__ddlcmd__= False
      else:
          self.__printer__.process_char(n) 
#
#  ddl command implementation
#
   def __cmd_ext__(self,frame):
       n= frame & 0xFF
       t= n>>5
       if t==5:   # DDL
          n=n & 31
          if (self.__ilstate__ & 0xC0) == 0x80: # are we listener?
             self.__devl__= n & 0xFF
             if n== 6:
                self.__ddlcmd__= True
       return(frame)
#
#  clear device: reset printer
#
   def __clear_device__(self):
      super().__clear_device__()
#
#     clear printer queue
#
      self.__print_queue_lock__.acquire()
      while True:
         try:
            self.__print_queue__.get_nowait()
            self.__print_queue__.task_done()
         except queue.Empty:
            break
      self.__print_queue_lock__.release()
#
#     reset device 
#
      self.__printer__.reset()

