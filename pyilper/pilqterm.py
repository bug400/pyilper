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
# Object classes of terminal widget ----------------------------------------
#
# This code was derived from the pyqterm widget of Henning Schröder
#
# Changelog
# 06.10.2015 jsi:
# - class statement syntax update
# - adjust super statements to python3+ syntax
# 21.11.2015 jsi:
# - disabled F7
# - enhanced error messages about unhandled escape sequences
# 20.02.2016 jsi:
# - _kbdfunc escape sequence handling improved
# 26.02.2016 jsi:
# - keyboard input delay introduced to improve stability
# - do not update terminal window if not visible
# 28.02.2016 jsi:
# - removed dead code
# - scroll line left and right does now work for wrapped lines
# - implemented block and arrow cursor, removed indicator function
# 01.03.2016 jsi:
# - removed more unneeded code, introduced first color scheme support
# 05.03.2016 jsi:
# - removed more unneeded code
# - disable autorepeat
# - fixed BS and ESC % handling
# 06.03.2016 jsi:
# - refactoring
# - use non blocking get in terminal output queue
# 07.03.2016 jsi:
# - fixed alt key, MAC OSX fix
# - introduced OS X like ALT shortcuts for { [ ] } @
# 09.03.2016 jsi:
# - introduced shortcut ALT-I to toggle insert mode
# 10.03.2016 jsi:
# - introduced transparent cursor
# 12.03.2016 jsi:
# - removed keyboard delay
# 20.03.2016 jsi:
# - improved insert cursor, use transform for cursor positioning
# 21.03.2016 jsi:
# - blinking cursor
# - refactoring
# 22.03.2016 jsi:
# - set blink on after updating cursor_rect
# - use single shot timer for processing the terminal output queue
# 29.03.2016 jsi:
# - enable ALT keycodes 200-255
# 31.03.2016 jsi:
# - revert last change, keys > 128 are mapped to characters < 128
# 17.04.2016 jsi:
# - reduce keyboard rate for autorepeated function keys to prevent hang up:
#   type: vers$[Return] and then press left arrow for three seconds
# 05.05.2016 jsi:
# - introduced new Object class for scrollable terminal widget
# 07.05.2016 jsi:
# - introduce parameter for scroll up buffersize
# 11.07.2016 jsi:
# - refactoring: move some constants to pilcore.py
# 05.10.2016 jsi:
# - implemented redraw method to refres terminal when parent widget was resized
# 14.10.2016 jsi:
# - consistent use of namespaces, removed vars.update call in _paint screen
# 31.01.2016 jsi:
# - do not issue paint events where nothing gets painted (this cleared the display
#   on qt5 (MAC OS)
# - catch index error in HPTerminal.dump()
# 03.02.2017 jsi:
# - do not fire cursor paint event, if cursor is off
# 30.08.2017 jsi:
# - make number of rows depend of window size
# 09.09.2017 jsi:
# - fixed incorrect cursor positioning for certain font sizes
# - fixed incorrect initialization of terminal if not visible at program start
# 12.09.2017 jsi
# - partial rewrite of the backend code, various bug fixes and documentation
#   improvements
# 14.09.2017 jsi
# - rewrite of the frontend code, use QGraphicsView and QGraphicsScene
# - refactoring
# 16.10.2017 jsi
# - charconv always returns one character
# - fixed error in ctrl_CR
# - check for line length overflows
#
# to do:
# fix the reason for a possible index error in HPTerminal.dump()

import array
import queue
import threading
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from .pilcharconv import charconv, CHARSET_HP71, CHARSET_HP41, CHARSET_ROMAN8
from .pilcore import UPDATE_TIMER, CURSOR_BLINK, isMACOS, MIN_TERMCHAR_SIZE, TERMINAL_MINIMUM_ROWS,FONT

CURSOR_OFF=0
CURSOR_INSERT=1
CURSOR_OVERWRITE=2
#
# scrolled terminal widget class ----------------------------------------------------
#
class QScrolledTerminalWidget(QtWidgets.QWidget):

    def __init__(self,parent, font_size, cols, colorscheme,scrollupbuffersize):
        super().__init__(parent)
        self.pildevice= None
#
#       create terminal window and scrollbar
#
        self.hbox= QtWidgets.QHBoxLayout()
        self.terminalwidget= QTerminalWidget(self,cols,font_size, colorscheme,scrollupbuffersize)
        self.hbox.addWidget(self.terminalwidget)
        self.scrollbar= QtWidgets.QScrollBar()
        self.hbox.addWidget(self.scrollbar)
        self.setLayout(self.hbox)
        self.HPTerminal= HPTerminal(self,cols,scrollupbuffersize)
        self.terminalwidget.setHPTerminal(self.HPTerminal)
#
#       initialize scrollbar
#
        self.scrollbar.valueChanged.connect(self.do_scrollbar)
        self.scrollbar.setEnabled(False)
#
#       enable/disable
#
    def enable(self):
        self.scrollbar.setEnabled(True)
        return

    def disable(self):
        self.scrollbar.setEnabled(False)
        return
