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
# lif utilities dialog classes -------------------------------------------------
#
# Changelog
# 02.01.2016 - jsi
# - added cls_lifview, cls_chkxrom
# - improved error checking of piped commands
# - added descramble HP-41 rom postprocessing option
# - added scramble HP-41 rom to HEPAX sdata file preprocessing option
# - refactoring
# 05.01.2016 - jsi
# - replaced process pipelines with temporary files to catch error conditions 
#   more reliable
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
# - removed duplicate dialog warning for overwriting existing file in  
#   cls_lifexport
# 01.10.2016 jsi
# - plotter rom added to xrom dialog
# 22.08.2017 jsi
# - cls_lifbarcode added
# - truncate error messages from external programs to 150 chars
# 01.09.2017 jsi
# - moved get_pdfFilename to cls_pdfprinter
# 16.08.2017 jsi
# - used barrconv instead of stringconv. There is no unicode exception any more.
# 28.10.2017 jsi
# - detection of lifutils extended and improved
# 11.11.2017 jsi:
# - Eramco MLDL-OS packed rom file pre- and postprocessing implemented
# 21.11.2017 jsi:
# - added -r 0 option to textlif to add HP-41 implementation specific bytes
# 05.02.2018 jsi:
# - apply BOM to saved "view" file only on Windows at the beginning of the file
# 10.02.2018 jsi:
# - fixed BOM handling
# 18.03.2018 jsi:
# - added options to import an ASCII file either for the HP-41 or the HP-71
# 20.03.2018 jsi:
# - code cleanup
# 12.12.2018 jsi:
# - changed all subprocess calls to the subprocess.run interface
# 31.5.2019 jsi:
# - added HP-75 text file import/export
# - do not run lifput in exec_double_import if first command failed
# 03.06.2019 jsi:
# - show HP-75 text files optional with or without line numbers
# 04.01.2021 jsi
# - exec_single did not get stderr output of executed program
# 04.04.2022 jsi
# - PySide6 migration
#
import subprocess
import tempfile
import os
import pathlib
from .lifcore import *
from .pilcharconv import barrconv
from .pilcore import isWINDOWS, FONT, decode_version, PDF_ORIENTATION_PORTRAIT
from .pilpdf import cls_pdfprinter
from .pilconfig import PILCONFIG
if isWINDOWS():
   import winreg
from .pilcore import QTBINDINGS
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtGui, QtWidgets
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtGui, QtWidgets


PDF_MARGINS=100
BARCODE_HEIGHT=100
BARCODE_NARROW_W= 5
BARCODE_WIDE_W= 10
BARCODE_SPACING= 5
#
# get lif version if 0 is returned then lifversion was not found
#
def get_lifversion(cmd):
   retval=0
   try:
      ret=subprocess.run(cmd,stdout=subprocess.PIPE)
      retval=int(ret.stdout.decode())
   finally:
      return retval
#
# check if lifutils are installed, return if required version found
#
def check_lifutils():
   set_lifutils_path("")
   required_version_installed=False
   installed_version= 0
#
#  check if we have a configured path to lifversion
#
   lifversionpath=PILCONFIG.get("pyilper","lifutilspath")
   if lifversionpath != "":
      installed_version=get_lifversion(lifversionpath)
#
#  not found, check if we have lifversion in the path
#
   if installed_version == 0:
      installed_version=get_lifversion("lifversion")
#
#  not found, use well known default locations
#
   if installed_version == 0:
#
#     Windows: query Registry to get install location from uninstaller info
#     local user installation preceeds system wide installation
#     Note: this requires at least lifutils version 1.7.7 (nsis package build)
#
      if isWINDOWS():
         path=""
         try:
            hkey=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\\Microsoft\\Windows\\CurrentVersion\\uninstall\\"+LIFUTILS_UUID)
            path=winreg.QueryValueEx(hkey,"InstallLocation")[0]
            hkey.Close()
         except OSError as e:
            pass
         if path=="":
            try:
               hkey=winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r"Software\\Microsoft\\Windows\\CurrentVersion\\uninstall\\"+LIFUTILS_UUID)
               path=winreg.QueryValueEx(hkey,"InstallLocation")[0]
               hkey.Close()
            except OSError as e:
               pass
         if path!="":
            p=pathlib.Path(path)
            p=p / "lifversion"
            lifversionpath=str(p)
            installed_version=get_lifversion(lifversionpath)
      else:
