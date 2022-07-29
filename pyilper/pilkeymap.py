#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# pyILPER 
#
# Keyboard mapping definitions
# Copyright (c) 2019 J. Siebold
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
# pyILPER keyboard definitions  ---------------------------------------------------
#
# Changelog
# 20.01.2019 - jsi:
# - initial release
# 21.01.2019 - jsi:
# - bug fixes
# 23.01.2019 - jsi
# - missing HP-75 keys added
# 25.01.2019 - jsi:
# - added Shift Alt I and Ctrl Alt I keystrokes for Shift I/R and Ctrl I/R
# - refactoring
# 11.02.2019 jsi:
# - fixed backtab key
# 04.05.2022 jsi
# - PySide6 migration

from .pilcore import isMACOS, QTBINDINGS
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtGui, QtWidgets
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtGui, QtWidgets

#
# Modifier masks
#
KEYBOARD_ALT = 0x100000000
KEYBOARD_SHIFT= 0x200000000
KEYBOARD_CTRL=0x400000000
ESC= 27

#
# Keyboard types
#
KEYBOARD_TYPE_HP71=0
KEYBOARD_TYPE_HP75=1
keyboardtypes= ["HP-71","HP-75"]
#
# Lookup Types (macOS keytab)
#
T_CHAR=0
T_KEY=1

#
# Keyboard map for the HP-71
#
keymap_hp71 = {
        QtCore.Qt.Key_Up :                     [ ESC , ord("A")],   # Up
        QtCore.Qt.Key_Down :                   [ ESC , ord("D")],   # Down
        QtCore.Qt.Key_Right :                  [ ESC , ord("C")],   # Right
        QtCore.Qt.Key_Left :                   [ ESC , ord("B")],   # Left
        QtCore.Qt.Key_Return:                  [ ESC , ord("R")],   # Endline
        QtCore.Qt.Key_Insert:                  [ ESC , ord("H")],   # I/R
        QtCore.Qt.Key_Delete:                  [ ESC , ord("G")],   # -CHAR
        QtCore.Qt.Key_Backspace:               [ ESC , ord("Q")],   # BACK
        QtCore.Qt.Key_Up | KEYBOARD_SHIFT:     [ ESC , ord("J")], # far up
        QtCore.Qt.Key_Down | KEYBOARD_SHIFT:   [ ESC , ord("K")], # far down
        QtCore.Qt.Key_Left | KEYBOARD_SHIFT :  [ ESC , ord("E")], # far left
        QtCore.Qt.Key_Home                  :  [ ESC , ord("E")], # far left
        QtCore.Qt.Key_Right | KEYBOARD_SHIFT:  [ ESC , ord("F")], # far right
        QtCore.Qt.Key_End                   :  [ ESC , ord("F")], # far right
        QtCore.Qt.Key_Down | KEYBOARD_CTRL:    [ ESC , ord("T")], # next catalog
        QtCore.Qt.Key_F1      :                [ ESC , ord("L")], # ATTN
        QtCore.Qt.Key_F2      :                [ ESC , ord("M")], # RUN
        QtCore.Qt.Key_F3      :                [ ESC , ord("N")], # CMDS
        QtCore.Qt.Key_F4      :                [ ESC , ord("P")], # SST
        QtCore.Qt.Key_F5      :                [ ESC , ord("I")], # -LINE
        QtCore.Qt.Key_F6      :                [ ESC , ord("O")], # LC

#       map PC keyboard keys to HP special characters
        0xc4 : [21],                      # Ä
        0xd6 : [23],                      # Ö
        0xdc : [25],                      # Ü
        0xc4 | KEYBOARD_SHIFT : [22],     # ä
        0xd6 | KEYBOARD_SHIFT : [24],     # ö
        0xdc | KEYBOARD_SHIFT : [26],     # ü
        QtCore.Qt.Key_sterling : [30]    # Sterling
}

