#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pyILPER 1.2.4 for Linux
#
# An emulator for virtual HP-IL devices for the PIL-Box
# derived from ILPER 1.4.5 for Windows
# Copyright (c) 2008-2013   Jean-Francois Garnier
# C++ version (c) 2013 Christoph Gießelink
# Python Version (c) 2015 Joachim Siebold
# HP82162a printer emulation derived from the nonpareil emulator
# (C) 1995, 2003, 2004, 2005, 2006, 2008 Eric Smith
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
# HP82162A virtual device classes  ---------------------------------------------
#
# Changelog
# 05.08.2017 jsi:
# - initial version
# 20.08.2017 jsi:
# - fixed: papersize for pdf output not configurable
# 21.08.2017 jsi:
# - refactoring: new pdf printer class used
# - store number of pdf columns in system configuration
# - disable gui if device not enabled
# 27.08.2017 jsi:
# - removed redraw timer: not needed
# - resize of printer tab now repositions everything correctly
# 28.08.2017 jsi:
# - remove alignments from GUI
# - get papersize config parameter in constructor of tab widget
# 03.09.2017 jsi
# - register pildevice is now method of commobject
# 16.09.2017 jsi
# - added missing entries in ASCII character table
# 19.09.2017 jsi
# - use raw strings in re.findall
# 19.09.2017 jsi
# - use raw strings in re.findall
# 24.09.2016 jsi
# - added mouse wheel scrolling support
# 02.12.2017 jsi
# - on the fly reconfiguration of the pixelsize
# - fix: keep scroll position on resize
# 04.01.2018 jsi
# - reconfigure log check box object
# - flush log buffer 
# 16.01.2018 jsi
# - adapt to cls_tabgeneric, implemented cascading config menu
# 20.01.2018 jsi
# - the pixel size is now a dual parameter
# 28.01.2018 jsi
# - set AutoDefault property of buttons to false
# 29.01.2018 jsi
# - shrink all parent widgets if the pixel size was changed
# 22.02.2018 jsi
# - disabled shrinking parent widgets becaus of errors on reconfiguration
# 04.05.2022 jsi
# - PySide6 migration
# 04.05.2022 jsi
# - force printer background to be always white (dark mode)
# 30.07.2022 jsi
# - do not use a default filename for pdf output file
#
import copy
import queue
import threading
import re
from .pilcore import UPDATE_TIMER, PDF_ORIENTATION_PORTRAIT, QTBINDINGS
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtWidgets
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtWidgets

from .pilconfig import PILCONFIG
from .pilcharconv import charconv, CHARSET_HP41, CHARSET_ROMAN8
from .pildevbase import cls_pildevbase
from .pilwidgets import cls_tabgeneric, LogCheckboxWidget, T_INTEGER, O_DEFAULT
from .pilpdf import cls_pdfprinter
from .pilcore import HP82162A_LINEBUFFERSIZE

#
# constants --------------------------------------------------------------
#
PRINTER_CHARACTER_WIDTH_PIXELS= 7
PRINTER_WIDTH_CHARS= 24
PRINTER_WIDTH= (PRINTER_WIDTH_CHARS * PRINTER_CHARACTER_WIDTH_PIXELS)
PRINTER_CHARACTER_HEIGHT_PIXELS= 13
DISPLAY_LINE_SPACING=0

PDF_LINES=70           # number of lines in pdf output
PDF_MARGINS=50         # margins (top,bot,left,right) of pdf output
PDF_MAX_COLS=3         # max number of columns in pdf output
PDF_COLUMN_SPACING=80  # spacing between columns
PDF_LINE_SPACING=0     # linespacing in (relative) pixel

#
# printer modeswitch
#
MODESWITCH_MAN=0
MODESWITCH_TRACE=1
MODESWITCH_NORM=2

# HP-IL Status bits
STA_SR= 64
STA_MB= 32
STA_MA= 16
STA_ER= 8
STA_PA= 4
STA_PR= 2
STA_LA= 1

STA_EL= 128 << 8
STA_ID= 64  << 8
STA_BE= 32  << 8
STA_EB= 16  << 8
STA_RJ= 8   << 8
STA_DW= 4   << 8
STA_CO= 2   << 8
STA_LC= 1   << 8

# Printer status bits
mode_8bit=       1
mode_lowercase=  2
mode_doublewide= 4
mode_column=      8
mode_rjust=      16
mode_parse=      32
mode_barcode=    64
mode_inhibit_advance= 128

#
# printer buffer data types
#
type_char=       1
type_column=     2
type_barcode=    3
type_format=     4
type_skip=       5

# GUI commands
CMD_MAN=            0
CMD_NORM=           1
CMD_TRACE=          2
CMD_PRINT_PRESSED=  3
CMD_ADV_PRESSED=    4
CMD_CLEAR=          5
CMD_PRINT_RELEASED= 6
CMD_ADV_RELEASED=   7

# HPIL-Thread commands
REMOTECMD_CLEAR=0
REMOTECMD_PRINT=1
REMOTECMD_LOG=2

#
# charsets
#
CHARSET_ASCII=0
CHARSET_ALTERNATE=1
#
# hp82162a character generator -------------------------------------------------
# character codes taken from the nonpareil calculator simulator
# (C) Eric Smith
#

class hp82162a_char(object):

   def __init__(self):   
      super().__init__()
