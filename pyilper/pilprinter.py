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
# HP-IL virtual printer object class ----------------------------------------
#
# Initial release derived from ILPER 1.4.3 for Windows
#
# Changelog
#
# 09.02.2015 Improvements and changes of IPLER 1.5
# - fixed __fprinter__ handling in do_cmd LAD/SAD
# - not implemented: auto extended address support switch
# - not implemeted: set/get AID, ID$
#
# 30.05.2015 fixed error in handling AP, added getstatus
#
# 06.10.2015 jsi:
# - class statement syntax update

class cls_printer:

   def __init__(self):

      self.__aid__ = 0x2E         # accessory id = printer
      self.__defaddr__ = 3        # default address alter AAU
      self.__did__ = "PRINTER"    # device id
      self.__status__ = 0         # HP-IL status (always 0 here)
      self.__addr__ = 0           # HP-IL primary address (by TAD,LAD)
                                  # bits 0-5=AAD or AEP, bit 7=1 means
                                  # auto address taken
      self.__addr2nd__ = 0        # HP-IL secondary address (by SAD)
                                  # bits 0-5=AES, bit 7 means auto addr taken
      self.__fprinter__ =0        # state machine flag
      self.__ptsdi__ = 0          # output pointer for device id
      self.__ptssi__ = 0          # output pointer for hp-il status
      self.__fesc__ = False       # no escape sequence
      self.__isactive__= False    # device active in loop
      self.__callback_clprint__= None
      self.__callback_printchar__=None
      self.__setsrqbit__=0        # srq bit mask (set)
      self.__clearsrqbit__=0      # srq bit mask (clear)


   def setsrqbit(self,devicecounter):
      self.__setsrqbit__= 1 << devicecounter
      self.__clearsrqbit= ~(1 << devicecounter)

   def setpilbox(self,obj):
      self.__pilbox__=obj

   def setactive(self, active):
      self.__isactive__= active

   def register_callback_clprint(self,func):
      self.__callback__clprint__= func

   def register_callback_printchar(self,func):
      self.__callback_printchar__= func
   
   def getstatus(self):
      return [self.__isactive__, self.__did__, self.__aid__, self.__addr__, self.__addr2nd__, self.__fprinter__]

#
#  handle special characters
#
   def __printer_str__(self,c):

#
#     no escape squence 
#
      if not self.__fesc__:
         t= ord(c)
         if t == 27:
            self.__fesc__ = True
         if not self.__fesc__:
            if self.__callback_printchar__ != None:
               self.__callback_printchar__(c)

#
#     ignore escape sequences
#
      else:
         self.__fesc__= False

#
#  clear printer
#
   def __clear_printer__(self):
      if self.__callback__clprint__ != None:
         self.__callback__clprint__() 
      return

#
#  manage HPIL data frames, returns the returned frame
#
   def __do_doe__(self,frame):

      n= frame & 0xFF

      if (self.__fprinter__ & 0x80) !=0:
#
#        addressed
#
         if (self.__fprinter__ & 0x40) != 0:
#
#           talker
#
            if self.__ptssi__ > 0:   # SST
               self.__ptssi__= self.__ptssi__-1 
               if self.__ptssi__ > 0:
                  frame= (self.__status__ >> (( self.__ptssi__ -1) * 8)) & 0xFF
            if self.__ptsdi__ > 0:   # SDI
               if self.__ptsdi__ == len(self.__did__):
                  frame=0
                  self.__ptsdi__=0
               else:
                  frame= ord(self.__did__ [self.__ptsdi__])
                  self.__ptsdi__= self.__ptsdi__+1
            if self.__ptssi__ == 0 and self.__ptsdi__ == 0 : # EOT
               frame= 0x540
               self.__fprinter__= 0x40
         else:
#
#         talker
#
            self.__printer_str__(chr(n))

      return(frame)
