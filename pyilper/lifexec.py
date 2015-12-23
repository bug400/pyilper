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
#
import os
import subprocess
import platform
from PyQt4 import QtCore, QtGui

 
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
         try:
            subprocess.check_output(["lifpack",lifimagefile],stderr=subprocess.STDOUT)
         except OSError as e:
            reply=QtGui.QMessageBox.critical(d,'Error',e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         except subprocess.CalledProcessError as exp:
            reply=QtGui.QMessageBox.critical(d,'Error',exp.output.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)

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
         try:
            subprocess.check_output(["lifpurge",lifimagefile,liffile],stderr=subprocess.STDOUT)
         except OSError as e:
            reply=QtGui.QMessageBox.critical(d,'Error',e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         except CalledProcessError as exc:
            reply=QtGui.QMessageBox.critical(d,'Error',exp.output.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)

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
         try:
            subprocess.check_output(["lifrename",lifimagefile,liffile,newfilename],stderr=subprocess.STDOUT)
         except OSError as e:
            reply=QtGui.QMessageBox.critical(d,'Error',e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         except subprocess.CalledProcessError as exc:
            reply=QtGui.QMessageBox.critical(d,'Error',exc.output.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      
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
      self.radio2= QtGui.QRadioButton("remove LIF header")
      self.radio3= QtGui.QRadioButton("None")
      if self.liffiletype== "TEXT":
         self.radio1.setChecked(True)
         self.outputextension=".txt"
      else:
         self.radio3.setChecked(True)
         self.outputextension=".lif"

      self.vbox=QtGui.QVBoxLayout()
      self.vbox.addWidget(self.radio1)
      self.vbox.addWidget(self.radio2)
      self.vbox.addWidget(self.radio3)
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
         if os.access(self.outputfile,os.W_OK):
            reply=QtGui.QMessageBox.warning(self,'Warning',"Do you really want to overwrite file "+self.outputfile,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Cancel)
            if reply== QtGui.QMessageBox.Cancel:
               self.close()
               return
         try:
            if self.radio1.isChecked():
               if platform.win32_ver()[0] != "":
                  fd= os.open(self.outputfile, os.O_WRONLY | os.O_BINARY |  os.O_TRUNC | os.O_CREAT, 0o644)
               else:
                  fd= os.open(self.outputfile, os.O_WRONLY | os.O_TRUNC | os.O_CREAT, 0o644)
               p1= subprocess.Popen(["lifget","-r",self.lifimagefile,self.liffilename],stdout=subprocess.PIPE)
               p2= subprocess.Popen("liftext",stdin=p1.stdout,stdout=fd)
               p1.stdout.close()
               output=p2.communicate()[0]
               os.close(fd)

            elif self.radio2.isChecked():
                  cmd=["lifget","-r",self.lifimagefile,self.liffilename,self.outputfile]
                  subprocess.check_output(cmd,stderr=subprocess.STDOUT)
            elif self.radio3.isChecked():
                  cmd=["lifget",self.lifimagefile,self.liffilename,self.outputfile]
                  subprocess.check_output(cmd,stderr=subprocess.STDOUT)
         except OSError as e:
            reply=QtGui.QMessageBox.critical(self,'Error',e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         except subprocess.CalledProcessError as exc:
            reply=QtGui.QMessageBox.critical(self,'Error',exc.output.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      
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
      self.radio2= QtGui.QRadioButton("None")
      self.radio2.setChecked(True)
      self.bGroup.addButton(self.radio1) 
      self.bGroup.addButton(self.radio2)
      self.bGroup.buttonClicked.connect(self.do_butclicked)

      self.vbox=QtGui.QVBoxLayout()
      self.vbox.addWidget(self.radio1)

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
      self.vbox.addWidget(self.radio2)
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
      if id== self.radio1:
         self.leditFileName.setEnabled(True)
      else:
         self.leditFileName.setEnabled(False)
      self.do_checkenable()

#
#  check, if the OK button can be enabled
#
   def do_checkenable(self):
      self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
      if self.radio1.isChecked() and self.leditFileName.text() != "":
         self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)
      if self.radio2.isChecked():
         self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)
      return

#
#  OK button callback import file
#
   def do_ok(self):
      if self.inputfile != "":
         try:
            if self.radio1.isChecked():
               self.liffilename=self.leditFileName.text()
               if platform.win32_ver()[0] != "":
                  fd= os.open(self.inputfile, os.O_RDONLY | os.O_BINARY )
               else:
                  fd= os.open(self.inputfile, os.O_RDONLY)
               p1= subprocess.Popen(["textlif",self.liffilename],stdin=fd,stdout=subprocess.PIPE)
               p2= subprocess.Popen(["lifput",self.lifimagefile],stdin=p1.stdout)
               p1.stdout.close()
               output=p2.communicate()[0]
               os.close(fd)
            else:
               cmd=["lifput",self.lifimagefile,self.inputfile]
               subprocess.check_output(cmd,stderr=subprocess.STDOUT)
         except OSError as e:
            reply=QtGui.QMessageBox.critical(self,'Error',e.strerror,QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
         except subprocess.CalledProcessError as exc:
            reply=QtGui.QMessageBox.critical(self,'Error',exc.output.decode(),QtGui.QMessageBox.Ok,QtGui.QMessageBox.Ok)
      
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