#
#     ASCII charset
#
      self.ac= { }
      self.ac[0x00] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x01] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x02] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x03] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x04] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x05] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x06] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x07] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x08] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x09] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x0a] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x0b] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x0c] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x0d] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x0e] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x0f] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x10] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x11] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x12] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x13] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x14] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x15] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x16] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x17] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x18] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x19] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x1A] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x1B] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x1C] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x1D] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x1E] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x1F] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  
      self.ac[0x20] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  # space
      self.ac[0x21] = bytes([ 0x00, 0x00, 0x5f, 0x00, 0x00 ])  # bang
      self.ac[0x22] = bytes([ 0x00, 0x03, 0x00, 0x03, 0x00 ])  # double quote
      self.ac[0x23] = bytes([ 0x14, 0x7f, 0x14, 0x7f, 0x14 ])  # hash (pound, octothorpe)
      self.ac[0x24] = bytes([ 0x24, 0x2a, 0x7f, 0x2a, 0x12 ])  # dollar
      self.ac[0x25] = bytes([ 0x23, 0x13, 0x08, 0x64, 0x62 ])  # percent
      self.ac[0x26] = bytes([ 0x36, 0x49, 0x56, 0x20, 0x50 ])  # ampersand
      self.ac[0x27] = bytes([ 0x00, 0x00, 0x03, 0x00, 0x00 ])  # single quote
      self.ac[0x28] = bytes([ 0x00, 0x1c, 0x22, 0x41, 0x00 ])  # left parenthesis
      self.ac[0x29] = bytes([ 0x00, 0x41, 0x22, 0x1c, 0x00 ])  # right parenthesis
      self.ac[0x2a] = bytes([ 0x14, 0x08, 0x3e, 0x08, 0x14 ])  # asterisk
      self.ac[0x2b] = bytes([ 0x08, 0x08, 0x3e, 0x08, 0x08 ])  # plus
      self.ac[0x2c] = bytes([ 0x00, 0x40, 0x30, 0x00, 0x00 ])  # comma
      self.ac[0x2d] = bytes([ 0x08, 0x08, 0x08, 0x08, 0x08 ])  # hyphen
      self.ac[0x2e] = bytes([ 0x00, 0x60, 0x60, 0x00, 0x00 ])  # period
      self.ac[0x2f] = bytes([ 0x20, 0x10, 0x08, 0x04, 0x02 ])  # slash
      self.ac[0x30] = bytes([ 0x3e, 0x51, 0x49, 0x45, 0x3e ])  # zero
      self.ac[0x31] = bytes([ 0x00, 0x42, 0x7f, 0x40, 0x00 ])  # one
      self.ac[0x32] = bytes([ 0x62, 0x51, 0x49, 0x49, 0x46 ])  # two
      self.ac[0x33] = bytes([ 0x21, 0x41, 0x49, 0x4d, 0x33 ])  # three
      self.ac[0x34] = bytes([ 0x18, 0x14, 0x12, 0x7f, 0x10 ])  # four
      self.ac[0x35] = bytes([ 0x27, 0x45, 0x45, 0x45, 0x39 ])  # five
      self.ac[0x36] = bytes([ 0x3c, 0x4a, 0x49, 0x48, 0x30 ])  # six
      self.ac[0x37] = bytes([ 0x01, 0x71, 0x09, 0x05, 0x03 ])  # seven
      self.ac[0x38] = bytes([ 0x36, 0x49, 0x49, 0x49, 0x36 ])  # eight
      self.ac[0x39] = bytes([ 0x06, 0x49, 0x49, 0x29, 0x1e ])  # nine
      self.ac[0x3a] = bytes([ 0x00, 0x00, 0x24, 0x00, 0x00 ])  # colon
      self.ac[0x3b] = bytes([ 0x00, 0x40, 0x34, 0x00, 0x00 ])  # semicolon
      self.ac[0x3c] = bytes([ 0x08, 0x14, 0x22, 0x41, 0x00 ])  # less than
      self.ac[0x3d] = bytes([ 0x14, 0x14, 0x14, 0x14, 0x14 ])  # equal
      self.ac[0x3e] = bytes([ 0x00, 0x41, 0x22, 0x14, 0x08 ])  # greater than
      self.ac[0x3f] = bytes([ 0x02, 0x01, 0x51, 0x09, 0x06 ])  # question mark
      self.ac[0x40] = bytes([ 0x3e, 0x41, 0x5d, 0x5d, 0x1e ])  # at
      self.ac[0x41] = bytes([ 0x7e, 0x11, 0x11, 0x11, 0x7e ])  # UC A
      self.ac[0x42] = bytes([ 0x7f, 0x49, 0x49, 0x49, 0x36 ])  # UC B
      self.ac[0x43] = bytes([ 0x3e, 0x41, 0x41, 0x41, 0x22 ])  # UC C
      self.ac[0x44] = bytes([ 0x41, 0x7f, 0x41, 0x41, 0x3e ])  # UC D
      self.ac[0x45] = bytes([ 0x7f, 0x49, 0x49, 0x49, 0x41 ])  # UC E
      self.ac[0x46] = bytes([ 0x7f, 0x09, 0x09, 0x09, 0x01 ])  # UC F
      self.ac[0x47] = bytes([ 0x3e, 0x41, 0x41, 0x51, 0x72 ])  # UC G
      self.ac[0x48] = bytes([ 0x7f, 0x08, 0x08, 0x08, 0x7f ])  # UC H
      self.ac[0x49] = bytes([ 0x00, 0x41, 0x7f, 0x41, 0x00 ])  # UC I
      self.ac[0x4a] = bytes([ 0x20, 0x40, 0x40, 0x40, 0x3f ])  # UC J
      self.ac[0x4b] = bytes([ 0x7f, 0x08, 0x14, 0x22, 0x41 ])  # UC K
      self.ac[0x4c] = bytes([ 0x7f, 0x40, 0x40, 0x40, 0x40 ])  # UC L
      self.ac[0x4d] = bytes([ 0x7f, 0x02, 0x0c, 0x02, 0x7f ])  # UC M
      self.ac[0x4e] = bytes([ 0x7f, 0x04, 0x08, 0x10, 0x7f ])  # UC N
      self.ac[0x4f] = bytes([ 0x3e, 0x41, 0x41, 0x41, 0x3e ])  # UC O
      self.ac[0x50] = bytes([ 0x7f, 0x09, 0x09, 0x09, 0x06 ])  # UC P
      self.ac[0x51] = bytes([ 0x3e, 0x41, 0x51, 0x21, 0x5e ])  # UC Q
      self.ac[0x52] = bytes([ 0x7f, 0x09, 0x19, 0x29, 0x46 ])  # UC R
      self.ac[0x53] = bytes([ 0x26, 0x49, 0x49, 0x49, 0x32 ])  # UC S
      self.ac[0x54] = bytes([ 0x01, 0x01, 0x7f, 0x01, 0x01 ])  # UC T
      self.ac[0x55] = bytes([ 0x3f, 0x40, 0x40, 0x40, 0x3f ])  # UC U
      self.ac[0x56] = bytes([ 0x07, 0x18, 0x60, 0x18, 0x07 ])  # UC V
      self.ac[0x57] = bytes([ 0x7f, 0x20, 0x18, 0x20, 0x7f ])  # UC W
      self.ac[0x58] = bytes([ 0x63, 0x14, 0x08, 0x14, 0x63 ])  # UC X
      self.ac[0x59] = bytes([ 0x03, 0x04, 0x78, 0x04, 0x03 ])  # UC Y
      self.ac[0x5a] = bytes([ 0x61, 0x51, 0x49, 0x45, 0x43 ])  # UC Z
      self.ac[0x5b] = bytes([ 0x00, 0x7f, 0x41, 0x41, 0x00 ])  # left bracket
      self.ac[0x5c] = bytes([ 0x02, 0x04, 0x08, 0x10, 0x20 ])  # backslash
      self.ac[0x5d] = bytes([ 0x00, 0x41, 0x41, 0x7f, 0x00 ])  # right bracket
      self.ac[0x5e] = bytes([ 0x04, 0x02, 0x01, 0x02, 0x04 ])  # ^
      self.ac[0x5f] = bytes([ 0x40, 0x40, 0x40, 0x40, 0x40 ])  # underscore
      self.ac[0x60] = bytes([ 0x00, 0x01, 0x02, 0x04, 0x00 ])  # `
      self.ac[0x61] = bytes([ 0x20, 0x54, 0x54, 0x54, 0x78 ])  # LC a
      self.ac[0x62] = bytes([ 0x7f, 0x48, 0x44, 0x44, 0x38 ])  # LC b
      self.ac[0x63] = bytes([ 0x38, 0x44, 0x44, 0x44, 0x20 ])  # LC c
      self.ac[0x64] = bytes([ 0x38, 0x44, 0x44, 0x48, 0x7f ])  # LC d
      self.ac[0x65] = bytes([ 0x38, 0x54, 0x54, 0x54, 0x08 ])  # LC e
      self.ac[0x66] = bytes([ 0x08, 0x7c, 0x0a, 0x01, 0x02 ])  # LC f
      self.ac[0x67] = bytes([ 0x08, 0x14, 0x54, 0x54, 0x38 ])  # LC g
      self.ac[0x68] = bytes([ 0x7f, 0x10, 0x08, 0x08, 0x70 ])  # LC h
      self.ac[0x69] = bytes([ 0x00, 0x44, 0x7d, 0x40, 0x00 ])  # LC i
      self.ac[0x6a] = bytes([ 0x20, 0x40, 0x40, 0x3d, 0x00 ])  # LC j
      self.ac[0x6b] = bytes([ 0x00, 0x7f, 0x28, 0x44, 0x00 ])  # LC k
      self.ac[0x6c] = bytes([ 0x00, 0x41, 0x7f, 0x40, 0x00 ])  # LC l
      self.ac[0x6d] = bytes([ 0x78, 0x04, 0x18, 0x04, 0x78 ])  # LC m
      self.ac[0x6e] = bytes([ 0x7c, 0x08, 0x04, 0x04, 0x78 ])  # LC n
      self.ac[0x6f] = bytes([ 0x38, 0x44, 0x44, 0x44, 0x38 ])  # LC o
      self.ac[0x70] = bytes([ 0x7c, 0x14, 0x24, 0x24, 0x18 ])  # LC p
      self.ac[0x71] = bytes([ 0x18, 0x24, 0x24, 0x7c, 0x40 ])  # LC q
      self.ac[0x72] = bytes([ 0x7c, 0x08, 0x04, 0x04, 0x08 ])  # LC r
      self.ac[0x73] = bytes([ 0x48, 0x54, 0x54, 0x54, 0x24 ])  # LC s
      self.ac[0x74] = bytes([ 0x04, 0x3e, 0x44, 0x20, 0x00 ])  # LC t
      self.ac[0x75] = bytes([ 0x3c, 0x40, 0x40, 0x20, 0x7c ])  # LC u
      self.ac[0x76] = bytes([ 0x1c, 0x20, 0x40, 0x20, 0x1c ])  # LC v
      self.ac[0x77] = bytes([ 0x3c, 0x40, 0x30, 0x40, 0x3c ])  # LC w
      self.ac[0x78] = bytes([ 0x44, 0x28, 0x10, 0x28, 0x44 ])  # LC x
      self.ac[0x79] = bytes([ 0x44, 0x28, 0x10, 0x08, 0x04 ])  # LC y
      self.ac[0x7a] = bytes([ 0x44, 0x64, 0x54, 0x4c, 0x44 ])  # LC z
      self.ac[0x7b] = bytes([ 0x00, 0x08, 0x36, 0x41, 0x00 ])  # {
      self.ac[0x7c] = bytes([ 0x00, 0x00, 0x7f, 0x00, 0x00 ])  # |
      self.ac[0x7d] = bytes([ 0x00, 0x41, 0x36, 0x08, 0x00 ])  # 
      self.ac[0x7e] = bytes([ 0x02, 0x01, 0x02, 0x04, 0x02 ])  # ~
      self.ac[0x7f] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  # 

