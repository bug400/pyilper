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

import array
import queue
import threading
import time

from PyQt4.QtCore import QRect, Qt, pyqtSignal, QTimer, QSize, QPoint
from PyQt4.QtGui import (
    QApplication, QClipboard, QWidget, QPainter, QFont, QBrush, QColor, QPolygon,
    QPen, QPixmap, QImage, QContextMenuEvent, QTransform, QHBoxLayout, QScrollBar,
    QFontMetrics)
from .pilcharconv import charconv, CHARSET_HP71, CHARSET_HP41, CHARSET_ROMAN8


CURSOR_OFF=0
CURSOR_INSERT=1
CURSOR_OVERWRITE=2
UPDATE_TIMER=25                 # Poll timer (ms) for terminal output queue
CURSOR_BLINK=500 / UPDATE_TIMER # 500 ms cursor blink rate

class QScrolledTerminalWidget(QWidget):

    def __init__(self,parent, font_name, font_size, cols, rows, colorscheme):
        super().__init__(parent)
        self.callback_scrollbar= None
#
#       determine font metrics and terminal window size in pixel
#
        font= QFont(font_name)
        font.setPixelSize(font_size)
        metrics= QFontMetrics(font)
        font_width=metrics.width("A")
        font_height=metrics.height()
        width= font_width*cols
        height= int(font_height* rows)
#
#       create terminal window and scrollbar
#
        self.hbox= QHBoxLayout()
        self.terminalwidget= QTerminalWidget(self,font_name,font_size,font_height, width,height, colorscheme)
        self.hbox.addWidget(self.terminalwidget)
        self.hbox.setAlignment(self.terminalwidget,Qt.AlignLeft)
        self.scrollbar= QScrollBar()
        self.hbox.addWidget(self.scrollbar)
        self.hbox.setAlignment(self.scrollbar,Qt.AlignLeft)
        self.setLayout(self.hbox)
#
#       initialize scrollbar
#
        self.scrollbar.valueChanged.connect(self.do_scrollbar)
        self.scrollbar.setEnabled(False)
#
#   scrollbar value changed action
#
    def do_scrollbar(self):
       self.callback_scrollbar(self.scrollbar.value())
#
#   register callback for scrolling
#
    def register_callback_scrollbar(self,func):
        self.callback_scrollbar=func
        self.scrollbar.setEnabled(True)

class QTerminalWidget(QWidget):

# color scheme: normal_foreground, normal_background, inverse_foreground, inverse_background, cursor_color

    color_scheme_names = { "white" : 0, "amber" : 1, "green": 2 }

    color_schemes= [
       [ QColor("#000"),QColor("#fff"), QColor(0xff,0xff, 0xff,0xc0) ],
       [ QColor("#000"), QColor("#ffbe00"), QColor(0xff, 0xbe, 0x00,0xc0) ],
       [ QColor("#000"), QColor("#18f018"), QColor(0x00,0xff,0x00,0xc0) ],
    ]
