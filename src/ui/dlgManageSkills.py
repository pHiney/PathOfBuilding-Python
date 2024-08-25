# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgManageSkills.ui'
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
    QLabel, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)
import PoB_rc

class Ui_ManageSkillSet(object):
    def setupUi(self, ManageSkillSet):
        if not ManageSkillSet.objectName():
            ManageSkillSet.setObjectName(u"ManageSkillSet")
        ManageSkillSet.resize(500, 500)
        icon = QIcon()
        icon.addFile(u":/Art/Icons/edit-list-order.png", QSize(), QIcon.Normal, QIcon.Off)
        ManageSkillSet.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(ManageSkillSet)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lbl_Info = QLabel(ManageSkillSet)
        self.lbl_Info.setObjectName(u"lbl_Info")
        self.lbl_Info.setWordWrap(True)

        self.verticalLayout.addWidget(self.lbl_Info)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.btnNew = QPushButton(ManageSkillSet)
        self.btnNew.setObjectName(u"btnNew")
        self.btnNew.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout.addWidget(self.btnNew)

        self.btnCopy = QPushButton(ManageSkillSet)
        self.btnCopy.setObjectName(u"btnCopy")
        self.btnCopy.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout.addWidget(self.btnCopy)

        self.btnDelete = QPushButton(ManageSkillSet)
        self.btnDelete.setObjectName(u"btnDelete")
        self.btnDelete.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout.addWidget(self.btnDelete)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.list_Skills = QListWidget(ManageSkillSet)
        self.list_Skills.setObjectName(u"list_Skills")
        font = QFont()
        font.setFamilies([u"Noto Sans"])
        font.setPointSize(10)
        self.list_Skills.setFont(font)
        self.list_Skills.setDragEnabled(True)
        self.list_Skills.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_Skills.setDefaultDropAction(Qt.MoveAction)
        self.list_Skills.setAlternatingRowColors(True)
        self.list_Skills.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_Skills.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.verticalLayout.addWidget(self.list_Skills)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.btnClose = QPushButton(ManageSkillSet)
        self.btnClose.setObjectName(u"btnClose")
        self.btnClose.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.btnClose)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        QWidget.setTabOrder(self.list_Skills, self.btnCopy)
        QWidget.setTabOrder(self.btnCopy, self.btnDelete)

        self.retranslateUi(ManageSkillSet)

        self.list_Skills.setCurrentRow(-1)


        QMetaObject.connectSlotsByName(ManageSkillSet)
    # setupUi

    def retranslateUi(self, ManageSkillSet):
        ManageSkillSet.setWindowTitle(QCoreApplication.translate("ManageSkillSet", u"Manage Skill Sets", None))
        self.lbl_Info.setText(QCoreApplication.translate("ManageSkillSet", u"Use the buttons below or shortcut keys. Hover over the button to see the shortcuts. Double-Click an entry to edit it's name", None))
#if QT_CONFIG(tooltip)
        self.btnNew.setToolTip(QCoreApplication.translate("ManageSkillSet", u"New _VERSION tree.  (Ctrl-N)", None))
#endif // QT_CONFIG(tooltip)
        self.btnNew.setText(QCoreApplication.translate("ManageSkillSet", u"&New", None))
#if QT_CONFIG(shortcut)
        self.btnNew.setShortcut(QCoreApplication.translate("ManageSkillSet", u"Ctrl+N", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.btnCopy.setToolTip(QCoreApplication.translate("ManageSkillSet", u"Copy selections. (Ctrl-C)", None))
#endif // QT_CONFIG(tooltip)
        self.btnCopy.setText(QCoreApplication.translate("ManageSkillSet", u"&Copy", None))
#if QT_CONFIG(shortcut)
        self.btnCopy.setShortcut(QCoreApplication.translate("ManageSkillSet", u"Ctrl+C", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.btnDelete.setToolTip(QCoreApplication.translate("ManageSkillSet", u"Delete selections. Beware !!!! (Delete)", None))
#endif // QT_CONFIG(tooltip)
        self.btnDelete.setText(QCoreApplication.translate("ManageSkillSet", u"&Delete", None))
#if QT_CONFIG(shortcut)
        self.btnDelete.setShortcut(QCoreApplication.translate("ManageSkillSet", u"Del", None))
#endif // QT_CONFIG(shortcut)
        self.btnClose.setText(QCoreApplication.translate("ManageSkillSet", u"Clos&e", None))
    # retranslateUi

