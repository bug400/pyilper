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
# pdf printer class ----------------------------------------------------
#
# Changelog
# 21.08.2017 - jsi
# - first version
# 01.09.2017 - jsi
# - minor layout changes
# - added static method to obtain pdf output file name
# - added textItem class
# 01.11.2017 - jsi
# - update page number
# 01.03.2018 - jsi
# - use monospaced font defined in pilcore.py
# 04.05.2022 jsi
# - PySide6 migration
#
from .pilcore import *
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtGui, QtWidgets,QtPrintSupport
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtGui, QtWidgets,QtPrintSupport

#
# PDF printer class:
# creates a PDF printer wich adds graphic items to a single or multi column
# output.
#
class cls_pdfprinter(QtCore.QObject):

   def __init__(self,papersize, orientation, outputfilename, title, pagenumbering, columns):
      super().__init__()
      self.papersize= papersize
      self.orientation= orientation
      self.outputfilename= outputfilename
      self.title= title
      self.pagenumbering= pagenumbering
      self.columns= columns
#
#     initialize printer and printer scene
#
      self.printer = QtPrintSupport.QPrinter (QtPrintSupport.QPrinter.HighResolution)
      if self.orientation== PDF_ORIENTATION_PORTRAIT:
         self.printer.setPageOrientation(QtGui.QPageLayout.Portrait)
      else:
         self.printer.setPageOrientation(QtGui.QPageLayout.Landscape)
      self.printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
      self.pdfscene=QtWidgets.QGraphicsScene()
#
#     page set up, we use 1/10 mm as scene units
#
      if self.papersize== PDF_FORMAT_A4:
         self.printer.setPageSize(QT_FORM_A4)
         self.scene_w= 2100
         self.scene_h=2970
         self.pdfscene.setSceneRect(0,0,self.scene_w,self.scene_h)
      else:
         self.printer.setPageSize(QT_FORM_LETTER)
         self.scene_w= 2160
         self.scene_h= 2790
         self.pdfscene.setSceneRect(0,0,self.scene_w,self.scene_h)

      self.pdfpainter = QtGui.QPainter()
      self.font=QtGui.QFont()
      self.font.setPointSize(20)
#
#     set output filename
#
      self.printer.setOutputFileName(self.outputfilename)
#
#     variables
#
      self.pdfitems=[]
      self.anzitems=0
      self.row=0
      self.column=0
      self.topy=0
      self.x=0
      self.y=0
      self.max_y= self.scene_h-PDF_MARGINS
      self.columnshift=(self.scene_w- 2* PDF_MARGINS)/ self.columns
#
#     start printing
#
   def begin(self):
      self.pdfpainter.begin(self.printer)
      self.titleitem=QtWidgets.QGraphicsSimpleTextItem(self.title)
      self.titleitem.setFont(self.font)
      self.pdfscene.addItem(self.titleitem)
      self.titleitem.setPos(PDF_MARGINS,PDF_MARGINS)
      self.pageno=1
      if self.pagenumbering:
         self.pagenumberitem=QtWidgets.QGraphicsSimpleTextItem("Page "+str(self.pageno))
         self.pagenumberitem.setFont(self.font)
         self.pdfscene.addItem(self.pagenumberitem)
         self.pagenumberitem.setPos(self.scene_w-self.pagenumberitem.boundingRect().width(),PDF_MARGINS)
#
#    init variables
#
      self.pdfitems=[]
      self.anzitems=0
      self.row=0
      self.column=0
      self.top_y=PDF_MARGINS+self.titleitem.boundingRect().height()+40
      self.x= PDF_MARGINS
      self.y= self.top_y

   def print_item(self,item):
#
#     no more rows on page
#
      if self.y > self.max_y:
#
#        no more columns, issue page break
#
         if self.column == self.columns-1:
            self.pdfscene.render(self.pdfpainter)
            self.printer.newPage()
            self.x=PDF_MARGINS
            self.y= self.top_y

            for l in reversed(range(self.anzitems)):
               self.pdfscene.removeItem(self.pdfitems[l])
               del self.pdfitems[-1]
            self.pageno+=1
            if self.pagenumbering:
               self.pagenumberitem.setText("Page "+str(self.pageno))
            self.anzitems=0
            self.column=0
            self.row=0
#
#        next column
#
         else:
            self.x+= self.columnshift
            self.y= self.top_y
            self.column+=1
            self.row=0
#
#     add item to scene
#
      self.row+=1
      self.pdfscene.addItem(item)
      self.y+= item.boundingRect().height()
      item.setPos(self.x,self.y)
      self.anzitems+=1
      self.pdfitems.append(item)
#
#  output remaining data and terminate printing
#
   def end(self):
      if self.anzitems > 0:
         self.pdfscene.render(self.pdfpainter)
         for l in reversed(range(self.anzitems)):
            self.pdfscene.removeItem(self.pdfitems[l])
            del self.pdfitems[-1]
#
#     clean up
#
      self.pdfscene.removeItem(self.titleitem)
      if self.pagenumbering:
         self.pdfscene.removeItem(self.pagenumberitem)
      self.pdfpainter.end()
 

#     file name input dialogue for pdf print file
#
   @staticmethod
   def get_pdfFilename():
      dialog=QtWidgets.QFileDialog()
      dialog.setWindowTitle("Enter PDF file name")
      dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
      dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
      dialog.setDefaultSuffix("pdf")
      dialog.setNameFilters( ["PDF (*.pdf )", "All Files (*)"] )
      dialog.setOptions(QtWidgets.QFileDialog.DontUseNativeDialog)
      if dialog.exec():
         return dialog.selectedFiles()
#
# custom class for text item
#
class cls_textItem(QtWidgets.QGraphicsItem):

   def __init__(self,text):
      super().__init__()
      self.text=text
#     self.font= QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
#     self.font.setStyleHint(QtGui.QFont.TypeWriter)
      self.font= QtGui.QFont(FONT)
      self.font.setPointSize(2)
      metrics= QtGui.QFontMetrics(self.font)
      self.font_h= metrics.height()
      self.font_w= metrics.boundingRect("A").width()
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