#
#      enable/disable keyboard input
#
    def enable_keyboard(self):
        self.terminalwidget.set_kbdfunc(self.pildevice.queueOutput)

    def disable_keyboard(self):
        self.terminalwidget.set_kbdfunc(None)
  
#
#   scrollbar value changed action
#
    def do_scrollbar(self):
       self.HPTerminal.scroll_to(self.scrollbar.value())
       self.scrollbar.setEnabled(True)
#
#   setting function pass through to backend
#
    def set_charset(self,charset):
        self.HPTerminal.set_charset(charset)
 
    def becomes_visible(self):
        self.HPTerminal.becomes_visible()

    def becomes_invisible(self):
        self.HPTerminal.becomes_invisible()
#
#   output character to terminal
#
    def out_terminal(self,s):
        self.HPTerminal.out_terminal(s)
#
#   reset terminal
#
    def reset_terminal(self):
        self.HPTerminal.reset_terminal()
#
#   redraw do nothing
#
    def redraw(self):
       return
#
#   set pildevice
#
    def set_pildevice(self,device):
        self.pildevice= device

#
#  terminal cursor custom class ------------------------------------------------------
#
class TermCursor(QtWidgets.QGraphicsItem):

   def __init__(self,w,h,cursortype,foregroundcolor):
      super().__init__()
      self.w=w
      self.h=h
      self.rect=QtCore.QRectF(0,0,w,h)
      self.cursorcolor=foregroundcolor
      self.cursortype=cursortype
      self.brush=QtGui.QBrush(foregroundcolor)
      self.draw=True
      self.blink_timer=QtCore.QTimer()
      self.blink_timer.setInterval(CURSOR_BLINK)
      self.blink_timer.timeout.connect(self.do_blink)
      self.blink_timer.start()
      self.insertpolygon=QtGui.QPolygon([QtCore.QPoint(0,0+(self.h/2)), QtCore.QPoint(0+(self.w*0.8),0+self.h), QtCore.QPoint(0+(self.w*0.8),0+(self.h*0.67)), QtCore.QPoint(0+self.w,0+(self.h*0.67)), QtCore.QPoint(0+self.w,0+(self.h*0.33)), QtCore.QPoint(0+(self.w*0.8),0+(self.h*0.33)), QtCore.QPoint(0+(self.w*0.8),0), QtCore.QPoint(0,0+(self.h/2))])
#
#  called when terminal widget becomes invisible, stop cursor blink
#
   def stop(self):
      self.blink_timer.stop()
#
#  called when terminal widget becomes visible, start cursor blink
#
   def start(self):
      self.blink_timer.start()
#
#  timeout procedure, switch self.draw and fire draw event
#
   def do_blink(self):
      if not self.scene():
         return
      self.draw= not self.draw
      self.update()
#
#  boundingRect and setPos are necessary for custim graphics items
#
   def boundingRect(self):
      return self.rect

   def setPos(self,x,y):
      super().setPos(x,y)
      return
#
#  paint cursor (insert or overwrite cursor)
#
   def paint(self,painter,option,widget):
      if self.draw:
         if self.cursortype== CURSOR_OVERWRITE:
            painter.setBrush(self.brush)
            painter.fillRect(0,0,self.w,self.h,self.cursorcolor)
         if self.cursortype== CURSOR_INSERT:
            painter.setBrush(self.brush)
            painter.drawPolygon(self.insertpolygon)

#
#  non scrolled terminal widget (front end) class ------------------------------------
#

class QTerminalWidget(QtWidgets.QGraphicsView):

# color scheme: normal_foreground, normal_background, inverse_foreground, inverse_background, cursor_color

    color_scheme_names = { "white" : 0, "amber" : 1, "green": 2 }

    color_schemes= [
       [ QtGui.QColor("#000"),QtGui.QColor("#fff"), QtGui.QColor(0xff,0xff, 0xff,0xc0) ],
       [ QtGui.QColor("#000"), QtGui.QColor("#ffbe00"), QtGui.QColor(0xff, 0xbe, 0x00,0xc0) ],
       [ QtGui.QColor("#000"), QtGui.QColor("#18f018"), QtGui.QColor(0x00,0xff,0x00,0xc0) ],
    ]
#
#   Keymap keycodes
#
    keymap = {
        QtCore.Qt.Key_Backspace: chr(127),
        QtCore.Qt.Key_Escape: chr(27),
        QtCore.Qt.Key_AsciiTilde: "~~",
        QtCore.Qt.Key_Up: "~A",
        QtCore.Qt.Key_Down: "~B",
        QtCore.Qt.Key_Left: "~D",
        QtCore.Qt.Key_Right: "~C",
        QtCore.Qt.Key_PageUp: "~1",
        QtCore.Qt.Key_PageDown: "~2",
        QtCore.Qt.Key_Home: "~H",
        QtCore.Qt.Key_End: "~F",
        QtCore.Qt.Key_Insert: "~3",
        QtCore.Qt.Key_Delete: "~4",
        QtCore.Qt.Key_F1: "~a",
        QtCore.Qt.Key_F2: "~b",
        QtCore.Qt.Key_F3:  "~c",
        QtCore.Qt.Key_F4:  "~d",
        QtCore.Qt.Key_F5:  "~e",
        QtCore.Qt.Key_F6:  "~f",
        QtCore.Qt.Key_F7:  "~g",
        QtCore.Qt.Key_F8:  "~h",
        QtCore.Qt.Key_F9:  "~i",
        QtCore.Qt.Key_F10:  "~j",
        QtCore.Qt.Key_F11:  "~k",
        QtCore.Qt.Key_F12:  "~l",
    }


    def __init__(self,parent, cols, font_size, colorscheme,scrollupbuffersize):
        super().__init__(parent)
