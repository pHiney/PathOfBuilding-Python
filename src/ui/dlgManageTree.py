# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgManageTree.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QDialog, QHBoxLayout,
    QLabel, QListWidgetItem, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

from widgets.listbox import ListBox
import PoB_rc

class Ui_ManageTree(object):
    def setupUi(self, ManageTree):
        if not ManageTree.objectName():
            ManageTree.setObjectName(u"ManageTree")
        ManageTree.resize(800, 500)
        icon = QIcon()
        icon.addFile(u":/Art/Icons/tree--pencil.png", QSize(), QIcon.Normal, QIcon.Off)
        ManageTree.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(ManageTree)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lbl_Info = QLabel(ManageTree)
        self.lbl_Info.setObjectName(u"lbl_Info")
        self.lbl_Info.setWordWrap(True)

        self.verticalLayout.addWidget(self.lbl_Info)

        self.hLayout_Buttons = QHBoxLayout()
        self.hLayout_Buttons.setObjectName(u"hLayout_Buttons")
        self.btnNew = QPushButton(ManageTree)
        self.btnNew.setObjectName(u"btnNew")
        self.btnNew.setMinimumSize(QSize(75, 0))
        self.btnNew.setFocusPolicy(Qt.NoFocus)

        self.hLayout_Buttons.addWidget(self.btnNew)

        self.btnCopy = QPushButton(ManageTree)
        self.btnCopy.setObjectName(u"btnCopy")
        self.btnCopy.setMinimumSize(QSize(75, 0))
        self.btnCopy.setFocusPolicy(Qt.NoFocus)

        self.hLayout_Buttons.addWidget(self.btnCopy)

        self.btnDelete = QPushButton(ManageTree)
        self.btnDelete.setObjectName(u"btnDelete")
        self.btnDelete.setMinimumSize(QSize(75, 0))
        self.btnDelete.setFocusPolicy(Qt.NoFocus)

        self.hLayout_Buttons.addWidget(self.btnDelete)

        self.btnConvert = QPushButton(ManageTree)
        self.btnConvert.setObjectName(u"btnConvert")
        self.btnConvert.setMinimumSize(QSize(75, 0))
        self.btnConvert.setFocusPolicy(Qt.NoFocus)

        self.hLayout_Buttons.addWidget(self.btnConvert)

        self.btnImport = QPushButton(ManageTree)
        self.btnImport.setObjectName(u"btnImport")
        self.btnImport.setMinimumSize(QSize(75, 0))
        self.btnImport.setFocusPolicy(Qt.NoFocus)

        self.hLayout_Buttons.addWidget(self.btnImport)

        self.btnExport = QPushButton(ManageTree)
        self.btnExport.setObjectName(u"btnExport")
        self.btnExport.setMinimumSize(QSize(75, 0))
        self.btnExport.setFocusPolicy(Qt.NoFocus)

        self.hLayout_Buttons.addWidget(self.btnExport)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hLayout_Buttons.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.hLayout_Buttons)

        self.list_Trees = ListBox(ManageTree)
        self.list_Trees.setObjectName(u"list_Trees")
        font = QFont()
        font.setFamilies([u"Noto Sans"])
        font.setPointSize(10)
        self.list_Trees.setFont(font)
        self.list_Trees.setDragEnabled(True)
        self.list_Trees.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_Trees.setDefaultDropAction(Qt.MoveAction)
        self.list_Trees.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_Trees.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.verticalLayout.addWidget(self.list_Trees)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.btnClose = QPushButton(ManageTree)
        self.btnClose.setObjectName(u"btnClose")
        self.btnClose.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.btnClose)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        QWidget.setTabOrder(self.list_Trees, self.btnCopy)
        QWidget.setTabOrder(self.btnCopy, self.btnDelete)
        QWidget.setTabOrder(self.btnDelete, self.btnConvert)

        self.retranslateUi(ManageTree)

        self.list_Trees.setCurrentRow(-1)


        QMetaObject.connectSlotsByName(ManageTree)
    # setupUi

    def retranslateUi(self, ManageTree):
        ManageTree.setWindowTitle(QCoreApplication.translate("ManageTree", u"Manage Trees", None))
        self.lbl_Info.setText(QCoreApplication.translate("ManageTree", u"Use the buttons below or shortcut keys. Hover over the button to see the shortcuts. Double-Click an entry to edit it's name", None))
#if QT_CONFIG(tooltip)
        self.btnNew.setToolTip(QCoreApplication.translate("ManageTree", u"New tree.  (Ctrl-N)", None))
#endif // QT_CONFIG(tooltip)
        self.btnNew.setText(QCoreApplication.translate("ManageTree", u"&New", None))
#if QT_CONFIG(shortcut)
        self.btnNew.setShortcut(QCoreApplication.translate("ManageTree", u"Ctrl+N", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.btnCopy.setToolTip(QCoreApplication.translate("ManageTree", u"Copy selections. (Ctrl-C)", None))
#endif // QT_CONFIG(tooltip)
        self.btnCopy.setText(QCoreApplication.translate("ManageTree", u"&Copy", None))
#if QT_CONFIG(shortcut)
        self.btnCopy.setShortcut(QCoreApplication.translate("ManageTree", u"Ctrl+C", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.btnDelete.setToolTip(QCoreApplication.translate("ManageTree", u"Delete selections. Beware !!!! (Delete)", None))
#endif // QT_CONFIG(tooltip)
        self.btnDelete.setText(QCoreApplication.translate("ManageTree", u"&Delete", None))
#if QT_CONFIG(shortcut)
        self.btnDelete.setShortcut(QCoreApplication.translate("ManageTree", u"Del", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.btnConvert.setToolTip(QCoreApplication.translate("ManageTree", u"Convert selections to _VERSION, ignoring Trees that are already the current version", None))
#endif // QT_CONFIG(tooltip)
        self.btnConvert.setText(QCoreApplication.translate("ManageTree", u"Con&vert", None))
#if QT_CONFIG(tooltip)
        self.btnImport.setToolTip(QCoreApplication.translate("ManageTree", u"Import a GGG or poeplanner url to a new Tree.", None))
#endif // QT_CONFIG(tooltip)
        self.btnImport.setText(QCoreApplication.translate("ManageTree", u"I&mport", None))
#if QT_CONFIG(tooltip)
        self.btnExport.setToolTip(QCoreApplication.translate("ManageTree", u"Export the current selection to a GGG URL", None))
#endif // QT_CONFIG(tooltip)
        self.btnExport.setText(QCoreApplication.translate("ManageTree", u"E&xport", None))
        self.btnClose.setText(QCoreApplication.translate("ManageTree", u"Clos&e", None))
    # retranslateUi