#
#   Keymap keycodes
#
    keymap = {
        Qt.Key_Backspace: chr(127),
        Qt.Key_Escape: chr(27),
        Qt.Key_AsciiTilde: "~~",
        Qt.Key_Up: "~A",
        Qt.Key_Down: "~B",
        Qt.Key_Left: "~D",
        Qt.Key_Right: "~C",
        Qt.Key_PageUp: "~1",
        Qt.Key_PageDown: "~2",
        Qt.Key_Home: "~H",
        Qt.Key_End: "~F",
        Qt.Key_Insert: "~3",
        Qt.Key_Delete: "~4",
        Qt.Key_F1: "~a",
        Qt.Key_F2: "~b",
        Qt.Key_F3:  "~c",
        Qt.Key_F4:  "~d",
        Qt.Key_F5:  "~e",
        Qt.Key_F6:  "~f",
        Qt.Key_F7:  "~g",
        Qt.Key_F8:  "~h",
        Qt.Key_F9:  "~i",
        Qt.Key_F10:  "~j",
        Qt.Key_F11:  "~k",
        Qt.Key_F12:  "~l",
    }


    def __init__(self,parent, font_name, font_size, font_height, w,h, colorscheme):
        super().__init__(parent)
        self.setFocusPolicy(Qt.WheelFocus)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setCursor(Qt.IBeamCursor)
        font = QFont(font_name)
        font.setPixelSize(font_size)
        self.setFont(font)
        self._screen = []
        self._text = []
        self._transform= QTransform()
        self._cursor_col = 0
        self._cursor_row = 0
        self._dirty = False
        self._kbdfunc= None
        self._w=w
        self._h=h
        self._alt_sequence= False
        self._alt_seq_length=0
        self._alt_seq_value=0
        self._cursortype= CURSOR_OFF
        self._color_scheme=self.color_schemes[self.color_scheme_names[colorscheme]]
        self._cursor_color=self._color_scheme[2]
        self._cursor_char= 0x20
        self._cursor_attr=-1
        self._cursor_update=True
        self._blink= True
        self._blink_counter=0
        self._cursor_rect = QRect(0, 0, self._char_width, self._char_height)
        self._cursor_polygon=QPolygon([QPoint(0,0+(self._char_height/2)), QPoint(0+(self._char_width*0.8),0+self._char_height), QPoint(0+(self._char_width*0.8),0+(self._char_height*0.67)), QPoint(0+self._char_width,0+(self._char_height*0.67)), QPoint(0+self._char_width,0+(self._char_height*0.33)), QPoint(0+(self._char_width*0.8),0+(self._char_height*0.33)), QPoint(0+(self._char_width*0.8),0), QPoint(0,0+(self._char_height/2))])
#
#  overwrite standard methods
#

    def sizeHint(self):
        return QSize(self._w,self._h)

    def minimumSizeHint(self):
        return QSize(self._w,self._h)

    def resizeEvent(self, event):
        self.resize(self._w, self._h)

    def setkbdfunc(self,func):
        self._kbdfunc= func

    def setFont(self, font):
        super().setFont(font)
        self._update_metrics()
#
#   overwrite standard events
#
#
#   Paint event, this event repaints the screen if the screen memory was changed or
#   paints the cursor
#   This event is fired if
#   - the terminal window becomes visible again
#   - after processing a new key in the termianl output queue 
#
    def paintEvent(self, event):
        painter = QPainter(self)
        if self._dirty:
            self._dirty = False
            self._paint_screen(painter)
        else:
            self._blink_counter+=1
            if self._blink_counter > CURSOR_BLINK:
               self._blink_counter=0
               self._paint_cursor(painter)
        event.accept()
#
#   keyboard pressed event, process keys and put them into the keyboard input buffer
#
    def keyPressEvent(self, event):
        text = event.text()
        key = event.key()
        modifiers = event.modifiers()
        alt = modifiers == Qt.AltModifier 
        if (event.isAutoRepeat() and text) or self._kbdfunc == None:
           event.accept()
           return
        if alt:
           if not self._alt_sequence:
              self._alt_sequence= True
              self._alt_seq_length=0
              self._alt_seq_value=0
           if self._alt_seq_length==0:
              if key== Qt.Key_5:
                 self._kbdfunc(ord("["),False)
                 self._alt_sequence=False
              elif key== Qt.Key_6:
                 self._kbdfunc(ord("]"),False)
                 self._alt_sequence=False
              elif key== Qt.Key_7:
                 self._kbdfunc(124,False)
                 self._alt_sequence=False
              elif key== Qt.Key_8:
                 self._kbdfunc(ord("{"),False)
                 self._alt_sequence=False
              elif key== Qt.Key_9:
                 self._kbdfunc(ord("}"),False)
                 self._alt_sequence=False
              elif key== Qt.Key_L:
                 self._kbdfunc(ord("@"),False)
                 self._alt_sequence=False
              elif key== Qt.Key_I:
                 self._kbdfunc(72,True)
                 self._alt_sequence=False
              elif key== Qt.Key_1 or key == Qt.Key_0 :
                 self._alt_seq_value+= key - Qt.Key_0
                 self._alt_seq_length+=1
              else:
                 self._alt_sequence=False
           else:
              if key >= Qt.Key_0 and key <= Qt.Key_9:
                 self._alt_seq_value*=10
                 self._alt_seq_value+= key - Qt.Key_0
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
#   internal methods
#
    def _update_metrics(self):
        fm = self.fontMetrics()
        self._char_height = fm.height()
        self._char_width = fm.width("W")
