# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgCraftItems.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_CraftItems(object):
    def setupUi(self, CraftItems):
        if not CraftItems.objectName():
            CraftItems.setObjectName(u"CraftItems")
        CraftItems.resize(871, 500)
        self.vlayout_Dialog = QVBoxLayout(CraftItems)
        self.vlayout_Dialog.setSpacing(0)
        self.vlayout_Dialog.setObjectName(u"vlayout_Dialog")
        self.vlayout_Dialog.setContentsMargins(2, 2, 2, 2)
        self.frame_Controls = QFrame(CraftItems)
        self.frame_Controls.setObjectName(u"frame_Controls")
        self.frame_Controls.setMinimumSize(QSize(650, 100))
        self.frame_Controls.setMaximumSize(QSize(16777215, 100))
        self.frame_Controls.setFrameShape(QFrame.NoFrame)
        self.frame_Controls.setFrameShadow(QFrame.Raised)
        self.Controls = QWidget(self.frame_Controls)
        self.Controls.setObjectName(u"Controls")
        self.Controls.setGeometry(QRect(10, 40, 620, 40))
        self.Controls.setMinimumSize(QSize(620, 0))
        self.horizontalLayout = QHBoxLayout(self.Controls)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.combo_Socket1 = QComboBox(self.Controls)
        self.combo_Socket1.setObjectName(u"combo_Socket1")

        self.horizontalLayout.addWidget(self.combo_Socket1)

        self.check_Connector2 = QCheckBox(self.Controls)
        self.check_Connector2.setObjectName(u"check_Connector2")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.check_Connector2.sizePolicy().hasHeightForWidth())
        self.check_Connector2.setSizePolicy(sizePolicy)
        self.check_Connector2.setMinimumSize(QSize(22, 0))
        self.check_Connector2.setMaximumSize(QSize(24, 16))
        self.check_Connector2.setStyleSheet(u"QCheckBox::indicator:unchecked {\n"
"border : 2px solid red;\n"
"width : 4px;\n"
"height : 16px;\n"
"padding : 5px;\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"border : 2px solid green;\n"
"width : 16px;\n"
"height : 4px;\n"
"}\n"
"\n"
"QCheckBox::indicator:indeterminate {\n"
"width : 10px;\n"
"height : 10px;\n"
"image : url(\":/Art/Icons/cross.png\")\n"
"}")
        self.check_Connector2.setChecked(True)

        self.horizontalLayout.addWidget(self.check_Connector2)

        self.combo_Socket2 = QComboBox(self.Controls)
        self.combo_Socket2.setObjectName(u"combo_Socket2")

        self.horizontalLayout.addWidget(self.combo_Socket2)

        self.check_Connector3 = QCheckBox(self.Controls)
        self.check_Connector3.setObjectName(u"check_Connector3")
        self.check_Connector3.setMinimumSize(QSize(22, 0))
        self.check_Connector3.setMaximumSize(QSize(24, 16))
        self.check_Connector3.setStyleSheet(u"QCheckBox::indicator:unchecked {\n"
"border : 2px solid red;\n"
"width : 4px;\n"
"height : 16px;\n"
"padding : 5px;\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"border : 2px solid green;\n"
"width : 16px;\n"
"height : 4px;\n"
"}\n"
"\n"
"QCheckBox::indicator:indeterminate {\n"
"width : 10px;\n"
"height : 10px;\n"
"image : url(\":/Art/Icons/cross.png\")\n"
"}")
        self.check_Connector3.setChecked(True)

        self.horizontalLayout.addWidget(self.check_Connector3)

        self.combo_Socket3 = QComboBox(self.Controls)
        self.combo_Socket3.setObjectName(u"combo_Socket3")

        self.horizontalLayout.addWidget(self.combo_Socket3)

        self.check_Connector4 = QCheckBox(self.Controls)
        self.check_Connector4.setObjectName(u"check_Connector4")
        self.check_Connector4.setMinimumSize(QSize(22, 0))
        self.check_Connector4.setMaximumSize(QSize(24, 16))
        self.check_Connector4.setStyleSheet(u"QCheckBox::indicator:unchecked {\n"
"border : 2px solid red;\n"
"width : 4px;\n"
"height : 16px;\n"
"padding : 5px;\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"border : 2px solid green;\n"
"width : 16px;\n"
"height : 4px;\n"
"}\n"
"\n"
"QCheckBox::indicator:indeterminate {\n"
"width : 10px;\n"
"height : 10px;\n"
"image : url(\":/Art/Icons/cross.png\")\n"
"}")
        self.check_Connector4.setChecked(True)

        self.horizontalLayout.addWidget(self.check_Connector4)

        self.combo_Socket4 = QComboBox(self.Controls)
        self.combo_Socket4.setObjectName(u"combo_Socket4")

        self.horizontalLayout.addWidget(self.combo_Socket4)

        self.check_Connector5 = QCheckBox(self.Controls)
        self.check_Connector5.setObjectName(u"check_Connector5")
        self.check_Connector5.setMinimumSize(QSize(22, 0))
        self.check_Connector5.setMaximumSize(QSize(24, 16))
        self.check_Connector5.setStyleSheet(u"QCheckBox::indicator:unchecked {\n"
"border : 2px solid red;\n"
"width : 4px;\n"
"height : 16px;\n"
"padding : 5px;\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"border : 2px solid green;\n"
"width : 16px;\n"
"height : 4px;\n"
"}\n"
"\n"
"QCheckBox::indicator:indeterminate {\n"
"width : 10px;\n"
"height : 10px;\n"
"image : url(\":/Art/Icons/cross.png\")\n"
"}")
        self.check_Connector5.setChecked(True)

        self.horizontalLayout.addWidget(self.check_Connector5)

        self.combo_Socket5 = QComboBox(self.Controls)
        self.combo_Socket5.setObjectName(u"combo_Socket5")

        self.horizontalLayout.addWidget(self.combo_Socket5)

        self.check_Connector6 = QCheckBox(self.Controls)
        self.check_Connector6.setObjectName(u"check_Connector6")
        self.check_Connector6.setMinimumSize(QSize(22, 0))
        self.check_Connector6.setMaximumSize(QSize(24, 16))
        self.check_Connector6.setStyleSheet(u"QCheckBox::indicator:unchecked {\n"
"border : 2px solid red;\n"
"width : 4px;\n"
"height : 16px;\n"
"padding : 5px;\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"border : 2px solid green;\n"
"width : 16px;\n"
"height : 4px;\n"
"}\n"
"\n"
"QCheckBox::indicator:indeterminate {\n"
"width : 10px;\n"
"height : 10px;\n"
"image : url(\":/Art/Icons/cross.png\")\n"
"}")
        self.check_Connector6.setChecked(True)

        self.horizontalLayout.addWidget(self.check_Connector6)

        self.combo_Socket6 = QComboBox(self.Controls)
        self.combo_Socket6.setObjectName(u"combo_Socket6")

        self.horizontalLayout.addWidget(self.combo_Socket6)

        self.hspacer_sockets = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.hspacer_sockets)

        self.combo_Influence2 = QComboBox(self.frame_Controls)
        self.combo_Influence2.addItem("")
        self.combo_Influence2.addItem("")
        self.combo_Influence2.addItem("")
        self.combo_Influence2.addItem("")
        self.combo_Influence2.addItem("")
        self.combo_Influence2.addItem("")
        self.combo_Influence2.addItem("")
        self.combo_Influence2.addItem("")
        self.combo_Influence2.addItem("")
        self.combo_Influence2.setObjectName(u"combo_Influence2")
        self.combo_Influence2.setGeometry(QRect(510, 10, 110, 22))
        self.btn_Implicit = QPushButton(self.frame_Controls)
        self.btn_Implicit.setObjectName(u"btn_Implicit")
        self.btn_Implicit.setGeometry(QRect(270, 10, 100, 24))
        self.btn_Corrupt = QPushButton(self.frame_Controls)
        self.btn_Corrupt.setObjectName(u"btn_Corrupt")
        self.btn_Corrupt.setGeometry(QRect(170, 10, 90, 24))
        self.btn_Enchantment = QPushButton(self.frame_Controls)
        self.btn_Enchantment.setObjectName(u"btn_Enchantment")
        self.btn_Enchantment.setGeometry(QRect(20, 10, 140, 24))
        self.combo_Influence1 = QComboBox(self.frame_Controls)
        self.combo_Influence1.addItem("")
        self.combo_Influence1.addItem("")
        self.combo_Influence1.addItem("")
        self.combo_Influence1.addItem("")
        self.combo_Influence1.addItem("")
        self.combo_Influence1.addItem("")
        self.combo_Influence1.addItem("")
        self.combo_Influence1.addItem("")
        self.combo_Influence1.addItem("")
        self.combo_Influence1.setObjectName(u"combo_Influence1")
        self.combo_Influence1.setGeometry(QRect(380, 10, 110, 22))
        self.label_Quality = QLabel(self.frame_Controls)
        self.label_Quality.setObjectName(u"label_Quality")
        self.label_Quality.setGeometry(QRect(730, 12, 60, 20))
        self.label_Quality.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.spin_Quality = QSpinBox(self.frame_Controls)
        self.spin_Quality.setObjectName(u"spin_Quality")
        self.spin_Quality.setGeometry(QRect(795, 11, 42, 22))
        self.spin_Quality.setMaximum(30)
        self.cbox_Corrupted = QCheckBox(self.frame_Controls)
        self.cbox_Corrupted.setObjectName(u"cbox_Corrupted")
        self.cbox_Corrupted.setGeometry(QRect(640, 10, 90, 24))
        self.cbox_Corrupted.setMinimumSize(QSize(40, 24))
        self.cbox_Corrupted.setChecked(False)

        self.vlayout_Dialog.addWidget(self.frame_Controls)

        self.frame_Item = QFrame(CraftItems)
        self.frame_Item.setObjectName(u"frame_Item")
        self.frame_Item.setFrameShape(QFrame.NoFrame)
        self.frame_Item.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_Item)
        self.horizontalLayout_2.setSpacing(3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.label_Item = QLabel(self.frame_Item)
        self.label_Item.setObjectName(u"label_Item")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_Item.sizePolicy().hasHeightForWidth())
        self.label_Item.setSizePolicy(sizePolicy1)
        self.label_Item.setMinimumSize(QSize(426, 310))
        self.label_Item.setFrameShape(QFrame.NoFrame)
        self.label_Item.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label_Item.setWordWrap(True)

        self.horizontalLayout_2.addWidget(self.label_Item)

        self.widget_Right = QWidget(self.frame_Item)
        self.widget_Right.setObjectName(u"widget_Right")
        self.verticalLayout = QVBoxLayout(self.widget_Right)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.gLayout_Mods = QGridLayout()
        self.gLayout_Mods.setObjectName(u"gLayout_Mods")
        self.label_Mods = QLabel(self.widget_Right)
        self.label_Mods.setObjectName(u"label_Mods")
        self.label_Mods.setMinimumSize(QSize(90, 0))
        self.label_Mods.setLayoutDirection(Qt.LeftToRight)
        self.label_Mods.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gLayout_Mods.addWidget(self.label_Mods, 0, 0, 1, 1)

        self.combo_Mods = QComboBox(self.widget_Right)
        self.combo_Mods.setObjectName(u"combo_Mods")

        self.gLayout_Mods.addWidget(self.combo_Mods, 0, 1, 1, 1)

        self.spin_Mods = QDoubleSpinBox(self.widget_Right)
        self.spin_Mods.setObjectName(u"spin_Mods")
        self.spin_Mods.setMinimumSize(QSize(45, 0))
        self.spin_Mods.setMaximum(1.000000000000000)
        self.spin_Mods.setSingleStep(0.100000000000000)

        self.gLayout_Mods.addWidget(self.spin_Mods, 0, 2, 1, 1)

        self.gLayout_Mods.setColumnStretch(1, 1)

        self.verticalLayout.addLayout(self.gLayout_Mods)

        self.gLayout_Variants1 = QGridLayout()
        self.gLayout_Variants1.setObjectName(u"gLayout_Variants1")
        self.label_Variants1 = QLabel(self.widget_Right)
        self.label_Variants1.setObjectName(u"label_Variants1")
        self.label_Variants1.setMinimumSize(QSize(90, 0))
        self.label_Variants1.setLayoutDirection(Qt.LeftToRight)
        self.label_Variants1.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gLayout_Variants1.addWidget(self.label_Variants1, 0, 0, 1, 1)

        self.combo_Variants1 = QComboBox(self.widget_Right)
        self.combo_Variants1.setObjectName(u"combo_Variants1")

        self.gLayout_Variants1.addWidget(self.combo_Variants1, 0, 1, 1, 1)

        self.gLayout_Variants1.setColumnStretch(1, 1)

        self.verticalLayout.addLayout(self.gLayout_Variants1)

        self.gLayout_Variants2 = QGridLayout()
        self.gLayout_Variants2.setObjectName(u"gLayout_Variants2")
        self.label_Variants2 = QLabel(self.widget_Right)
        self.label_Variants2.setObjectName(u"label_Variants2")
        self.label_Variants2.setMinimumSize(QSize(90, 0))
        self.label_Variants2.setLayoutDirection(Qt.LeftToRight)
        self.label_Variants2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gLayout_Variants2.addWidget(self.label_Variants2, 0, 0, 1, 1)

        self.combo_Variants2 = QComboBox(self.widget_Right)
        self.combo_Variants2.setObjectName(u"combo_Variants2")

        self.gLayout_Variants2.addWidget(self.combo_Variants2, 0, 1, 1, 1)

        self.gLayout_Variants2.setColumnStretch(1, 1)

        self.verticalLayout.addLayout(self.gLayout_Variants2)

        self.gLayout_Variants3 = QGridLayout()
        self.gLayout_Variants3.setObjectName(u"gLayout_Variants3")
        self.label_Variants3 = QLabel(self.widget_Right)
        self.label_Variants3.setObjectName(u"label_Variants3")
        self.label_Variants3.setMinimumSize(QSize(90, 0))
        self.label_Variants3.setLayoutDirection(Qt.LeftToRight)
        self.label_Variants3.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gLayout_Variants3.addWidget(self.label_Variants3, 0, 0, 1, 1)

        self.combo_Variants3 = QComboBox(self.widget_Right)
        self.combo_Variants3.setObjectName(u"combo_Variants3")

        self.gLayout_Variants3.addWidget(self.combo_Variants3, 0, 1, 1, 1)

        self.gLayout_Variants3.setColumnStretch(1, 1)

        self.verticalLayout.addLayout(self.gLayout_Variants3)

        self.verticalSpacer = QSpacerItem(40, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.horizontalLayout_2.addWidget(self.widget_Right)

        self.horizontalLayout_2.setStretch(0, 4)
        self.horizontalLayout_2.setStretch(1, 3)

        self.vlayout_Dialog.addWidget(self.frame_Item)

        self.btnBox = QDialogButtonBox(CraftItems)
        self.btnBox.setObjectName(u"btnBox")
        self.btnBox.setOrientation(Qt.Horizontal)
        self.btnBox.setStandardButtons(QDialogButtonBox.Reset)
        self.btnBox.setCenterButtons(True)

        self.vlayout_Dialog.addWidget(self.btnBox)

        self.label_StatusBar = QLabel(CraftItems)
        self.label_StatusBar.setObjectName(u"label_StatusBar")
        self.label_StatusBar.setMaximumSize(QSize(16777215, 24))

        self.vlayout_Dialog.addWidget(self.label_StatusBar)

#if QT_CONFIG(shortcut)
        self.label_Quality.setBuddy(self.spin_Quality)
        self.label_Variants1.setBuddy(self.combo_Variants1)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(CraftItems)
        self.btnBox.accepted.connect(CraftItems.accept)
        self.btnBox.rejected.connect(CraftItems.reject)

        QMetaObject.connectSlotsByName(CraftItems)
    # setupUi

    def retranslateUi(self, CraftItems):
        CraftItems.setWindowTitle(QCoreApplication.translate("CraftItems", u"Dialog", None))
#if QT_CONFIG(tooltip)
        self.check_Connector2.setToolTip(QCoreApplication.translate("CraftItems", u"Click to (dis)connect these sockets", None))
#endif // QT_CONFIG(tooltip)
        self.check_Connector2.setText("")
#if QT_CONFIG(tooltip)
        self.check_Connector3.setToolTip(QCoreApplication.translate("CraftItems", u"Click to (dis)connect these sockets", None))
#endif // QT_CONFIG(tooltip)
        self.check_Connector3.setText("")
#if QT_CONFIG(tooltip)
        self.check_Connector4.setToolTip(QCoreApplication.translate("CraftItems", u"Click to (dis)connect these sockets", None))
#endif // QT_CONFIG(tooltip)
        self.check_Connector4.setText("")
#if QT_CONFIG(tooltip)
        self.check_Connector5.setToolTip(QCoreApplication.translate("CraftItems", u"Click to (dis)connect these sockets", None))
#endif // QT_CONFIG(tooltip)
        self.check_Connector5.setText("")
#if QT_CONFIG(tooltip)
        self.check_Connector6.setToolTip(QCoreApplication.translate("CraftItems", u"Click to (dis)connect these sockets", None))
#endif // QT_CONFIG(tooltip)
        self.check_Connector6.setText("")
        self.combo_Influence2.setItemText(0, QCoreApplication.translate("CraftItems", u"Influence", None))
        self.combo_Influence2.setItemText(1, QCoreApplication.translate("CraftItems", u"Shaper", None))
        self.combo_Influence2.setItemText(2, QCoreApplication.translate("CraftItems", u"Elder", None))
        self.combo_Influence2.setItemText(3, QCoreApplication.translate("CraftItems", u"Warlord", None))
        self.combo_Influence2.setItemText(4, QCoreApplication.translate("CraftItems", u"Hunter", None))
        self.combo_Influence2.setItemText(5, QCoreApplication.translate("CraftItems", u"Crusader", None))
        self.combo_Influence2.setItemText(6, QCoreApplication.translate("CraftItems", u"Redeemer", None))
        self.combo_Influence2.setItemText(7, QCoreApplication.translate("CraftItems", u"Searing Exarch", None))
        self.combo_Influence2.setItemText(8, QCoreApplication.translate("CraftItems", u"Eater of Worlds", None))

        self.btn_Implicit.setText(QCoreApplication.translate("CraftItems", u"Add Implicit ....", None))
        self.btn_Corrupt.setText(QCoreApplication.translate("CraftItems", u"Corrupt ...", None))
        self.btn_Enchantment.setText(QCoreApplication.translate("CraftItems", u"Add Enchantment ...", None))
        self.combo_Influence1.setItemText(0, QCoreApplication.translate("CraftItems", u"Influence", None))
        self.combo_Influence1.setItemText(1, QCoreApplication.translate("CraftItems", u"Shaper", None))
        self.combo_Influence1.setItemText(2, QCoreApplication.translate("CraftItems", u"Elder", None))
        self.combo_Influence1.setItemText(3, QCoreApplication.translate("CraftItems", u"Warlord", None))
        self.combo_Influence1.setItemText(4, QCoreApplication.translate("CraftItems", u"Hunter", None))
        self.combo_Influence1.setItemText(5, QCoreApplication.translate("CraftItems", u"Crusader", None))
        self.combo_Influence1.setItemText(6, QCoreApplication.translate("CraftItems", u"Redeemer", None))
        self.combo_Influence1.setItemText(7, QCoreApplication.translate("CraftItems", u"Searing Exarch", None))
        self.combo_Influence1.setItemText(8, QCoreApplication.translate("CraftItems", u"Eater of Worlds", None))

        self.label_Quality.setText(QCoreApplication.translate("CraftItems", u"&Quality:", None))
        self.cbox_Corrupted.setText(QCoreApplication.translate("CraftItems", u"&Corrupted", None))
        self.label_Item.setText("")
        self.label_Mods.setText(QCoreApplication.translate("CraftItems", u"Variable Mods :", None))
        self.label_Variants1.setText(QCoreApplication.translate("CraftItems", u"Variants :", None))
        self.label_Variants2.setText(QCoreApplication.translate("CraftItems", u"Variants :", None))
        self.label_Variants3.setText(QCoreApplication.translate("CraftItems", u"Variants :", None))
    # retranslateUi