#
#       set font, determine font metrics and character size in pixel
#
        self._font=QtGui.QFont(FONT)
        if font_size > MIN_TERMCHAR_SIZE:
           self._font.setPixelSize(font_size)
        metrics= QtGui.QFontMetrics(self._font)
        self._char_width=metrics.maxWidth()
        self._char_height=metrics.height()
#
#       we can't relay that the nth column begins at (n-1)*self._char_width
#       because of rounding errors, so determine the correct column position
#       the last element is used to determine the true line width
#
        s=""
        self._true_w= []
        for i in range(cols+1):
            self._true_w.append(metrics.width(s))
            s+="A"
#
#       set minimum dimensions for "cols" columns and 24 rows
#
        self._minw= self._true_w[len(self._true_w)-1] # true width
        self._minh= self._char_height* TERMINAL_MINIMUM_ROWS
#
#       calculate size hints
#
        self._sizew= self._minw
        self._sizeh= self._char_height* scrollupbuffersize
        self.setMaximumSize(self._sizew,self._sizeh)
#
#       widget cursor type
#
        self.setCursor(QtCore.Qt.IBeamCursor)
#
#       initialize Variables
#
        self._HPTerminal= None        # backend object,set by setHPterminal
        self._screen = []             # frontend screen buffer
        self._cursor_col = 0          # cursor position
        self._cursor_row = 0          # dto.
        self._kbdfunc= None           # function that is called to send keyboard input
                                      # to the loop, set by setkbdfunc
        self._alt_sequence= False     # Variables for parsing ALT keyboard sequences
        self._alt_seq_length=0        #
        self._alt_seq_value=0         #
        self._cursortype= CURSOR_OFF  # cursor mode (off, overwrite, insert)
        self._cursor_char= 0x20       # character at cursor position
        self._cursor_attr=-1          # attribute at cursor position
#
#       initialize selected color scheme
#
        self._color_scheme=self.color_schemes[self.color_scheme_names[colorscheme]]
        self._cursor_color=self._color_scheme[2]
#
#       Initialize graphics view and screne, set view background
#
        self._scene= QtWidgets.QGraphicsScene()
        self._scene.setSceneRect(0,0,self._minw,self._minh)
        self.setScene(self._scene)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(self._color_scheme[0]))
        self._cursorItem=None
#
#  overwrite standard methods
#
#   minimum size hint
#
    def minimumSizeHint(self):
        return QtCore.QSize(self._minw,self._minh)
#
#   resize event, adjust number of rows and reconfigure graphicsscene and backend
# 
    def resizeEvent(self, event):
        rows= self.height() // self._char_height
        self._HPTerminal.resize_rows(rows)
        self._scene.setSceneRect(0,0,self._sizew, self._char_height* rows)
        self.fitInView(0,0,self._sizew, self._char_height* rows)
#
#   hide/show event: stop/start timer of cursor
#
    def hideEvent(self,event):
       if self._cursorItem != None:
          self._cursorItem.stop()

    def showEvent(self,event):
       if self._cursorItem != None:
          self._cursorItem.start()
