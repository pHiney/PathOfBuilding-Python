# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgManageItems.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
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

class Ui_ManageItemSet(object):
    def setupUi(self, ManageItemSet):
        if not ManageItemSet.objectName():
            ManageItemSet.setObjectName(u"ManageItemSet")
        ManageItemSet.resize(500, 500)
        icon = QIcon()
        icon.addFile(u":/Art/Icons/edit-list-order.png", QSize(), QIcon.Normal, QIcon.Off)
        ManageItemSet.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(ManageItemSet)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lbl_Info = QLabel(ManageItemSet)
        self.lbl_Info.setObjectName(u"lbl_Info")
        self.lbl_Info.setWordWrap(True)

        self.verticalLayout.addWidget(self.lbl_Info)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btnNew = QPushButton(ManageItemSet)
        self.btnNew.setObjectName(u"btnNew")
        self.btnNew.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.btnNew)

        self.btnCopy = QPushButton(ManageItemSet)
        self.btnCopy.setObjectName(u"btnCopy")
        self.btnCopy.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.btnCopy)

        self.btnDelete = QPushButton(ManageItemSet)
        self.btnDelete.setObjectName(u"btnDelete")
        self.btnDelete.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.btnDelete)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.list_Items = ListBox(ManageItemSet)
        self.list_Items.setObjectName(u"list_Items")
        self.list_Items.setDragEnabled(True)
        self.list_Items.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_Items.setDefaultDropAction(Qt.MoveAction)
        self.list_Items.setAlternatingRowColors(True)
        self.list_Items.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_Items.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.verticalLayout.addWidget(self.list_Items)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.btnClose = QPushButton(ManageItemSet)
        self.btnClose.setObjectName(u"btnClose")
        self.btnClose.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout.addWidget(self.btnClose)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        QWidget.setTabOrder(self.list_Items, self.btnCopy)
        QWidget.setTabOrder(self.btnCopy, self.btnDelete)

        self.retranslateUi(ManageItemSet)

        self.list_Items.setCurrentRow(-1)


        QMetaObject.connectSlotsByName(ManageItemSet)
    # setupUi

    def retranslateUi(self, ManageItemSet):
        ManageItemSet.setWindowTitle(QCoreApplication.translate("ManageItemSet", u"Manage Item Sets", None))
        self.lbl_Info.setText(QCoreApplication.translate("ManageItemSet", u"Use the buttons below or shortcut keys. Hover over the button to see the shortcuts. Double-Click an entry to edit it's name", None))
#if QT_CONFIG(tooltip)
        self.btnNew.setToolTip(QCoreApplication.translate("ManageItemSet", u"New _VERSION tree.  (Ctrl-N)", None))
#endif // QT_CONFIG(tooltip)
        self.btnNew.setText(QCoreApplication.translate("ManageItemSet", u"&New", None))
#if QT_CONFIG(shortcut)
        self.btnNew.setShortcut(QCoreApplication.translate("ManageItemSet", u"Ctrl+N", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.btnCopy.setToolTip(QCoreApplication.translate("ManageItemSet", u"Copy selections. (Ctrl-C)", None))
#endif // QT_CONFIG(tooltip)
        self.btnCopy.setText(QCoreApplication.translate("ManageItemSet", u"&Copy", None))
#if QT_CONFIG(shortcut)
        self.btnCopy.setShortcut(QCoreApplication.translate("ManageItemSet", u"Ctrl+C", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.btnDelete.setToolTip(QCoreApplication.translate("ManageItemSet", u"Delete selections. Beware !!!! (Delete)", None))
#endif // QT_CONFIG(tooltip)
        self.btnDelete.setText(QCoreApplication.translate("ManageItemSet", u"&Delete", None))
#if QT_CONFIG(shortcut)
        self.btnDelete.setShortcut(QCoreApplication.translate("ManageItemSet", u"Del", None))
#endif // QT_CONFIG(shortcut)
        self.btnClose.setText(QCoreApplication.translate("ManageItemSet", u"Clos&e", None))
    # retranslateUi