#
#  update cursor position
#
    def _update_cursor_rect(self):
        if self._cursortype== CURSOR_OFF or (self._cursor_col== -1 and self._cursor_row==-1):
           return
        cx, cy = self._pos2pixel(self._cursor_col, self._cursor_row)
        self._transform.reset()
        self._transform.translate(cx,cy)
        self._cursor_update=True
        self._blink=True
#
#   determine pixel position from rowl, column
#
    def _pos2pixel(self, col, row):
        x = (col * self._char_width)
        y = row * self._char_height
        return x, y
#
#   paint cursor
#
    def _paint_cursor(self, painter):
        if self._cursortype== CURSOR_OFF or (self._cursor_col== -1 and self._cursor_row==-1):
           return
#
#       cursor position was updated initialize some variables
#
        if self._cursor_update:
           self._cursor_update= False
           self._blink_brush=QBrush(self._cursor_color)
           self._blink_pen=QPen(self._cursor_color)
           self._blink_pen.setStyle(0)
           if self._cursor_attr:
              self._noblink_background_color = self._color_scheme[1]
              self._noblink_foreground_color = self._color_scheme[0]
           else:
              self._noblink_background_color = self._color_scheme[0]
              self._noblink_foreground_color = self._color_scheme[1]
           self._noblink_brush = QBrush(self._noblink_background_color)
#
#       blink on: draw cursor
#
        if self._blink:
           painter.setPen(self._blink_pen)
           painter.setBrush(self._blink_brush)
           painter.setTransform(self._transform)
           if self._cursortype== CURSOR_OVERWRITE:
              painter.drawRect(self._cursor_rect)
           else:
              painter.drawPolygon(self._cursor_polygon)
           self._blink= not self._blink
#
#       blink off: draw character
#
        else:
           painter.setBrush(self._noblink_brush)
           painter.setTransform(self._transform)
           painter.setPen(QPen(self._noblink_background_color))
           painter.drawRect(self._cursor_rect)
           painter.fillRect(self._cursor_rect, self._noblink_brush)
           painter.setPen(QPen(self._noblink_foreground_color))
           painter.drawText(self._cursor_rect,Qt.AlignTop | Qt.AlignLeft,chr(self._cursor_char))
           self._blink= not self._blink
#
#   paint screen from screen memory 
#
    def _paint_screen(self, painter):
        # Speed hacks: local name lookups are faster
        vars().update(QColor=QColor, QBrush=QBrush, QPen=QPen, QRect=QRect)
        char_width = self._char_width
        char_height = self._char_height
        painter_drawText = painter.drawText
        painter_fillRect = painter.fillRect
        painter_setPen = painter.setPen
        align = Qt.AlignTop | Qt.AlignLeft
        color_scheme= self._color_scheme
        # set defaults
        background_color = color_scheme[1]
        foreground_color = color_scheme[0]
        brush = QBrush(background_color)
        painter_fillRect(self.rect(), brush)
        pen = QPen(foreground_color)
        painter_setPen(pen)
        y = 0
        text = []
        text_append = text.append
        for row, line in enumerate(self._screen):
            col = 0
            text_line = ""
            for item in line:
                if isinstance(item, str):
                    x = col * char_width
                    length = len(item)
                    rect = QRect(
                        x, y, x + char_width * length, y + char_height)
                    painter_fillRect(rect, brush)
                    painter_drawText(rect, align, item)
                    col += length
                    text_line += item
                else:
                    invers_flag = item
                    if invers_flag:
                       background_color = color_scheme[1]
                       foreground_color = color_scheme[0]
                    else:
                       background_color = color_scheme[0]
                       foreground_color = color_scheme[1]
                    pen = QPen(foreground_color)
                    brush = QBrush(background_color)
                    painter_setPen(pen)
                    painter.setBrush(brush)
            y += char_height
            text_append(text_line)
        self._text = text