#
#     alternate characterset
#
      self.hc= { }
      self.hc[0x00] = bytes([ 0x08, 0x1c, 0x3e, 0x1c, 0x08 ])  # diamond
      self.hc[0x01] = bytes([ 0x00, 0x14, 0x08, 0x14, 0x00 ])  # small x
      self.hc[0x02] = bytes([ 0x44, 0x29, 0x11, 0x29, 0x44 ])  # x-bar
      self.hc[0x03] = bytes([ 0x08, 0x1c, 0x2a, 0x08, 0x08 ])  # left arrow
      self.hc[0x04] = bytes([ 0x38, 0x44, 0x44, 0x38, 0x44 ])  # LC alpha
      self.hc[0x05] = bytes([ 0x7e, 0x15, 0x25, 0x25, 0x1a ])  # UC beta
      self.hc[0x06] = bytes([ 0x7f, 0x01, 0x01, 0x01, 0x03 ])  # UC gamma
      self.hc[0x07] = bytes([ 0x10, 0x30, 0x7f, 0x30, 0x10 ])  # down arrow
      self.hc[0x08] = bytes([ 0x60, 0x18, 0x06, 0x18, 0x60 ])  # UC delta
      self.hc[0x09] = bytes([ 0x38, 0x44, 0x44, 0x3c, 0x04 ])  # LC sigma
      self.hc[0x0a] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  # nothing (LF)
      self.hc[0x0b] = bytes([ 0x62, 0x14, 0x08, 0x10, 0x60 ])  # LC lambda
      self.hc[0x0c] = bytes([ 0x40, 0x3c, 0x20, 0x20, 0x1c ])  # LC mu
      self.hc[0x0d] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  # nothing (CR)
      self.hc[0x0e] = bytes([ 0x10, 0x18, 0x78, 0x04, 0x02 ])  # LC tau
      self.hc[0x0f] = bytes([ 0x08, 0x55, 0x77, 0x55, 0x08 ])  # UC phi
      self.hc[0x10] = bytes([ 0x3e, 0x49, 0x49, 0x49, 0x3e ])  # UC theta
      self.hc[0x11] = bytes([ 0x5e, 0x61, 0x01, 0x61, 0x5e ])  # UC omega
      self.hc[0x12] = bytes([ 0x30, 0x4a, 0x4d, 0x49, 0x30 ])  # LC delta
      self.hc[0x13] = bytes([ 0x78, 0x14, 0x15, 0x14, 0x78 ])  # UC A dot
      self.hc[0x14] = bytes([ 0x38, 0x44, 0x45, 0x3e, 0x44 ])  # LC a dot
      self.hc[0x15] = bytes([ 0x78, 0x15, 0x14, 0x15, 0x78 ])  # UC A umlaut
      self.hc[0x16] = bytes([ 0x38, 0x45, 0x44, 0x7d, 0x40 ])  # LC a umlaut
      self.hc[0x17] = bytes([ 0x3c, 0x43, 0x42, 0x43, 0x3c ])  # UC O umlaut
      self.hc[0x18] = bytes([ 0x38, 0x45, 0x44, 0x45, 0x38 ])  # LC o umlaut
      self.hc[0x19] = bytes([ 0x3e, 0x41, 0x40, 0x41, 0x3e ])  # UC U umlaut
      self.hc[0x1a] = bytes([ 0x3c, 0x41, 0x40, 0x41, 0x3c ])  # LC u umlaut
      self.hc[0x1b] = bytes([ 0x7e, 0x09, 0x7f, 0x49, 0x49 ])  # UC AE
      self.hc[0x1c] = bytes([ 0x38, 0x44, 0x38, 0x54, 0x58 ])  # LC ae
      self.hc[0x1d] = bytes([ 0x14, 0x34, 0x1c, 0x16, 0x14 ])  # not equal
      self.hc[0x1e] = bytes([ 0x48, 0x7e, 0x49, 0x41, 0x22 ])  # pound sterling
      self.hc[0x1f] = bytes([ 0x55, 0x2a, 0x55, 0x2a, 0x55 ])  # ?
      self.hc[0x20] = bytes([ 0x00, 0x00, 0x00, 0x00, 0x00 ])  # space
      self.hc[0x21] = bytes([ 0x00, 0x00, 0x5f, 0x00, 0x00 ])  # bang
      self.hc[0x22] = bytes([ 0x00, 0x03, 0x00, 0x03, 0x00 ])  # double quote
      self.hc[0x23] = bytes([ 0x14, 0x7f, 0x14, 0x7f, 0x14 ])  # hash (pound, octothorpe)
      self.hc[0x24] = bytes([ 0x24, 0x2a, 0x7f, 0x2a, 0x12 ])  # dollar
      self.hc[0x25] = bytes([ 0x23, 0x13, 0x08, 0x64, 0x62 ])  # percent
      self.hc[0x26] = bytes([ 0x36, 0x49, 0x56, 0x20, 0x50 ])  # ampersand
      self.hc[0x27] = bytes([ 0x00, 0x00, 0x03, 0x00, 0x00 ])  # single quote
      self.hc[0x28] = bytes([ 0x00, 0x1c, 0x22, 0x41, 0x00 ])  # left parenthesis
      self.hc[0x29] = bytes([ 0x00, 0x41, 0x22, 0x1c, 0x00 ])  # right parenthesis
      self.hc[0x2a] = bytes([ 0x14, 0x08, 0x3e, 0x08, 0x14 ])  # asterisk
      self.hc[0x2b] = bytes([ 0x08, 0x08, 0x3e, 0x08, 0x08 ])  # plus
      self.hc[0x2c] = bytes([ 0x00, 0x40, 0x30, 0x00, 0x00 ])  # comma
      self.hc[0x2d] = bytes([ 0x08, 0x08, 0x08, 0x08, 0x08 ])  # hyphen
      self.hc[0x2e] = bytes([ 0x00, 0x60, 0x60, 0x00, 0x00 ])  # period
      self.hc[0x2f] = bytes([ 0x20, 0x10, 0x08, 0x04, 0x02 ])  # slash
      self.hc[0x30] = bytes([ 0x3e, 0x51, 0x49, 0x45, 0x3e ])  # zero
      self.hc[0x31] = bytes([ 0x00, 0x42, 0x7f, 0x40, 0x00 ])  # one
      self.hc[0x32] = bytes([ 0x62, 0x51, 0x49, 0x49, 0x46 ])  # two
      self.hc[0x33] = bytes([ 0x21, 0x41, 0x49, 0x4d, 0x33 ])  # three
      self.hc[0x34] = bytes([ 0x18, 0x14, 0x12, 0x7f, 0x10 ])  # four
      self.hc[0x35] = bytes([ 0x27, 0x45, 0x45, 0x45, 0x39 ])  # five
      self.hc[0x36] = bytes([ 0x3c, 0x4a, 0x49, 0x48, 0x30 ])  # six
      self.hc[0x37] = bytes([ 0x01, 0x71, 0x09, 0x05, 0x03 ])  # seven
      self.hc[0x38] = bytes([ 0x36, 0x49, 0x49, 0x49, 0x36 ])  # eight
      self.hc[0x39] = bytes([ 0x06, 0x49, 0x49, 0x29, 0x1e ])  # nine
      self.hc[0x3a] = bytes([ 0x00, 0x00, 0x24, 0x00, 0x00 ])  # colon
      self.hc[0x3b] = bytes([ 0x00, 0x40, 0x34, 0x00, 0x00 ])  # semicolon
      self.hc[0x3c] = bytes([ 0x08, 0x14, 0x22, 0x41, 0x00 ])  # less than
      self.hc[0x3d] = bytes([ 0x14, 0x14, 0x14, 0x14, 0x14 ])  # equal
      self.hc[0x3e] = bytes([ 0x00, 0x41, 0x22, 0x14, 0x08 ])  # greater than
      self.hc[0x3f] = bytes([ 0x02, 0x01, 0x51, 0x09, 0x06 ])  # question mark
      self.hc[0x40] = bytes([ 0x3e, 0x41, 0x5d, 0x5d, 0x1e ])  # at
      self.hc[0x41] = bytes([ 0x7e, 0x11, 0x11, 0x11, 0x7e ])  # UC A
      self.hc[0x42] = bytes([ 0x7f, 0x49, 0x49, 0x49, 0x36 ])  # UC B
      self.hc[0x43] = bytes([ 0x3e, 0x41, 0x41, 0x41, 0x22 ])  # UC C
      self.hc[0x44] = bytes([ 0x41, 0x7f, 0x41, 0x41, 0x3e ])  # UC D
      self.hc[0x45] = bytes([ 0x7f, 0x49, 0x49, 0x49, 0x41 ])  # UC E
      self.hc[0x46] = bytes([ 0x7f, 0x09, 0x09, 0x09, 0x01 ])  # UC F
      self.hc[0x47] = bytes([ 0x3e, 0x41, 0x41, 0x51, 0x72 ])  # UC G
      self.hc[0x48] = bytes([ 0x7f, 0x08, 0x08, 0x08, 0x7f ])  # UC H
      self.hc[0x49] = bytes([ 0x00, 0x41, 0x7f, 0x41, 0x00 ])  # UC I
      self.hc[0x4a] = bytes([ 0x20, 0x40, 0x40, 0x40, 0x3f ])  # UC J
      self.hc[0x4b] = bytes([ 0x7f, 0x08, 0x14, 0x22, 0x41 ])  # UC K
      self.hc[0x4c] = bytes([ 0x7f, 0x40, 0x40, 0x40, 0x40 ])  # UC L
      self.hc[0x4d] = bytes([ 0x7f, 0x02, 0x0c, 0x02, 0x7f ])  # UC M
      self.hc[0x4e] = bytes([ 0x7f, 0x04, 0x08, 0x10, 0x7f ])  # UC N
      self.hc[0x4f] = bytes([ 0x3e, 0x41, 0x41, 0x41, 0x3e ])  # UC O
      self.hc[0x50] = bytes([ 0x7f, 0x09, 0x09, 0x09, 0x06 ])  # UC P
      self.hc[0x51] = bytes([ 0x3e, 0x41, 0x51, 0x21, 0x5e ])  # UC Q
      self.hc[0x52] = bytes([ 0x7f, 0x09, 0x19, 0x29, 0x46 ])  # UC R
      self.hc[0x53] = bytes([ 0x26, 0x49, 0x49, 0x49, 0x32 ])  # UC S
      self.hc[0x54] = bytes([ 0x01, 0x01, 0x7f, 0x01, 0x01 ])  # UC T
      self.hc[0x55] = bytes([ 0x3f, 0x40, 0x40, 0x40, 0x3f ])  # UC U
      self.hc[0x56] = bytes([ 0x07, 0x18, 0x60, 0x18, 0x07 ])  # UC V
      self.hc[0x57] = bytes([ 0x7f, 0x20, 0x18, 0x20, 0x7f ])  # UC W
      self.hc[0x58] = bytes([ 0x63, 0x14, 0x08, 0x14, 0x63 ])  # UC X
      self.hc[0x59] = bytes([ 0x03, 0x04, 0x78, 0x04, 0x03 ])  # UC Y
      self.hc[0x5a] = bytes([ 0x61, 0x51, 0x49, 0x45, 0x43 ])  # UC Z
      self.hc[0x5b] = bytes([ 0x00, 0x7f, 0x41, 0x41, 0x00 ])  # left bracket
      self.hc[0x5c] = bytes([ 0x02, 0x04, 0x08, 0x10, 0x20 ])  # backslash
      self.hc[0x5d] = bytes([ 0x00, 0x41, 0x41, 0x7f, 0x00 ])  # right bracket
      self.hc[0x5e] = bytes([ 0x04, 0x02, 0x7f, 0x02, 0x04 ])  # up arrow
      self.hc[0x5f] = bytes([ 0x40, 0x40, 0x40, 0x40, 0x40 ])  # underscore
      self.hc[0x60] = bytes([ 0x00, 0x01, 0x07, 0x01, 0x00 ])  # superscript T
      self.hc[0x61] = bytes([ 0x20, 0x54, 0x54, 0x54, 0x78 ])  # LC a
      self.hc[0x62] = bytes([ 0x7f, 0x48, 0x44, 0x44, 0x38 ])  # LC b
      self.hc[0x63] = bytes([ 0x38, 0x44, 0x44, 0x44, 0x20 ])  # LC c
      self.hc[0x64] = bytes([ 0x38, 0x44, 0x44, 0x48, 0x7f ])  # LC d
      self.hc[0x65] = bytes([ 0x38, 0x54, 0x54, 0x54, 0x08 ])  # LC e
      self.hc[0x66] = bytes([ 0x08, 0x7c, 0x0a, 0x01, 0x02 ])  # LC f
      self.hc[0x67] = bytes([ 0x08, 0x14, 0x54, 0x54, 0x38 ])  # LC g
      self.hc[0x68] = bytes([ 0x7f, 0x10, 0x08, 0x08, 0x70 ])  # LC h
      self.hc[0x69] = bytes([ 0x00, 0x44, 0x7d, 0x40, 0x00 ])  # LC i
      self.hc[0x6a] = bytes([ 0x20, 0x40, 0x40, 0x3d, 0x00 ])  # LC j
      self.hc[0x6b] = bytes([ 0x00, 0x7f, 0x28, 0x44, 0x00 ])  # LC k
      self.hc[0x6c] = bytes([ 0x00, 0x41, 0x7f, 0x40, 0x00 ])  # LC l
      self.hc[0x6d] = bytes([ 0x78, 0x04, 0x18, 0x04, 0x78 ])  # LC m
      self.hc[0x6e] = bytes([ 0x7c, 0x08, 0x04, 0x04, 0x78 ])  # LC n
      self.hc[0x6f] = bytes([ 0x38, 0x44, 0x44, 0x44, 0x38 ])  # LC o
      self.hc[0x70] = bytes([ 0x7c, 0x14, 0x24, 0x24, 0x18 ])  # LC p
      self.hc[0x71] = bytes([ 0x18, 0x24, 0x24, 0x7c, 0x40 ])  # LC q
      self.hc[0x72] = bytes([ 0x7c, 0x08, 0x04, 0x04, 0x08 ])  # LC r
      self.hc[0x73] = bytes([ 0x48, 0x54, 0x54, 0x54, 0x24 ])  # LC s
      self.hc[0x74] = bytes([ 0x04, 0x3e, 0x44, 0x20, 0x00 ])  # LC t
      self.hc[0x75] = bytes([ 0x3c, 0x40, 0x40, 0x20, 0x7c ])  # LC u
      self.hc[0x76] = bytes([ 0x1c, 0x20, 0x40, 0x20, 0x1c ])  # LC v
      self.hc[0x77] = bytes([ 0x3c, 0x40, 0x30, 0x40, 0x3c ])  # LC w
      self.hc[0x78] = bytes([ 0x44, 0x28, 0x10, 0x28, 0x44 ])  # LC x
      self.hc[0x79] = bytes([ 0x44, 0x28, 0x10, 0x08, 0x04 ])  # LC y
      self.hc[0x7a] = bytes([ 0x44, 0x64, 0x54, 0x4c, 0x44 ])  # LC z
      self.hc[0x7b] = bytes([ 0x08, 0x78, 0x08, 0x78, 0x04 ])  # LC pi
      self.hc[0x7c] = bytes([ 0x60, 0x50, 0x58, 0x64, 0x42 ])  # angle
      self.hc[0x7d] = bytes([ 0x08, 0x08, 0x2a, 0x1c, 0x08 ])  # right arrow
      self.hc[0x7e] = bytes([ 0x63, 0x55, 0x49, 0x41, 0x63 ])  # UC sigma
      self.hc[0x7f] = bytes([ 0x7f, 0x08, 0x08, 0x08, 0x08 ])  # lazy T
      self.charset= CHARSET_ASCII

   def set_charset(self,c):
      self.charset=c

   def get(self,c,i):
      if self.charset== CHARSET_ASCII:
         return self.ac[c][i]
      else:
         return self.hc[c][i]