#
#   keyboard pressed event, process keys and put them into the keyboard input buffer
#
    def keyPressEvent(self, event):
        text = event.text()
        key = event.key()
        modifiers = event.modifiers()
        alt = modifiers == QtCore.Qt.AltModifier 
        if (event.isAutoRepeat() and text) or self._kbdfunc == None:
           event.accept()
           return
        if alt:
           if not self._alt_sequence:
              self._alt_sequence= True
              self._alt_seq_length=0
              self._alt_seq_value=0
           if self._alt_seq_length==0:
              if key== QtCore.Qt.Key_5:
                 self._kbdfunc(ord("["),False)
                 self._alt_sequence=False
              elif key== QtCore.Qt.Key_6:
                 self._kbdfunc(ord("]"),False)
                 self._alt_sequence=False
              elif key== QtCore.Qt.Key_7:
                 self._kbdfunc(124,False)
                 self._alt_sequence=False
              elif key== QtCore.Qt.Key_8:
                 self._kbdfunc(ord("{"),False)
                 self._alt_sequence=False
              elif key== QtCore.Qt.Key_9:
                 self._kbdfunc(ord("}"),False)
                 self._alt_sequence=False
              elif key== QtCore.Qt.Key_L:
                 self._kbdfunc(ord("@"),False)
                 self._alt_sequence=False
              elif key== QtCore.Qt.Key_I:
                 self._kbdfunc(72,True)
                 self._alt_sequence=False
              elif key== QtCore.Qt.Key_1 or key == QtCore.Qt.Key_0 :
                 self._alt_seq_value+= key - QtCore.Qt.Key_0
                 self._alt_seq_length+=1
              else:
                 self._alt_sequence=False
           else:
              if key >= QtCore.Qt.Key_0 and key <= QtCore.Qt.Key_9:
                 self._alt_seq_value*=10
                 self._alt_seq_value+= key - QtCore.Qt.Key_0
                 self._alt_seq_length+=1
                 if self._alt_seq_length == 3:
                    if self._alt_seq_value <= 127:
                       self._kbdfunc(self._alt_seq_value,False)
                    self._alt_sequence= False
              else:
                 self._alt_sequence= False
        elif text:
           t=ord(text)
           if t== 13:  # lf -> Endline
              self._kbdfunc(82, True)
           elif t== 8: # BACK  ESC Q
              self._kbdfunc(81, True)
           elif t== 127: # -CHAR ESC G
              self._kbdfunc(71, True)
           else:
              if t < 128: # > 127 generates BASIC KEYWORDS!
                 self._kbdfunc(t, False)
        else:
           s = self.keymap.get(key)
           if s:
              if s == "~A":        # cursor up ESC A
                 self._kbdfunc(65,True)
              elif s == "~B":      # cursor down ESC D
                 self._kbdfunc(68, True)
              elif s == "~C":      # cursor right ESC C
                 self._kbdfunc(67,True)
              elif s == "~D":      # cursor left ESC B
                 self._kbdfunc(66, True)
              elif s == "~3":      # I/R ESC H
                 self._kbdfunc(72, True)
              elif s == "~4":      # -CHAR ESC G
                 self._kbdfunc(71,True)
              elif s == "~1":      # Page Up ESC J
                 self._kbdfunc(74,True)
              elif s == "~2":      # Page Down ESC K
                 self._kbdfunc(75, True)
              elif s == "~H":      # Begin of line ESC E
                 self._kbdfunc(69,True)
              elif s == "~F":      # End of line ESC F
                 self._kbdfunc(70, True)
              elif s == "~a":      # F1 -> Attn ESC L
                 self._kbdfunc(76, True)
              elif s == "~b":      # F2 -> Run ESC M
                 self._kbdfunc(77, True)
              elif s == "~c":      # F3 -> Cmds ESC N
                 self._kbdfunc(78, True)
              elif s == "~d":      # F4 -> SST ESC P
                 self._kbdfunc(80, True)
              elif s == "~e":      # F5 -> -Line ESC I
                 self._kbdfunc(73, True)
              elif s == "~f":      # F6 -> LC ESC O
                 self._kbdfunc(79, True)
#             elif s == "~g":      # F7 -> Ctrl ESC S
#                self._kbdfunc(83, True)
              else:
                 pass
                
        if (event.isAutoRepeat() and not text) :
           time.sleep(0.05)
        event.accept()
#
#   External interface
#
#   make backend known to frontend
#
    def setHPTerminal(self,hpterminal):
       self._HPTerminal= hpterminal
#
#   get cursor type (insert, replace, off
#
    def getCursorType(self):
       return(self._cursortype)
#
#   set cursor type (insert, replace, off)
#
    def setCursorType(self,t):
        self._cursortype=t
#
#   register external function to process keyboard requests
#
    def set_kbdfunc(self,func):
        self._kbdfunc= func
# 
#   draw terminal content, this is called by the backend
#    
    def update_term(self,dump):
#
#      fetch screen buffer dump from backend
#
       (self._cursor_col, self._cursor_row, self._cursor_char, self._cursor_attr), self._screen = dump()
#
#      clear scene, remove and delete display items
#
       olditemlist= self._scene.items()
       for item in olditemlist:
          self._scene.removeItem(item)
          item=None
       self._cursorItem=None
       y=0
       text=[]
#
#      initialize attributes (bg/fg-color, invers attribute
#
       background_color = self._color_scheme[0]
       foreground_color = self._color_scheme[1]
       fgbrush=QtGui.QBrush(foreground_color)
       invers_flag=False
#
#      loop over each row
#
       for row,line in enumerate(self._screen):
          col=0
          text_line=""
#
#         loop over each item in a row
#
          for item in line:
#
#             item is a string
#
              if isinstance (item,str):
                 x=self._true_w[col]
                 length= len(item)
#
#                if inverse flag set, add background rectangle to scene
#
                 if invers_flag:
                    fillItem=QtWidgets.QGraphicsRectItem(0,0,self._true_w[col+length]- self._true_w[col],self._char_height)
                    fillItem.setBrush(bgbrush)
                    fillItem.setPos(x,y)
                    self._scene.addItem(fillItem)
#
#                add text to scene
#
                 txtItem=QtWidgets.QGraphicsSimpleTextItem(item)
                 txtItem.setFont(self._font)
                 txtItem.setPos(x,y)
                 txtItem.setBrush(fgbrush)
                 self._scene.addItem(txtItem)
                 col += length
              else:
#
#                item is attribute, set fg/bg color
# 
                 invers_flag = item
                 if invers_flag:
                    background_color = self._color_scheme[1]
                    foreground_color = self._color_scheme[0]
                 else:
                    background_color = self._color_scheme[0]
                    foreground_color = self._color_scheme[1]
                 fgbrush=QtGui.QBrush(foreground_color)
                 bgbrush=QtGui.QBrush(background_color)
          y += self._char_height