#
#   external interface
#
#   set cursor type (insert, replace, off)
#
    def setCursorType(self,t):
        self._cursortype=t

#:
#   get terminal memory and cursor information
#    
    def update_term(self,dump):
        (self._cursor_col, self._cursor_row, self._cursor_char, self._cursor_attr), self._screen = dump()
        self._update_cursor_rect()
        self._dirty = True

    def setDirty(self):
        self._dirty= True


class HPTerminal:

    def __init__(self, w, h, scrollupbuffersize,win):
        self.w = w
        self.h = scrollupbuffersize
        self.actual_h=0
        self.termqueue= queue.Queue()
        self.termqueue_lock= threading.Lock()
        self.fesc= False
        self.movecursor= 0
        self.movecol=0
        self.UpdateTimer= QTimer()
        self.UpdateTimer.setSingleShot(True)
        self.UpdateTimer.timeout.connect(self.process_queue)
        self.win=win
        self.view_h= h
        self.view_y0=0
        self.view_y1=self.view_h-1
        self.charset=CHARSET_HP71
        self.update_win= False
        self.reset_hard()
        self.win.register_callback_scrollbar(self.scroll_to)
        self.UpdateTimer.start(UPDATE_TIMER)
#
#   Reset functions
#
    def reset_hard(self):
        # Attribute mask: 0x0X000000
        #	X:	Bit 0 - Underlined (not used)
        #		Bit 1 - Negative
        #		Bit 2 - Concealed (not used)
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
#   Low-level terminal functions
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
#   Scrolling functions
#
    def scroll_area_up(self, y0, y1):
        n = 1
        self.poke(y0, 0, self.peek(y0 + n, 0, y1, self.w))
        self.clear(y1 - n, 0, y1, self.w)
        self.linelength[0:self.h-1]=self.linelength[1:]
        self.linelength[self.h-1]=0

    def scroll_line_right(self, y, x):
        if x < self.w:
            # scroll up needed?
            if self.linelength[y] > self.w and y== self.h-1:
               self.scroll_area_up(0, self.h)
               y=y-1
               self.cy=self.cy-1
               self.linelength[y+1]=-1

            # wrap line
            if self.linelength[y] > self.w:
               self.poke(y+1,1,self.peek(y+1, 0, y + 2, self.w))
               self.poke(y+1,0,self.peek(y,self.w-1,y+1,self.w))
               if self.linelength[y] == self.w+1:
                  self.scroll_view_down()
                  self.update_size(1)
            self.poke(y, x + 1, self.peek(y, x, y + 1, self.w - 1))
            self.clear(y, x, y + 1, x + 1)

    def scroll_line_left(self, y, x):
        if x < self.w:
            self.poke(y, x, self.peek(y, x + 1, y + 1, self.w))
            self.clear(y, self.w - 1, y + 1, self.w)
            # wrapped line
            if self.linelength[y] > self.w:
               self.poke(y,self.w-1,self.peek(y+1,0,y+2,1))
               self.poke(y+1, 0, self.peek(y+1, 1, y + 2, self.w))
               if self.linelength[y]== self.w+1:
                  self.linelength[y+1]=0
                  self.scroll_view_up()
                  self.update_size(-1)
            self.linelength[y]-=1
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

    def update_size(self,n):
        if n > 0:
           if self.actual_h < self.h:
              self.actual_h=self.actual_h+1
        else:
           if self.actual_h > 0:
              self.actual_h=self.actual_h-1
        if self.actual_h < self.view_h:
           self.win.scrollbar.setMaximum(0)
        else:
           self.win.scrollbar.setMaximum(self.actual_h-self.view_h+1)
           self.win.scrollbar.setValue(self.actual_h)


    def scroll_view_to_bottom(self):
       self.win.scrollbar.setValue(self.win.scrollbar.maximum())
       return
       
