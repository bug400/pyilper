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
# 05.01.2016 - jsi
# - replaced process pipelines with temporary files to catch error conditions more
#   reliable
# - added viewing LEX file contents
# - decode output of textfiles in HP-ROMAN8 character set
# 08.01.2016 - jsi
# - introduced lifglobal.py, refactoring
# 16.01.2016 - jsi
# - introduced cls_chk_import
# 24.01.2016 - jsi
# - corrected regexp syntax of validators, hint by cg
# - new validator class automatically converts to capital letters
# - fixed "cancel" behaviour of cls_liflabel, refactores cls_lifrename
# - disable ok button if filename is empty in cls_lifrename
# - fixed "OK" not enabled in cls_lifimport for FOCAL raw files
# - check if outputfile overwrites existing file in cls_lifexport
# 30.01.2016 - jsi:
# - added unpack HEPAX ROM file postprocessiong option to cls_lifexport
# - added check if LIFUTILS are installed
# 01.02.2016 - jsi
# - added save button to save the contents of the viewer to a file
# - added LIFUTILS installation check dialog
# 08.02.2016 - jsi
# - changed os detection to platform.system()
# 19.02.2016 jsi
# - added configurable character set encoding to cls_lifview
# 05.03.2016 jsi
# - removed unneeded variables
# 12.03.2016 jsi
# - open view outputfile as unicode
# 13.03.2016 jsi
# - modified exit of modal dialogs
# 14.04.2016 jsi
# - modified filter for all files to * in file dialog
# 27.04.2016 jsi
# - do not set path for QFileDialog, it remembers the last dir automatically
# 11.07.2016 jsi
# - use functions from pilcore.py for platform detection
# 27.08.2016 jsi
# - removed duplicate dialog warning for overwriting existing file in  cls_lifexport
# 01.10.2016 jsi
# - plotter rom added to xrom dialog
# 22.08.2017 jsi
# - cls_lifbarcode added
# - truncate error messages from external programs to 150 chars
# 01.09.2017 jsi
# - moved get_pdfFilename to cls_pdfprinter
# 16.08.2017 jsi
# - used barrconv instead of stringconv. There is no unicode exception any more.
#
import os
import subprocess
import tempfile
from PyQt5 import QtCore, QtGui, QtWidgets, QtPrintSupport
from .lifcore import *
from .pilcharconv import barrconv, CHARSET_HP71, CHARSET_HP41, CHARSET_ROMAN8, charsets
from .pilcore import isWINDOWS, FONT, decode_version, PDF_ORIENTATION_PORTRAIT
from .pilconfig import PILCONFIG
from .pilpdf import cls_pdfprinter

PDF_MARGINS=100
BARCODE_HEIGHT=100
BARCODE_NARROW_W= 5
BARCODE_WIDE_W= 10
BARCODE_SPACING= 5
#
# decode an error message to string and truncate it to 150 chars
#
def trunc_message(msg):
   temp= msg.decode()
   return (temp[:75] + '.. (truncated)') if len(temp) > 150 else temp

#
# check if lifutils are installed, return if required version found
#
def check_lifutils():
   required_version_installed=False
   installed_version=0
   try:
      result=subprocess.check_output("lifversion")
      installed_version=int(result.decode())
      if int(installed_version) >= LIFUTILS_REQUIRED_VERSION:
         required_version_installed=True
   except OSError as e:
      pass
   except subprocess.CalledProcessError as exp:
      pass
   return required_version_installed, installed_version
#
# exec single command
#
def exec_single(parent,cmd):
   try:
      subprocess.check_output(cmd,stderr=subprocess.STDOUT)
   except OSError as e:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
   except subprocess.CalledProcessError as exp:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',trunc_message(exp.output),QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