#
#      Linux / mac OS: try /usr/ or /usr/local
#
         lifversionpath="/usr/bin/lifversion"
         installed_version=get_lifversion(lifversionpath)
         if installed_version == 0:
            lifversionpath="/usr/local/bin/lifversion"
            installed_version=get_lifversion(lifversionpath)
#
#  lifutils path found, set lifutils_path as prefix for calling the 
#  executables and set LIFUTILSXROMDIR as environment variable
#
   if installed_version != 0 and lifversionpath !="" :
      p= pathlib.Path(lifversionpath)
      set_lifutils_path(str(p.parent))
      if isWINDOWS():
         xromdir=p.parent / "xroms"
      else:
         xromdir=p.parents[1] / "share" / "lifutils" / "xroms"
      if xromdir.is_dir():
         os.environ["LIFUTILSXROMDIR"]=str(xromdir)
#
#  check if we have the required version
#
   if installed_version >= LIFUTILS_REQUIRED_VERSION:
      required_version_installed=True
   return required_version_installed, installed_version
#
#  check and display messages of lifutils
#
def check_errormessages(parent,ret):
   msg= ret.stderr.decode()
   if msg == "":
      return
#
#  truncate message if length > 150 
#
   if len(msg)  >150:
      msg=msg[:75] + '.. (truncated)'