#
# HP82162A tab widget ---------------------------------------------------------
#
class cls_tabhp82162a(cls_tabgeneric):


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
      self.pixelsize=PILCONFIG.get(self.name,"hp82162a_pixelsize",-1)
#
#     create Printer GUI object
#
      self.guiobject=cls_HP82162AWidget(self,self.name,self.papersize)
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
      self.cBut.add_option("Pixel size","hp82162a_pixelsize",T_INTEGER,[O_DEFAULT,1,2])
#
#     add logging control widget
#
      self.add_logging()
#
#     create IL-Interface object, notify printer processor object
#
      self.pildevice= cls_pilhp82162a(self.guiobject)
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
# HP82162A widget classes - GUI component of the HP82162A HP-IL printer
#
class cls_HP82162AWidget(QtWidgets.QWidget):

   def __init__(self,parent,name,papersize):
      super().__init__()
      self.name= name
      self.parent= parent
      self.papersize= papersize
      self.pildevice= None
#
#     configuration
#
      self.pdfpixelsize=3
      self.pixelsize=PILCONFIG.get_dual(self.name,"hp82162a_pixelsize")
      self.linebuffersize=HP82162A_LINEBUFFERSIZE
      self.printer_modeswitch= PILCONFIG.get(self.name,"modeswitch",MODESWITCH_MAN)
#
#     create user interface of printer widget
#
      self.hbox=QtWidgets.QHBoxLayout()
      self.hbox.addStretch(1)
#
#     scrolled printer view
#
      self.printview=cls_ScrolledHP82162AView(self,self.name,self.pixelsize, self.pdfpixelsize,self.papersize,self.linebuffersize)
      self.hbox.addWidget(self.printview)
      self.vbox=QtWidgets.QVBoxLayout()
#
#     radio buttons Man, Norm, Trace
#
      self.gbox= QtWidgets.QGroupBox()
      self.gbox.setFlat(True)
      self.gbox.setTitle("Printer mode")
      self.vboxgbox= QtWidgets.QVBoxLayout()
      self.gbox.setLayout(self.vboxgbox)
#
#     Man Mode
#
      self.radbutMan= QtWidgets.QRadioButton(self.gbox)
      self.radbutMan.setEnabled(False)
      self.radbutMan.setText("Man")
      self.radbutMan.toggled.connect(self.toggledCheckBoxes)
      self.vboxgbox.addWidget(self.radbutMan)
#
#     Trace Mode
#
      self.radbutTrace= QtWidgets.QRadioButton(self.gbox)
      self.radbutTrace.setEnabled(False)
      self.radbutTrace.setText("Trace")
      self.radbutTrace.toggled.connect(self.toggledCheckBoxes)
      self.vboxgbox.addWidget(self.radbutTrace)
#
#     Norm Mode
#
      self.radbutNorm= QtWidgets.QRadioButton(self.gbox)
      self.radbutNorm.setEnabled(False)
      self.radbutNorm.setText("Norm")
      self.radbutNorm.toggled.connect(self.toggledCheckBoxes)
      self.vboxgbox.addWidget(self.radbutNorm)

      self.vbox.addWidget(self.gbox)
#
#     Clear Button
#
      self.clearButton= QtWidgets.QPushButton("Clear")
      self.clearButton.setEnabled(False)
      self.clearButton.setAutoDefault(False)
      self.vbox.addWidget(self.clearButton)
      self.clearButton.clicked.connect(self.do_clear)
#
#     Print Button
#
      self.printButton= QtWidgets.QPushButton("Print")
      self.printButton.setEnabled(False)
      self.printButton.setAutoDefault(False)
      self.vbox.addWidget(self.printButton)
      self.printButton.pressed.connect(self.do_print_pressed)
      self.printButton.released.connect(self.do_print_released)
