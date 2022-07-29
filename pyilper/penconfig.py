#!/usr/bin/python3
# -*- coding: utf-8 -*-
# penconfig for pyILPER
#
# (c) 2016 Joachim Siebold
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
# penconfig class -------------------------------------------
#
# Changelog
# 17.10.2016 jsi:
# - first version (merged)
# 12.02.2018 jsi:
# - added the clean parameter to the open method
# 10.08.2018 jsi:
# - cls_PenConfigWindow moved from pilplotter.py
# 12.12.2021 jsi:
# - add configversion parameter to open method
# 04.05.2022 jsi:
# - PySide6 migration
#
import copy
from .pilcore import QTBINDINGS
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtGui, QtWidgets
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtGui, QtWidgets

from .userconfig import cls_userconfig, ConfigError
#
# Plotter pen table model class --------------------------------------------
#
class PenTableModel(QtCore.QAbstractTableModel):
   def __init__(self, datain, parent = None):
      super().__init__()
      self.arraydata = datain

   def rowCount(self, parent):
      return len(self.arraydata)

   def columnCount(self, parent):
      return len(self.arraydata[0])

   def data(self, index, role):
      if not index.isValid():
          return None
      elif role != QtCore.Qt.DisplayRole:
          return None
      return (self.arraydata[index.row()][index.column()])

   def setData(self, index, value,role):
      if index.column()==0:
         self.arraydata[index.row()][index.column()] = value
      else:
         self.arraydata[index.row()][index.column()] = int(value)
      self.dataChanged.emit(index,index) # this updates the edited cell
      return True

   def flags(self, index):
      return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

   def headerData(self,section,orientation,role):
      if role != QtCore.Qt.DisplayRole:
         return None
      if (orientation == QtCore.Qt.Horizontal):
         if section==0:
            return("Description")
         elif section==1:
            return("R")
         elif section==2:
            return("G")
         elif section==3:
            return("B")
         elif section==3:
            return("A")
         elif section==4:
            return("Alpha")
         elif section==5:
            return("Width")
         else:
            return("")

   def getTable(self):
      return self.arraydata

   def setAll(self,penconfig):
      self.arraydata=penconfig
      self.layoutChanged.emit() # this updates all cells
         
#
# Custom class with input validators ---------------------------------------
#
class PenDelegate(QtWidgets.QItemDelegate):

   def createEditor(self, parent, option, index):
      editor= super(PenDelegate,self).createEditor(parent,option,index)
      if index.column() > 0 and index.column()< 5:
         editor.setValidator(QtGui.QIntValidator(0,255))
      elif index.column() == 5:
         editor.setValidator(QtGui.QDoubleValidator(0.0,5.0,1))
      return(editor)

   def setEditorData(self, editor, index):
      # Gets display text if edit data hasn't been set.
      text = index.data(QtCore.Qt.EditRole) or index.data(QtCore.Qt.DisplayRole)
      editor.setText(str(text))         

#
# Plotter pen  configuration class -----------------------------------
#
class cls_PenConfigWindow(QtWidgets.QDialog):

   def __init__(self): 
      super().__init__()
      self.setWindowTitle('Plotter pen config')
      self.vlayout = QtWidgets.QVBoxLayout()
#
#     table widget
#
      self.tablemodel=PenTableModel(PENCONFIG.get_all())
      self.tableview= QtWidgets.QTableView()
      self.tableview.setModel(self.tablemodel)
      self.tableview.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
      self.tableview.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
      self.delegate= PenDelegate()
      self.tableview.setItemDelegate(self.delegate)
      self.vlayout.addWidget(self.tableview)