#
# Keyboard map for the HP-75
#
keymap_hp75 = {
#       non modifier group
        QtCore.Qt.Key_Backspace:                         [8],
        QtCore.Qt.Key_Return:                            [13],
        QtCore.Qt.Key_Escape  :                          [27],
        QtCore.Qt.Key_F1      :                          [128],  # ATTN
        QtCore.Qt.Key_F2      :                          [129],  # TIME
        QtCore.Qt.Key_F3      :                          [130],  # APPT 
        QtCore.Qt.Key_F4      :                          [131],  # APPT
        QtCore.Qt.Key_Up :                               [132],
        QtCore.Qt.Key_Down :                             [133],
        QtCore.Qt.Key_Left :                             [134],
        QtCore.Qt.Key_Right :                            [135],
        QtCore.Qt.Key_Insert:                            [136],
        QtCore.Qt.Key_F5      :                          [137],  # FET
        QtCore.Qt.Key_F6      :                          [139],  # CLR
        QtCore.Qt.Key_Delete:                            [138],  # DEL
        QtCore.Qt.Key_F8      :                          [141],  # RUN
        QtCore.Qt.Key_Tab      :                         [142],  # TAB
        QtCore.Qt.Key_Home                 :             [166], # Goto BOL
        QtCore.Qt.Key_End                   :            [167], # Goto EOL
        QtCore.Qt.Key_F7      :                          [168],  # Lit.

#       Shift modifier group
        QtCore.Qt.Key_F1 | KEYBOARD_SHIFT:               [160], # OFF
        QtCore.Qt.Key_F2 | KEYBOARD_SHIFT :              [161], # --
        QtCore.Qt.Key_F3 | KEYBOARD_SHIFT:               [162], # chk interval
        QtCore.Qt.Key_F4 | KEYBOARD_SHIFT:               [163], # --
        QtCore.Qt.Key_Up   | KEYBOARD_SHIFT :            [164], # Page up
        QtCore.Qt.Key_Down | KEYBOARD_SHIFT:             [165], # Page down
        QtCore.Qt.Key_Left | KEYBOARD_SHIFT:             [166], # Goto BOL
        QtCore.Qt.Key_Right| KEYBOARD_SHIFT :            [167], # Goto EOL
        QtCore.Qt.Key_Insert | KEYBOARD_SHIFT:           [168], # Enter char
        QtCore.Qt.Key_F5 | KEYBOARD_SHIFT:               [169], # last err
        QtCore.Qt.Key_Delete | KEYBOARD_SHIFT:           [170], # Del to EOL
        QtCore.Qt.Key_F6 | KEYBOARD_SHIFT:               [171], # --
        QtCore.Qt.Key_F8  | KEYBOARD_SHIFT  :            [173], # SST
        QtCore.Qt.Key_Backtab | KEYBOARD_SHIFT:          [174], # Tab back
        QtCore.Qt.Key_F7  | KEYBOARD_SHIFT  :            [200], # Lit and _

#       Control modifier group
        QtCore.Qt.Key_Plus | KEYBOARD_CTRL:              [28],  # sigma
        QtCore.Qt.Key_Equal | KEYBOARD_CTRL:             [29],  # not equal
        QtCore.Qt.Key_Semicolon | KEYBOARD_CTRL:         [30],  # Sterling
        QtCore.Qt.Key_8 | KEYBOARD_CTRL:                 [31],  # smear
        QtCore.Qt.Key_9 | KEYBOARD_CTRL:                 [127], # append
        QtCore.Qt.Key_0 | KEYBOARD_CTRL:                 [176], # underscore 0
        QtCore.Qt.Key_1 | KEYBOARD_CTRL:                 [177], # underscore 1
        QtCore.Qt.Key_2 | KEYBOARD_CTRL:                 [178], # underscore 2
        QtCore.Qt.Key_3 | KEYBOARD_CTRL:                 [179], # underscore 3
        QtCore.Qt.Key_4 | KEYBOARD_CTRL:                 [180], # underscore 4
        QtCore.Qt.Key_5 | KEYBOARD_CTRL:                 [181], # underscore 5
        QtCore.Qt.Key_6 | KEYBOARD_CTRL:                 [182], # underscore 6
        QtCore.Qt.Key_F1 | KEYBOARD_CTRL :               [192], # --
        QtCore.Qt.Key_F2 | KEYBOARD_CTRL  :              [193], # --
        QtCore.Qt.Key_F3 | KEYBOARD_CTRL :               [194], # --
        QtCore.Qt.Key_F4 | KEYBOARD_CTRL :               [195], # --
        QtCore.Qt.Key_Up   | KEYBOARD_CTRL  :            [196], # send ESC S
        QtCore.Qt.Key_Down | KEYBOARD_CTRL :             [197], # send ESC T
        QtCore.Qt.Key_Left | KEYBOARD_CTRL :             [198], # 32 <-
        QtCore.Qt.Key_Right| KEYBOARD_CTRL  :            [199], # 32 ->
        QtCore.Qt.Key_Insert | KEYBOARD_CTRL :           [200], # lit+undersc.
        QtCore.Qt.Key_F5 | KEYBOARD_CTRL :               [201], # last entry
        QtCore.Qt.Key_F6 | KEYBOARD_CTRL :               [203], # reset display
        QtCore.Qt.Key_Delete | KEYBOARD_CTRL :           [202], # Delete to BOL
        QtCore.Qt.Key_F8  | KEYBOARD_CTRL   :            [205], # --
        QtCore.Qt.Key_F7  | KEYBOARD_CTRL   :            [201], # lit+undersc.
        QtCore.Qt.Key_Tab | KEYBOARD_CTRL :              [206], # --
        
#       Shift+Control modifier group
        QtCore.Qt.Key_F1 | KEYBOARD_CTRL | KEYBOARD_SHIFT:   [224], # --
        QtCore.Qt.Key_F2 | KEYBOARD_CTRL | KEYBOARD_SHIFT:   [225], # --
        QtCore.Qt.Key_F3 | KEYBOARD_CTRL | KEYBOARD_SHIFT:   [226], # --
        QtCore.Qt.Key_F4 | KEYBOARD_CTRL | KEYBOARD_SHIFT:   [227], # --
        QtCore.Qt.Key_Up   | KEYBOARD_CTRL | KEYBOARD_SHIFT: [228], # --
        QtCore.Qt.Key_Down | KEYBOARD_CTRL | KEYBOARD_SHIFT: [229], # --
        QtCore.Qt.Key_Left | KEYBOARD_CTRL | KEYBOARD_SHIFT: [230], # find prv char
        QtCore.Qt.Key_Right| KEYBOARD_CTRL | KEYBOARD_SHIFT: [231], # find next char
        QtCore.Qt.Key_Insert | KEYBOARD_CTRL | KEYBOARD_SHIFT:[232], # --
        QtCore.Qt.Key_F5 | KEYBOARD_CTRL | KEYBOARD_SHIFT:   [233], # --
        QtCore.Qt.Key_Delete | KEYBOARD_CTRL | KEYBOARD_SHIFT:[234], # --
        QtCore.Qt.Key_F6 | KEYBOARD_CTRL | KEYBOARD_SHIFT:    [255], # reset
        QtCore.Qt.Key_F7  | KEYBOARD_CTRL | KEYBOARD_SHIFT:  [232], #  --
        QtCore.Qt.Key_F8  | KEYBOARD_CTRL | KEYBOARD_SHIFT:  [237], # Reset
        QtCore.Qt.Key_Backtab | KEYBOARD_CTRL | KEYBOARD_SHIFT:  [238], # --



#       map PC keyboard keys to HP special characters
        0xc4 : [21],                      # Ä
        0xd6 : [23],                      # Ö
        0xdc : [25],                      # Ü
        0xc4 | KEYBOARD_SHIFT : [22],     # ä
        0xd6 | KEYBOARD_SHIFT : [24],     # ö
        0xdc | KEYBOARD_SHIFT : [26],     # ü
        QtCore.Qt.Key_sterling : [30]    # Sterling

}