#
#     Paper Advance Button
#
      self.advanceButton= QtWidgets.QPushButton("Advance")
      self.advanceButton.setEnabled(False)
      self.advanceButton.setAutoDefault(False)
      self.vbox.addWidget(self.advanceButton)
      self.advanceButton.pressed.connect(self.do_advance_pressed)
      self.advanceButton.released.connect(self.do_advance_released)
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
#     initialize timer for the repeated pressed advance button action
#
      self.repeatedAdvpressedTimer=QtCore.QTimer()
      self.repeatedAdvpressedTimer.timeout.connect(self.repeated_advpressed)
      self.repeatedAdvpressedTimer.setInterval(1500)
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
      self.setCheckBoxes()
      if self.printer_modeswitch== MODESWITCH_MAN:
         self.pildevice.put_cmd(CMD_MAN)
      if self.printer_modeswitch== MODESWITCH_TRACE:
         self.pildevice.put_cmd(CMD_TRACE)
      if self.printer_modeswitch== MODESWITCH_NORM:
         self.pildevice.put_cmd(CMD_NORM)
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
         self.radbutMan.setEnabled(True)
         self.radbutTrace.setEnabled(True)
         self.radbutNorm.setEnabled(True)
         self.clearButton.setEnabled(True)
         self.printButton.setEnabled(True)
         self.advanceButton.setEnabled(True)
         self.pdfButton.setEnabled(True)
      else:
         self.radbutMan.setEnabled(False)
         self.radbutTrace.setEnabled(False)
         self.radbutNorm.setEnabled(False)
         self.clearButton.setEnabled(False)
         self.printButton.setEnabled(False)
         self.advanceButton.setEnabled(False)
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

   def do_print_pressed(self):
      self.pildevice.put_cmd(CMD_PRINT_PRESSED)
      return

   def do_advance_pressed(self):
      self.pildevice.put_cmd(CMD_ADV_PRESSED)
      self.repeatedAdvpressedTimer.start()
      return

   def do_print_released(self):
      self.pildevice.put_cmd(CMD_PRINT_RELEASED)
      return

   def do_advance_released(self):
      self.pildevice.put_cmd(CMD_ADV_RELEASED)
      self.repeatedAdvpressedTimer.stop()
      return

   def do_pdf(self):
      self.pdf_columns=PILCONFIG.get(self.name,"pdfcolumns",3)
      options=cls_PdfOptions.getPdfOptions(self.pdf_columns,"")
      if options== "":
         return
      PILCONFIG.put(self.name,"pdfcolumns",options[1])
      self.printview.pdf(options[0],options[1],options[2])
      return
#
#  handle change of check boxes
#
   def toggledCheckBoxes(self):
      if self.radbutMan.isChecked():
         self.pildevice.put_cmd(CMD_MAN)
         self.printer_modeswitch= MODESWITCH_MAN
         self.setCheckBoxes()
      if self.radbutTrace.isChecked():
         self.pildevice.put_cmd(CMD_TRACE)
         self.printer_modeswitch= MODESWITCH_TRACE
         self.setCheckBoxes()
      if self.radbutNorm.isChecked():
         self.pildevice.put_cmd(CMD_NORM)
         self.printer_modeswitch= MODESWITCH_NORM
         self.setCheckBoxes()
      PILCONFIG.put(self.name,"modeswitch",self.printer_modeswitch)
#
#  set check box according to self.printer_modeswitch
#
   def setCheckBoxes(self):
      if self.printer_modeswitch== MODESWITCH_NORM:
         self.radbutNorm.setChecked(True)
         self.radbutMan.setChecked(False)
         self.radbutTrace.setChecked(False)
      if self.printer_modeswitch== MODESWITCH_MAN:
         self.radbutNorm.setChecked(False)
         self.radbutMan.setChecked(True)
         self.radbutTrace.setChecked(False)
      if self.printer_modeswitch== MODESWITCH_TRACE:
         self.radbutNorm.setChecked(False)
         self.radbutMan.setChecked(False)
         self.radbutTrace.setChecked(True)
      return
#
#  put command into the GUI-command queue, this is called by the thread component
#
   def put_cmd(self,item):
       self.gui_queue_lock.acquire()
       self.gui_queue.put(item)
       self.gui_queue_lock.release()
#
#  repeated adv pressed action
#
   def repeated_advpressed(self):
      b=bytes(0)
      self.put_cmd([REMOTECMD_PRINT,b,1])
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
   def process(self,item):
      cmd= item[0]
#
#     clear graphhics views 
#
      if cmd==  REMOTECMD_CLEAR:
         self.printview.reset()
#
#     output line
#
      elif cmd== REMOTECMD_PRINT:
         line= item[1]
         col_idx= item[2]
         self.printview.add_line(line,col_idx)
#
#     log line
#
      elif cmd== REMOTECMD_LOG:
         self.parent.cbLogging.logWrite(item[1])
         self.parent.cbLogging.logFlush()
#
# custom class for scrolled hp82162a output widget ----------------------------
#
class cls_ScrolledHP82162AView(QtWidgets.QWidget):

   def __init__(self,parent,name,pixelsize,pdfpixelsize,papersize,linebuffersize):
      super().__init__(parent)
      self.parent=parent
      self.name=name
#     
#     create window and scrollbars
#
      
      self.hbox= QtWidgets.QHBoxLayout()
      self.scrollbar= QtWidgets.QScrollBar()
      self.hp82162awidget= cls_HP82162aView(self,self.name,pixelsize,pdfpixelsize,papersize,linebuffersize)
      self.hp82162awidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
      self.hp82162awidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
      self.hbox.addWidget(self.hp82162awidget)
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
      self.hp82162awidget.do_scroll(self.scrollbar.value())
#
#   add line to printer output window
#
   def add_line(self,line,col_idx):
      self.hp82162awidget.add_line(line,col_idx)
#
#   reset output window
#
   def reset(self):
      self.hp82162awidget.reset()
      self.scrollbar.setMinimum(0)
      self.scrollbar.setMaximum(0)
      self.scrollbar.setSingleStep(1)
#
#   generate pdf output
#
   def pdf(self,filename,columns,title):
      self.hp82162awidget.pdf(filename,columns,title)
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
      self.hp82162awidget.reconfigure()
      return
      
#
# custom class for hp82162a output  -----------------------------------------
#
class cls_HP82162aView(QtWidgets.QGraphicsView):

   def __init__(self,parent,name,pixelsize,pdfpixelsize,papersize,linebuffersize):
      super().__init__()
      self.parent=parent
      self.name= name
#
#     initial output window in reconfigure
#
      self.pixelsize= -1
      self.w=-1
      self.h=-1
      self.pdfpixelsize= pdfpixelsize
      self.pdfw=PRINTER_WIDTH_CHARS*PRINTER_CHARACTER_WIDTH_PIXELS*pdfpixelsize
      self.pdfh=PRINTER_CHARACTER_HEIGHT_PIXELS*pdfpixelsize
      self.rows= 0
      self.linebuffersize= linebuffersize
      self.papersize= papersize
#
#     background is always white
#
      self.setAutoFillBackground(True)
      p=self.palette()
      p.setColor(self.backgroundRole(),QtCore.Qt.white)
      self.setPalette(p)

#
#     initialize line bitmap buffer
#
      self.lb= [None] * linebuffersize
      self.lb_current= -1
      self.lb_anz=0
      self.lb_position=0

      self.printscene=None
      self.pdfprinter=None
      self.reconfigure()
#
#     configure/reconfigure the printview widget, scene and its content
#
   def reconfigure(self):
      tmp=PILCONFIG.get_dual(self.name,"hp82162a_pixelsize")
#
#     re/configure the printview widget
#
      if tmp != self.pixelsize:
         self.pixelsize=tmp
         self.w=PRINTER_WIDTH_CHARS*PRINTER_CHARACTER_WIDTH_PIXELS*self.pixelsize
         self.h=PRINTER_CHARACTER_HEIGHT_PIXELS*self.pixelsize
#
#        set fixed width
#
         self.setFixedWidth(self.w+2*self.pixelsize)
#
#        initialize scene if not existing
#
         if  self.printscene is None:
            self.printscene= cls_hp82162a_scene(self,self.pixelsize)
            self.setScene(self.printscene)
            self.reset()
#
#        otherwise reconfigure scene and its content
#
         else:
            self.printscene.reconfigure(self.pixelsize)
            for i in range(0,self.linebuffersize):
               if self.lb[i] is not None:
                  self.lb[i].reconfigure(self.pixelsize)
            self.do_resize()
#
#       now shrink all parent windows to minimum size
#
#        w=self.parentWidget()
#        while w is not None:
#           w.adjustSize()
#           w=w.parentWidget()
      return
#
#      reset output window
#
   def reset(self):
      for i in range(0,self.linebuffersize):
         if self.lb[i] is not None:
            self.lb[i]= None
      self.lb_current= -1
      self.lb_anz=0
      self.lb_position=0
      self.printscene.reset()
#
#  overwrite standard events
#
#  resize event, adjust the scene size, reposition everything and redraw
#
   def resizeEvent(self,event):
      self.do_resize()

   def do_resize(self):
      h=self.height()
      self.rows=h // (PRINTER_CHARACTER_HEIGHT_PIXELS*self.pixelsize) 
      self.printscene.set_scenesize(self.rows)
      scroll_max=self.lb_current- self.rows+1
      if scroll_max < 0:
         scroll_max=0
      self.parent.scrollbar.setMaximum(scroll_max)
      self.parent.scrollbar.setPageStep(self.rows)
      self.printscene.update_scene()
      return
#
#  Mouse wheel event
#
   def wheelEvent(self,event):
       numDegrees= event.angleDelta()/8
       delta=0
       if numDegrees.y() is not None:
          if numDegrees.y() < 0:
             delta=1 
          if numDegrees.y() > 0:
             delta=-1
       event.accept()
       if self.lb_current < self.rows:
          return
       if self.lb_position+delta <0 or self.lb_position+delta+self.rows-1 > self.lb_current:
          return
       self.lb_position+=delta
       self.parent.scrollbar.setValue(self.lb_position)
       self.printscene.update_scene()
       return