#
#   Cursor functions
#

    def utf8_charwidth(self, char):
        if char == 0x0304:
            return 0
        if char >= 0x2e80:
            return 2
        else:
            return 1

    def cursor_line_width(self, next_char):
        wx = self.utf8_charwidth(next_char)
        lx = 0
        for x in range(min(self.cx, self.w)):
            char = self.peek(self.cy, x, self.cy + 1, x + 1)[0] & 0xffff
            wx += self.utf8_charwidth(char)
            lx += 1
        return wx, lx

    def cursor_up(self):
        self.cy = max(0, self.cy - 1)

    def cursor_down(self):
        self.cy = min(self.h - 1, self.cy + 1)

    def cursor_left(self):
        self.cx= self.cx -1
        if self.cx < 0:
           self.cx= self.w-1
           self.cy= self.cy-1
           if self.cy < 0:
              self.cy=0
              self.cx=0

    def cursor_right(self):
        self.cx= self.cx +1
        if self.cx == self.w:
           self.cx=0
           self.cy= self.cy+1
           if self.cy- self.view_y0 >= self.view_h:
              self.scroll_view_down()
           if self.cy == self.h:
              self.scroll_area_up(0, self.h)
              self.cy=self.cy-1
              self.linelength[self.cy]=-1

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

    def ctrl_LF(self):
        if self.cy == self.h - 1:
            self.scroll_area_up(0, self.h)
        else:
            self.cy+=1
            if self.cy >= self.actual_h:
               self.update_size(1)
            if self.cy - self.view_y0 >= self.view_h:
               self.scroll_view_down()

    def ctrl_CR(self):
        self.cursor_set_x(0)

    def dumb_echo(self, char):
        if self.linelength[self.cy]== -1:
           self.linelength[self.cy-1]+=1
        else: 
           self.linelength[self.cy]+=1
        # wrap
        wx, cx = self.cursor_line_width(char)
        if wx > self.w:
             self.ctrl_CR()
             self.ctrl_LF()
             self.linelength[self.cy]= -1
        # insert
        if self.insert:
            self.scroll_line_right(self.cy, self.cx)
        self.poke(self.cy, self.cx, array.array('i', [self.attr | char]))
        self.cursor_set_x(self.cx + 1)
#
#   dump screen to terminal window
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
                d = self.screen[y * self.w + x]
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
                wx += self.utf8_charwidth(char)
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
       self.termqueue_lock.acquire()
       while True:
          try:
             i=self.termqueue.get_nowait()
             items.append(i)
             self.termqueue.task_done()
          except queue.Empty:
             break
       self.termqueue_lock.release()
       if len(items):
          for c in items:
             self.process(c)
          if self.update_win:
             self.win.terminalwidget.update_term(self.dump)
       if self.update_win:
          self.win.terminalwidget.update() # fire the paintEvent always to update cursor blink
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
 #     process escape sequences, translate to pyqterm
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
                for i in range(len(cc)):
                   if t > 127 and (not self.charset == CHARSET_ROMAN8):
                      self.attr |= 0x02000000
                   self.dumb_echo(ord(cc[i])) 
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
#   register keyboard function
#
    def set_kbdfunc(self,func):
       self.win.terminalwidget.setkbdfunc(func)
#
#   put character into terminal output buffer
# 
    def putchar (self,c):
       self.termqueue_lock.acquire()
       self.termqueue.put(c)
       self.termqueue_lock.release()
#
#   reset terminal
# 
    def reset(self):
       self.termqueue_lock.acquire()
       self.termqueue.put("\x1b")
       self.termqueue.put("e")
       self.termqueue_lock.release()
#
#    becomes visible
#
    def becomes_visible(self):
       self.update_win=True
       self.win.terminalwidget.update_term(self.dump)
#
#    becomes_invisible(self):
#
    def becomes_invisible(self):
       self.update_win=False
#
#    callback for scrollbar
#
    def scroll_to(self,value):
       self.view_y0= value
       self.view_y1= value + self.view_h-1
       self.win.terminalwidget.update_term(self.dump)
