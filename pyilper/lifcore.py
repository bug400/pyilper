#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# LIF utilities
#
# Python classes to handle LIF image files 
# derived from the LIF utilities of Tony Duell
# Copyright (c) 2008 A. R. Duell
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
# LIF image file classes ---------------------------------------------------
#
# Changelog
# 08.01.16 - jsi:
# fixed getLifString if string contains blanks
# 16.01.16 - jsi
# fixed missing file types
# 23.01.16 - jsi
# fixed getLifString to handle empty strings
# 30.01.16 - jsi
# added LIFUTILS_REQUIRED_VERSION constant
# 17.10.2016 jsi
# - set required version of lifutils to 1.7.6
# 01.12.2016 jsi
# - use wcat41 instead of wall to display wall files
# 28.10.2017 jsi
# - lifutils UUID constant added
# 30.10.2017 jsi
# - LIFUTILS_PATH module variable and functions added
# 11.11.2017 jsi
# - set required version of lifutils to 1.7.7
# 31.05.2019 jsi
# - set required version of lifutils to 1.7.9
# - text75 is now liftext75
# 04.06.2019 jsi
# - lexcat75 added to display information of HP-75 lex files
#
# core constants and functions to handle lif image files
#

import pathlib


dict_finfo_type={0x0001:["TEXT","liftext"],0x00FF:["D-LEX","lexcat71"],0xE020:["WAXM41",""],0xE030:["XM41",""],0xE040:["ALL41","wcat41"],0xE050:["KEY41","key41"],0xE052:["TXT75","liftext75"],0xE053:["APP75",""],0xE058:["DAT75",""],0xE060:["STA41","stat41"],0xE070:["X-M41",""],0xE080:["PGM41","decomp41"],0xE088:["BAS75",""],0xE089:["LEX75","lexcat75"],0xE08A:["WKS75",""],0xE08B:["ROM75",""],0xE0D0:["SDATA","sdata"],0xE0D1:["TEXT (S)","liftext"],0xE0F0:["DAT71",""],0xE0F1:["DAT71 (S)",""],0xE204:["BIN71",""],0xE205:["BIN71 (S)",""],0xE206:["BIN71 (P)",""],0xE207:["BIN71 (SP)",""],0xE208:["LEX71","lexcat71"],0xE209:["LEX71 (S)","lexcat71"],0xE20A:["LEX71 (P)","lexcat71"],0xE20B:["LEX71 (SP)","lexcat71"],0xE20C:["KEY71",""],0xE20D:["KEY71 (S)",""],0xE214:["BAS71",""],0xE215:["BAS71 (S)",""],0xE216:["BAS71 (P)",""],0xE217:["BAS71 (SP)",""],0xE218:["FTH71",""],0xE219:["FTH71 (S)",""],0xE21A:["FTH71 (P)",""],0xE21B:["FTH71 (SP)",""],0xE222:["GRA71",""],0xE224:["ADR71",""],0xE22E:["SYM71",""],0xE21C:["ROM71",""]}

dict_finfo_name={"TEXT":0x0001,"D-LEX":0x00FF,"WAXM41":0xE020,"XM41":0xE030,"ALL41":0xE040,"KEY41":0xE050,"TXT75":0xE052,"APP75":0xE053,"DAT75":0xE058,"STA41":0xE060,"X-M41":0xE070,"PGM41":0xE080,"BAS75":0xE088,"LEX75":0xE089,"WKS75":0xE08A,"ROM75":0xE08B,"SDATA":0xE0D0,"TEXT (S)":0xE0D1,"DAT71":0xE0F0,"DAT71 (S)":0xE0F1,"BIN71":0xE204,"BIN71 (S)":0xE205,"BIN71 (P)":0xE206,"BIN71 (SP)":0xE207,"LEX71":0xE208,"LEX71 (S)":0xE209,"LEX71 (P)":0xE20A,"LEX71 (SP)":0xE20B,"KEY71":0xE20C,"KEY71 (S)":0xE20D,"BAS71":0xE214,"BAS71 (S)":0xE215,"BAS71 (P)":0xE216,"BAS71 (SP)":0xE217,"FTH71":0xE218,"FTH71 (S)":0xE219,"FTH71 (P)":0xE21A,"FTH71 (SP)":0xE21B,"GRA71":0xE222,"ADR71":0xE224,"SYM71":0xE22E,"ROM71":0xE21C}
#
# Minimum Version number of LIFUTILS
#
LIFUTILS_REQUIRED_VERSION=10709
#
# GUID of a lifutils > 1.7.x windows installation
#
LIFUTILS_UUID="{0C786F40-D1C6-4681-9B1D-AFC920428192}"
#
# current path to lifutils programs
#
LIFUTILS_PATH=""
#
# set/get current path to lifutils programs
def set_lifutils_path(path):
   global LIFUTILS_PATH
   LIFUTILS_PATH=path

def get_lifutils_path():
   return LIFUTILS_PATH
#
#  add LIFUTILS_PATH to program
#
def add_path(cmd):
   lifutils_path= get_lifutils_path()
   if lifutils_path !="":
      p=pathlib.Path(lifutils_path) / cmd
      cmd= str(p)
   return(cmd)


# get numeric filetype for a file file type name
#
def get_finfo_name(ftype_name):
   if ftype_name in dict_finfo_name:
      return(dict_finfo_name[ftype_name])
   else:
      return None 

#
# get file type name and additional information for a numeric file type
#
def get_finfo_type(ftype):
   if ftype in dict_finfo_type:
      return(dict_finfo_type[ftype]) 
   else:
      return None

#
# store an inter into a byte array
#
def putLifInt(data,offset,length,value):
   i=length - 1
   while i >= 0:
      data[offset+i]= value & 0xFF
      value=value >> 8
      i-=1
   return
#
# get an integer from a byt array
#
def getLifInt(data,offset,length):
   i=0
   value=0
   while i < length:
      value= (value <<8) + data[offset+i]
      i+=1
   return value

def bcdtodec(c):
   return(((c&0xf0)>>4)*10 +(c &0x0f))

#
# get time and date from a byte string
#
def getLifDateTime(b,offset):
   day=bcdtodec(b[offset])
   month=bcdtodec(b[offset+1])
   year=bcdtodec(b[offset+2])
   hour=bcdtodec(b[offset+3])
   minute=bcdtodec(b[offset+4])
   sec=bcdtodec(b[offset+5])
   return("{:02d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(day,month,year,hour,minute,sec))
#
# get a lif string, also those that contain a blank in between
#
def getLifString(data,offset,length):
   str_list= []
   j= -1
   for i in range(length):
      if data[offset+i] != 0x20:
         j=i
   if j == -1:
      return ""
   else:
      for i in range(j+1):
         str_list.append(chr(data[offset+i]))
      return "".join(str_list)
 