#
#     ok/cancel button box
#    
      self.buttonBox = QtWidgets.QDialogButtonBox()
      self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Reset| QtWidgets.QDialogButtonBox.Ok)
      self.buttonBox.setCenterButtons(True)
      self.buttonBox.accepted.connect(self.do_ok)
      self.buttonBox.rejected.connect(self.do_cancel)
      self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.do_reset)
      self.vlayout.addWidget(self.buttonBox)
      self.setLayout(self.vlayout)

   def do_ok(self):
      PENCONFIG.set_all(self.tablemodel.getTable())
      super().accept()

   def do_cancel(self):
      super().reject()
#
#     reset populates table with the default configuration
#
   def do_reset(self):
      self.tablemodel.setAll(PENCONFIG.default_config())

   @staticmethod
   def getPenConfig():
      dialog= cls_PenConfigWindow()
      dialog.resize(650,600)
      result= dialog.exec()
      if result== QtWidgets.QDialog.Accepted:
         return True
      else:
         return False
class PenConfigError(Exception):
   def __init__(self,msg,add_msg= None):
      self.msg= msg
      self.add_msg = add_msg


class cls_penconfig:
#
#  initialize: set penconfig to the default configuration
#
   def __init__(self):
      self.__penconfig__= None
      self.__userconfig__ = None
      return
#
#  default config
#
   def default_config(self):
      return [
       ["Black   0.3 mm", 0x00,0x00,0x00,0xff,1.0],
       ["Red     0.3 mm", 0xff,0x00,0x00,0xff,1.0],
       ["Green   0.3 mm", 0x00,0xff,0x00,0xff,1.0],
       ["Blue    0.3 mm", 0x00,0x00,0xff,0xff,1.0],
       ["Yellow  0.3 mm", 0xff,0xff,0x00,0xff,1.0],
       ["Cyan    0.3 mm", 0x00,0xff,0xff,0xff,1.0],
       ["Magenta 0.3 mm", 0xff,0x00,0xff,0xff,1.0],
       ["Black   0.7 mm", 0x00,0x00,0x00,0xff,2.0],
       ["Red     0.7 mm", 0xff,0x00,0x00,0xff,2.0],
       ["Green   0.7 mm", 0x00,0xff,0x00,0xff,2.0],
       ["Blue    0.7 mm", 0x00,0x00,0xff,0xff,2.0],
       ["Yellow  0.7 mm", 0x00,0xff,0xff,0xff,2.0],
       ["Cyan    0.7 mm", 0x00,0xff,0xff,0xff,2.0],
       ["Magenta 0.7 mm", 0xff,0x00,0xff,0xff,2.0], 
       ["Custom1 0.3 mm", 0x00,0x00,0x00,0xff,1.0],
       ["Custom2 0.3 mm", 0x00,0x00,0x00,0xff,1.0]]
   

#
#  open: read in the pen configuration. If the configuration file does not 
#  exist, the default configuration is written to the pen config file
#  If clean is true do not read an existing config file
#
   def open(self,name,configversion,instance,production,clean):
      self.__userconfig__= cls_userconfig(name,"penconfig",configversion,instance,production)
      if clean:
         return
      try:
         self.__penconfig__= self.__userconfig__.read(self.default_config())
      except ConfigError as e:
         raise PenConfigError(e.msg,e.add_msg)
#
#  Get the list of pens
#
   def get_penlist(self):
      penlist= []
      for p in self.__penconfig__:
         penlist.append(p[0])
      return penlist 
#
# Get the config of the nth pen 
#
   def get_pen(self,n):
      return(self.__penconfig__[n][1:]) 
#
# Get the whole table as a copy
#
   def get_all(self):
      return copy.deepcopy(self.__penconfig__)
       
#
# Populate the whole table
#
   def set_all(self,newlist):
      self.__penconfig__= []
      self.__penconfig__= copy.deepcopy(newlist)

#
#  Save the penconfig to the configuration file
#
   def save(self):
      try:
         self.__userconfig__.write(self.__penconfig__)
      except ConfigError as e:
         raise PenConfigError(e.msg,e.add_msg)
#
PENCONFIG=  cls_penconfig()
