#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Dialogs for lif utilities operations
# (c) 2015 Joachim Siebold
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
# lif utilities dialog classes ---------------------------------------------------
#
# Changelog
# 02.01.2016 - jsi
# - added cls_lifview, cls_chkxrom
# - improved error checking of piped commands
# - added descramble HP-41 rom postprocessing option
# - added scramble HP-41 rom to HEPAX sdata file preprocessing option
# - refactoring
#
# 05.01.2016 - jsi
# - replaced process pipelines with temporary files to catch error conditions more
#   reliable
# - added viewing LEX file contents
# - decode output of textfiles in HP-ROMAN8 character set
#
# 08.01.2016 - jsi
# - introduced lifglobal.py, refactoring
#
import os
import subprocess
import platform
import tempfile
from PyQt4 import QtCore, QtGui
from .lifcore import *

#
# exec single command
#
def exec_single(parent,cmd):
   try:
      subprocess.check_output(cmd,stderr=subprocess.STDOUT)
   except OSError as e:
      reply=QtGui.QMessageBox.critical(parent,'Error',e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
   except subprocess.CalledProcessError as exp:
      reply=QtGui.QMessageBox.critical(parent,'Error',exp.output.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)

#
# exec piped command, read input from file, return True if success, False otherwise
#
def exec_double_import(parent,cmd1,cmd2,inputfile):

   try:
      if platform.win32_ver()[0] != "":
         fd= os.open(inputfile, os.O_RDONLY | os.O_BINARY )
      else:
         fd= os.open(inputfile, os.O_RDONLY)
#
# create temporary file
#
      tmpfile=tempfile.TemporaryFile()
#
#  execute first command
#
      p1= subprocess.Popen(cmd1,stdin=fd,stdout=tmpfile,stderr=subprocess.PIPE)
      output1,err1= p1.communicate()
      if err1.decode() != "":
         reply=QtGui.QMessageBox.critical(d,'Error',err1.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         tmpfile.close()
         os.close(fd)
#
#  execute second command
#
      tmpfile.seek(0)
      p2= subprocess.Popen(cmd2,stdin=tmpfile,stderr=subprocess.PIPE)
      output2,err2=p2.communicate()
      if err2.decode() != "":
         reply=QtGui.QMessageBox.critical(parent,'Error',err2.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         tmpfile.close()
         os.close(fd)
#
#  catch errors
#
   except OSError as e:
      reply=QtGui.QMessageBox.critical(parent,'Error',e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
   except subprocess.CalledProcessError as exc:
      reply=QtGui.QMessageBox.critical(parent,'Error',exc.output.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      tmpfile.close()
      os.close(fd)
#
# exec piped command, write output to file or stdout
#
def exec_double_export(parent,cmd1,cmd2,outputfile): 
   try:
      fd=None
      if outputfile != "":
#
# open output file if specified
#
         if os.access(outputfile,os.W_OK):
            reply=QtGui.QMessageBox.warning(parent,'Warning',"Do you really want to overwrite file "+outputfile,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Cancel)
            if reply== QtGui.QMessageBox.Cancel:
               return
         if platform.win32_ver()[0] != "":
            fd= os.open(outputfile, os.O_WRONLY | os.O_BINARY |  os.O_TRUNC | os.O_CREAT, 0o644)
         else:
            fd= os.open(outputfile, os.O_WRONLY | os.O_TRUNC | os.O_CREAT, 0o644)
#
# create temporary file
#
      tmpfile=tempfile.TemporaryFile()
#
# execute first command
#
      p1= subprocess.Popen(cmd1,stdout=tmpfile,stderr=subprocess.PIPE)
      output1,err1= p1.communicate()
      if err1.decode() != "":
         reply=QtGui.QMessageBox.critical(parent,'Error',err1.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         tmpfile.close()
         if fd != None:
            os.close(fd)
         return None
#
# execute second command
#
      tmpfile.seek(0)
      if outputfile != "":
         p2= subprocess.Popen(cmd2,stdin=tmpfile,stdout=fd,stderr=subprocess.PIPE)
      else:
         p2= subprocess.Popen(cmd2,stdin=tmpfile,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      output2,err2=p2.communicate()
      if err2.decode() != "":
         reply=QtGui.QMessageBox.critical(parent,'Error',err2.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         if fd != None:
            os.close(fd)
         return None
      if fd != None:
         os.close(fd)
#
#  catch errors
#
   except OSError as e:
      reply=QtGui.QMessageBox.critical(parent,'Error',e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      tmpfile.close()
      return None
   except subprocess.CalledProcessError as exc:
      reply=QtGui.QMessageBox.critical(parent,'Error',exc.output.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      tmpfile.close()
      return None
   tmpfile.close()
   return output2

#
# pack lif image file dialog
#
class cls_lifpack(QtGui.QDialog):

   def __init__(self,parent= None):
      super().__init__()

   @staticmethod
   def exec(lifimagefile):
      d=cls_lifpack()
      reply = QtGui.QMessageBox.question(d, 'Message', 'Do you really want to pack the LIF image file', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
      if reply == QtGui.QMessageBox.Yes:
         exec_single(d,["lifpack",lifimagefile])

#
# purge file dialog
#
class cls_lifpurge(QtGui.QDialog):

   def __init__(self,parent= None):
      super().__init__()

   @staticmethod
   def exec(lifimagefile,liffile):
      d=cls_lifpurge()
      reply = QtGui.QMessageBox.question(d, 'Message', 'Do you really want to purge '+liffile, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
      if reply == QtGui.QMessageBox.Yes:
         exec_single(d,["lifpurge",lifimagefile, liffile])

#
# rename file dialog
#
class cls_lifrename (QtGui.QDialog):

   def __init__(self,filename,parent= None):
      super().__init__()
      self.newfilename=""
      self.setWindowTitle("Rename File")
      self.vlayout= QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.lbl=QtGui.QLabel("Rename file:")
      self.vlayout.addWidget(self.lbl)
      self.leditFileName=QtGui.QLineEdit(self)
      self.leditFileName.setText(filename)
      self.leditFileName.setMaxLength(10)
      self.regexp = QtCore.QRegExp('[A-Z][A-Z,0-9]*')
      self.validator = QtGui.QRegExpValidator(self.regexp)
      self.leditFileName.setValidator(self.validator)
      self.vlayout.addWidget(self.leditFileName)

      self.buttonBox = QtGui.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.buttonBox)


   def do_ok(self):
      self.newfilename=self.leditFileName.text()
      self.close()

   def do_cancel(self):
      self.newfilename=""
      self.close()

   def getFilename(self):
      return(self.newfilename)

   @staticmethod
   def exec(lifimagefile,liffile):
      d=cls_lifrename(liffile)
      result= d.exec_()
      newfilename= d.getFilename()
      if newfilename != "":
         exec_single(d,["lifrename",lifimagefile, liffile,newfilename])
#
# export file dialog
#
class cls_lifexport (QtGui.QDialog):

   def __init__(self,lifimagefile,liffilename,liffiletype,workdir,parent= None):
      super().__init__()
      self.lifimagefile= lifimagefile
      self.liffiletype= liffiletype
      self.liffilename= liffilename
      self.workdir=workdir
      self.setWindowTitle("Export File")
      self.vlayout= QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.gBox0=QtGui.QGroupBox("File to be exported to file system")
      self.lblLifFilename=QtGui.QLabel(self.liffilename+" (type: "+self.liffiletype+")")
      self.vbox0=QtGui.QVBoxLayout()
      self.vbox0.addWidget(self.lblLifFilename)
      self.vbox0.addStretch(1)
      self.gBox0.setLayout(self.vbox0)
      self.vlayout.addWidget(self.gBox0)
      
      self.gBox1=QtGui.QGroupBox("Postprocessing options")
      self.radio1= QtGui.QRadioButton("convert LIF-Text to ASCII")
      self.radio1.setEnabled(False)
      self.radio2= QtGui.QRadioButton("descramble HP41 rom file")
      self.radio2.setEnabled(False)
      self.radio3= QtGui.QRadioButton("remove LIF header")
      self.radio4= QtGui.QRadioButton("None")

      if self.liffiletype== "TEXT":
         self.radio1.setEnabled(True)
         self.radio1.setChecked(True)
         self.outputextension=".txt"
      elif self.liffiletype== "ROM41":
         self.radio2.setEnabled(True)
         self.radio2.setChecked(True)
         self.outputextension=".rom"
      else:
         self.radio4.setChecked(True)
         self.outputextension=".lif"

      self.vbox=QtGui.QVBoxLayout()
      self.vbox.addWidget(self.radio1)
      self.vbox.addWidget(self.radio2)
      self.vbox.addWidget(self.radio3)
      self.vbox.addWidget(self.radio4)
      self.vbox.addStretch(1)
      self.gBox1.setLayout(self.vbox)

      self.vlayout.addWidget(self.gBox1)

      self.gBox2=QtGui.QGroupBox("Output file")
      self.hbox=QtGui.QHBoxLayout()
      self.outputfile=os.path.join(workdir, liffilename.lower()+self.outputextension)
      self.lblFilename=QtGui.QLabel(self.outputfile)
      self.hbox.addWidget(self.lblFilename)
      self.hbox.addStretch(1)
      self.butChange= QtGui.QPushButton("Change")
      self.butChange.clicked.connect(self.do_filenameChanged)
      self.hbox.addWidget(self.butChange)
      self.gBox2.setLayout(self.hbox)

      self.vlayout.addWidget(self.gBox2)

      self.buttonBox = QtGui.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.buttonBox)
#
#  enter output file name dialog
#
   def get_outputFilename(self):
      dialog=QtGui.QFileDialog()
      dialog.setWindowTitle("Select Output File")
      dialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtGui.QFileDialog.AnyFile)
      dialog.setNameFilters( ["All Files (*.*)"] )
      dialog.selectFile(self.liffilename.lower()+self.outputextension)
      dialog.setOptions(QtGui.QFileDialog.DontUseNativeDialog)
      dialog.setDirectory(self.workdir)
      if dialog.exec():
         return dialog.selectedFiles()
#
#  callback
#
#
#  change output file name
#

   def do_filenameChanged(self):
      flist= self.get_outputFilename()
      if flist == None:
         return
      self.outputfile=flist[0]
      self.lblFilename.setText(self.outputfile)
#
#  export
#
   def do_ok(self):
      if self.outputfile != "":
         if self.radio1.isChecked():
            exec_double_export(self,["lifget","-r",self.lifimagefile,self.liffilename],"liftext",self.outputfile)
         elif self.radio2.isChecked():
            exec_double_export(self,["lifget","-r",self.lifimagefile,self.liffilename],"rom41",self.outputfile)
         elif self.radio3.isChecked():
            exec_single(self,["lifget","-r",self.lifimagefile,self.liffilename,self.outputfile])
         elif self.radio4.isChecked():
            exec_single(self,["lifget",self.lifimagefile,self.liffilename,self.outputfile])
      self.close()
#
#  cancel: do nothing
#
   def do_cancel(self):
      self.close()

   @staticmethod
   def exec(lifimagefile,liffilename,liffiletype,workdir):
      d=cls_lifexport(lifimagefile,liffilename,liffiletype,workdir)
      result= d.exec_()

#
# label lif image file dialog
#
class cls_liflabel (QtGui.QDialog):

   def __init__(self,oldlabel,parent= None):
      super().__init__()
      self.newlabel=""
      self.oldlabel=oldlabel
      self.setWindowTitle("Label LIF image file")
      self.vlayout= QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.lbl=QtGui.QLabel("Label:")
      self.vlayout.addWidget(self.lbl)
      self.leditLabel=QtGui.QLineEdit(self)
      self.leditLabel.setText(oldlabel)
      self.leditLabel.setMaxLength(6)
      self.regexp = QtCore.QRegExp('[A-Z][A-Z,0-9]*')
      self.validator = QtGui.QRegExpValidator(self.regexp)
      self.leditLabel.setValidator(self.validator)
      self.vlayout.addWidget(self.leditLabel)

      self.buttonBox = QtGui.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.buttonBox)

   def do_ok(self):
      self.newlabel=self.leditLabel.text()
      self.close()

   def do_cancel(self):
      self.newlabel=""
      self.close()

   def getLabel(self):
      return(self.newlabel)

   @staticmethod
   def exec(lifimagefile,oldlabel):
      d=cls_liflabel(oldlabel)
      result= d.exec_()
      newlabel= d.getLabel()
      if newlabel != "":
         exec_single(d,["liflabel",lifimagefile, newlabel])
      else:
         exec_single(d,["liflabel","-c",lifimagefile])
#
# import file dialog
#
class cls_lifimport (QtGui.QDialog):

   def __init__(self,lifimagefile,workdir,parent= None):
      super().__init__()
      self.inputfile=""
      self.lifimagefile=lifimagefile
      self.workdir= workdir
      self.liffilename=""

      self.setWindowTitle("Import File")
      self.vlayout= QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.gBox0=QtGui.QGroupBox("Input file")
      self.hbox=QtGui.QHBoxLayout()
      self.lblFilename=QtGui.QLabel(self.inputfile)
      self.hbox.addWidget(self.lblFilename)
      self.hbox.addStretch(1)
      self.butChange= QtGui.QPushButton("Change")
      self.butChange.clicked.connect(self.do_filenameChanged)
      self.hbox.addWidget(self.butChange)
      self.gBox0.setLayout(self.hbox)
      self.vlayout.addWidget(self.gBox0)

      self.gBox1=QtGui.QGroupBox("Preprocessing options")
      self.bGroup=QtGui.QButtonGroup()
      self.radio1= QtGui.QRadioButton("convert from ASCII to LIF-Text")
      self.radio2= QtGui.QRadioButton("convert HP-41 rom file to SDATA file (HEPAX)")
      self.radio3= QtGui.QRadioButton("add LIF header to HP41 FOCAL raw file")
      self.radio4= QtGui.QRadioButton("None")
      self.radio4.setChecked(True)
      self.bGroup.addButton(self.radio1) 
      self.bGroup.addButton(self.radio2)
      self.bGroup.addButton(self.radio3)
      self.bGroup.addButton(self.radio4)
      self.bGroup.buttonClicked.connect(self.do_butclicked)

      self.vbox=QtGui.QVBoxLayout()
      self.vbox.addWidget(self.radio1)
      self.vbox.addWidget(self.radio2)
      self.vbox.addWidget(self.radio3)

      self.hbox2=QtGui.QHBoxLayout()
      self.lbl=QtGui.QLabel("LIF Filename:")
      self.hbox2.addWidget(self.lbl)
      self.leditFileName=QtGui.QLineEdit(self)
      self.leditFileName.setText(self.liffilename)
      self.leditFileName.setMaxLength(10)
      self.regexp = QtCore.QRegExp('[A-Z][A-Z,0-9]*')
      self.validator = QtGui.QRegExpValidator(self.regexp)
      self.leditFileName.setValidator(self.validator)
      self.leditFileName.setEnabled(False)
      self.leditFileName.textChanged.connect(self.do_checkenable)
      self.hbox2.addWidget(self.leditFileName)
      self.vbox.addLayout(self.hbox2)
      self.gBox1.setLayout(self.vbox)
      self.gBox1.setEnabled(False)
      self.vlayout.addWidget(self.gBox1)
      self.vbox.addWidget(self.radio4)
      self.vbox.addStretch(1)

      self.buttonBox = QtGui.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
      self.vlayout.addWidget(self.buttonBox)
#
#  dialog to enter input file name
#
   def get_inputFilename(self):
      dialog=QtGui.QFileDialog()
      dialog.setWindowTitle("Select Input File")
      dialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
      dialog.setNameFilters( ["All Files (*.*)"] )
      dialog.setOptions(QtGui.QFileDialog.DontUseNativeDialog)
      dialog.setDirectory(self.workdir)
      if dialog.exec():
         return dialog.selectedFiles()

#
# callbacks
#

#
# change filename button
#
   def do_filenameChanged(self):
      flist= self.get_inputFilename()
      if flist == None:
         return
      self.inputfile=flist[0]
      self.lblFilename.setText(self.inputfile)
      self.gBox1.setEnabled(True)
      self.do_checkenable()
#
#  any radio button clicked, enable/disable lif filename entry, check ok button
#
   def do_butclicked(self,id):
      if id== self.radio1 or id==self.radio2 or id==self.radio3:
         self.leditFileName.setEnabled(True)
      else:
         self.leditFileName.setEnabled(False)
      self.do_checkenable()

#
#  check, if the OK button can be enabled
#
   def do_checkenable(self):
      self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
      if (self.radio1.isChecked() or self.radio2.isChecked() or self.radio2.isChecked()) and self.leditFileName.text() != "":
         self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)
      if self.radio4.isChecked():
         self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)
      return

#
#  OK button callback import file
#
   def do_ok(self):
      if self.inputfile != "":
         if self.radio1.isChecked() or self.radio2.isChecked() or self.radio3.isChecked():
            self.liffilename=self.leditFileName.text()
            if self.radio1.isChecked():
               exec_double_import(self,["textlif",self.liffilename],["lifput",self.lifimagefile],self.inputfile)
            elif self.radio2.isChecked():
               exec_double_import(self,["rom41hx",self.liffilename],["lifput",self.lifimagefile],self.inputfile)
            elif self.radio3.isChecked():
               exec_double_import(self,["raw41lif",self.liffilename],["lifput",self.lifimagefile],self.inputfile)
         else:
            exec_single(self,["lifput",self.lifimagefile,self.inputfile])
      self.close()

#
#  cancel
#
   def do_cancel(self):
      self.close()

   @staticmethod
   def exec(lifimagefile,workdir):
      d=cls_lifimport(lifimagefile,workdir)
      result= d.exec_()
#
# check xroms dialog
#
class cls_chkxrom(QtGui.QDialog):

   def __init__(self,parent=None):
      super().__init__()
      self.call=["decomp41"]

      self.setWindowTitle("Check ROM Modules")
      self.vlayout= QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.cardrdr= QtGui.QCheckBox("Card Reader")
      self.vlayout.addWidget(self.cardrdr)
      self.printer= QtGui.QCheckBox("Printer")
      self.vlayout.addWidget(self.printer)
      self.wand= QtGui.QCheckBox("Wand")
      self.vlayout.addWidget(self.wand)
      self.hpil= QtGui.QCheckBox("HP-IL")
      self.vlayout.addWidget(self.hpil)
      self.hpil.setChecked(True)
      self.xfunc= QtGui.QCheckBox("X-Function")
      self.vlayout.addWidget(self.xfunc)
      self.xfunc.setChecked(True)
      self.time= QtGui.QCheckBox("Time")
      self.vlayout.addWidget(self.time)
      self.hepax= QtGui.QCheckBox("HEPAX")
      self.vlayout.addWidget(self.hepax)
      self.xio= QtGui.QCheckBox("Extended IO")
      self.vlayout.addWidget(self.xio)
      self.devil= QtGui.QCheckBox("HP-IL Devel")
      self.vlayout.addWidget(self.devil)

      self.exitButton= QtGui.QPushButton("Exit")
      self.exitButton.setFixedWidth(60)
      self.exitButton.clicked.connect(self.do_exit)
      self.hlayout= QtGui.QHBoxLayout()
      self.hlayout.addWidget(self.exitButton)
      self.vlayout.addLayout(self.hlayout)
#
# exit, return the parameters of the selected modules
#
   def do_exit(self):
      if self.cardrdr.isChecked():
         self.call.append("-x")
         self.call.append("cardrdr")
      if self.printer.isChecked():
         self.call.append("-x")
         self.call.append("printer")
      if self.wand.isChecked():
         self.call.append("-x")
         self.call.append("wand")
      if self.hpil.isChecked():
         self.call.append("-x")
         self.call.append("hpil")
      if self.xfunc.isChecked():
         self.call.append("-x")
         self.call.append("xfn")
      if self.time.isChecked():
         self.call.append("-x")
         self.call.append("time")
      if self.hepax.isChecked():
         self.call.append("-x")
         self.call.append("hepax")
      if self.xio.isChecked():
         self.call.append("-x")
         self.call.append("xio")
      if self.devil.isChecked():
         self.call.append("-x")
         self.call.append("devil")
      self.close()

   def get_call(self):
      return self.call

   @staticmethod
   def exec():
      d=cls_chkxrom()
      result= d.exec_()
      return d.get_call()
#
# view file dialog
#
class cls_lifview(QtGui.QDialog):

   def __init__(self,parent= None):
      super().__init__()

      self.setWindowTitle("View File")
      self.vlayout= QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.viewer=QtGui.QTextEdit()
      self.viewer.setMinimumWidth(600)
      self.viewer.setMinimumHeight(600)
      self.viewer.setReadOnly(True)
      if platform.dist()[0] != "":
         fontname="Monospace"
      else:
         fontname="Courier New"
      self.font=QtGui.QFont(fontname)
      self.font.setPixelSize(12)
      self.viewer.setFont(self.font)

      self.vlayout.addWidget(self.viewer)
      self.exitButton= QtGui.QPushButton("Exit")
      self.exitButton.setFixedWidth(60)
      self.exitButton.clicked.connect(self.do_exit)
      self.hlayout= QtGui.QHBoxLayout()
      self.hlayout.addWidget(self.exitButton)
      self.vlayout.addLayout(self.hlayout)

   def set_text(self,output):
      self.viewer.setText(output)
      return
   
#
# exit, do nothing
#
   def do_exit(self):
      self.close()

#
# get file and pipe it to filter program, show output in editor window
#
   @staticmethod
   def exec(lifimagefile, liffilename, liffiletype):
      d=cls_lifview()
      ft=get_finfo_name(liffiletype)
      call= get_finfo_type(ft)[1]
#
# decomp41 needs additional parameters (xrmoms)
#
      if call == "decomp41":
         call= cls_chkxrom.exec()
      output=exec_double_export(d,["lifget","-r",lifimagefile,liffilename],call,"")
#
# at the moment the text is only converted to ROMAN-8
#
      if output == None:
         return
      try:
         d.set_text(output.decode("HP-ROMAN8"))
      except UnicodeDecodeError as e:
         reply=QtGui.QMessageBox.critical(d,'Error','cannot decode file',QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         return
      result= d.exec_()
#
# Init LIF image file dialog
#      
class cls_lifinit (QtGui.QDialog):

   def __init__(self,workdir,parent= None):
      super().__init__()
      self.lifimagefile=""
      self.workdir= workdir
      self.mt="hdrive1"

      self.setWindowTitle("Initialize LIF Image File")
      self.vlayout= QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.gBox0=QtGui.QGroupBox("LIF image file")
      self.hbox=QtGui.QHBoxLayout()
      self.lblFilename=QtGui.QLabel(self.lifimagefile)
      self.hbox.addWidget(self.lblFilename)
      self.hbox.addStretch(1)
      self.butChange= QtGui.QPushButton("Change")
      self.butChange.clicked.connect(self.do_filenameChanged)
      self.hbox.addWidget(self.butChange)

      self.gBox0.setLayout(self.hbox)
      self.vlayout.addWidget(self.gBox0)

      self.gBox1=QtGui.QGroupBox("Medium type")
      self.bGroup=QtGui.QButtonGroup()
      self.radio1= QtGui.QRadioButton("HP 82161A cassette")
      self.radio2= QtGui.QRadioButton("HP 9114B double sided disk ")
      self.radio3= QtGui.QRadioButton("HDRIVE1 640 KB")
      self.radio4= QtGui.QRadioButton("HDRIVE1 2 MB")
      self.radio5= QtGui.QRadioButton("HDRIVE1 4 MB")
      self.radio6= QtGui.QRadioButton("HDRIVE1 8 MB")
      self.radio7= QtGui.QRadioButton("HDRIVE1 16 MB")
      self.radio3.setChecked(True)
      self.bGroup.addButton(self.radio1) 
      self.bGroup.addButton(self.radio2)
      self.bGroup.addButton(self.radio3)
      self.bGroup.addButton(self.radio4)
      self.bGroup.addButton(self.radio5)
      self.bGroup.addButton(self.radio6)
      self.bGroup.addButton(self.radio7)
      self.bGroup.buttonClicked.connect(self.do_butclicked)

      self.vbox=QtGui.QVBoxLayout()
      self.vbox.addWidget(self.radio1)
      self.vbox.addWidget(self.radio2)
      self.vbox.addWidget(self.radio3)
      self.vbox.addWidget(self.radio4)
      self.vbox.addWidget(self.radio5)
      self.vbox.addWidget(self.radio6)
      self.vbox.addWidget(self.radio7)

      self.hbox1=QtGui.QHBoxLayout()
      self.lbl1=QtGui.QLabel("Directory size:")
      self.hbox1.addWidget(self.lbl1)
      self.leditDirSize=QtGui.QLineEdit(self)
      self.leditDirSize.setText("500")
      self.leditDirSize.setMaxLength(4)
      self.regexpDirSize = QtCore.QRegExp('[1-9][0-9]*')
      self.validatorDirSize = QtGui.QRegExpValidator(self.regexpDirSize)
      self.leditDirSize.setValidator(self.validatorDirSize)
      self.leditDirSize.textChanged.connect(self.do_checkenable)
      self.hbox1.addWidget(self.leditDirSize)
      self.vbox.addLayout(self.hbox1)

      self.hbox2=QtGui.QHBoxLayout()
      self.lbl2=QtGui.QLabel("LIF Label:")
      self.hbox2.addWidget(self.lbl2)
      self.leditLabel=QtGui.QLineEdit(self)
      self.leditLabel.setText("")
      self.leditLabel.setMaxLength(6)
      self.regexpLabel = QtCore.QRegExp('[A-Z][A-Z,0-9]*')
      self.validatorLabel = QtGui.QRegExpValidator(self.regexpLabel)
      self.leditLabel.setValidator(self.validatorLabel)
      self.hbox2.addWidget(self.leditLabel)
      self.vbox.addLayout(self.hbox2)

      self.gBox1.setLayout(self.vbox)
      self.gBox1.setEnabled(False)
      self.vlayout.addWidget(self.gBox1)
      self.vbox.addStretch(1)

      self.buttonBox = QtGui.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
      self.vlayout.addWidget(self.buttonBox)
#
#  dialog to enter input file name
#
   def get_inputFilename(self):
      dialog=QtGui.QFileDialog()
      dialog.setWindowTitle("Select LIF Image File")
      dialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtGui.QFileDialog.AnyFile)
      dialog.setNameFilters( ["All Files (*.*)"] )
      dialog.setOptions(QtGui.QFileDialog.DontUseNativeDialog)
      dialog.setDirectory(self.workdir)
      if dialog.exec():
         return dialog.selectedFiles()
#
# callbacks
#

#
# change filename button
#
   def do_filenameChanged(self):
      flist= self.get_inputFilename()
      if flist == None:
         return
      self.lifimagefile=flist[0]
      self.lblFilename.setText(self.lifimagefile)
      self.gBox1.setEnabled(True)
      self.do_checkenable()
#
#  radio button clicked, set default directory size
#
   def do_butclicked(self):

      if self.radio1.isChecked():
         self.leditDirSize.setText("150")
         self.mt="cass"
      if self.radio2.isChecked():
         self.leditDirSize.setText("500")
         self.mt="disk"
      if self.radio3.isChecked():
         self.leditDirSize.setText("500")
         self.mt="hdrive1"
      if self.radio4.isChecked():
         self.leditDirSize.setText("1000")
         self.mt="hdrive2"
      if self.radio5.isChecked():
         self.leditDirSize.setText("2000")
         self.mt="hdrive4"
      if self.radio6.isChecked():
         self.leditDirSize.setText("2000")
         self.mt="hdrive8"
      if self.radio7.isChecked():
         self.leditDirSize.setText("2000")
         self.mt="hdrive16"
      self.do_checkenable()
#
#  check, if the OK button can be enabled
#
   def do_checkenable(self):
      self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
      if (self.leditDirSize != "" and self.lifimagefile != ""):
         self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)
      return

#
#  OK button, initialize file
#
   def do_ok(self):
      if self.lifimagefile != "":
         if os.access(self.lifimagefile,os.W_OK):
            reply=QtGui.QMessageBox.warning(self,'Warning',"Do you really want to overwrite file "+self.lifimagefile,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Cancel)
            if reply== QtGui.QMessageBox.Cancel:
               return
         exec_single(self,["lifinit","-m",self.mt,self.lifimagefile,self.leditDirSize.text()])
         if self.leditLabel.text() != "":
            exec_single(self,["liflabel",self.lifimagefile,self.leditLabel.text()])
      self.close()

#
#  cancel
#
   def do_cancel(self):
      self.close()

   @staticmethod
   def exec(workdir):
      d=cls_lifinit(workdir)
      result= d.exec_()
#
# fix LIF header dialog
#
class cls_liffix (QtGui.QDialog):

   def __init__(self,workdir,parent= None):
      super().__init__()
      self.lifimagefile=""
      self.workdir= workdir
      self.mt="hdrive1"

      self.setWindowTitle("Fix header of LIF Image File")
      self.vlayout= QtGui.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.gBox0=QtGui.QGroupBox("LIF image file")
      self.hbox=QtGui.QHBoxLayout()
      self.lblFilename=QtGui.QLabel(self.lifimagefile)
      self.hbox.addWidget(self.lblFilename)
      self.hbox.addStretch(1)
      self.butChange= QtGui.QPushButton("Change")
      self.butChange.clicked.connect(self.do_filenameChanged)
      self.hbox.addWidget(self.butChange)

      self.gBox0.setLayout(self.hbox)
      self.vlayout.addWidget(self.gBox0)

      self.gBox1=QtGui.QGroupBox("Medium type")
      self.bGroup=QtGui.QButtonGroup()
      self.radio1= QtGui.QRadioButton("HP 82161A cassette")
      self.radio2= QtGui.QRadioButton("HP 9114B double sided disk ")
      self.radio3= QtGui.QRadioButton("HDRIVE1 640 KB")
      self.radio4= QtGui.QRadioButton("HDRIVE1 2 MB")
      self.radio5= QtGui.QRadioButton("HDRIVE1 4 MB")
      self.radio6= QtGui.QRadioButton("HDRIVE1 8 MB")
      self.radio7= QtGui.QRadioButton("HDRIVE1 16 MB")
      self.radio3.setChecked(True)
      self.bGroup.addButton(self.radio1) 
      self.bGroup.addButton(self.radio2)
      self.bGroup.addButton(self.radio3)
      self.bGroup.addButton(self.radio4)
      self.bGroup.addButton(self.radio5)
      self.bGroup.addButton(self.radio6)
      self.bGroup.addButton(self.radio7)
      self.bGroup.buttonClicked.connect(self.do_butclicked)

      self.vbox=QtGui.QVBoxLayout()
      self.vbox.addWidget(self.radio1)
      self.vbox.addWidget(self.radio2)
      self.vbox.addWidget(self.radio3)
      self.vbox.addWidget(self.radio4)
      self.vbox.addWidget(self.radio5)
      self.vbox.addWidget(self.radio6)
      self.vbox.addWidget(self.radio7)

      self.vbox.addStretch(1)
      self.vlayout.addLayout(self.vbox)

      self.buttonBox = QtGui.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
      self.vlayout.addWidget(self.buttonBox)
#
#  dialog to enter input file name
#
   def get_inputFilename(self):
      dialog=QtGui.QFileDialog()
      dialog.setWindowTitle("Select LIF Image File")
      dialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
      dialog.setNameFilters( ["All Files (*.*)"] )
      dialog.setOptions(QtGui.QFileDialog.DontUseNativeDialog)
      dialog.setDirectory(self.workdir)
      if dialog.exec():
         return dialog.selectedFiles()
#
# callbacks
#

#
# change filename button
#
   def do_filenameChanged(self):
      flist= self.get_inputFilename()
      if flist == None:
         return
      self.lifimagefile=flist[0]
      self.lblFilename.setText(self.lifimagefile)
      self.gBox1.setEnabled(True)
      self.do_checkenable()
#
#  radio button clicked, set default directory size
#
   def do_butclicked(self):

      if self.radio1.isChecked():
         self.mt="cass"
      if self.radio2.isChecked():
         self.mt="disk"
      if self.radio3.isChecked():
         self.mt="hdrive1"
      if self.radio4.isChecked():
         self.mt="hdrive2"
      if self.radio5.isChecked():
         self.mt="hdrive4"
      if self.radio6.isChecked():
         self.mt="hdrive8"
      if self.radio7.isChecked():
         self.mt="hdrive16"
      self.do_checkenable()
#
#  check, if the OK button can be enabled
#
   def do_checkenable(self):
      self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
      if self.lifimagefile != "":
         self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)
      return

#
#  OK button, initialize file
#
   def do_ok(self):
      if self.lifimagefile != "":
         exec_single(self,["liffix","-m",self.mt,self.lifimagefile])
      self.close()
#
#  cancel
#
   def do_cancel(self):
      self.close()

   @staticmethod
   def exec(workdir):
      d=cls_liffix(workdir)
      result= d.exec_()
#
