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
# - fixed alt key

import array
import queue
import threading
import time

from PyQt4.QtCore import QRect, Qt, pyqtSignal, QTimer, QSize, QPoint
from PyQt4.QtGui import (
    QApplication, QClipboard, QWidget, QPainter, QFont, QBrush, QColor, QPolygon,
    QPen, QPixmap, QImage, QContextMenuEvent)
from .pilcharconv import charconv, CHARSET_HP71, CHARSET_HP41, CHARSET_ROMAN8


KEYBOARD_DELAY=0.2
CURSOR_OFF=0
CURSOR_INSERT=1
CURSOR_OVERWRITE=2

class QTerminalWidget(QWidget):

# color scheme: normal_foreground, normal_background, inverse_foreground, inverse_background, cursor_color

    color_scheme_names = { "white" : 0, "amber" : 1, "green": 2 }

    color_schemes= [
       [ "#000", "#fff", "#aaa" ],
       [ "#000", "#ffbe00", "#aa0" ],
       [ "#000", "#18f018", "#0a0" ],
    ]

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


    def __init__(self,parent, font_name, font_size, w,h, colorscheme,kbd_delay):
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
        self._cursor_rect = None
        self._cursor_poygon= None
        self._cursor_col = 0
        self._cursor_row = 0
        self._dirty = False
        self._kbdfunc= None
        self._w=w
        self._h=h
        self._alt_sequence= False
        self._alt_seq_length=0
        self._alt_seq_value=0
        self._kbd_delay= kbd_delay
        self._cursortype= CURSOR_OVERWRITE
        self._color_scheme=self.color_scheme_names[colorscheme]

    def sizeHint(self):
        return QSize(self._w,self._h)

    def minimumSizeHint(self):
        return QSize(self._w,self._h)

    def resizeEvent(self, event):
        self.resize(self._w, self._h)

    def setCursorType(self,t):
        self._cursortype=t

    def setkbdfunc(self,func):
        self._kbdfunc= func

    def setFont(self, font):
        super().setFont(font)
        self._update_metrics()
#
#   Update screen routine
#    
    def update_term(self,dump):
        (self._cursor_col, self._cursor_row), self._screen = dump()
        self._update_cursor_rect()
        self._dirty = True
        self.update()

    def _update_metrics(self):
        fm = self.fontMetrics()
        self._char_height = fm.height()
        self._char_width = fm.width("W")

    def _update_cursor_rect(self):
        cx, cy = self._pos2pixel(self._cursor_col, self._cursor_row)
        self._cursor_rect = QRect(cx, cy, self._char_width, self._char_height)
        self._cursor_polygon=QPolygon([QPoint(cx,cy+(self._char_height/2)),QPoint(cx+self._char_width,cy+self._char_height),QPoint(cx+self._char_width,cy),QPoint(cx,cy+(self._char_height/2))])


    def paintEvent(self, event):
        painter = QPainter(self)
        if self._dirty:
            self._dirty = False
            self._paint_screen(painter)
        else:
            self._paint_cursor(painter)

    def _pos2pixel(self, col, row):
        x = (col * self._char_width)
        y = row * self._char_height
        return x, y

    def _paint_cursor(self, painter):
        if self._cursortype== CURSOR_OFF or self._cursor_rect== None:
           return
        color = self.color_schemes[self._color_scheme][2]
        brush = QBrush(QColor(color))
        painter.setPen(QPen(QColor(color)))
        painter.setBrush(brush)
        if self._cursortype== CURSOR_OVERWRITE:
           painter.drawRect(self._cursor_rect)
        else:
           painter.drawPolygon(self._cursor_polygon)

    def _paint_screen(self, painter):
        # Speed hacks: local name lookups are faster
        vars().update(QColor=QColor, QBrush=QBrush, QPen=QPen, QRect=QRect)
        char_width = self._char_width
        char_height = self._char_height
        painter_drawText = painter.drawText
        painter_fillRect = painter.fillRect
        painter_setPen = painter.setPen
        align = Qt.AlignTop | Qt.AlignLeft
        color_schemes= self.color_schemes
        color_scheme= self._color_scheme
        # set defaults
        background_color = color_schemes[color_scheme][1]
        foreground_color = color_schemes[color_scheme][0]
        brush = QBrush(QColor(background_color))
        painter_fillRect(self.rect(), brush)
        pen = QPen(QColor(foreground_color))
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
                       background_color = color_schemes[color_scheme][1]
                       foreground_color = color_schemes[color_scheme][0]
                    else:
                       background_color = color_schemes[color_scheme][0]
                       foreground_color = color_schemes[color_scheme][1]
                    pen = QPen(QColor(foreground_color))
                    brush = QBrush(QColor(background_color))
                    painter_setPen(pen)
                    painter.setBrush(brush)
            y += char_height
            text_append(text_line)
        self._text = text
        self._paint_cursor(painter)


    def keyPressEvent(self, event):
        text = event.text()
        key = event.key()
        modifiers = event.modifiers()
        alt = modifiers == Qt.AltModifier 
        if (event.isAutoRepeat() and text) or self._kbdfunc == None:
           event.accept()
           return
        if alt:
           if key== Qt.Key_1 or key == Qt.Key_2 or key== Qt.Key_3 or \
           key== Qt.Key_4 or key == Qt.Key_5 or key== Qt.Key_6 or  \
           key== Qt.Key_7 or key == Qt.Key_8 or key== Qt.Key_9 or \
           key== Qt.Key_0:
              if not self._alt_sequence:
                 self._alt_sequence= True
                 self._alt_seq_length=0
                 self._alt_seq_value=0
              self._alt_seq_value*=10
              self._alt_seq_value+= ord(text)-0x30
              self._alt_seq_length+=1
              if self._alt_seq_length == 3:
                 text= chr(self._alt_seq_value)
                 self._alt_sequence= False
              else:
                 event.accept()
                 return
           else:
              self._alt_sequence= False
              event.accept()
              return

        if text:
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
                
        event.accept()
        if self._kbd_delay:
          time.sleep(KEYBOARD_DELAY)