#
#      add cursor at cursor position to scene
#
       if self._cursortype != CURSOR_OFF:
          if self._cursor_attr:
             cursor_foreground_color= self._color_scheme[0]
          else:
             cursor_foreground_color= self._color_scheme[1]
          self._cursorItem= TermCursor(self._char_width,self._char_height,self._cursortype, cursor_foreground_color)
          self._cursorItem.setPos(self._true_w[self._cursor_col],self._cursor_row*self._char_height)
          self._scene.addItem(self._cursorItem)
#
# Terminal backend class -----------------------------------------------------------
#
# The terminal backend class maintains the terminal line buffer. The terminal
# line buffer content is arranged by the input of text and escape sequences that
# control editing and and the cursor position.
# The backend class also maintains the boundaries of the visible part of the
# line buffer that is rendered by the frontend widget and sets the scrollbar parameters.
#
class HPTerminal:

    def __init__(self, win, w,scrollupbuffersize):
        self.w = w                        # terminal/buffer width (characters)
        self.h = scrollupbuffersize       # buffer size (lines)
        self.actual_h=0                   # number of lines in the buffer
        self.fesc= False                  # status indicator for parsing esc 
                                          # sequences
        self.movecursor= 0                # status indicator for parsing the
                                          # move cursor escape sequence
        self.movecol=0                    # same as above
        self.win=win                      # terminal widget
        self.view_h= 0                    # terminal size (lines)
                                          # initialized if window was resized
        self.view_y0=0                    # bottom of buffer view
        self.view_y1=0                    # top of buffer view
        self.blink_counter=0              # counter that controls cursor blink
        self.charset=CHARSET_HP71         # character set used for output
        self.cx=0                         # actual cursor position
        self.cy=0 
        self.insert=False                 # inser mode flag
        self.attr = 0x00000000            # character attribute mask:
                                          # Bit 0 - Underlined (not used)
                                          # Bit 1 - Negative
                                          # Bit 2 - Concealed (not used)
        self.screen=None                  # Terminal line buffer array
                                          # initialized by reset_screen
        self.linelength=None              # Vector with length of each line
                                          # in the buffer array, initialized
                                          # by reset screen
                                          # a value of -1 indicates a continuation
                                          # line of a wrapped line
        self.reset_hard()
#
#       Queue with input data that will be displayed
#
        self.termqueue= queue.Queue()
        self.termqueue_lock= threading.Lock()
#
#       Timer that triggers the processing of the input queue
#
        self.UpdateTimer= QtCore.QTimer()
        self.UpdateTimer.setSingleShot(True)
        self.UpdateTimer.timeout.connect(self.process_queue)
#
#   Reset functions
#
    def reset_hard(self):
        self.attr = 0x00000000
        # Invoke other resets
        self.reset_screen()
        self.reset_soft()

    def reset_soft(self):
        self.attr = 0x00000000
        # Scroll parameters
        # Modes
        self.insert = False
        self.movecursor=0

    def reset_screen(self):
        # Screen
        self.screen = array.array('i', [self.attr | 0x20] * self.w * self.h)
        self.linelength= array.array('i', [0] * self.h)
        self.linewrapped= array.array('i',[False] * self.h)
        # Scroll parameters
        self.view_y0=0
        self.view_y1= self.view_h-1

        # Cursor position
        self.cx = 0
        self.cy = 0
        self.movecursor=0

        # Number of lines and scroll bar
        self.actual_h=0
        self.win.scrollbar.setMinimum(0)
        self.win.scrollbar.setMaximum(0)
        self.win.scrollbar.setSingleStep(1)
        self.win.scrollbar.setPageStep(self.view_h)
#
#   Terminal window was resized, update display and scrollbar
#
    def resize_rows(self,rows):
        if self.view_h == rows:
           return
        self.view_h= rows
        if self.view_y1 == -1:
           self.view_y1 = self.view_h-1
        if self.view_y1 > rows:
           self.view_y1= rows-1
        self.view_y0= self.view_y1-rows
        if self.view_y0<0:
           self.view_y0=0
        if self.actual_h >= self.view_h:
           self.win.scrollbar.setMaximum(self.actual_h-self.view_h+1)
        self.win.scrollbar.setPageStep(self.view_h)
        self.win.scrollbar.setValue(self.win.scrollbar.maximum())
        self.win.terminalwidget.update_term(self.dump)
#
#   Low-level terminal functions on terminal line buffer
#
    def peek(self, y0, x0, y1, x1):
        return self.screen[self.w * y0 + x0:self.w * (y1 - 1) + x1]

    def poke(self, y, x, s):
        pos = self.w * y + x
        self.screen[pos:pos + len(s)] = s

    def fill(self, y0, x0, y1, x1, char):
        n = self.w * (y1 - y0 - 1) + (x1 - x0)
        self.poke(y0, x0, array.array('i', [char] * n))

    def clear(self, y0, x0, y1, x1):
        self.fill(y0, x0, y1, x1, self.attr | 0x20)
#
#   utility functions for wrapped lines
#
#   get length of a wrapped line
#
    def get_wrapped_linelength(self,cy):
       if self.linelength[cy]==-1:
          return(self.linelength[cy-1])
       else:
          return(self.linelength[cy])