#
#  external methods
#
   def add_line(self,line,col_idx):
#
#     add line bitmap to line bitmap buffer
#
      if self.lb_anz < self.linebuffersize:
         self.lb_anz+=1
         self.lb_current+=1
         self.lb[self.lb_current]=cls_hp82162a_line(line,col_idx,self.pixelsize,)
      else:
         self.lb= self.lb[1:] + self.lb[:1]
         self.lb[self.lb_current]=cls_hp82162a_line(line,col_idx,self.pixelsize,)
      self.lb_position=self.lb_current- self.rows+1
      if self.lb_position < 0:
         self.lb_position=0
      self.parent.scrollbar.setMaximum(self.lb_position)
      self.parent.scrollbar.setValue(self.lb_position)

      self.printscene.update_scene()
#
#     scroll bar action
#
   def do_scroll(self,value):
      self.lb_position=value
      self.printscene.update_scene()
#
#     PDF output of lb buffer content, prints with page number and optional
#     header. Output is formatted in 1-3 columns
#
   def pdf(self,filename,columns,title):
      
      self.pdfprinter= cls_pdfprinter(self.papersize,PDF_ORIENTATION_PORTRAIT,filename, title, True, columns)
      self.pdfprinter.begin()
# 
#     process lines
#
      k=0
      while True:
#
#         end of output
#
          if k == self.lb_anz:
             break
          item_args= cls_hp82162a_line.from_hp82162a_line(self.lb[k])
          item= cls_hp82162a_line(item_args[0],item_args[1],self.pdfpixelsize)
          self.pdfprinter.print_item(item)
          k+=1
      self.pdfprinter.end()

#
# custom class for line bitmap ----------------------------------------------
#
class cls_hp82162a_line(QtWidgets.QGraphicsItem):

   def __init__(self,line, col_idx, pixelsize):
      super().__init__()
      self.pixelsize=-1
      self.w=-1
      self.h=-1
      self.rect= QtCore.QRectF(0,0,1,1)
      self.col_idx=col_idx
      self.line=bytes(line[:col_idx])
      self.reconfigure(pixelsize)

   def reconfigure(self,pixelsize):
      self.pixelsize=pixelsize
      self.w=PRINTER_WIDTH_CHARS*PRINTER_CHARACTER_WIDTH_PIXELS*pixelsize
      self.h=PRINTER_CHARACTER_HEIGHT_PIXELS*pixelsize
      self.rect= QtCore.QRectF(0,0,self.w,self.h)

   def setPos(self,x,y):
      super().setPos(x,y-self.h)


   def boundingRect(self):
      return self.rect
#
#  paint bitmap
#
   def paint(self,painter,option,widget):
      
       posx=0
       for b in self.line:
          posy=0
          for i in range(0,8):
             if b & 0x01:
                painter.fillRect(posx,posy,self.pixelsize,self.pixelsize,QtCore.Qt.black)
             b= b>>1
             posy+= self.pixelsize
          posx+= self.pixelsize
#
# get a copy of the constructor parameters
#
   @classmethod
   def from_hp82162a_line(cls, class_instance):
      line= copy.deepcopy(class_instance.line)
      return(line,class_instance.col_idx)

#
# custom class for hp82162a graphics scene
#
class cls_hp82162a_scene(QtWidgets.QGraphicsScene):

   def __init__(self,parent,pixelsize):
      super().__init__()
      self.rows= 0
      self.w=0
      self.h=0
      self.parent=parent
      self.si= None
      self.reconfigure(pixelsize)
      return
#
#  re/configure graphics scene
#
   def reconfigure(self,pixelsize):
      self.pixelsize=pixelsize
      self.w=PRINTER_WIDTH_CHARS*PRINTER_CHARACTER_WIDTH_PIXELS*pixelsize
      self.h=PRINTER_CHARACTER_HEIGHT_PIXELS*pixelsize
      return
#
#  set or change the size of the scene
#
   def set_scenesize(self,rows):
      self.reset()
      self.rows= rows
      self.si= [None] * rows
      self.setSceneRect(0,0,self.w,self.h*self.rows)
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
      y=self.h
      j=0
      for i in range(start,end):
         self.si[j]=self.parent.lb[i]
         self.addItem(self.si[j])
         self.si[j].setPos(0,y)
         y+=self.h+DISPLAY_LINE_SPACING*self.pixelsize
         j+=1                         
#
# custom class open pdf output file and set options
#

class cls_PdfOptions(QtWidgets.QDialog):

   def __init__(self,columns,title):
      super().__init__()
      self.columns=columns
      self.title=title
      self.filename=""
      self.setWindowTitle('HP82162A PDF output')
      self.vlayout = QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)
      self.glayout = QtWidgets.QGridLayout()
      self.vlayout.addLayout(self.glayout)

      self.glayout.addWidget(QtWidgets.QLabel("PDF Output Options"),0,0,1,3)
      self.glayout.addWidget(QtWidgets.QLabel("Output file:"),1,0)
      self.lfilename=QtWidgets.QLabel(self.filename)
      self.glayout.addWidget(self.lfilename,1,1)
      self.butchange=QtWidgets.QPushButton("Change")
      self.butchange.setFixedWidth(60)
      self.glayout.addWidget(self.butchange,1,2)
      self.glayout.addWidget(QtWidgets.QLabel("Title:"),2,0)
      self.edttitle=QtWidgets.QLineEdit()
      self.edttitle.setText(self.title)
      self.edttitle.setFixedWidth(200)
      self.glayout.addWidget(self.edttitle,2,1,1,2)
      self.glayout.addWidget(QtWidgets.QLabel("Columns:"),3,0)
      self.spincolumns=QtWidgets.QSpinBox()
      self.spincolumns.setMinimum(1)
      self.spincolumns.setMaximum(PDF_MAX_COLS)
      self.spincolumns.setValue(self.columns)
      self.glayout.addWidget(self.spincolumns,3,1,1,2)

      self.buttonBox = QtWidgets.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.hlayout = QtWidgets.QHBoxLayout()
      self.hlayout.addWidget(self.buttonBox)
      self.vlayout.addLayout(self.hlayout)
      self.butchange.clicked.connect(self.change_pdffile)

   def get_pdfFilename(self):
      dialog=QtWidgets.QFileDialog()
      dialog.setWindowTitle("Enter PDF file name")
      dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
      dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
      dialog.setDefaultSuffix("pdf")
      dialog.setNameFilters( ["PDF (*.pdf )", "All Files (*)"] )
      dialog.setOptions(QtWidgets.QFileDialog.DontUseNativeDialog)
      if dialog.exec():
         return dialog.selectedFiles()

   def change_pdffile(self):
      flist= self.get_pdfFilename()
      if flist is None:
         return
      self.filename= flist [0]
      self.lfilename.setText(self.filename)
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
           

   def do_ok(self):
      super().accept()

   def do_cancel(self):
      super().reject()

   @staticmethod
   def getPdfOptions(columns,title):
      dialog= cls_PdfOptions(columns,title)
      result= dialog.exec()
      if result== QtWidgets.QDialog.Accepted:
         return dialog.lfilename.text(), dialog.spincolumns.value(), dialog.edttitle.text()
      else:
         return ""
#
# Printer buffer object each entry has the following information:
# value: value of entry
# types: character, column data, barcode data
# mode: current printer mode (we need double wide and lowercase mode)
# width: pixel width of information
#
class cls_printer_buffer(object):

   def __init__(self):
      self.buffer= []
      self.buffer_pxlen=0         # total length of buffer entries in pixel
      self.buffer_fmtpos=-1       # position of first fmt specifier

   def add(self,v,t,m):
      s=0
      if t== type_column:
         if m & mode_doublewide:
            s=2
         else:
            s=1
      if t== type_char:
         if m & mode_doublewide:
            s=14
         else:
            s=7
      if t== type_skip:
         if v >= 0xa0 and v <= 0xb7:
            n= v - 0xa0
            if m & mode_doublewide:
               s= 14 * n
            else:
               s= 7 * n
         if v >= 0xb8 and v <= 0xbf:
            n= v- 0xb8
            if m & mode_doublewide:
               s= 2 * n
            else:
               s= n
      if t== type_format and self.buffer_fmtpos<0:
            self.buffer_fmtpos=len(self.buffer)
      self.buffer.append([v,t,m,s])
      self.buffer_pxlen+=s
      return 

   def get(self,idx):
      if idx >= len(self.buffer):
         return None
      return self.buffer[idx]

   def clear(self):
      self.buffer_pxlen=0
      self.buffer_fmtpos= -1
      del self.buffer[:]

   def length(self):
      return len(self.buffer)
   
   def pxlen(self):
      return (self.buffer_pxlen)

   def fmtpos(self):
      return(self.buffer_fmtpos)
#
# line buffer object -------------------------------------------------------
#
class cls_line_buffer(object):

   def __init__(self,guiobject):
      self.guiobject= guiobject                 # reference to GUI object 
      self.linebuffer= bytearray(PRINTER_WIDTH) # the line buffer
      self.linebuffer_index=0                   # current index in line buffer
      self.wrap_position=-1                     # pointer to wrap line position
#
#  clear line buffer
#
   def clear(self):
      self.linebuffer_index=0
      self.wrap_position= -1