#
# add special shortcuts for macOS to the HP-71 and HP-75 keymap
#
if isMACOS():
#  Shift+Alt modifier 
   keymap_hp75[QtCore.Qt.Key_I | KEYBOARD_SHIFT | KEYBOARD_ALT]= [168] # Enter char
#  Control+Alt modifier
   keymap_hp75[QtCore.Qt.Key_I | KEYBOARD_CTRL | KEYBOARD_ALT]= [200] # Enter char and literalize
   keymap_hp71[QtCore.Qt.Key_5 | KEYBOARD_ALT]= [ord("[")]
   keymap_hp75[QtCore.Qt.Key_5 | KEYBOARD_ALT]= [ord("[")]
   keymap_hp71[QtCore.Qt.Key_6 | KEYBOARD_ALT]= [ord("]")]
   keymap_hp75[QtCore.Qt.Key_6 | KEYBOARD_ALT]= [ord("]")]
   keymap_hp71[QtCore.Qt.Key_7 | KEYBOARD_ALT]= [124]
   keymap_hp75[QtCore.Qt.Key_7 | KEYBOARD_ALT]= [124]
   keymap_hp71[QtCore.Qt.Key_8 | KEYBOARD_ALT]= [ord("{")]
   keymap_hp75[QtCore.Qt.Key_8 | KEYBOARD_ALT]= [ord("{")]
   keymap_hp71[QtCore.Qt.Key_9 | KEYBOARD_ALT]= [ord("}")]
   keymap_hp75[QtCore.Qt.Key_9 | KEYBOARD_ALT]= [ord("}")]
   keymap_hp71[QtCore.Qt.Key_L | KEYBOARD_ALT]= [ord("@")]
   keymap_hp75[QtCore.Qt.Key_L | KEYBOARD_ALT]= [ord("@")]
   keymap_hp71[QtCore.Qt.Key_I | KEYBOARD_ALT]= [ ESC , ord("H")]  # I/R
   keymap_hp75[QtCore.Qt.Key_I | KEYBOARD_ALT]= [136]              # I/R

#
# lookup keyboard map
#
def keyboard_lookup(keycode, keyboard_type):

   try:
      if keyboard_type== KEYBOARD_TYPE_HP71:
         return(keymap_hp71[keycode])
      else:
         return(keymap_hp75[keycode])
   except KeyError as e:
       return []
