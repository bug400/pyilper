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

import array
import queue
import threading
import time

from PyQt4.QtCore import QRect, Qt, pyqtSignal, QTimer, QSize
from PyQt4.QtGui import (
    QApplication, QClipboard, QWidget, QPainter, QFont, QBrush, QColor,
    QPen, QPixmap, QImage, QContextMenuEvent)
from .pilcharconv import charconv, CHARSET_HP71, CHARSET_HP41, CHARSET_ROMAN8


DEBUG = False
KEYBOARD_DELAY=0.2

class QTerminalWidget(QWidget):

    foreground_color_map = {
        0: "#000",
        1: "#b00",
        2: "#0b0",
        3: "#bb0",
        4: "#00b",
        5: "#b0b",
        6: "#0bb",
        7: "#bbb",
        8: "#666",
        9: "#f00",
        10: "#0f0",
        11: "#ff0",
        12: "#00f",  # concelaed
        13: "#f0f",
        14: "#000",  # negative
        15: "#fff",  # default
    }
    background_color_map = {
        0: "#000",
        1: "#b00",
        2: "#0b0",
        3: "#bb0",
        4: "#00b",
        5: "#b0b",
        6: "#0bb",
        7: "#bbb",
        12: "#aaa",  # cursor
        14: "#000",  # default
        15: "#fff",  # negative
    }
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


    def __init__(self,parent, font_name, font_size, w,h):
        super().__init__(parent)
        self.setFocusPolicy(Qt.WheelFocus)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setCursor(Qt.IBeamCursor)
        font = QFont(font_name)
        font.setPixelSize(font_size)
        self.setFont(font)
        self._last_update = None
        self._screen = []
        self._text = []
        self._cursor_rect = None
        self._cursor_col = 0
        self._cursor_row = 0
        self._dirty = False
        self._blink = False
        self._press_pos = None
        self._clipboard = QApplication.clipboard()
        self._kbdfunc= None
        self._w=w
        self._h=h
        self._alt_sequence= False
        self._alt_seq_length=0
        self._alt_seq_value=0

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

    def setSize(self,w,h):
        self._w=w
        self._h=h
        self.resize(w,h)
    
    def update_term(self,dump):
        (self._cursor_col, self._cursor_row), self._screen = dump()
        self._update_cursor_rect()
        self._dirty = True
        if self.hasFocus():
            self._blink = not self._blink
        self.update()


    def _update_metrics(self):
        fm = self.fontMetrics()
        self._char_height = fm.height()
        self._char_width = fm.width("W")

    def _update_cursor_rect(self):
        cx, cy = self._pos2pixel(self._cursor_col, self._cursor_row)
        self._cursor_rect = QRect(cx, cy, self._char_width, self._char_height)

    def _reset(self):
        self._update_metrics()
        self._update_cursor_rect()
#       self.resizeEvent(None)
        self.update_screen()

    def update_screen(self):
        self._dirty = True
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._dirty:
            self._dirty = False
            self._paint_screen(painter)

    def _pixel2pos(self, x, y):
        col = int(round(x / self._char_width))
        row = int(round(y / self._char_height))
        return col, row

    def _pos2pixel(self, col, row):
        x = (col * self._char_width)
        y = row * self._char_height
        return x, y

    def _paint_cursor(self, painter):
        if self._blink:
            color = "#aaa"
        else:
            color = "#fff"
        painter.setPen(QPen(QColor(color)))
        painter.drawRect(self._cursor_rect)

    def _paint_screen(self, painter):
        # Speed hacks: local name lookups are faster
        vars().update(QColor=QColor, QBrush=QBrush, QPen=QPen, QRect=QRect)
        background_color_map = self.background_color_map
        foreground_color_map = self.foreground_color_map
        char_width = self._char_width
        char_height = self._char_height
        painter_drawText = painter.drawText
        painter_fillRect = painter.fillRect
        painter_setPen = painter.setPen
        align = Qt.AlignTop | Qt.AlignLeft
        # set defaults
        background_color = background_color_map[14]
        foreground_color = foreground_color_map[15]
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
                    foreground_color_idx, background_color_idx, underline_flag = item
                    foreground_color = foreground_color_map[
                        foreground_color_idx]
                    background_color = background_color_map[
                        background_color_idx]
                    pen = QPen(QColor(foreground_color))
                    brush = QBrush(QColor(background_color))
                    painter_setPen(pen)
                    # painter.setBrush(brush)
            y += char_height
            text_append(text_line)
        self._text = text


    def keyPressEvent(self, event):
        text = event.text()
        key = event.key()
        modifiers = event.modifiers()
        if self._kbdfunc == None:
           event.accept()
           return
        alt = modifiers == Qt.AltModifier 
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
        time.sleep(KEYBOARD_DELAY)


    def column_count(self):
        return self._columns

    def row_count(self):
        return self._rows