#
#   set length of a wrapped line
#
    def set_wrapped_linelength(self,cy,ll):
       if self.linelength[cy]==-1:
          self.linelength[cy-1]= ll
       else:
          self.linelength[cy]= ll
#
#   get the position of the cursor in the wrapped line
#
    def get_wrapped_cursor_x(self,cx,cy):
       if self.linelength[cy]==-1:
          return(cx+self.w)
       else:
          return(cx)
#
#   check if line is wrapped, cursor may or may not be in the wrapped part
#
    def is_wrapped(self,cy):
       if self.linelength[cy]==-1:
          return(self.linewrapped[cy-1])
       else:
          return(self.linewrapped[cy])
#
#   check, if cursor position is in the wrapped part
#
    def in_wrapped_part(self,cy):
       return(self.linelength[cy]== -1)
#
#   add wrapped part of a line, cy must be in the wrapped part
#
    def add_wrapped_part(self,cy):
       self.linewrapped[cy-1]=True
       self.linelength[cy]=-1
       self.linewrapped[cy]=False
#
#   remove wrapped part of a line, cy must be in the non wrapped part
#
    def remove_wrapped_part(self,cy):
       self.linewrapped[cy]=False
       self.linelength[cy+1]=0
       self.linewrapped[cy+1]=False
#
#   scroll screen buffer up if no room to add a new line
#   note: this adjust the object variables self.cy and self.actual_h
#   the method returns the new value of self.cy
#
    def scroll_screenbuffer_up(self,n):
        self.poke(0, 0, self.peek(0 + n, 0, self.h, self.w))
        self.clear(self.h - n, 0, self.h, self.w)
        self.linelength[0:self.h-n]=self.linelength[n:]
        self.linewrapped[0:self.h-n]=self.linewrapped[n:]
        for i in range(n):
           self.linelength[self.h-n]=0
           self.linewrapped[self.h-n]=False
        self.cy-=n
        self.actual_h-=n
        return(self.cy)
#
# Scroll line right, add wrapped part if needed. If we exceed the length of the
# wrapped line, ignore characters
#
    def scroll_line_right(self, y, x):
        wx= self.get_wrapped_cursor_x(x,y)
        oldlinelength= self.get_wrapped_linelength(y)
        if oldlinelength == self.w*2:
           return
        if wx  < oldlinelength:
           newlinelength= oldlinelength+1
           self.set_wrapped_linelength(y,newlinelength)
#
#          move characters in wrapped part, add wrapped part if needed
#
           if self.get_wrapped_linelength(y) > self.w:
              if oldlinelength== self.w:
                 self.cy=self.add_bufferline(self.cy)
                 self.add_wrapped_part(self.cy)
                 y=self.cy
              self.poke(y+1,1,self.peek(y+1, 0, y + 2, self.w))
              self.poke(y+1,0,self.peek(y,self.w-1,y+1,self.w))
           self.poke(y, x + 1, self.peek(y, x, y + 1, self.w - 1))
           self.clear(y, x, y + 1, x + 1)
#
#   scroll line left, remove character at cursor position
#
    def scroll_line_left(self, y, x):
        wx= self.get_wrapped_cursor_x(x,y)
        oldlinelength= self.get_wrapped_linelength(y)
        if wx  < oldlinelength:
#
#           remove character, shift left, adjust line length
#
            self.poke(y, x, self.peek(y, x + 1, y + 1, self.w))
            self.clear(y, self.w - 1, y + 1, self.w)
            self.set_wrapped_linelength(y,oldlinelength-1)
#
#           we are in a wrapped line and must move the wrapped part too.
#
            if oldlinelength > self.w:
               self.poke(y,self.w-1,self.peek(y+1,0,y+2,1))
               self.poke(y+1, 0, self.peek(y+1, 1, y + 2, self.w))
#
#           if the wrapped part is empty and the cursor is in the non wrapped part
#           remove the wrapped part
# 
            if oldlinelength-1<= self.w and wx< self.w and self.is_wrapped(y):
               self.remove_wrapped_part(y)
               self.cy=self.remove_bufferline(y+1)
#
#   View functions, scroll up and down
#
    def scroll_view_down(self):
       if self.view_y1< self.cy:
          self.view_y0+=1
          self.view_y1+=1

    def scroll_view_up(self):
       if self.view_y0 >0:
          self.view_y0-=1
          self.view_y1-=1
#
#   scroll to the last line of the buffer
#
    def scroll_view_to_bottom(self):
       self.win.scrollbar.setValue(self.win.scrollbar.maximum())
       return
#
#   add new buffer line, scroll up the screen line buffer if needed
#   note: this adjusts the object variables self.cy and self.last_h
#   the scrollbar is adjusted to the new size of the screen line buffer
#
    def add_bufferline(self,cy):
       n=1
#      if self.is_wrapped(0):
#         n=2
       newcy=cy+1
       if newcy < self.h:
          self.actual_h= max(self.actual_h, newcy)
       if newcy == self.h:
          newcy=self.scroll_screenbuffer_up(n)+1
          self.actual_h+=1
       self.update_scrollbar()
       return(newcy)