#
#  print whole content of line buffer (end of line condition)
#
   def prt(self):
      linebuffer_copy=copy.deepcopy(self.linebuffer)
      self.guiobject.put_cmd([REMOTECMD_PRINT,linebuffer_copy,self.linebuffer_index])
      self.linebuffer_index=0
      self.wrap_position= -1
#
#  add column to line buffer, if we have an overflow then print it. If we are in
#  parse mode then break line at self.wrap_position
#
   def add(self,c,mode,wrap):
      if wrap:
         self.wrap_position=self.linebuffer_index
      if self.linebuffer_index== PRINTER_WIDTH:
         if mode & mode_parse and self.wrap_position>0:
            linebuffer_copy=copy.deepcopy(self.linebuffer[:self.wrap_position-1])
            self.guiobject.put_cmd([REMOTECMD_PRINT,linebuffer_copy,self.wrap_position-1])
#           next data
            do_copy=False
            j=1
            self.linebuffer[0]=0
            for i in range (PRINTER_WIDTH- self.wrap_position):
               k=i+self.wrap_position
               if self.linebuffer[k]!= 0 and not do_copy:
                  do_copy= True
               if do_copy:
                  self.linebuffer[j]= self.linebuffer[k]
                  self.linebuffer[k]= 0
                  j+=1

            self.linebuffer_index= j
            self.wrap_positon= -1
         else:
            linebuffer_copy=copy.deepcopy(self.linebuffer)
            self.guiobject.put_cmd([REMOTECMD_PRINT,linebuffer_copy,self.linebuffer_index])
            self.linebuffer_index=0
            self.wrap_position= -1

      self.linebuffer[self.linebuffer_index]=c
      self.linebuffer_index+=1
#
# HP82162A emulator (thread component) --------------------------------------
#

class cls_special_k(QtCore.QObject):

   def __init__(self,parent,guiobject):
      super().__init__()
      self.pildevice=parent
      self.guiobject= guiobject
      self.printer_buffer= cls_printer_buffer()         # printer buffer
      self.line_buffer= cls_line_buffer(self.guiobject) # line buffer
      self.char_gen= hp82162a_char() # character generator
      self.esc= False                # escape mode
      self.esc_seq=""                # escape sequence
      self.esc_prefix=""             # prefix of combined esc sequence
      self.printer_mode=0            # printer mode bits
      self.num_barcode=0             # number of barcodes to read
      self.num_graphics=0            # number of graphics codes to read
      self.bclist= { }
      self.bcline= { }
#
#     device clear, carriage positioned to right, print buffer cleared modes set
#     to Escape, Single Wide, Left-Justify and Nonparse
#
   def reset(self):
      self.printer_buffer.clear()
      self.line_buffer.clear()
      self.esc= False           
      self.esc_seq=""           
      self.esc_prefix=""
      self.printer_mode=0
      self.char_gen.set_charset(CHARSET_ASCII)
      self.num_barcode=0
      self.num_graphics=0
#
#     issue clear to GUI
#
      self.guiobject.put_cmd([REMOTECMD_CLEAR])
#
#     we are idle and buffer is empty
#
      self.set_status(STA_BE)
      self.set_status(STA_ID) 
#
#  set, clear, query printer mode
#
   def setMode(self,mode_bit):
      self.printer_mode= self.printer_mode | mode_bit

   def clearMode(self,mode_bit):
      mask= ~ mode_bit
      self.printer_mode= self.printer_mode & mask

   def isMode(self,mode_bit):
      if (self.printer_mode & mode_bit):
         return True
      else:
         return False
#
#  process barcodes
#
   def add_bar(self,length,fill):
      for i in range(length):
         if len(self.bcline)== PRINTER_CHARACTER_HEIGHT_PIXELS:
            self.bclist.append(self.bcline)
            self.bcline= []
         if fill:
            self.bcline.append(1)
         else:
            self.bcline.append(0)
      
   def process_barcodes(self):

      self.bclist= []
      self.bcline= []
      self.add_bar(3,True)
      self.add_bar(3,False)
      self.add_bar(3,True)
      self.add_bar(3,False)
      for i in range (self.printer_buffer.length()):
         ret= self.printer_buffer.get(i)
         code=ret[0]
         b= 128
         for j in range(8):
            if b & code:
               self.add_bar(6,True)
            else:
               self.add_bar(3,True)
            self.add_bar(3,False)
            b= b // 2
      self.add_bar(6,True)
      self.add_bar(3,False)
      self.add_bar(3,True)
      while len(self.bcline)< PRINTER_CHARACTER_HEIGHT_PIXELS:
         self.add_bar(1,False)
      self.bclist.append(self.bcline)
      return
#
#  add column to line buffer
#
   def add_column(self,c,mode):
#
#     put column data into line buffer
#
      self.line_buffer.add(c,mode,False)
      if mode & mode_doublewide:
         self.line_buffer.add(c,mode,False)

#
#  generate character in line buffer
#
   def add_char(self,c,mode):
#
#     blank is wrap position
#
      wrap=False
      if c== 0x20:
         wrap=True
#
#     in lowercase mode convert uppercase chars
#
      if (mode & mode_lowercase) and (c >=0x41 and  c <= 0x5A):
         c+=0x20
#
#     leading space
#
      self.line_buffer.add(0,mode,wrap)
      if mode & mode_doublewide:
         self.line_buffer.add(0,mode,False)
#
#     get bitmap, handle double wide
#
      for col in range(0,5):
         col_data=self.char_gen.get(c, col)
         self.line_buffer.add(col_data,mode,False)
         if mode & mode_doublewide:
            self.line_buffer.add(col_data,mode,False)
#
#     trailing space
#
      self.line_buffer.add(0,mode,False)
      if mode & mode_doublewide:
         self.line_buffer.add(0,mode,False)
      return True

#
#  end of line, process buffer
#
   def process_line(self):

      buffer_idx=0
      fmtpos= self.printer_buffer.fmtpos()
      log_line=""
#
#     right justify buffer if we do not have a format specifier
#
      if (self.isMode(mode_rjust) and fmtpos<0):
         shift= PRINTER_WIDTH - self.printer_buffer.pxlen()
         for i in range(shift):
            self.add_column(0,0)
#
#     center, if format specifier is at the beginning or the end of the buffer
#
      if fmtpos >=0:
         if fmtpos==0 or fmtpos== self.printer_buffer.length()-2:
            freecols=PRINTER_WIDTH - self.printer_buffer.pxlen()
            shift= freecols//2
            if freecols % 2 == 1:
               shift+=1
            for i in range(shift):
               self.add_column(0,0)
            fmtpos= -1
#
#     output content
#
      while buffer_idx < self.printer_buffer.length():
         ret= self.printer_buffer.get(buffer_idx)
         v= ret[0]
         t= ret[1]
         m= ret[2]
#
#        check if we have spacing format specifier right in the middle
#
         if fmtpos >=0:
            if buffer_idx== fmtpos:
               freecols=PRINTER_WIDTH - self.printer_buffer.pxlen()
               for i in range(freecols):
                  self.add_column(0,0) 
               fmtpos= -1
#
#        add character to line buffer
#
         if t== type_char:
            self.add_char(v,m)
            if self.isMode(mode_8bit):
               log_line+= charconv(chr(v),CHARSET_HP41)
            else:
               log_line+= charconv(chr(v),CHARSET_ROMAN8)
#
#        add column to line buffer
#
         if t== type_column:
            self.add_column(v,m)
#
#        generate blank characters or blank columns to line buffer
#
         if t== type_skip:
            if v >= 0xa0 and v <= 0xb7:
               n= v-0xa0
               for i in range(n):
                  self.add_char(0x20,m)
            if v >= 0xb8 and v <= 0xbf:
               n=v-0xb8
               for i in range(n):
                  self.add_column(0,m)
         buffer_idx+=1
#
#     send line buffer to GUI
#
      self.line_buffer.prt()
#
#     send log output to GUI
#
      if log_line !="":
         log_line+="\n"
         self.guiobject.put_cmd([REMOTECMD_LOG,log_line])
#
# clear line buffer and printer buffer
#
      self.line_buffer.clear()
      self.printer_buffer.clear()
#
# update status information
#
      self.set_status(STA_EL)
      self.set_status(STA_BE)
#
#  process escape sequences
#
   def process_esc(self):
#
#     switch to 8 bit mode
#
      if self.esc_seq=="|":
         self.setMode(mode_8bit)
         self.set_status(STA_EB)
         self.char_gen.set_charset(CHARSET_ALTERNATE)
         return
#
#     single width
#
      elif self.esc_seq=="&k0S":
         self.clearMode(mode_doublewide)
         self.clear_status(STA_DW)
         return
#
#     double width
#
      elif self.esc_seq=="&k1S":
         self.setMode(mode_doublewide)
         self.set_status(STA_DW)
         return
#
#     left justify
#
      elif self.esc_seq=="&l0J":
         self.clearMode(mode_rjust)
         self.clear_status(STA_RJ)
         return
#
#     right justify
#
      elif self.esc_seq=="&l1J":
         self.setMode(mode_rjust)
         self.set_status(STA_RJ)
         return
#
#     Graphic
#
      elif self.esc_seq.startswith("*b") and self.esc_seq.endswith("G"):
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
         return
#
#     barcode
#
      elif self.esc_seq.startswith("*z") and self.esc_seq.endswith("B"):
         ret=re.findall(r"\d+",self.esc_seq)
         if ret== []:
            return
         try:
            n=int(ret[0])
         except ValueError:
            return
         if n<0 or n> 16:
            return
         self.num_barcode=n
         return