__version__ = "0.1"


class HPTerminal:

    def __init__(self, w, h, win):
        self.w = w
        self.h = h
        self.termqueue= queue.Queue()
        self.termqueue_lock= threading.Lock()
        self.fesc= False
        self.movecursor= 0
        self.movecol=0
        self.timer= QTimer()
        self.timer.timeout.connect(self.update)
        self.irindicfunc= None
        self.win=win
        self.charset=CHARSET_HP71
        self.update_win= False

        self.vt100_charset_graph = [
            0x25ca, 0x2026, 0x2022, 0x3f,
            0xb6, 0x3f, 0xb0, 0xb1,
            0x3f, 0x3f, 0x2b, 0x2b,
            0x2b, 0x2b, 0x2b, 0xaf,
            0x2014, 0x2014, 0x2014, 0x5f,
            0x2b, 0x2b, 0x2b, 0x2b,
            0x7c, 0x2264, 0x2265, 0xb6,
            0x2260, 0xa3, 0xb7, 0x7f
        ]
        self.vt100_keyfilter_ansikeys = {
            '~': '~',
            'A': '\x1b[A',
            'B': '\x1b[B',
            'C': '\x1b[C',
            'D': '\x1b[D',
            'F': '\x1b[F',
            'H': '\x1b[H',
            '1': '\x1b[5~',
            '2': '\x1b[6~',
            '3': '\x1b[2~',
            '4': '\x1b[3~',
            'a': '\x1bOP',
            'b': '\x1bOQ',
            'c': '\x1bOR',
            'd': '\x1bOS',
            'e': '\x1b[15~',
            'f': '\x1b[17~',
            'g': '\x1b[18~',
            'h': '\x1b[19~',
            'i': '\x1b[20~',
            'j': '\x1b[21~',
            'k': '\x1b[23~',
            'l': '\x1b[24~',
        }
        self.vt100_keyfilter_appkeys = {
            '~': '~',
            'A': '\x1bOA',
            'B': '\x1bOB',
            'C': '\x1bOC',
            'D': '\x1bOD',
            'F': '\x1bOF',
            'H': '\x1bOH',
            '1': '\x1b[5~',
            '2': '\x1b[6~',
            '3': '\x1b[2~',
            '4': '\x1b[3~',
            'a': '\x1bOP',
            'b': '\x1bOQ',
            'c': '\x1bOR',
            'd': '\x1bOS',
            'e': '\x1b[15~',
            'f': '\x1b[17~',
            'g': '\x1b[18~',
            'h': '\x1b[19~',
            'i': '\x1b[20~',
            'j': '\x1b[21~',
            'k': '\x1b[23~',
            'l': '\x1b[24~',
        }
        self.reset_hard()

    # Reset functions
    def reset_hard(self):
        # Attribute mask: 0x0XFB0000
        #	X:	Bit 0 - Underlined
        #		Bit 1 - Negative
        #		Bit 2 - Concealed
        #	F:	Foreground
        #	B:	Background
        self.attr = 0x00fe0000
        # Key filter
        self.vt100_keyfilter_escape = False
        # Last char
        self.vt100_lastchar = 0
        # Control sequences
        self.vt100_parse_len = 0
        self.vt100_parse_state = ""
        self.vt100_parse_func = ""
        self.vt100_parse_param = ""
        # Buffers
        self.vt100_out = ""
        # Invoke other resets
        self.reset_screen()
        self.reset_soft()

    def reset_soft(self):
        # Attribute mask: 0x0XFB0000
        #	X:	Bit 0 - Underlined
        #		Bit 1 - Negative
        #		Bit 2 - Concealed
        #	F:	Foreground
        #	B:	Background
        self.attr = 0x00fe0000
        # Scroll parameters
        self.scroll_area_y0 = 0
        self.scroll_area_y1 = self.h
        # Character sets
        self.vt100_charset_is_single_shift = False
        self.vt100_charset_is_graphical = False
        self.vt100_charset_g_sel = 0
        self.vt100_charset_g = [0, 0]
        # Modes
        self.vt100_mode_insert = False
        self.vt100_mode_lfnewline = False
        self.vt100_mode_cursorkey = False
        self.vt100_mode_column_switch = False
        self.vt100_mode_inverse = False
        self.vt100_mode_origin = False
        self.vt100_mode_autowrap = True
        self.vt100_mode_cursor = True
        self.vt100_mode_alt_screen = False
        self.vt100_mode_backspace = False

    def reset_screen(self):
        # Screen
        self.screen = array.array('i', [self.attr | 0x20] * self.w * self.h)
        self.screen2 = array.array('i', [self.attr | 0x20] * self.w * self.h)
        # Scroll parameters
        self.scroll_area_y0 = 0
        self.scroll_area_y1 = self.h
        # Cursor position
        self.cx = 0
        self.cy = 0
        # Tab stops
        self.tab_stops = range(0, self.w, 8)

    def set_charset(self,charset):
       self.charset= charset

    def utf8_charwidth(self, char):
        if char == 0x0304:
            return 0
        if char >= 0x2e80:
            return 2
        else:
            return 1

    # Low-level terminal functions
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

    # Scrolling functions
    def scroll_area_up(self, y0, y1, n=1):
        n = min(y1 - y0, n)
        self.poke(y0, 0, self.peek(y0 + n, 0, y1, self.w))
        self.clear(y1 - n, 0, y1, self.w)

    def scroll_area_down(self, y0, y1, n=1):
        n = min(y1 - y0, n)
        self.poke(y0 + n, 0, self.peek(y0, 0, y1 - n, self.w))
        self.clear(y0, 0, y0 + n, self.w)

    def scroll_area_set(self, y0, y1):
        y0 = max(0, min(self.h - 1, y0))
        y1 = max(1, min(self.h, y1))
        if y1 > y0:
            self.scroll_area_y0 = y0
            self.scroll_area_y1 = y1

    def scroll_line_right(self, y, x, n=1):
        if x < self.w:
            n = min(self.w - self.cx, n)
            self.poke(y, x + n, self.peek(y, x, y + 1, self.w - n))
            self.clear(y, x, y + 1, x + n)

    def scroll_line_left(self, y, x, n=1):
        if x < self.w:
            n = min(self.w - self.cx, n)
            self.poke(y, x, self.peek(y, x + n, y + 1, self.w))
            self.clear(y, self.w - n, y + 1, self.w)

    # Cursor functions
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

    def cursor_left(self, n=1):
        self.cx = max(0, self.cx - n)

    def cursor_right(self, n=1):
        self.cx = min(self.w - 1, self.cx + n)

    def cursor_set_x(self, x):
        self.cx = max(0, x)

    def cursor_set_y(self, y):
        self.cy = max(0, min(self.h - 1, y))

    def cursor_set(self, y, x):
        self.cursor_set_x(x)
        self.cursor_set_y(y)

    # Dumb terminal
    def ctrl_BS(self):
        delta_y, cx = divmod(self.cx - 1, self.w)
        cy = max(self.scroll_area_y0, self.cy + delta_y)
        self.cursor_set(cy, cx)

    def ctrl_HT(self, n=1):
        if n > 0 and self.cx >= self.w:
            return
        if n <= 0 and self.cx == 0:
            return
        ts = 0
        for i in range(len(self.tab_stops)):
            if self.cx >= self.tab_stops[i]:
                ts = i
        ts += n
        if ts < len(self.tab_stops) and ts >= 0:
            self.cursor_set_x(self.tab_stops[ts])
        else:
            self.cursor_set_x(self.w - 1)

    def ctrl_LF(self):
        if self.vt100_mode_lfnewline:
            self.ctrl_CR()
        if self.cy == self.scroll_area_y1 - 1:
            self.scroll_area_up(self.scroll_area_y0, self.scroll_area_y1)
        else:
            self.cursor_down()

    def ctrl_CR(self):
        self.cursor_set_x(0)

    def dumb_write(self, char):
        if char < 32:
            if char == 8:
                self.ctrl_BS()
            elif char == 9:
                self.ctrl_HT()
            elif char >= 10 and char <= 12:
                self.ctrl_LF()
            elif char == 13:
                self.ctrl_CR()
            return True
        return False

    def dumb_echo(self, char):
        # Check right bound
        wx, cx = self.cursor_line_width(char)
        # Newline
        if wx > self.w:
            if self.vt100_mode_autowrap:
                self.ctrl_CR()
                self.ctrl_LF()
            else:
                self.cx = cx - 1
        if self.vt100_mode_insert:
            self.scroll_line_right(self.cy, self.cx)
        self.poke(self.cy, self.cx, array.array('i', [self.attr | char]))
        self.cursor_set_x(self.cx + 1)

    # External interface
    def set_size(self, w, h):
        if w < 2 or w > 256 or h < 2 or h > 256:
            return False
        self.w = w
        self.h = h
        self.reset_screen()
        return True

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
                # Cursor
                if cy == y and cx == x and self.vt100_mode_cursor:
                    attr = attr & 0xfff0 | 0x000c
                # Attributes
                if attr != attr_:
                    if attr_ != -1:
                        line.append("")
                    bg = attr & 0x000f
                    fg = (attr & 0x00f0) >> 4
                    # Inverse
                    inv = attr & 0x0200
                    inv2 = self.vt100_mode_inverse
                    if (inv and not inv2) or (inv2 and not inv):
                        fg, bg = bg, fg
                    # Concealed
                    if attr & 0x0400:
                        fg = 0xc
                    # Underline
                    if attr & 0x0100:
                        ul = True
                    else:
                        ul = False
                    line.append((fg, bg, ul))
                    line.append("")
                    attr_ = attr
                wx += self.utf8_charwidth(char)
                if wx <= self.w:
                    line[-1] += chr(char)
            screen.append(line)

        return (cx, cy), screen


    def set_kbdfunc(self,func):
       self.win.setkbdfunc(func)
 
    def set_irindicfunc(self,func):
       self.irindicfunc= func
 
    def start_update(self,ms):
       self.timer.start(ms)

    def stop_update(self):
       self.timer.stop()
 
    def putchar (self,c):
       self.termqueue_lock.acquire()
       self.termqueue.put(c)
       self.termqueue_lock.release()
 
    def reset(self):
       self.termqueue_lock.acquire()
       self.termqueue.put("\x1b")
       self.termqueue.put("e")
       self.termqueue_lock.release()
        
    def update(self):
       self.termqueue_lock.acquire()
       if self.termqueue.empty():
          self.termqueue_lock.release()
          return
       items=[]
       while not self.termqueue.empty():
           items.append(self.termqueue.get())
       self.termqueue_lock.release()
       for c in items:
          self.process(c)
       if self.update_win:
          self.win.update_term(self.dump)
 
    def refresh(self):
        self.win.update_term(self.dump)
 
    def process(self,c):
 
       t=ord(c)
       if t == 27:
          self.fesc= True
          return
 
       if not self.fesc:
          if t == 0xD:         # CR
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
                tc=ord(cc[i])
                if t > 127 and (not self.charset == CHARSET_ROMAN8):
                   self.attr |= 0x02000000
                self.dumb_echo(ord(cc[i])) 
                self.attr = 0x00fe0000
          return
 #
 #     process escape sequences, translate to pyqterm
 #
       if self.movecursor == 1:
          self.movecursor=2
          self.movecol=t
          return
 
       if self.movecursor == 2:
          self.cursor_set(self.movecol,t)
          self.movecursor=0
          self.win.update_term(self.dump)
          self.fesc= False
          return
 
       if t== 67: # cursor right (ESC C)
          self.cx= self.cx +1
          if self.cx > self.w:
             self.cx=0
             self.cy= self.cy+1
             if self.cy > self.h:
                self.cy=0
       elif t== 68: # cursor left (ESC D)
          self.cx= self.cx -1
          if self.cx < 0:
             self.cx= self.w-1
             self.cy= self.cy-1
             if self.cy < 0:
                self.cy=0
                self.cx=0
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
          self.vt100_mode_cursor = True
       elif t== 60: # Cursor off (ESC <)
          self.vt100_mode_cursor = False
       elif t== 69: # Reset (ESC E)
          self.reset_soft()
          self.reset_screen()
       elif t== 80: # Clear Character (ESC P) ??
          self.clear(self.cy,self.cx,self.cy+1,self.cx)
       elif t== 79: # Clear Character with wrap back (ESC O)
          self.scroll_line_left(self.cy, self.cx,1)
       elif t== 81: # switch to insert cursor (ESC Q)
          self.vt100_mode_insert = True
       elif t== 78: # swicht to insert cursor and insert mode (ESC N)
          self.vt100_mode_insert = True
          self.irindicfunc(True)
       elif t== 82: # switch to replace cursor and replace mode (ESC R)
          self.vt100_mode_insert = False
          self.irindicfunc(False)
       elif t== 101: # reset hard (ESC e)
          self.reset_hard()
       elif t== 3:  # move cursor far right (ESC Ctrl c)
          pass
       elif t== 4:  # move cursor far left (ESC ctrl d)
          pass
       elif t== 37: # Move Cursor to display position (ESC %)
          self.movecursor=1
          return
       elif t==122:  # reset
          self.reset_hard()
       else:
          print("unhandled escape sequence %d" % t)
       self.fesc= False
 