class HPTerminal:

    def __init__(self, w, h, win):
        self.w = w
        self.h = h
        self.termqueue= queue.Queue()
        self.termqueue_lock= threading.Lock()
        self.fesc= False
        self.movecursor= 0
        self.movecol=0
        self.UpdateTimer= QTimer()
        self.UpdateTimer.timeout.connect(self.update)
        self.win=win
        self.charset=CHARSET_HP71
        self.update_win= False
        self.reset_hard()
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
        self.scroll_area_y0 = 0
        self.scroll_area_y1 = self.h
        # Modes
        self.insert = False
        self.movecursor=0

    def reset_screen(self):
        # Screen
        self.screen = array.array('i', [self.attr | 0x20] * self.w * self.h)
        self.linelength= array.array('i', [0] * self.h)
        # Scroll parameters
        self.scroll_area_y0 = 0
        self.scroll_area_y1 = self.h
        # Cursor position
        self.cx = 0
        self.cy = 0
        self.movecursor=0
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
               self.scroll_area_up(self.scroll_area_y0, self.scroll_area_y1)
               y=y-1
               self.cy=self.cy-1
               self.linelength[y+1]=-1

            # wrap line
            if self.linelength[y] > self.w:
               self.poke(y+1,1,self.peek(y+1, 0, y + 2, self.w))
               self.poke(y+1,0,self.peek(y,self.w-1,y+1,self.w))
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
            self.linelength[y]-=1
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

    def cursor_up(self, n=1):
        self.cy = max(self.scroll_area_y0, self.cy - n)

    def cursor_down(self, n=1):
        self.cy = min(self.scroll_area_y1 - 1, self.cy + n)

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
           if self.cy == self.h:
              self.scroll_area_up(self.scroll_area_y0, self.scroll_area_y1)
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
        if self.cy == self.scroll_area_y1 - 1:
            self.scroll_area_up(self.scroll_area_y0, self.scroll_area_y1)
        else:
            self.cursor_down()

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
        cx, cy = min(self.cx, self.w - 1), self.cy
        for y in range(0, self.h):
            wx = 0
            line = [""]
            for x in range(0, self.w):
                d = self.screen[y * self.w + x]
                char = d & 0xffff
                attr = d >> 16
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

        return (cx, cy), screen
#
#   process terminal output queue
#        
    def update(self):
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
             self.win.update_term(self.dump)
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
             self.cursor_up(1)
          elif t== 66: # cursor down (ESC B)
             self.cursor_down(1)
          elif t== 72: # move cursor to home position (ESC H)
             self.cursor_set(0,0)
          elif t== 74: # erase from cursor to end of screen (ESC J)
             self.clear(self.cy,self.cx,self.h, self.w)
          elif t== 75: # erase from cursor to end of the line (ESC K)
             self.clear(self.cy,self.cx,self.cy+1,self.w)
          elif t== 62: # Cursor on (ESC >)
             if self.insert:
                self.win.setCursorType(CURSOR_INSERT)
             else:
                self.win.setCursorType(CURSOR_OVERWRITE)
          elif t== 60: # Cursor off (ESC <)
             self.win.setCursorType(CURSOR_OFF)
          elif t== 69: # Reset (ESC E)
             self.reset_soft()
             self.reset_screen()
          elif t== 80: # Clear Character (ESC P) ??
             self.clear(self.cy,self.cx,self.cy+1,self.cx+1)
          elif t== 79: # Clear Character with wrap back (ESC O)
             self.scroll_line_left(self.cy, self.cx)
          elif t== 81: # switch to insert cursor (ESC Q)
             self.win.setCursorType(CURSOR_INSERT)
             self.insert = True
          elif t== 78: # swicht to insert cursor and insert mode (ESC N)
             self.insert = True
             self.win.setCursorType(CURSOR_INSERT)
          elif t== 82: # switch to replace cursor and replace mode (ESC R)
             self.insert = False
             self.win.setCursorType(CURSOR_OVERWRITE)
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
       self.win.setkbdfunc(func)
#
#   start processing the terminal output buffer
# 
    def start_update(self,ms):
       self.UpdateTimer.start(ms)
#
#   stop processing the terminal output buffer
#
    def stop_update(self):
       self.UpdateTimer.stop()
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
#   refresh terminal
# 
    def refresh(self):
        self.win.update_term(self.dump)