#
#     format
#
      elif self.esc_seq=="&l2J":
         self.printer_buffer.add(0,type_format,self.printer_mode)
         self.printer_buffer.add(0,type_format,self.printer_mode)
         return
#
#     skip characters
#
      elif self.esc_seq.startswith("&a+") and self.esc_seq.endswith("C"):
         ret=re.findall(r"\d+",self.esc_seq)
         if ret== []:
            return
         try:
            n=int(ret[0])
         except ValueError:
            return
         if n<0 or n> 23:
            return
         n+= 0xa0
         self.printer_buffer.add(n,type_skip,self.printer_mode)
         return
#
#    skip columns
#
      elif self.esc_seq.startswith("&a+") and self.esc_seq.endswith("D"):
         ret=re.findall(r"\d+",self.esc_seq)
         if ret== []:
            return
         try:
            n=int(ret[0])
         except ValueError:
            return
         if n<0 or n> 7:
            return
         n+= 0xb8
         self.printer_buffer.add(n,type_skip,self.printer_mode)
         return
#
#    skip absolute
#
      elif self.esc_seq.startswith("&a") and self.esc_seq.endswith("D"):
         ret=re.findall(r"\d+",self.esc_seq)
         if ret== []:
            return
         try:
            n=int(ret[0])
         except ValueError:
            return
         if n<0 or n> 168:
            return
         skip=n-self.printer_buffer.pxlen()
         if n<=0:
            return
         skip_chars= skip // PRINTER_CHARACTER_WIDTH_PIXELS
         n= skip_chars+ 0xa0
         self.printer_buffer.add(n,type_skip,self.printer_mode)
         skip_columns= skip % PRINTER_CHARACTER_WIDTH_PIXELS
         n= skip_columns+ 0xb8
         self.printer_buffer.add(n,type_skip,self.printer_mode)
         return
#
#     nonparse mode
#
      elif self.esc_seq=="&k0H":
         self.clearMode(mode_parse)
         return
#
#     parse mode
#
      elif self.esc_seq=="&k1H":
         self.setMode(mode_parse)
         return
      return
#
#  main printer data processing method
#
   def process_char(self,ch):
#
#     barcode mode, accumulate code numbers to buffer
#
      if self.num_barcode > 0:
         self.printer_buffer.add(ch,type_barcode,self.printer_mode)
         self.num_barcode-=1
#
#        all barcodes read, process line
#
         if self.num_barcode==0:
            self.process_barcodes()
         return
#
#     graphics mode (ESC mode only), add columns to buffer
#
      if self.num_graphics > 0:
         self.printer_buffer.add(ch,type_column,self.printer_mode)
         self.num_graphics-=1
         return
#
#     process ESC sequences
#
      if (self.esc== False) and (ch== 0x1B) and not self.isMode(mode_8bit):
         self.esc= True
         self.esc_seq=""
         self.esc_prefix=""
         return
      if self.esc:
#
#        ESC | or escape sequence terminated with capital letter
#
#        if ch == 0x7c or (ch >= 0x41 and ch <= 0x5A):
         if chr(ch) in "|CDHSJGB":
            self.esc_seq+= chr(ch)
            if self.esc_prefix!="":
               self.esc_seq= self.esc_prefix+self.esc_seq
            self.process_esc()
            self.esc= False
            self.esc_seq=""
            self.esc_prefix=""
            return
#
#        repeated escape sequence terminated with lowercase letter
#        unfortunately b occurs in two escape sequences at different positions
#
         if chr(ch) in "cdhsjgb" and len(self.esc_seq)>2:
            if self.esc_prefix == "":
               self.esc_prefix= self.esc_seq[:2]
               self.esc_seq= self.esc_seq[2:]
            self.esc_seq= self.esc_prefix+self.esc_seq+chr(ch).upper()
            self.process_esc()
            self.esc_seq=""
            return
#
#        still in escape sequence, accumulate characters
#            
         self.esc_seq+= chr(ch)
         return
#
#     not in escape sequence, everything goes to the printer buffer now
#
#
#     ignore line feed
#
      if ch== 0x0A and not self.isMode(mode_column):
         return
#
#     cr is end of line
#
      if ch == 0x0D and not self.isMode(mode_column):
         self.process_line()
         return
#
#     do normal processing: 8bit and escape mode
#
      if self.isMode(mode_8bit):
#
#        normal character or column
#
         if ch <= 0x7F:
            self.clear_status(STA_EL)
            self.clear_status(STA_BE)
            if self.isMode(mode_column):
               self.printer_buffer.add(ch,type_column,self.printer_mode)
            else:
               self.printer_buffer.add(ch,type_char,self.printer_mode)
#
#        barcode (only valid in column mode, this is not handled here)
#        buffers are reset
#
         elif ch >= 0x80 and ch <= 0x8F:
            self.num_barcode= ch - 0x7F
            self.printer_buffer.clear()
            self.line_buffer.clear()
#
#        skip characters
#
         elif ch >= 0xA0 and ch <= 0xB7:
            self.printer_buffer.add(ch,type_skip,self.printer_mode)
#
#        skip columns
#
         elif ch >= 0xB8 and ch <= 0xBF:
            self.printer_buffer.add(ch,type_skip,self.printer_mode)
#
#        format specifier (2 characters to read)
#
         elif ch== 0xC0:
            self.printer_buffer.add(0,type_format,self.printer_mode)
            self.printer_buffer.add(0,type_format,self.printer_mode)
#
#        select width, upper/lowercase, character/column mode
#        bit0 is lowercase flag
#        bit1 is column mode flag
#        bit2 is double wide flag
#        bit3 is used, but unknown to me (Parse mode?)
#
         elif ch >= 0xD0 and ch <= 0xDF:
            if ch & 0x01:
               self.setMode(mode_lowercase)
               self.set_status(STA_LC)
            else:
               self.clearMode(mode_lowercase)
               self.clear_status(STA_LC)
            if ch & 0x02:
               self.setMode(mode_column)
               self.set_status(STA_CO)
            else:
               self.clearMode(mode_column)
               self.clear_status(STA_CO)
            if ch & 0x04:
               self.setMode(mode_doublewide)
               self.set_status(STA_DW)
            else:
               self.clearMode(mode_doublewide)
               self.clear_status(STA_DW)

#
#        left justify
#
         elif ch== 0xE0:
            self.clearMode(mode_rjust)
            self.clear_status(STA_RJ)
#
#        right justify
#
         elif ch== 0xE8:
            self.setMode(mode_rjust)
            self.set_status(STA_RJ)
#
#        escape mode
#
         elif ch== 0xFC:
            self.clearMode(mode_8bit)
            self.clear_status(STA_EB)
            self.char_gen.set_charset(CHARSET_ASCII)
#
#        allow paper advance
#
         elif ch== 0xFE:
            self.clearMode(mode_inhibit_advance)
#
#        inhibit paper advance
#
         elif ch== 0xFF:
            self.setMode(mode_inhibit_advance)
#
#       unknown 8 bit command
#
         else:
            pass
#
#        escape mode
#
      else:
         if ch< 0x80:
            self.printer_buffer.add(ch,type_char,self.printer_mode)

#
#  HP-IL device status bits
#
   def set_status(self,bitmask):
      s= self.pildevice.get_status()
      s= s | bitmask
      self.pildevice.set_status(s)
      return
   
   def clear_status(self,bitmask):
      s= self.pildevice.get_status()
      s= s & ( ~ bitmask)
      self.pildevice.set_status(s)
      return

   def get_status(self,bitmask):
      s= self.pildevice.get_status()
      return(s & bitmask)
#
# process commands sent from the GUI
#
   def process(self,command):

      if command== CMD_MAN:
         self.clear_status(STA_MB)
         self.clear_status(STA_MA)
         return
      if command== CMD_NORM:
         self.set_status(STA_MB)
         self.clear_status(STA_MA)
         return
      if command== CMD_TRACE:
         self.clear_status(STA_MB)
         self.set_status(STA_MA)
         return
      if command== CMD_PRINT_PRESSED:
         self.set_status(STA_SR)
         self.set_status(STA_PR)
         return
      if command== CMD_ADV_PRESSED:
         if not self.isMode(mode_inhibit_advance):
            self.set_status(STA_SR)
            self.set_status(STA_PA)
         return
      if command== CMD_PRINT_RELEASED:
         self.clear_status(STA_SR)
         self.clear_status(STA_PR)
         return
      if command== CMD_ADV_RELEASED:
         if not self.isMode(mode_inhibit_advance):
            self.clear_status(STA_SR)
            self.clear_status(STA_PA)
         return
      if command== CMD_CLEAR:
         return

#
# HP-IL virtual HP82162A object class ---------------------------------------
#


class cls_pilhp82162a(cls_pildevbase):

   def __init__(self,guiobject):
      super().__init__()

#
#     overloaded variable initialization
#
      self.__aid__ = 0x20         # accessory id 
      self.__defaddr__ = 1        # default address alter AAU
      self.__did__ = ""           # device id
      self.__status_len__=2       # device status is 2 bytes
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
      self.__printer__=cls_special_k(self,self.__guiobject__)

#
# public (overloaded) --------
#
#  enable: reset
#
   def enable(self):
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
#  output character to HP82162A
#
   def __indata__(self,frame):
      self.__printer__.process_char(frame & 0xFF) 
    
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