#
# exec single command, return output
#
def exec_single_export(parent,cmd):
   try:
      p= subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      output,err=p.communicate()
      if err.decode() != "":
         reply=QtWidgets.QMessageBox.critical(parent,'Error',trunc_message(err),QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         return None
#
#  catch errors
#
   except OSError as e:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
      return None
   except subprocess.CalledProcessError as exc:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',trunc_message(exc.output),QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
      return None
   return output

#
# exec piped command, read input from file, return True if success, False otherwise
#
def exec_double_import(parent,cmd1,cmd2,inputfile):

   try:
      if isWINDOWS():
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
         reply=QtWidgets.QMessageBox.critical(d,'Error',trunc_message(err1),QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         tmpfile.close()
         os.close(fd)
         return
      os.close(fd)
#
#  execute second command
#
      tmpfile.seek(0)
      if  not cls_chk_import.exec(tmpfile.fileno(), None):
         tmpfile.close()
         return
      tmpfile.seek(0)
      p2= subprocess.Popen(cmd2,stdin=tmpfile,stderr=subprocess.PIPE)
      output2,err2=p2.communicate()
      if err2.decode() != "":
         reply=QtWidgets.QMessageBox.critical(parent,'Error',trunc_message(err2),QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         tmpfile.close()
         return
#
#  catch errors
#
   except OSError as e:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
   except subprocess.CalledProcessError as exc:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',trunc_message(exc.output),QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
      tmpfile.close()
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
            reply=QtWidgets.QMessageBox.warning(parent,'Warning',"Do you really want to overwrite file "+outputfile,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Cancel)
            if reply== QtWidgets.QMessageBox.Cancel:
               return
         if isWINDOWS():
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
         reply=QtWidgets.QMessageBox.critical(parent,'Error',trunc_message(err1),QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
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
         reply=QtWidgets.QMessageBox.critical(parent,'Error',trunc_message(err2),QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
         if fd != None:
            os.close(fd)
         return None
      if fd != None:
         os.close(fd)
#
#  catch errors
#
   except OSError as e:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
      tmpfile.close()
      return None
   except subprocess.CalledProcessError as exc:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',trunc_message(exc.output),QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
      tmpfile.close()
      return None
   tmpfile.close()
   return output2

#
# validator checks for valid lif label or file names, converts to capital lettes
#
class cls_LIF_validator(QtGui.QValidator):

   def validate(self,string,pos):
      self.regexp = QtCore.QRegExp('[A-Za-z][A-Za-z0-9]*')
      self.validator = QtGui.QRegExpValidator(self.regexp)
      result=self.validator.validate(string,pos)
      return result[0], result[1].upper(), result[2]
#
# pack lif image file dialog
#
class cls_lifpack(QtWidgets.QDialog):

   def __init__(self,parent= None):
      super().__init__()

   @staticmethod
   def exec(lifimagefile):
      d=cls_lifpack()
      reply = QtWidgets.QMessageBox.question(d, 'Message', 'Do you really want to pack the LIF image file', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
      if reply == QtWidgets.QMessageBox.Yes:
         exec_single(d,["lifpack",lifimagefile])
#
# custom class for text item
#
class cls_textItem(QtWidgets.QGraphicsItem):

   def __init__(self,text):
      super().__init__()
      self.text=text
      self.font= QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
      self.font.setStyleHint(QtGui.QFont.TypeWriter)
      self.font.setPointSize(2)
      metrics= QtGui.QFontMetrics(self.font)
      self.font_h= metrics.height()
      self.font_w= metrics.width("A")
      self.spacing=20
      self.h= self.font_h+self.spacing*2
      self.w= len(text)* self.font_w
      self.rect= QtCore.QRectF(0,0,self.w,self.h)

   def setPos(self,x,y):
      super().setPos(x,y-self.h)

   def boundingRect(self):
      return self.rect

   def paint(self,painter,option,widget):
      posx=0
      posy=self.font_h
      painter.setFont(self.font)
      painter.drawText(posx,posy,self.text)
#
# custom class for barcode
#
class cls_barcodeItem(QtWidgets.QGraphicsItem):

   def __init__(self,barcode_title,barcode_row, barcode_height, barcode_narrow_w, barcode_wide_w, barcode_spacing):
      super().__init__()
      self.font=QtGui.QFont()
      self.font.setPointSize(2)
      metrics= QtGui.QFontMetrics(self.font)
      self.font_h= metrics.height()
      self.spacing=20
      self.h= self.font_h+barcode_height+self.spacing*3
      self.w= len(barcode_row)*(barcode_wide_w+barcode_spacing)*8+(barcode_wide_w+barcode_spacing)*4
      self.barcode_title= barcode_title
      self.barcode_row= barcode_row
      self.barcode_height= barcode_height
      self.barcode_narrow_w= barcode_narrow_w
      self.barcode_wide_w= barcode_wide_w
      self.barcode_spacing= barcode_spacing
      self.rect= QtCore.QRectF(0,0,self.w,self.h)
      
   def setPos(self,x,y):
      super().setPos(x,y-self.h)

   def boundingRect(self):
      return self.rect

   def paint(self,painter,option,widget):
      posx=0
      posy=self.font_h
#
#     header text
#
      painter.setFont(self.font)
      painter.drawText(posx,posy,self.barcode_title)
      posy+=self.spacing
#
#     barcodes
#
      painter.fillRect(posx,posy,self.barcode_narrow_w,self.barcode_height,QtCore.Qt.black)
      posx+= self.barcode_narrow_w+self.barcode_spacing
      painter.fillRect(posx,posy,self.barcode_narrow_w,self.barcode_height,QtCore.Qt.black)
      posx+= self.barcode_narrow_w+self.barcode_spacing

      for i in range(len(self.barcode_row)):
         for k in reversed(range(8)):
            if self.barcode_row[i] & (1 << k):
               painter.fillRect(posx,posy,self.barcode_wide_w,self.barcode_height,QtCore.Qt.black)
               posx+= self.barcode_wide_w+self.barcode_spacing
            else:
               painter.fillRect(posx,posy,self.barcode_narrow_w,self.barcode_height,QtCore.Qt.black)
               posx+= self.barcode_narrow_w+self.barcode_spacing
      painter.fillRect(posx,posy,self.barcode_wide_w,self.barcode_height,QtCore.Qt.black)
      posx+= self.barcode_wide_w+self.barcode_spacing
      painter.fillRect(posx,posy,self.barcode_narrow_w,self.barcode_height,QtCore.Qt.black)
      posx+= self.barcode_narrow_w+self.barcode_spacing
      return
#
# output barcode dialog
#
class cls_lifbarcode(QtWidgets.QDialog):
 

   def __init__(self):
      super().__init__()

   @staticmethod
   def exec (lifimagefile, liffilename, ft,papersize):
      d= cls_lifbarcode()
#
#     get output file name
#
      flist= cls_pdfprinter.get_pdfFilename()
      if flist== None:
         return
      output_filename= flist[0]
#
#     generate binary barcode data from lifutils prog41bar or sdatabar
#
      if ft== 0xE080:
         output=exec_double_export(d,["lifget","-r",lifimagefile,liffilename],["prog41bar"],"")
         title="Barcodes for HP-41 program file: "+liffilename
      else:
         output=exec_double_export(d,["lifget","-r",lifimagefile,liffilename],["sdatabar"],"")
         title="Barcodes for HP-41 data file: "+liffilename
      if output == None:
         return

#
#     initialize pdf printer
#
      pdfprinter=cls_pdfprinter(papersize,PDF_ORIENTATION_PORTRAIT, output_filename,title,True,1)
      pdfprinter.begin()
#
#     process binary barcode data and generate PDF file
#
      i=0
      row=0
      while i < len(output):
#        Process barcode, print title
#
         row+=1
         length=(output[i] &0xF)+1
         barcode_row= []
         i+=1
         for k in range(length):
           if i== len(output):
              return
           barcode_row.append(output[i])
           i+=1
         barcode_header="Row: "+str(row)
         barcode_item= cls_barcodeItem(barcode_header,barcode_row,BARCODE_HEIGHT, BARCODE_NARROW_W, BARCODE_WIDE_W, BARCODE_SPACING)
         pdfprinter.print_item(barcode_item)
#
      pdfprinter.end()

#
# purge file dialog
#
class cls_lifpurge(QtWidgets.QDialog):

   def __init__(self,parent= None):
      super().__init__()

   @staticmethod
   def exec(lifimagefile,liffile):
      d=cls_lifpurge()
      reply = QtWidgets.QMessageBox.question(d, 'Message', 'Do you really want to purge '+liffile, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
      if reply == QtWidgets.QMessageBox.Yes:
         exec_single(d,["lifpurge",lifimagefile, liffile])

#
# rename file dialog
#
class cls_lifrename (QtWidgets.QDialog):

   def __init__(self,lifimagefile,filename,parent= None):
      super().__init__()
      self.lifimagefile=lifimagefile
      self.oldfilename=filename
      self.setWindowTitle("Rename File")
      self.vlayout= QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.lbl=QtWidgets.QLabel("Rename file:")
      self.vlayout.addWidget(self.lbl)
      self.leditFileName=QtWidgets.QLineEdit(self)
      self.leditFileName.setText(filename)
      self.leditFileName.setMaxLength(10)
      self.leditFileName.textChanged.connect(self.do_checkenable)
      self.validator = cls_LIF_validator()
      self.leditFileName.setValidator(self.validator)
      self.vlayout.addWidget(self.leditFileName)

      self.buttonBox = QtWidgets.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.buttonBox)

#
#  check, if the OK button can be enabled
#
   def do_checkenable(self):
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      if (self.leditFileName.text() != ""):
         self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
      return

# 
#  ok rename file
#
   def do_ok(self):
      newfilename=self.leditFileName.text()
      if newfilename != "":
         exec_single(self,["lifrename",self.lifimagefile,self.oldfilename,newfilename])
      super().accept()

#
#  cancel do nothing
#
   def do_cancel(self):
      super().reject()

   @staticmethod
   def exec(lifimagefile,liffile):
      d=cls_lifrename(lifimagefile,liffile)
      result= d.exec_()
#
# export file dialog
#
class cls_lifexport (QtWidgets.QDialog):

   def __init__(self,lifimagefile,liffilename,liffiletype,workdir,parent= None):
      super().__init__()
      self.lifimagefile= lifimagefile
      self.liffiletype= liffiletype
      self.liffilename= liffilename
      self.workdir=workdir
      self.setWindowTitle("Export File")
      self.vlayout= QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.gBox0=QtWidgets.QGroupBox("File to be exported to file system")
      self.lblLifFilename=QtWidgets.QLabel(self.liffilename+" (type: "+self.liffiletype+")")
      self.vbox0=QtWidgets.QVBoxLayout()
      self.vbox0.addWidget(self.lblLifFilename)
      self.vbox0.addStretch(1)
      self.gBox0.setLayout(self.vbox0)
      self.vlayout.addWidget(self.gBox0)
      
      self.gBox1=QtWidgets.QGroupBox("Postprocessing options")
      self.radio1= QtWidgets.QRadioButton("convert LIF-Text to ASCII")
      self.radio1.setEnabled(False)
      self.radio2= QtWidgets.QRadioButton("descramble HP41 ROM file")
      self.radio2.setEnabled(False)
      self.radio3= QtWidgets.QRadioButton("unpack HEPAX HP41 SDATA ROM file")
      self.radio3.setEnabled(False)
      self.radio4= QtWidgets.QRadioButton("remove LIF header")
      self.radio5= QtWidgets.QRadioButton("None")

      if self.liffiletype== "TEXT":
         self.radio1.setEnabled(True)
         self.radio1.setChecked(True)
         self.outputextension=".txt"
      elif self.liffiletype== "ROM41":
         self.radio2.setEnabled(True)
         self.radio2.setChecked(True)
         self.outputextension=".rom"
      elif self.liffiletype== "SDATA":
         self.radio5.setChecked(True)
         self.radio3.setEnabled(True)
         self.radio3.clicked.connect(self.do_radio3)
         self.outputextension=".lif"
      else:
         self.radio5.setChecked(True)
         self.outputextension=".lif"

      self.vbox=QtWidgets.QVBoxLayout()
      self.vbox.addWidget(self.radio1)
      self.vbox.addWidget(self.radio2)
      self.vbox.addWidget(self.radio3)
      self.vbox.addWidget(self.radio4)
      self.vbox.addWidget(self.radio5)
      self.vbox.addStretch(1)
      self.gBox1.setLayout(self.vbox)

      self.vlayout.addWidget(self.gBox1)

      self.gBox2=QtWidgets.QGroupBox("Output file")
      self.hbox=QtWidgets.QHBoxLayout()
      self.outputfile=os.path.join(self.workdir, self.liffilename.lower()+self.outputextension)
      self.lblFilename=QtWidgets.QLabel(self.outputfile)
      self.hbox.addWidget(self.lblFilename)
      self.hbox.addStretch(1)
      self.butChange= QtWidgets.QPushButton("Change")
      self.butChange.clicked.connect(self.do_filenameChanged)
      self.hbox.addWidget(self.butChange)
      self.gBox2.setLayout(self.hbox)

      self.vlayout.addWidget(self.gBox2)

      self.buttonBox = QtWidgets.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.buttonBox)

   def do_radio3(self):
      if self.radio3.isChecked():
         self.outputextension=".rom"
      else:
         self.outputextension=".lif"
      self.outputfile=os.path.join(self.workdir, self.liffilename.lower()+self.outputextension)
      self.lblFilename.setText(self.outputfile)
#
#  enter output file name dialog
#
   def get_outputFilename(self):
      dialog=QtWidgets.QFileDialog()
      dialog.setWindowTitle("Select Output File")
      dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
      dialog.setNameFilters( ["All Files (*)"] )
      dialog.selectFile(self.liffilename.lower()+self.outputextension)
      dialog.setOptions(QtWidgets.QFileDialog.DontUseNativeDialog)
#     dialog.setDirectory(self.workdir)
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
            exec_double_export(self,["lifget","-r",self.lifimagefile,self.liffilename],"hx41rom",self.outputfile)
         elif self.radio4.isChecked():
            exec_single(self,["lifget","-r",self.lifimagefile,self.liffilename,self.outputfile])
         elif self.radio5.isChecked():
            exec_single(self,["lifget",self.lifimagefile,self.liffilename,self.outputfile])
      super().accept()
#
#  cancel: do nothing
#
   def do_cancel(self):
      super().reject()

   @staticmethod
   def exec(lifimagefile,liffilename,liffiletype,workdir):
      d=cls_lifexport(lifimagefile,liffilename,liffiletype,workdir)
      result= d.exec_()

#
# label lif image file dialog
#
class cls_liflabel (QtWidgets.QDialog):

   def __init__(self,lifimagefile,oldlabel,parent= None):
      super().__init__()
      self.lifimagefile=lifimagefile
      self.setWindowTitle("Label LIF image file")
      self.vlayout= QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.lbl=QtWidgets.QLabel("Label:")
      self.vlayout.addWidget(self.lbl)
      self.leditLabel=QtWidgets.QLineEdit(self)
      self.leditLabel.setText(oldlabel)
      self.leditLabel.setMaxLength(6)
      self.validator = cls_LIF_validator()
      self.leditLabel.setValidator(self.validator)
      self.vlayout.addWidget(self.leditLabel)

      self.buttonBox = QtWidgets.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.buttonBox)

   def do_ok(self):
      newlabel=self.leditLabel.text()
      if newlabel != "":
         exec_single(self,["liflabel",self.lifimagefile, newlabel])
      else:
         exec_single(self,["liflabel","-c",self.lifimagefile])
      super().accept()

   def do_cancel(self):
      super().reject()

   @staticmethod
   def exec(lifimagefile,oldlabel):
      d=cls_liflabel(lifimagefile,oldlabel)
      result= d.exec_()
#
# import file dialog
#
class cls_lifimport (QtWidgets.QDialog):

   def __init__(self,lifimagefile,workdir,parent= None):
      super().__init__()
      self.inputfile=""
      self.lifimagefile=lifimagefile
      self.workdir= workdir
      self.liffilename=""

      self.setWindowTitle("Import File")
      self.vlayout= QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.gBox0=QtWidgets.QGroupBox("Input file")
      self.hbox=QtWidgets.QHBoxLayout()
      self.lblFilename=QtWidgets.QLabel(self.inputfile)
      self.hbox.addWidget(self.lblFilename)
      self.hbox.addStretch(1)
      self.butChange= QtWidgets.QPushButton("Change")
      self.butChange.clicked.connect(self.do_filenameChanged)
      self.hbox.addWidget(self.butChange)
      self.gBox0.setLayout(self.hbox)
      self.vlayout.addWidget(self.gBox0)

      self.gBox1=QtWidgets.QGroupBox("Preprocessing options")
      self.bGroup=QtWidgets.QButtonGroup()
      self.radio1= QtWidgets.QRadioButton("convert from ASCII to LIF-Text")
      self.radio2= QtWidgets.QRadioButton("convert HP-41 rom file to SDATA file (HEPAX)")
      self.radio3= QtWidgets.QRadioButton("add LIF header to HP41 FOCAL raw file")
      self.radio4= QtWidgets.QRadioButton("None")
      self.radio4.setChecked(True)
      self.bGroup.addButton(self.radio1) 
      self.bGroup.addButton(self.radio2)
      self.bGroup.addButton(self.radio3)
      self.bGroup.addButton(self.radio4)
      self.bGroup.buttonClicked.connect(self.do_butclicked)

      self.vbox=QtWidgets.QVBoxLayout()
      self.vbox.addWidget(self.radio1)
      self.vbox.addWidget(self.radio2)
      self.vbox.addWidget(self.radio3)

      self.hbox2=QtWidgets.QHBoxLayout()
      self.lbl=QtWidgets.QLabel("LIF Filename:")
      self.hbox2.addWidget(self.lbl)
      self.leditFileName=QtWidgets.QLineEdit(self)
      self.leditFileName.setText(self.liffilename)
      self.leditFileName.setMaxLength(10)
      self.validator = cls_LIF_validator()
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

      self.buttonBox = QtWidgets.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      self.vlayout.addWidget(self.buttonBox)
#
#  dialog to enter input file name
#
   def get_inputFilename(self):
      dialog=QtWidgets.QFileDialog()
      dialog.setWindowTitle("Select Input File")
      dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
      dialog.setNameFilters( ["All Files (*)"] )
      dialog.setOptions(QtWidgets.QFileDialog.DontUseNativeDialog)
#     dialog.setDirectory(self.workdir)
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
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      if (self.radio1.isChecked() or self.radio2.isChecked() or self.radio3.isChecked()) and self.leditFileName.text() != "":
         self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
      if self.radio4.isChecked():
         self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
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
            if  cls_chk_import.exec(None, self.inputfile):
               exec_single(self,["lifput",self.lifimagefile,self.inputfile])
      super().accept()

#
#  cancel
#
   def do_cancel(self):
      super().reject()

   @staticmethod
   def exec(lifimagefile,workdir):
      d=cls_lifimport(lifimagefile,workdir)
      result= d.exec_()
#
# check import dialog, ensure that we import a valid LIF transport file
#
class cls_chk_import(QtWidgets.QDialog):
   def __init__(self,fd,inputfile,parent=None):
      super().__init__()
      self.filename=""
      self.ftype_num=0
      self.blocks=0
      self.retval=False
      self.setWindowTitle("Import File to LIF Image file")
      self.vlayout= QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)
      self.vlayout.addWidget(QtWidgets.QLabel("Import this file?"))
      self.grid=QtWidgets.QGridLayout()
      self.grid.addWidget(QtWidgets.QLabel("Filename:"),0,0)
      self.grid.addWidget(QtWidgets.QLabel("Filetype:"),1,0)
      self.grid.addWidget(QtWidgets.QLabel("Filesize (Blocks):"),2,0)
      self.lblFilename=QtWidgets.QLabel("")
      self.grid.addWidget(self.lblFilename,0,1)
      self.lblFiletype=QtWidgets.QLabel("")
      self.grid.addWidget(self.lblFiletype,1,1)
      self.lblFilesize=QtWidgets.QLabel("")
      self.grid.addWidget(self.lblFilesize,2,1)

      self.vlayout.addLayout(self.grid)
      self.lblMessage=QtWidgets.QLabel("")
      self.vlayout.addWidget(self.lblMessage)
      self.buttonBox = QtWidgets.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.vlayout.addWidget(self.buttonBox)
#
#     examine header information, if inputfile is None then we have a file descriptor
#
      try:
         if inputfile is not None:
            if isWINDOWS():
               fd= os.open(inputfile, os.O_RDONLY | os.O_BINARY )
            else:
               fd= os.open(inputfile, os.O_RDONLY)
         b=os.read(fd,32)
         if len(b) <32:
            self.lblMessage.setText("File is too short")
         else:
            self.filename=getLifString(b,0,10)
            self.ftype_num=getLifInt(b,10,2)
            self.blocks=getLifInt(b,16,4)
            self.filetype=get_finfo_type(self.ftype_num)
            if self.filetype== None:
               self.filetype="Unknown"
            else:
               self.filetype= self.filetype[0]
            self.lblFilename.setText(self.filename)
            self.lblFiletype.setText(self.filetype)
            self.lblFilesize.setText(str(self.blocks))
         if inputfile is not None:
            os.close(fd)
#
#        Check valid header
#
         if self.blocks < 1:
            self.lblMessage.setText("Illegal file length")
            return
         if self.filetype=="Unknown":
            self.lblMessage.setText("Unknown file type")
            return
         self.regexp = QtCore.QRegExp('[A-Z][A-Z0-9]*')
         self.validator = QtGui.QRegExpValidator(self.regexp)
         result=self.validator.validate(self.filename,0)[0]
         if result != QtGui.QValidator.Acceptable:
            self.lblMessage.setText("Illegal file name")
            return
         self.lblMessage.setText("Ready to import")
         self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
      
      except OSError as e:
         self.lblMessage.setText("Error while examining file")

   def do_ok(self):
      self.retval=True
      super().accept()

   def do_cancel(self):
      super().reject()

   def get_retval(self):
      return self.retval


   @staticmethod
   def exec(fd,inputfile):
      d=cls_chk_import(fd,inputfile)
      result= d.exec_()
      return d.get_retval()
#
# check xroms dialog
#
class cls_chkxrom(QtWidgets.QDialog):

   def __init__(self,parent=None):
      super().__init__()
      self.call=["decomp41"]

      self.setWindowTitle("Check ROM Modules")
      self.vlayout= QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.cardrdr= QtWidgets.QCheckBox("Card Reader")
      self.vlayout.addWidget(self.cardrdr)
      self.printer= QtWidgets.QCheckBox("Printer")
      self.vlayout.addWidget(self.printer)
      self.wand= QtWidgets.QCheckBox("Wand")
      self.vlayout.addWidget(self.wand)
      self.hpil= QtWidgets.QCheckBox("HP-IL")
      self.vlayout.addWidget(self.hpil)
      self.hpil.setChecked(True)
      self.xfunc= QtWidgets.QCheckBox("X-Function")
      self.vlayout.addWidget(self.xfunc)
      self.xfunc.setChecked(True)
      self.time= QtWidgets.QCheckBox("Time")
      self.vlayout.addWidget(self.time)
      self.hepax= QtWidgets.QCheckBox("HEPAX")
      self.vlayout.addWidget(self.hepax)
      self.xio= QtWidgets.QCheckBox("Extended IO")
      self.vlayout.addWidget(self.xio)
      self.devil= QtWidgets.QCheckBox("HP-IL Devel")
      self.vlayout.addWidget(self.devil)
      self.plotter= QtWidgets.QCheckBox("Plotter")
      self.vlayout.addWidget(self.plotter)

      self.exitButton= QtWidgets.QPushButton("Exit")
      self.exitButton.setFixedWidth(60)
      self.exitButton.clicked.connect(self.do_exit)
      self.hlayout= QtWidgets.QHBoxLayout()
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
      if self.plotter.isChecked():
         self.call.append("-x")
         self.call.append("plotter")
      super().accept()

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
class cls_lifview(QtWidgets.QDialog):

   def __init__(self,workdir,parent= None):
      super().__init__()
      self.workdir=workdir
      self.outputfile=""

      self.setWindowTitle("View File")
      self.vlayout= QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.viewer=QtWidgets.QTextEdit()
      self.viewer.setMinimumWidth(600)
      self.viewer.setMinimumHeight(600)
      self.viewer.setReadOnly(True)
      self.font=QtGui.QFont(FONT)
      self.font.setPixelSize(12)
      self.viewer.setFont(self.font)

      self.vlayout.addWidget(self.viewer)
      self.saveButton= QtWidgets.QPushButton("Save")
      self.saveButton.setFixedWidth(60)
      self.saveButton.clicked.connect(self.do_save)
      self.exitButton= QtWidgets.QPushButton("Exit")
      self.exitButton.setFixedWidth(60)
      self.exitButton.clicked.connect(self.do_exit)
      self.hlayout= QtWidgets.QHBoxLayout()
      self.hlayout.addWidget(self.saveButton)
      self.hlayout.addWidget(self.exitButton)
      self.vlayout.addLayout(self.hlayout)

   def set_text(self,output):
      self.viewer.setText(output)
      return
#
#  enter output file name dialog
#
   def get_outputFilename(self):
      dialog=QtWidgets.QFileDialog()
      dialog.setWindowTitle("Select Output File")
      dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
      dialog.setNameFilters( ["All Files (*)"] )
      dialog.setOptions(QtWidgets.QFileDialog.DontUseNativeDialog)
#     dialog.setDirectory(self.workdir)
      if dialog.exec():
         return dialog.selectedFiles()
#
# save content to file
#
   def do_save(self):
      flist= self.get_outputFilename()
      if flist == None:
         return
      self.outputfile=flist[0]
      if os.access(self.outputfile,os.W_OK):
         reply=QtWidgets.QMessageBox.warning(self,'Warning',"Do you really want to overwrite file "+self.outputfile,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Cancel)
         if reply== QtWidgets.QMessageBox.Cancel:
            return
      try:
         with open(self.outputfile,"w",encoding="UTF-8-SIG") as outfile:
            outfile.write(str(self.viewer.toPlainText()))
      except OSError as e:
         reply=QtWidgets.QMessageBox.critical(self,'Error',"Cannot write to file: "+ e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
      return

#
# exit, do nothing
#
   def do_exit(self):
      super().accept()

#
# get file and pipe it to filter program, show output in editor window
#
   @staticmethod
   def exec(lifimagefile, liffilename, liffiletype,workdir,charset):
      d=cls_lifview(workdir)
      ft=get_finfo_name(liffiletype)
      call= get_finfo_type(ft)[1]
#
# decomp41 needs additional parameters (xrmoms)
#
      if call == "decomp41":
         call= cls_chkxrom.exec()
      output=exec_double_export(d,["lifget","-r",lifimagefile,liffilename],call,"")
#
# convert and show the file content
#
      if output == None:
         return
      d.set_text(barrconv(output,charset))
      result= d.exec_()
#
# Init LIF image file dialog
#      
class cls_lifinit (QtWidgets.QDialog):

   def __init__(self,workdir,parent= None):
      super().__init__()
      self.lifimagefile=""
      self.workdir= workdir
      self.mt="hdrive1"

      self.setWindowTitle("Initialize LIF Image File")
      self.vlayout= QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.gBox0=QtWidgets.QGroupBox("LIF image file")
      self.hbox=QtWidgets.QHBoxLayout()
      self.lblFilename=QtWidgets.QLabel(self.lifimagefile)
      self.hbox.addWidget(self.lblFilename)
      self.hbox.addStretch(1)
      self.butChange= QtWidgets.QPushButton("Change")
      self.butChange.clicked.connect(self.do_filenameChanged)
      self.hbox.addWidget(self.butChange)

      self.gBox0.setLayout(self.hbox)
      self.vlayout.addWidget(self.gBox0)

      self.gBox1=QtWidgets.QGroupBox("Medium type")
      self.bGroup=QtWidgets.QButtonGroup()
      self.radio1= QtWidgets.QRadioButton("HP 82161A cassette")
      self.radio2= QtWidgets.QRadioButton("HP 9114B double sided disk ")
      self.radio3= QtWidgets.QRadioButton("HDRIVE1 640 KB")
      self.radio4= QtWidgets.QRadioButton("HDRIVE1 2 MB")
      self.radio5= QtWidgets.QRadioButton("HDRIVE1 4 MB")
      self.radio6= QtWidgets.QRadioButton("HDRIVE1 8 MB")
      self.radio7= QtWidgets.QRadioButton("HDRIVE1 16 MB")
      self.radio3.setChecked(True)
      self.bGroup.addButton(self.radio1) 
      self.bGroup.addButton(self.radio2)
      self.bGroup.addButton(self.radio3)
      self.bGroup.addButton(self.radio4)
      self.bGroup.addButton(self.radio5)
      self.bGroup.addButton(self.radio6)
      self.bGroup.addButton(self.radio7)
      self.bGroup.buttonClicked.connect(self.do_butclicked)

      self.vbox=QtWidgets.QVBoxLayout()
      self.vbox.addWidget(self.radio1)
      self.vbox.addWidget(self.radio2)
      self.vbox.addWidget(self.radio3)
      self.vbox.addWidget(self.radio4)
      self.vbox.addWidget(self.radio5)
      self.vbox.addWidget(self.radio6)
      self.vbox.addWidget(self.radio7)

      self.hbox1=QtWidgets.QHBoxLayout()
      self.lbl1=QtWidgets.QLabel("Directory size:")
      self.hbox1.addWidget(self.lbl1)
      self.leditDirSize=QtWidgets.QLineEdit(self)
      self.leditDirSize.setText("500")
      self.leditDirSize.setMaxLength(4)
      self.regexpDirSize = QtCore.QRegExp('[1-9][0-9]*')
      self.validatorDirSize = QtGui.QRegExpValidator(self.regexpDirSize)
      self.leditDirSize.setValidator(self.validatorDirSize)
      self.leditDirSize.textChanged.connect(self.do_checkenable)
      self.hbox1.addWidget(self.leditDirSize)
      self.vbox.addLayout(self.hbox1)

      self.hbox2=QtWidgets.QHBoxLayout()
      self.lbl2=QtWidgets.QLabel("LIF Label:")
      self.hbox2.addWidget(self.lbl2)
      self.leditLabel=QtWidgets.QLineEdit(self)
      self.leditLabel.setText("")
      self.leditLabel.setMaxLength(6)
      self.validatorLabel =  cls_LIF_validator()
      self.leditLabel.setValidator(self.validatorLabel)
      self.hbox2.addWidget(self.leditLabel)
      self.vbox.addLayout(self.hbox2)

      self.gBox1.setLayout(self.vbox)
      self.gBox1.setEnabled(False)
      self.vlayout.addWidget(self.gBox1)
      self.vbox.addStretch(1)

      self.buttonBox = QtWidgets.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      self.vlayout.addWidget(self.buttonBox)
#
#  dialog to enter input file name
#
   def get_inputFilename(self):
      dialog=QtWidgets.QFileDialog()
      dialog.setWindowTitle("Select LIF Image File")
      dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
      dialog.setNameFilters( ["All Files (*)"] )
      dialog.setOptions(QtWidgets.QFileDialog.DontUseNativeDialog)
#     dialog.setDirectory(self.workdir)
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
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      if (self.leditDirSize.text() != "" and self.lifimagefile != ""):
         self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
      return

#
#  OK button, initialize file
#
   def do_ok(self):
      if self.lifimagefile != "":
         if os.access(self.lifimagefile,os.W_OK):
            reply=QtWidgets.QMessageBox.warning(self,'Warning',"Do you really want to overwrite file "+self.lifimagefile,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Cancel)
            if reply== QtWidgets.QMessageBox.Cancel:
               return
         exec_single(self,["lifinit","-m",self.mt,self.lifimagefile,self.leditDirSize.text()])
         if self.leditLabel.text() != "":
            exec_single(self,["liflabel",self.lifimagefile,self.leditLabel.text()])
      super().accept()

#
#  cancel
#
   def do_cancel(self):
      super().reject()

   @staticmethod
   def exec(workdir):
      d=cls_lifinit(workdir)
      result= d.exec_()
#
# fix LIF header dialog
#
class cls_liffix (QtWidgets.QDialog):

   def __init__(self,workdir,parent= None):
      super().__init__()
      self.lifimagefile=""
      self.workdir= workdir
      self.mt="hdrive1"

      self.setWindowTitle("Fix header of LIF Image File")
      self.vlayout= QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)

      self.gBox0=QtWidgets.QGroupBox("LIF image file")
      self.hbox=QtWidgets.QHBoxLayout()
      self.lblFilename=QtWidgets.QLabel(self.lifimagefile)
      self.hbox.addWidget(self.lblFilename)
      self.hbox.addStretch(1)
      self.butChange= QtWidgets.QPushButton("Change")
      self.butChange.clicked.connect(self.do_filenameChanged)
      self.hbox.addWidget(self.butChange)

      self.gBox0.setLayout(self.hbox)
      self.vlayout.addWidget(self.gBox0)

      self.gBox1=QtWidgets.QGroupBox("Medium type")
      self.bGroup=QtWidgets.QButtonGroup()
      self.radio1= QtWidgets.QRadioButton("HP 82161A cassette")
      self.radio2= QtWidgets.QRadioButton("HP 9114B double sided disk ")
      self.radio3= QtWidgets.QRadioButton("HDRIVE1 640 KB")
      self.radio4= QtWidgets.QRadioButton("HDRIVE1 2 MB")
      self.radio5= QtWidgets.QRadioButton("HDRIVE1 4 MB")
      self.radio6= QtWidgets.QRadioButton("HDRIVE1 8 MB")
      self.radio7= QtWidgets.QRadioButton("HDRIVE1 16 MB")
      self.radio3.setChecked(True)
      self.bGroup.addButton(self.radio1) 
      self.bGroup.addButton(self.radio2)
      self.bGroup.addButton(self.radio3)
      self.bGroup.addButton(self.radio4)
      self.bGroup.addButton(self.radio5)
      self.bGroup.addButton(self.radio6)
      self.bGroup.addButton(self.radio7)
      self.bGroup.buttonClicked.connect(self.do_butclicked)

      self.vbox=QtWidgets.QVBoxLayout()
      self.vbox.addWidget(self.radio1)
      self.vbox.addWidget(self.radio2)
      self.vbox.addWidget(self.radio3)
      self.vbox.addWidget(self.radio4)
      self.vbox.addWidget(self.radio5)
      self.vbox.addWidget(self.radio6)
      self.vbox.addWidget(self.radio7)

      self.vbox.addStretch(1)
      self.vlayout.addLayout(self.vbox)

      self.buttonBox = QtWidgets.QDialogButtonBox(self)
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      self.vlayout.addWidget(self.buttonBox)
#
#  dialog to enter input file name
#
   def get_inputFilename(self):
      dialog=QtWidgets.QFileDialog()
      dialog.setWindowTitle("Select LIF Image File")
      dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
      dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
      dialog.setNameFilters( ["All Files (*)"] )
      dialog.setOptions(QtWidgets.QFileDialog.DontUseNativeDialog)
#     dialog.setDirectory(self.workdir)
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
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      if self.lifimagefile != "":
         self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
      return

#
#  OK button, initialize file
#
   def do_ok(self):
      if self.lifimagefile != "":
         exec_single(self,["liffix","-m",self.mt,self.lifimagefile])
      super().accept()
#
#  cancel
#
   def do_cancel(self):
      super().reject()

   @staticmethod
   def exec(workdir):
      d=cls_liffix(workdir)
      result= d.exec_()
#
# Check installation of LIFUTILS dialog
#
class cls_installcheck(QtWidgets.QDialog):

   def __init__(self):
      super().__init__()
      self.setWindowTitle('Status of LIFUTILS installation')
      self.vlayout = QtWidgets.QVBoxLayout()
      self.setLayout(self.vlayout)
      self.view = QtWidgets.QLabel()
      self.view.setFixedWidth(500)
      self.view.setWordWrap(True)
      self.button = QtWidgets.QPushButton('OK')
      self.button.setFixedWidth(60)
      self.button.clicked.connect(self.do_exit)
      self.vlayout.addWidget(self.view)
      self.hlayout = QtWidgets.QHBoxLayout()
      self.hlayout.addWidget(self.button)
      self.vlayout.addLayout(self.hlayout)
      required_version_installed, installed_version= check_lifutils()

      text="This version of pyILPER requires at least version "+decode_version(LIFUTILS_REQUIRED_VERSION)+" of the LIFUTILS installed."

      if required_version_installed:
         text+=" Version "+decode_version(installed_version)+" was found on this system. File management controls are enabled."
      else:
         if installed_version !=0:
            text+=" Version "+decode_version(installed_version)+" was found of this system. Please upgrade to the latest version of LIFUTILS and restart pyILPER."
         else:
            text+=" No version of LIFUTILS was found on this system or the installed version is too old to report a version number. Please install the latest version of LIFUTILS and restart pyILPER."
         text+=" File management controls are disabled."
      self.view.setText(text)

   def do_exit(self):
      super().accept()

   @staticmethod
   def exec():
      d=cls_installcheck()
      result= d.exec_()
