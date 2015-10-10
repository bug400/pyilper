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
# scope object class -------------------------------------------------------
#
# Changelog
# 06.10.2015 jsi:
# - class statement syntax update

#
class cls_scope:

   def __init__ (self):
      self.__mnemo__= ["DAB", "DSR", "END", "ESR", "CMD", "RDY", "IDY", "ISR"]
      self.__scmd0__= ["NUL", "GTL", "???", "???", "SDC", "PPD", "???", "???",
                    "GET", "???", "???", "???", "???", "???", "???", "ELN",
                    "NOP", "LLO", "???", "???", "DCL", "PPU", "???", "???",
                    "EAR", "???", "???", "???", "???", "???", "???", "???" ]
      self.__scmd9__= ["IFC", "???", "REN", "NRE", "???", "???", "???", "???",
                    "???", "???", "AAU", "LPD", "???", "???", "???", "???"]
      self.__isactive__= False
      self.__callback_dispchar__= None
      self.__count__ = 0
      self.__setsrqbit__=0        # srq bit mask (set)
      self.__clearsrqbit__=0      # srq bit mask (clear)

   def setsrqbit(self,devicecounter):
      self.__setsrqbit__= 1 << devicecounter
      self.__clearsrqbit= ~(1 << devicecounter)

   def setpilbox(self,obj):
      self.__pilbox__=obj

   def setactive(self, active):
      self.__isactive__= active

   def register_callback_dispchar(self,func):
      self.__callback_dispchar__= func

   def process (self,frame):
      if not self.__isactive__:
         return(frame)
      n= frame & 255
      s= "{:3s} {:02X}".format(self.__mnemo__[frame // 256], n)
      
#
#     CMD
#
      if (frame & 0x700) == 0x400 :
         t= n // 32
         
         if t == 0:
            s= self.__scmd0__[n & 31 ]
         elif t == 1:
            if (n & 31) == 31:
               s="UNL"
            else:
               s= "LAD {:02X}".format( n & 31)
         elif t == 2:
            if (n & 31) == 31:
               s="UNT"
            else:
               s= "TAD {:02X}".format( n & 31)
         elif t == 3:
            s= "SAD {:02X}".format( n & 31)
         elif t == 4:
            if (n & 31) < 16:
               s= "PPE {:02X}".format( n & 31)
            else:
               s= self.__scmd9__[n & 15]
         elif t == 5:
            s= "DDL {:02X}".format( n & 31)
         elif t == 6:
            s= "DDT {:02X}".format( n & 31)
         if s[0] =="?":
            s="CMD {:02x}".format(n)
      else:
#
#        RDY
#
         if (frame & 0x700) == 0x500:
            if n < 128:
               if n == 0:
                  s= "RFC"
               elif n == 64:
                  s= "ETO"
               elif n == 65:
                  s= "ETE"
               elif n == 66:
                  s= "NRD"
               elif n == 96:
                  s= "SDA"
               elif n == 97:
                  s= "SST"
               elif n== 98:
                  s = "SDI"
               elif n == 99:
                  s = "SAI"
               elif n == 100:
                  s = "TCT"
               else:
                  s = "RDY {:2X}".format(n)
            else:
               t= n // 32
               if t == 4:
                  s = "AAD {:2X}".format(n & 31)
               elif t == 5:
                  s = "AEP {:2X}".format(n & 31)
               elif t == 6:
                  s = "AES {:2X}".format(n & 31)
               elif t == 7:
                  s = "AMP {:2X}".format(n & 31)
               else:
                  s = "RDY {:2X}".format(n)

      s= s.ljust(8)
      if self.__callback_dispchar__ != None:
         self.__callback_dispchar__(s)
      return (frame)