#
#  display an error if returncode !=0 otherwise a warning
#
   if ret.returncode == 0:
      reply=QtWidgets.QMessageBox.warning(parent,'Warning',msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
   else:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',msg,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
   return
#
# exec single command
#
def exec_single(parent,cmd):
   try:
      ret=subprocess.run(cmd,stderr=subprocess.PIPE)
      check_errormessages(parent,ret)
   except OSError as e:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
   finally:
      return
#
# exec single command, return output
#
def exec_single_export(parent,cmd):
   returnvalue=None
   try:
      ret= subprocess.run(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      check_errormessages(parent,ret)
      if ret.returncode==0:
         returnvalue= ret.stdout
#
#  catch errors
#
   except OSError as e:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
   finally:
      return returnvalue

#
# exec piped command, read input from file, return True if success, False otherwise
#
def exec_double_import(parent,cmd1,cmd2,inputfile):

   tmpfile=None
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
      ret= subprocess.run(cmd1,stdin=fd,stdout=tmpfile,stderr=subprocess.PIPE)
      check_errormessages(parent,ret)
      os.close(fd)
      if ret.returncode!=0:
         tempfile.close()
         return
#
#  execute second command
#
      tmpfile.seek(0)
      if  not cls_chk_import.execute(tmpfile.fileno(), None):
         tmpfile.close()
         return
      tmpfile.seek(0)
      ret= subprocess.run(cmd2,stdin=tmpfile,stderr=subprocess.PIPE)
      check_errormessages(parent,ret)
#
#  catch errors
#
   except OSError as e:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
   finally:
      if tmpfile is not None:
         tmpfile.close()
      return
#
# exec piped command, write output to file or stdout
#
def exec_double_export(parent,cmd1,cmd2,outputfile):
   tmpfile=None
   returnvalue= None
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
      ret= subprocess.run(cmd1,stdout=tmpfile,stderr=subprocess.PIPE)
      check_errormessages(parent,ret)
      if ret.returncode!=0:
         tmpfile.close()
         if fd is not None:
            os.close(fd)
         return None
#
# execute second command
#
      tmpfile.seek(0)
      if outputfile != "":
         ret= subprocess.run(cmd2,stdin=tmpfile,stdout=fd,stderr=subprocess.PIPE)
      else:
         ret= subprocess.run(cmd2,stdin=tmpfile,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
         if ret.returncode==0:
            returnvalue= ret.stdout
      check_errormessages(parent,ret)
#
#  catch errors
#
   except OSError as e:
      reply=QtWidgets.QMessageBox.critical(parent,'Error',e.strerror,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Ok)
   finally:
      if tmpfile is not None:
         tmpfile.close()
      if fd is not None:
         os.close(fd)
      return returnvalue

#
# validator checks for valid lif label or file names, converts to capital lettes
#
class cls_LIF_validator(QtGui.QValidator):

   def validate(self,string,pos):
      self.regexp = QtCore.QRegularExpression('[A-Za-z][A-Za-z0-9]*')
      self.validator = QtGui.QRegularExpressionValidator(self.regexp)
      result=self.validator.validate(string,pos)
      return result[0], result[1].upper(), result[2]
#
# pack lif image file dialog
#
class cls_lifpack(QtWidgets.QDialog):

   def __init__(self,parent= None):
      super().__init__()

   @staticmethod
   def execute(lifimagefile):
      d=cls_lifpack()
      reply = QtWidgets.QMessageBox.question(d, 'Message', 'Do you really want to pack the LIF image file', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
      if reply == QtWidgets.QMessageBox.Yes:
         exec_single(d,[add_path("lifpack"),lifimagefile])
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
   def execute (lifimagefile, liffilename, ft,papersize):
      d= cls_lifbarcode()
#
#     get output file name
#
      flist= cls_pdfprinter.get_pdfFilename()
      if flist is None:
         return
      output_filename= flist[0]
#
#     generate binary barcode data from lifutils prog41bar or sdatabar
#
      if ft== 0xE080:
         output=exec_double_export(d,[add_path("lifget"),"-r",lifimagefile,liffilename],[add_path("prog41bar")],"")
         title="Barcodes for HP-41 program file: "+liffilename
      else:
         output=exec_double_export(d,[add_path("lifget"),"-r",lifimagefile,liffilename],[add_path("sdatabar")],"")
         title="Barcodes for HP-41 data file: "+liffilename
      if output is None:
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
   def execute(lifimagefile,liffile):
      d=cls_lifpurge()
      reply = QtWidgets.QMessageBox.question(d, 'Message', 'Do you really want to purge '+liffile, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
      if reply == QtWidgets.QMessageBox.Yes:
         exec_single(d,[add_path("lifpurge"),lifimagefile, liffile])

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
         exec_single(self,[add_path("lifrename"),self.lifimagefile,self.oldfilename,newfilename])
      super().accept()

#
#  cancel do nothing
#
   def do_cancel(self):
      super().reject()

   @staticmethod
   def execute(lifimagefile,liffile):
      d=cls_lifrename(lifimagefile,liffile)
      result= d.exec()
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
      self.radioLifAscii= QtWidgets.QRadioButton("convert LIF-Text to ASCII")
      self.radioLifAscii.clicked.connect(self.do_radio)
      self.radioLifAscii.setEnabled(False)
      self.radioTxt75Ascii= QtWidgets.QRadioButton("convert HP-75 text file to ASCII, omit line numbers")
      self.radioTxt75Ascii.clicked.connect(self.do_radio)
      self.radioTxt75Ascii.setEnabled(False)
      self.radioTxt75AsciiNumbers= QtWidgets.QRadioButton("convert HP-75 text file to ASCII, retain line numbers")
      self.radioTxt75AsciiNumbers.clicked.connect(self.do_radio)
      self.radioTxt75AsciiNumbers.setEnabled(False)
      self.radioEramco= QtWidgets.QRadioButton("unpack Eramco MLDL-OS ROM file")
      self.radioEramco.clicked.connect(self.do_radio)
      self.radioEramco.setEnabled(False)
      self.radioHepax= QtWidgets.QRadioButton("unpack HEPAX HP41 SDATA ROM file")
      self.radioHepax.setEnabled(False)
      self.radioHepax.clicked.connect(self.do_radio)
      self.radioRaw= QtWidgets.QRadioButton("remove LIF header, create RAW file")
      self.radioRaw.clicked.connect(self.do_radio)
      self.radioNone= QtWidgets.QRadioButton("None")
      self.radioNone.clicked.connect(self.do_radio)

      if self.liffiletype== "TEXT":
         self.radioLifAscii.setEnabled(True)
         self.radioLifAscii.setChecked(True)
         self.outputextension=".txt"
      elif self.liffiletype== "TXT75":
         self.radioTxt75Ascii.setEnabled(True)
         self.radioTxt75Ascii.setChecked(True)
         self.radioTxt75AsciiNumbers.setEnabled(True)
         self.outputextension=".txt"
      elif self.liffiletype== "X-M41":
         self.radioEramco.setEnabled(True)
         self.radioEramco.setChecked(True)
         self.outputextension=".rom"
      elif self.liffiletype== "SDATA":
         self.radioNone.setChecked(True)
         self.radioHepax.setEnabled(True)
         self.outputextension=".lif"
      else:
         self.radioNone.setChecked(True)
         self.outputextension=".lif"

      self.vbox=QtWidgets.QVBoxLayout()
      self.vbox.addWidget(self.radioLifAscii)
      self.vbox.addWidget(self.radioTxt75Ascii)
      self.vbox.addWidget(self.radioTxt75AsciiNumbers)
      self.vbox.addWidget(self.radioEramco)
      self.vbox.addWidget(self.radioHepax)
      self.vbox.addWidget(self.radioRaw)
      self.vbox.addWidget(self.radioNone)
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
#
#  Radio button clicked, adjust file type
#
   def do_radio(self):
      if self.radioLifAscii.isChecked():
         self.outputextension=".txt"
      elif self.radioTxt75Ascii.isChecked():
         self.outputextension=".txt"
      elif self.radioTxt75AsciiNumbers.isChecked():
         self.outputextension=".txt"
      elif self.radioHepax.isChecked():
         self.outputextension=".rom"
      elif self.radioEramco.isChecked():
         self.outputextension=".rom"
      elif self.radioRaw.isChecked():
         self.outputextension=".raw"
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
      if flist is None:
         return
      self.outputfile=flist[0]
      self.lblFilename.setText(self.outputfile)
#
#  export
#
   def do_ok(self):
      if self.outputfile != "":

         if self.radioLifAscii.isChecked():
            exec_double_export(self,[add_path("lifget"),"-r",self.lifimagefile,self.liffilename],add_path("liftext"),self.outputfile)
         elif self.radioTxt75Ascii.isChecked():
            exec_double_export(self,[add_path("lifget"),"-r",self.lifimagefile,self.liffilename],add_path("liftext75"),self.outputfile)
         elif self.radioTxt75AsciiNumbers.isChecked():
            exec_double_export(self,[add_path("lifget"),"-r",self.lifimagefile,self.liffilename], [add_path("liftext75"),"-n"],self.outputfile)
         elif self.radioEramco.isChecked():
            exec_double_export(self,[add_path("lifget"),"-r",self.lifimagefile,self.liffilename],add_path("er41rom"),self.outputfile)
         elif self.radioHepax.isChecked():
            exec_double_export(self,[add_path("lifget"),"-r",self.lifimagefile,self.liffilename],add_path("hx41rom"),self.outputfile)
         elif self.radioRaw.isChecked():
            exec_single(self,[add_path("lifget"),"-r",self.lifimagefile,self.liffilename,self.outputfile])
         elif self.radioNone.isChecked():
            exec_single(self,[add_path("lifget"),self.lifimagefile,self.liffilename,self.outputfile])
      super().accept()
#
#  cancel: do nothing
#
   def do_cancel(self):
      super().reject()

   @staticmethod
   def execute(lifimagefile,liffilename,liffiletype,workdir):
      d=cls_lifexport(lifimagefile,liffilename,liffiletype,workdir)
      result= d.exec()

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
         exec_single(self,[add_path("liflabel"),self.lifimagefile, newlabel])
      else:
         exec_single(self,[add_path("liflabel"),"-c",self.lifimagefile])
      super().accept()

   def do_cancel(self):
      super().reject()

   @staticmethod
   def execute(lifimagefile,oldlabel):
      d=cls_liflabel(lifimagefile,oldlabel)
      result= d.exec()
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
      self.radioLif41= QtWidgets.QRadioButton("convert from ASCII to LIF-Text (HP-41)")
      self.radioLif71= QtWidgets.QRadioButton("convert from ASCII to LIF-Text (HP-71)")
      self.radioTxt75= QtWidgets.QRadioButton("convert from ASCII to HP-75 text, create new line numbers")
      self.radioTxt75Numbers= QtWidgets.QRadioButton("convert from ASCII to HP-75 text, take existing line numbers")
      self.radioHepax= QtWidgets.QRadioButton("convert HP-41 rom file to SDATA file (HEPAX)")
      self.radioEramco= QtWidgets.QRadioButton("convert HP-41 rom file to XM-41 file (Eramco MLDL-OS)")
      self.radioFocal= QtWidgets.QRadioButton("add LIF header to HP41 FOCAL raw file")
      self.radioNone= QtWidgets.QRadioButton("None")
      self.radioNone.setChecked(True)
      self.bGroup.addButton(self.radioLif41) 
      self.bGroup.addButton(self.radioLif71)
      self.bGroup.addButton(self.radioTxt75)
      self.bGroup.addButton(self.radioTxt75Numbers)
      self.bGroup.addButton(self.radioHepax)
      self.bGroup.addButton(self.radioEramco)
      self.bGroup.addButton(self.radioFocal)
      self.bGroup.addButton(self.radioNone)
      self.bGroup.buttonClicked.connect(self.do_butclicked)

      self.vbox=QtWidgets.QVBoxLayout()
      self.vbox.addWidget(self.radioLif41)
      self.vbox.addWidget(self.radioLif71)
      self.vbox.addWidget(self.radioTxt75)
      self.vbox.addWidget(self.radioTxt75Numbers)
      self.vbox.addWidget(self.radioHepax)
      self.vbox.addWidget(self.radioEramco)
      self.vbox.addWidget(self.radioFocal)

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
      self.vbox.addWidget(self.radioNone)
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
      if flist is None:
         return
      self.inputfile=flist[0]
      self.lblFilename.setText(self.inputfile)
      self.gBox1.setEnabled(True)
      self.do_checkenable()
#
#  any radio button clicked, enable/disable lif filename entry, check ok button
#
   def do_butclicked(self,id):
      if id== self.radioNone:
         self.leditFileName.setEnabled(False)
      else:
         self.leditFileName.setEnabled(True)
      self.do_checkenable()

#
#  check, if the OK button can be enabled
#
   def do_checkenable(self):
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
      if self.radioNone.isChecked():
         self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
      else:
         if self.leditFileName.text() != "":
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
      return

#
#  OK button callback import file
#
   def do_ok(self):
      if self.inputfile != "":
         if self.radioNone.isChecked():
            if  cls_chk_import.execute(None, self.inputfile):
               exec_single(self,[add_path("lifput"),self.lifimagefile,self.inputfile])
         else:
            self.liffilename=self.leditFileName.text()
            if self.radioLif41.isChecked():
               exec_double_import(self,[add_path("textlif"),"-r 0",self.liffilename],[add_path("lifput"),self.lifimagefile],self.inputfile)
            elif self.radioLif71.isChecked():
               exec_double_import(self,[add_path("textlif"),self.liffilename],[add_path("lifput"),self.lifimagefile],self.inputfile)
            elif self.radioTxt75.isChecked():
               exec_double_import(self,[add_path("textlif75"),self.liffilename],[add_path("lifput"),self.lifimagefile],self.inputfile)
            elif self.radioTxt75Numbers.isChecked():
               exec_double_import(self,[add_path("textlif75"),"-n",self.liffilename],[add_path("lifput"),self.lifimagefile],self.inputfile)
            elif self.radioHepax.isChecked():
               exec_double_import(self,[add_path("rom41hx"),self.liffilename],[add_path("lifput"),self.lifimagefile],self.inputfile)
            elif self.radioEramco.isChecked():
               exec_double_import(self,[add_path("rom41er"),self.liffilename],[add_path("lifput"),self.lifimagefile],self.inputfile)
            elif self.radioFocal.isChecked():
               exec_double_import(self,[add_path("raw41lif"),self.liffilename],[add_path("lifput"),self.lifimagefile],self.inputfile)
      super().accept()

#
#  cancel
#
   def do_cancel(self):
      super().reject()

   @staticmethod
   def execute(lifimagefile,workdir):
      d=cls_lifimport(lifimagefile,workdir)
      result= d.exec()
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
            if self.filetype is None:
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
         self.regexp = QtCore.QRegularExpression('[A-Z][A-Z0-9]*')
         self.validator = QtGui.QRegularExpressionValidator(self.regexp)
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
   def execute(fd,inputfile):
      d=cls_chk_import(fd,inputfile)
      result= d.exec()
      return d.get_retval()
#
# check xroms dialog
#
class cls_chkxrom(QtWidgets.QDialog):

   def __init__(self,parent=None):
      super().__init__()
      self.call=[add_path("decomp41")]

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
   def execute():
      d=cls_chkxrom()
      result= d.exec()
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
      if dialog.exec():
         return dialog.selectedFiles()
#
# save content to file
#
   def do_save(self):
      flist= self.get_outputFilename()
      if flist is None:
         return
      outputfile=flist[0]
      if os.access(self.outputfile,os.W_OK):
         reply=QtWidgets.QMessageBox.warning(self,'Warning',"Do you really want to overwrite file "+self.outputfile,QtWidgets.QMessageBox.Ok,QtWidgets.QMessageBox.Cancel)
         if reply== QtWidgets.QMessageBox.Cancel:
            return
      try:
         if isWINDOWS() and PILCONFIG.get("pyilper","usebom"):
            outfile=open(outputfile,"a",encoding="UTF-8-SIG")
         else:
            outfile=open(outputfile,"a",encoding="UTF-8")

         outfile.write(str(self.viewer.toPlainText()))
         outfile.close()
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
   def execute(lifimagefile, liffilename, liffiletype,workdir,charset):
      d=cls_lifview(workdir)
      ft=get_finfo_name(liffiletype)
      call= get_finfo_type(ft)[1]
#
# decomp41 needs additional parameters (xmoms)
#
      if call == "decomp41":
         call= cls_chkxrom.execute()
#
# liftext75 has the option to show line numbers
#
      elif call == "liftext75":
         call= add_path(call)
         reply=QtWidgets.QMessageBox.question(None,'',"Show line numbers?",QtWidgets.QMessageBox.Yes,QtWidgets.QMessageBox.No)
         if reply== QtWidgets.QMessageBox.Yes:
            call= [ add_path(call), "-n"]
#
# all other lifutil progs
#
      else:
         call= add_path(call)
      output=exec_double_export(d,[add_path("lifget"),"-r",lifimagefile,liffilename],call,"")
#
# convert and show the file content
#
      if output is None:
         return
      d.set_text(barrconv(output,charset))
      result= d.exec()
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
      self.regexpDirSize = QtCore.QRegularExpression('[1-9][0-9]*')
      self.validatorDirSize = QtGui.QRegularExpressionValidator(self.regexpDirSize)
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
      if flist is None:
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
         exec_single(self,[add_path("lifinit"),"-m",self.mt,self.lifimagefile,self.leditDirSize.text()])
         if self.leditLabel.text() != "":
            exec_single(self,[add_path("liflabel"),self.lifimagefile,self.leditLabel.text()])
      super().accept()

#
#  cancel
#
   def do_cancel(self):
      super().reject()

   @staticmethod
   def execute(workdir):
      d=cls_lifinit(workdir)
      result= d.exec()
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
      if flist is None:
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
         exec_single(self,[add_path("liffix"),"-m",self.mt,self.lifimagefile])
      super().accept()
#
#  cancel
#
   def do_cancel(self):
      super().reject()

   @staticmethod
   def execute(workdir):
      d=cls_liffix(workdir)
      result= d.exec()
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
   def execute():
      d=cls_installcheck()
      result= d.exec()
