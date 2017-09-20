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
# pilwinpipe object class (Windows named pipe) ------------------------------
#
#
# Changelog
# 07.09.2017 jsi
# - first version (never thought that I would do Windows low level programming one
#   fine day)
#
import win32event
import win32pipe
import win32file
import win32con
import win32api
import pywintypes

INVALID_HANDLE_VALUE = -1
BUFSIZE=1

class WinPipeError(Exception):
   def __init__(self,msg,add_msg=None):
      self.msg = msg
      if add_msg is None:
         self.add_msg= add_msg
      else:
         self.add_msg = add_msg

class cls_pilwinpipe:

   def __init__(self,pipename):
      self.__pipename__= pipename          # name of pipe
      self.__pipe__= None                  # pipe handle
      self.__connected__= False
      self.__last_error__=0
      self.__overlapped__= pywintypes.OVERLAPPED()
      self.__event__= win32event.CreateEvent(None,0,0,None)
      self.__overlapped__.hEvent= self.__event__
      self.__io_pending__= False
      self.__readbuffer__= win32file.AllocateReadBuffer(1)


   def isConnected(self):
      return self.__connected__ 
#
#  Connect to pipe
#
   def open(self):
#
#     create pipe
#
      self.__pipe__= win32pipe.CreateNamedPipe(self.__pipename__,
                             win32con.PIPE_ACCESS_DUPLEX 
                             | win32con.FILE_FLAG_OVERLAPPED 
                             ,
                             win32con.PIPE_TYPE_MESSAGE |
                             win32con.PIPE_READMODE_MESSAGE ,
                             1,
                             BUFSIZE,
                             BUFSIZE,
                             0,
                             None
                             )
      if (self.__pipe__ == INVALID_HANDLE_VALUE):
         self.__last_error__= win32api.GetLastError()
         raise WinPipeError("Error in creating Named Pipe",str(self.__last_error_))
      self.__io_pending__= False

#
#  Disconnect and close pipe
#
   def close(self):
      self.cleanupIO()
      win32api.CloseHandle(self.__pipe__)
#     print("Handle closed")
#
#  do clean up, cancel pending i/o, flush buffers and disconnect pipe
#
   def cleanupIO(self):
#     print("cleaning up io")
      if self.__io_pending__:
         win32file.CancelIo(self.__pipe__)
      if self.__connected__:
         win32file.FlushFileBuffers(self.__pipe__)
         win32pipe.DisconnectNamedPipe(self.__pipe__)
         self.__connected__=False
#     print("clean up finished")
#
#  Read byte from pipe with time out, handle client connects
#
   def read(self,timeout):
#
#     no io pending, issue io connect or read
#
      if not self.__io_pending__:
         if self.__connected__:
#
#           issue read pipe
#
            try:
               retval, self.__readbuffer__= win32file.ReadFile(self.__pipe__, self.__readbuffer__,self.__overlapped__)
#              print("read pipe called")
            except pywintypes.error:
               self.__last_error__= win32api.GetLastError()
#              print("Error: %d" % self.__last_error__)
               self.cleanupIO()
               # throw exception
               return None
#           print("after read, retval: %d" % retval)
         else:
#
#        issue connect: if this fails, we set status to not connected
#
            try:
               retval= win32pipe.ConnectNamedPipe(self.__pipe__, self.__overlapped__)
#              print("connect named pipe called")
            except pywintypes.error:
               self.__last_error__= win32api.GetLastError()
#              print("Error: %d" % self.__last_error__)
               self.__connected__= False
               return None
#           print("after connect, retval %d" % retval)
         self.__io_pending__= True
#        print("set i/o pending")
#
#     i/o operation pending, wait for completion until timeout
#
      mtimeout=int(timeout)*1000
      retval= win32event.WaitForSingleObject(self.__overlapped__.hEvent,mtimeout)
#
#     timeout, return None
#
      if retval== win32event.WAIT_TIMEOUT:
         return None
#
#     The operation connect or read pipe completed
#
      elif retval== win32event.WAIT_OBJECT_0:
#        print("wait event signaled")
         win32event.ResetEvent(self.__overlapped__.hEvent)
         self.__io_pending__= False
#
#        get result of completet operation
#
         try:
            n= win32pipe.GetOverlappedResult(self.__pipe__,self.__overlapped__,1)
         except pywintypes.error:
            self.__last_error__= win32api.GetLastError()
#           print("Error: %d" % self.__last_error__)
            self.cleanupIO()
            return None
#
#        get result of read
#
         self.__last_error__= win32api.GetLastError()
#        print("last error")
#        print(self.__last_error__)
         if self.__connected__:
            if n ==1:
#              print("Have data:")
#              print(bytes(self.__readbuffer__))
               return(bytes(self.__readbuffer__))
#
#        get result of connect
#
         else:
#           print("connect completed")
            self.__connected__= True
      else:
#        print("wait for single object returned something else")
         pass
      return None
#
#  write to pipe with timeout
#
   def write(self,byte,timeout):
      mtimeout=int(timeout*1000)
      win32event.ResetEvent(self.__overlapped__.hEvent)
#
#     issue overlapped write
#
      self.__readbuffer__[0]=byte
#     print("write to pipe %x" % byte)

      retval,length= win32file.WriteFile(self.__pipe__,self.__readbuffer__,self.__overlapped__)
#     print("after write retval: %d length: %d" % (retval,length))
      self.__io_pending__= True
#
#     wait until timeout
#
      retval= win32event.WaitForSingleObject(self.__overlapped__.hEvent,mtimeout)
      win32event.ResetEvent(self.__overlapped__.hEvent)
#
#     timeout, something is wrong, disconnect
#
      if retval!= win32event.WAIT_OBJECT_0:
         self.__last_error__= win32api.GetLastError()
#        print("Error: %d" % self.__last_error__)
         self.cleanupIO()
         return 
#
#        get result of completet operation
#
      self.__io_pending__= False
      try:
         n= win32pipe.GetOverlappedResult(self.__pipe__,self.__overlapped__,1)
      except pywintypes.error:
         self.__last_error__= win32api.GetLastError()
#        print("Error: %d" % self.__last_error__)
         self.cleanupIO()
         return
#     print("write completed n= %d" % n)
      return