#
#  remove buffer line
#
    def remove_bufferline(self,cy):
       newcy= cy-1
       self.actual_h= newcy
       self.update_scrollbar()
       return(newcy)
#
#   Update scroll bar parameters
#       
    def update_scrollbar(self):
        if self.actual_h < self.view_h:
           self.win.scrollbar.setMaximum(0)
        else:
           self.win.scrollbar.setMaximum(self.actual_h-self.view_h+1)
           self.win.scrollbar.setValue(self.actual_h)
#
#   Cursor functions, up and down
#
    def cursor_up(self):
        self.cy = max(0, self.cy - 1)

    def cursor_down(self):
      self.cy = min(self.h - 1, self.cy + 1)
#
# Move cursor left, if the cursor is at the beginning of the wrapped part of a line
# then remove that wrapped part
#
    def cursor_left(self):
        self.cx= self.cx -1
        if self.cx < 0:
           self.cx= self.w-1
           self.cy= self.cy-1
           if self.cy < 0:
              self.cy=0
              self.cx=0
           if self.get_wrapped_linelength(self.cy) <= self.w and self.is_wrapped(self.cy):
              self.remove_wrapped_part(self.cy)
              self.cy=self.remove_bufferline(self.cy+1)
#
#   move cursor right, add wrapped part of a line if needed
#
    def cursor_right(self):
        self.cx= self.cx +1
        if self.cx == self.w:
           self.cx=0
           if self.get_wrapped_linelength(self.cy)== self.w and not self.is_wrapped(self.cy):
              self.cy=self.add_bufferline(self.cy)
              self.add_wrapped_part(self.cy)

    def cursor_set_x(self, x):
        self.cx = max(0, x)

    def cursor_set_y(self, y):
        self.cy = max(0, min(self.h - 1, y))

    def cursor_set(self, y, x):
        self.cursor_set_x(x)
        self.cursor_set_y(y)

    def cursor_far_left(self):
        if self.linelength[self.cy] == -1:
           self.cursor_set(self.cy-1,0)
        else:
           self.cursor_set(self.cy,0)

    def cursor_far_right(self):
        if self.linelength[self.cy] == -1:
           self.cursor_set(self.cy, (self.linelengt[self.cy-1]-self.w-1))
        else:
           self.cursor_set(self.cy, (self.linelength[self.cy]-1))
#
#   Dumb terminal output
#
#   Backspace
#
    def ctrl_BS(self):
        cx= self.cx-1
        cy= self.cy
        if cx < 0:
           cy= cy-1
           if cy < 0:
              cx=0
              cy=0
           else:
              cx=self.w-1
        self.cursor_set(cy, cx)
#
#   Linefeed
#
    def ctrl_LF(self):
        if self.is_wrapped(self.cy)  and not self.in_wrapped_part(self.cy):
           self.cy+=1
        self.cy=self.add_bufferline(self.cy)
#
#   Carriage Return
#
    def ctrl_CR(self):
        if self.is_wrapped(self.cy) and self.in_wrapped_part(self.cy):
           self.cy-=1
        self.cursor_set_x(0)
#
#   Dumb echo, if we exceed the wrapped part then issue a CR/LF
#
    def dumb_echo(self, char):
        if self.insert:
           self.scroll_line_right(self.cy, self.cx)
           self.poke(self.cy, self.cx, array.array('i', [self.attr | char]))
        else:
           oldwrappedlinelength=self.get_wrapped_linelength(self.cy)
           if oldwrappedlinelength == self.w*2:
              self.ctrl_CR()
              self.ctrl_LF()
           self.poke(self.cy, self.cx, array.array('i', [self.attr | char]))
           self.set_wrapped_linelength(self.cy,oldwrappedlinelength+1)
        self.cursor_right()
#
#   dump screen to terminal window, the data are painted during a paint event
#
    def dump(self):
        screen = []
        attr_ = -1
        cursor_char=0x20
        cursor_attr= -1
        cx, cy = min(self.cx, self.w - 1), self.cy
        for y in range(self.view_y0, self.view_y1+1):
            wx = 0
            line = [""]
            for x in range(0, self.w):
                try:
                   d = self.screen[y * self.w + x] # fix possible index out of range error
                except IndexError:
                   print("self.screen Index error %d %d"% (y,x))
                   continue
                char = d & 0xffff
                attr = d >> 16
                if x== cx and y== cy:
                   cursor_char=char
                   cursor_attr=attr
                # Attributes (inverse only)
                if attr != attr_:
                    if attr_ != -1:
                        line.append("")
                    # Inverse
                    inv = attr & 0x0200
                    line.append(inv)
                    line.append("")
                    attr_ = attr
                wx += 1
                if wx <= self.w:
                    line[-1] += chr(char)
            screen.append(line)

        if cy >= self.view_y0 and cy <= self.view_y1:
           cy= cy- self.view_y0
        else:
           cy= -1
           cx= -1

        return (cx, cy, cursor_char, cursor_attr), screen
#
#   process terminal output queue and refresh display
#        
    def process_queue(self):
       items=[]