#
# manage HP-IL command frames
#
   def __do_cmd__(self,frame):

      n= frame & 0xff
      t= n >> 5
      if t == 0:
         if n == 4:   # SDC
            if (self.__fprinter__ & 0x80) != 0:
               self.__clear_printer__()
         elif n == 20: # DCL
             self.__clear_printer__()
      elif t == 1:  # LAD
         n= n & 31
         if n == 31: # UNL, if not talker then go to idle state
             if (self.__fprinter__ & 0x50) == 0: # other 0x40!
                self.__fprinter__= 0
         else:       # if MLA go to listen state
             if (self.__fprinter__ & 0x80)== 0 and n == (self.__addr__ & 31):
                if (self.__addr2nd__ & 0x80) == 0:
                   self.__fprinter__ = 0x80  
                else:
                   self.__fprinter__ = 0x20
      elif t == 2:  # TAD  
         n= n & 31
         if n == (self.__addr__ & 31):
            if (self.__addr2nd__ & 0x80) == 0: # if MTA go to talker state
               self.__fprinter__= 0x40
            else:
               self.__fprinter__= 0x10
         else:
            if ( self.__fprinter__ & 0x50) != 0:
               self.__fprinter__= 0
      elif t == 3: # SAD
         if self.__fprinter__ & 0x30 !=0: # LAD or TAD address match
            n = n & 31
            if n == (self.__addr2nd__ & 31):
               self.__fprinter__<<=2  # switch to addressed listener/talker
            else:
               self.__fprinter__=0    # second addr. don't match
      elif t == 4: 
         n= n & 31
         if n == 16: # IFC
            self.__fprinter__= 0x0
         elif n == 26: # AAU
            self.__addr__=  self.__defaddr__
            self.__addr2nd__= 0
      return(frame)
            
#
# HP-IL ready frames
#
   def __do_rdy__(self,frame):

      n= frame & 0xFF
      if n <= 127:
         if ( self.__fprinter__ & 0x40) !=0:  # SOT
#           if addressed talker
            if  n == 66:  #NRD
               self.__ptdsi__ = 0
            elif n == 96: # SDA
                # no response
                pass
            elif n == 97: # SST
                # update IL status and return no. of status bytes
                self.__ptssi__ = 1
                if self.__ptssi__ > 0: # response to status request
                   frame = (self.__status__ >> ((self.__ptssi__ -1) * 8)) & 0xFF
                   self.__fprinter__= 0xC0 # active talker
            elif n == 98:  # SDI
               if self.__did__ != None:
                  frame= ord(self.__did__[0])
                  self.__ptsdi__ = 1 # other 2
                  self.__fprinter__= 0xC0
            elif n == 99: # SAI
                  frame= self.__aid__ & 0xFF
                  self.__fprinter__= 0xC0
      else:
         if n < 0x80 +31: # AAD
            if ((self.__addr__ & 0x80) == 0 and self.__addr2nd__ ==0):
               # AAD, if not already an assigned address, take it
               self.__addr__ = n
               frame=frame+1
         elif  (n >= 0xA0 and n < 0xA0 + 31): # AEP
            # AEP, if not already an assigned address and got an AES frame,
            if ((self.__addr__ & 0x80) == 0 and (self.__addr2nd__ & 0x80) != 0):
               # take it
               self.__addr__= n & 0x9F
         elif (n >= 0xC0 and n < 0xC0 +31): # AES
            if (self.__addr__ & 0x80) == 0:
               self.__addr2nd__= n & 0x9F
               frame=frame + 1
      return (frame)

#
#  Process device
#
   def process(self,frame):

      if not self.__isactive__:
         return(frame)
      if (frame & 0x400) == 0:
         frame= self.__do_doe__(frame)
      elif (frame & 0x700) == 0x400:
         frame= self.__do_cmd__(frame)
      elif (frame & 0x700) == 0x500:
         frame= self.__do_rdy__(frame)
      return(frame)
