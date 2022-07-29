#!/usr/bin/python3
# -*- coding: utf-8 -*-
# shortcutconfig for pyILPER
#
# (c) 2018 Joachim Siebold
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
# shortcutconfig class -------------------------------------------
#
# Changelog
# 11.08.2018 jsi
# - first version
# 15.08.2018 jsi
# - SHORTCUT_INSERT shortcut type added
# 12.12.2021 jsi
# - add configversion parameter to open method
# 04.05.2022 jsi
# - PySide6 migration
#
import copy
from .pilcore import QTBINDINGS
if QTBINDINGS=="PySide6":
   from PySide6 import QtCore, QtGui, QtWidgets
if QTBINDINGS=="PyQt5":
   from PyQt5 import QtCore, QtGui, QtWidgets

from .userconfig import cls_userconfig, ConfigError

SHORTCUT_INPUT=0
SHORTCUT_EXEC=1
SHORTCUT_EDIT=2
SHORTCUT_INSERT=3
#
# Terminal shortcut table model class -----------------------------------------
#
class ShortcutTableModel(QtCore.QAbstractTableModel):
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
      if index.column()<2:
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
            return("Key")
         elif section==1:
             return("Text")
         elif section==2:
             return("Type")
         else:
            return("")

   def getTable(self):
      return self.arraydata

   def setAll(self,shortcutconfig):
      self.arraydata=shortcutconfig
      self.layoutChanged.emit() # this updates all cells
         
#
# Custom delegate class ---------------------------------------
#
# This delegate does:
# - no editing for the first column (shortcut key)
# - text editing for the second column (shortcut text)
# - combo box editing for the third column (shortcut type)
#
class ShortcutDelegate(QtWidgets.QItemDelegate):

   def __init__(self, parent=None):
      super(ShortcutDelegate, self).__init__(parent)
      self.items = ["Input only","Input+Endline","Input+2*Cursor left","Input+2*Cursor left+Insert"]

#
#  do not create an editor for the first column, create text editor for
#  the second column and a QComboBox for the third column
#
   def createEditor(self, parent, option, index):
      editor= None
      if index.column()==1:
         editor= super(ShortcutDelegate,self).createEditor(parent,option,index)
      if index.column()==2:
         editor=QtWidgets.QComboBox(parent)
         editor.addItems(self.items)
      return(editor)
#
#  set text for editing (second column) or current index (third column)
#
   def setEditorData(self, editor, index):
      # Gets display text if edit data hasn't been set.
      text = index.data(QtCore.Qt.EditRole) or index.data(QtCore.Qt.DisplayRole)
      if index.column()==1:
        editor.setText(str(text))         
      if index.column()==2:
        editor.setCurrentIndex(int(text))
#
#  return edited data to the model (text for second, index for third column)
#
   def setModelData(self,editor,model,index):
      if index.column()==1:
         model.setData(index,editor.text(),QtCore.Qt.EditRole)
      if index.column()==2:
         model.setData(index,editor.currentIndex(),QtCore.Qt.EditRole)
#
#  paint item text for the third column and text for the other columns
#
   def paint(self, painter, option, index):
      if index.column()==2:
         text = self.items[index.data()]
         option.text = text
         QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.CE_ItemViewItem, option, painter)
      else:
         super(ShortcutDelegate, self).paint(painter,option,index)

#
# Shortcut configuration class -----------------------------------
#
class cls_ShortcutConfigWindow(QtWidgets.QDialog):

   def __init__(self): 
      super().__init__()
      self.setWindowTitle('Terminal shortcut config')
      self.vlayout = QtWidgets.QVBoxLayout()
#
#     table widget
#
      self.tablemodel=ShortcutTableModel(SHORTCUTCONFIG.get_all())
      self.tableview= QtWidgets.QTableView()
      self.tableview.setModel(self.tablemodel)
      self.tableview.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
      self.tableview.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
      self.delegate= ShortcutDelegate()
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
      SHORTCUTCONFIG.set_all(self.tablemodel.getTable())
      super().accept()

   def do_cancel(self):
      super().reject()
#
#     reset populates table with the default configuration
#
   def do_reset(self):
      self.tablemodel.setAll(SHORTCUTCONFIG.default_config())

   @staticmethod
   def getShortcutConfig():
      dialog= cls_ShortcutConfigWindow()
      dialog.resize(650,600)
      result= dialog.exec()
      if result== QtWidgets.QDialog.Accepted:
         return True
      else:
         return False


class ShortcutConfigError(Exception):
   def __init__(self,msg,add_msg= None):
      self.msg= msg
      self.add_msg = add_msg


class cls_shortcutconfig:
#
#  initialize: set shortcutconfig to the default configuration
#
   def __init__(self):
      self.__shortcutconfig__= None
      self.__userconfig__ = None
      return
#
#  default config
#
   def default_config(self):
      return [
       ["ALT-A","",0],
       ["ALT-B","",0],
       ["ALT-C","",0],
       ["ALT-D","",0],
       ["ALT-E","",0],
       ["ALT-F","",0],
       ["ALT-G","",0],
       ["ALT-H","",0],
       ["ALT-I","Reserved!",0],
       ["ALT-J","",0],
       ["ALT-K","",0],
       ["ALT-L","Reserved!",0],
       ["ALT-M","",0],
       ["ALT-N","",0],
       ["ALT-O","",0],
       ["ALT-P","",0],
       ["ALT-Q","",0],
       ["ALT-R","",0],
       ["ALT-S","",0],
       ["ALT-T","",0],
       ["ALT-U","",0],
       ["ALT-V","",0],
       ["ALT-W","",0],
       ["ALT-X","",0],
       ["ALT-Y","",0],
       ["ALT-Z","",0]]

#
#  open: read in the shortcut configuration. If the configuration file does not 
#  exist, the default configuration is written to the shortcut config file
#  If clean is true do not read an existing config file
#
   def open(self,name,configversion,instance,production,clean):
      self.__userconfig__= cls_userconfig(name,"shortcutconfig",configversion,instance,clean)
      if clean:
         return
      try:
         self.__shortcutconfig__= self.__userconfig__.read(self.default_config())
      except ConfigError as e:
         raise ShortcutConfigError(e.msg,e.add_msg)
#
#  Get the list of shortcuts
#
   def get_shortcutlist(self):
      shortcutlist= []
      for p in self.__shortcutconfig__:
         shortcutlist.append(p[0])
      return shortcutlist 
#
# Get the config of the nth shortcut
#
   def get_shortcut(self,n):
      return(self.__shortcutconfig__[n][1:]) 
#
# Get the whole table as a copy
#
   def get_all(self):
      return copy.deepcopy(self.__shortcutconfig__)
       
#
# Populate the whole table
#
   def set_all(self,newlist):
      self.__shortcutconfig__= []
      self.__shortcutconfig__= copy.deepcopy(newlist)

#
#  Save the shortcutconfig to the configuration file
#
   def save(self):
      try:
         self.__userconfig__.write(self.__shortcutconfig__)
      except ConfigError as e:
         raise ShortcutConfigError(e.msg,e.add_msg)
#
SHORTCUTCONFIG=  cls_shortcutconfig()