#
#      get items from terminal input queue
#
       self.termqueue_lock.acquire()
       while True:
          try:
             i=self.termqueue.get_nowait()
             items.append(i)
             self.termqueue.task_done()
          except queue.Empty:
             break
       self.termqueue_lock.release()
#
#      process items and generate new terminal screen dump
#
       if len(items):
          for c in items:
             self.process(c)
          self.win.terminalwidget.update_term(self.dump)
       self.UpdateTimer.start(UPDATE_TIMER)
       return
#
#   process keyboard input
# 
    def process(self,c):
 
       t=ord(c)
#
#      start of ESC sequence, set flag and return
#
       if t == 27:
          self.fesc= True
          return
#
#      process escape sequences, translate to pyqterm
#
       if self.fesc:
          if t== 67: # cursor right (ESC C)
             self.cursor_right()
          elif t== 68: # cursor left (ESC D)
             self.cursor_left()
          elif t== 65: # cursor up (ESC A)
             self.cursor_up()
          elif t== 66: # cursor down (ESC B)
             self.cursor_down()
          elif t== 72: # move cursor to home position (ESC H)
             self.cursor_set(0,0)
          elif t== 74: # erase from cursor to end of screen (ESC J)
             self.clear(self.cy,self.cx,self.h, self.w)
          elif t== 75: # erase from cursor to end of the line (ESC K)
             self.clear(self.cy,self.cx,self.cy+1,self.w)
          elif t== 62: # Cursor on (ESC >)
             if self.insert:
                self.win.terminalwidget.setCursorType(CURSOR_INSERT)
             else:
                self.win.terminalwidget.setCursorType(CURSOR_OVERWRITE)
          elif t== 60: # Cursor off (ESC <)
             self.win.terminalwidget.setCursorType(CURSOR_OFF)
          elif t== 69: # Reset (ESC E)
             self.reset_soft()
             self.reset_screen()
          elif t== 80: # Clear Character (ESC P) ??
             self.clear(self.cy,self.cx,self.cy+1,self.cx+1)
          elif t== 79: # Clear Character with wrap back (ESC O)
             self.scroll_line_left(self.cy, self.cx)
          elif t== 81: # switch to insert cursor (ESC Q)
             self.win.terminalwidget.setCursorType(CURSOR_INSERT)
             self.insert = True
          elif t== 78: # swicht to insert cursor and insert mode (ESC N)
             self.insert = True
             self.win.terminalwidget.setCursorType(CURSOR_INSERT)
          elif t== 82: # switch to replace cursor and replace mode (ESC R)
             self.insert = False
             self.win.terminalwidget.setCursorType(CURSOR_OVERWRITE)
          elif t== 83: # roll up (ESC S)
             self.scroll_view_up()
          elif t== 84: # roll down (ESC T)
             self.scroll_view_down()
          elif t== 101: # reset hard (ESC e)
             self.reset_hard()
          elif t== 3:  # move cursor far right (ESC Ctrl c)
             self.cursor_far_right()
          elif t== 4:  # move cursor far left (ESC ctrl d)
             self.cursor_far_left()
          elif t== 37: # Move Cursor to display position (ESC %)
             self.movecursor=1
          elif t==122:  # reset
             self.reset_hard()
          else:
             print("unhandled escape sequence %d" % t)
          self.fesc= False

       else:
#
#      Move cursor sequence part 1
#
          if self.movecursor == 1:
             self.movecursor=2
             self.movecol=t

#
#      Move cursor sequence part 2
#
          elif self.movecursor == 2:
             self.movecursor=0
             if self.movecol < self.w and t < self.h:
                self.cursor_set(t,self.movecol)
#
#     single character processing
# 
          else:
             self.scroll_view_to_bottom()
             if t == 0xD:      # CR
                self.ctrl_CR()
             elif t == 0xA:    # LF
                self.ctrl_LF()
             elif t== 0x08:    # BS
                self.ctrl_BS()
             elif t== 0x7F:    # DEL
                self.clear(self.cy, self.cx, self.cy+1, self.cx+1)
             else:
                cc= charconv(c,self.charset)
                if t > 127 and (not self.charset == CHARSET_ROMAN8):
                   self.attr |= 0x02000000
                self.dumb_echo(ord(cc)) 
                self.attr = 0x00000000
       return
 
#
#   External interface
#
#
#   set character set
#
    def set_charset(self,charset):
       self.charset= charset
#
#   put character into terminal output buffer
# 
    def out_terminal (self,c):
       self.termqueue_lock.acquire()
       self.termqueue.put(c)
       self.termqueue_lock.release()
#
#   reset terminal
# 
    def reset_terminal(self):
       self.termqueue_lock.acquire()
       self.termqueue.put("\x1b")
       self.termqueue.put("e")
       self.termqueue_lock.release()
#
#    becomes visible
#
    def becomes_visible(self):
       self.UpdateTimer.start(UPDATE_TIMER)
#      self.win.terminalwidget.update_term(self.dump)
#
#    becomes_invisible(self):
#
    def becomes_invisible(self):
       pass
#
#    callback for scrollbar
#
    def scroll_to(self,value):
       self.view_y0= value
       self.view_y1= value + self.view_h-1
       self.win.terminalwidget.update_term(self.dump)
