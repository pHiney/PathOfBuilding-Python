# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dlgBuildExport.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QGroupBox, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QWidget)
import PoB_rc

class Ui_BuildExport(object):
    def setupUi(self, BuildExport):
        if not BuildExport.objectName():
            BuildExport.setObjectName(u"BuildExport")
        BuildExport.resize(645, 220)
        BuildExport.setMaximumSize(QSize(645, 220))
        icon = QIcon()
        icon.addFile(u":/Art/Icons/paper-plane.png", QSize(), QIcon.Normal, QIcon.Off)
        BuildExport.setWindowIcon(icon)
        self.buttonBox = QDialogButtonBox(BuildExport)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(380, 180, 231, 32))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
        self.label_Info = QLabel(BuildExport)
        self.label_Info.setObjectName(u"label_Info")
        self.label_Info.setGeometry(QRect(20, 42, 40, 16))
        self.lineEdit_Code = QLineEdit(BuildExport)
        self.lineEdit_Code.setObjectName(u"lineEdit_Code")
        self.lineEdit_Code.setGeometry(QRect(65, 40, 455, 22))
        self.lineEdit_Code.setInputMask(u"")
        self.label_Share = QLabel(BuildExport)
        self.label_Share.setObjectName(u"label_Share")
        self.label_Share.setGeometry(QRect(20, 72, 351, 16))
        self.btn_Copy = QPushButton(BuildExport)
        self.btn_Copy.setObjectName(u"btn_Copy")
        self.btn_Copy.setEnabled(True)
        self.btn_Copy.setGeometry(QRect(540, 40, 75, 24))
        self.btn_Share = QPushButton(BuildExport)
        self.btn_Share.setObjectName(u"btn_Share")
        self.btn_Share.setEnabled(True)
        self.btn_Share.setGeometry(QRect(540, 70, 75, 24))
        self.combo_ShareSite = QComboBox(BuildExport)
        self.combo_ShareSite.setObjectName(u"combo_ShareSite")
        self.combo_ShareSite.setGeometry(QRect(400, 70, 121, 22))
        self.label_Export = QLabel(BuildExport)
        self.label_Export.setObjectName(u"label_Export")
        self.label_Export.setGeometry(QRect(20, 10, 141, 16))
        self.label_Status = QLabel(BuildExport)
        self.label_Status.setObjectName(u"label_Status")
        self.label_Status.setGeometry(QRect(170, 10, 431, 16))
        self.groupBox_PasteBin = QGroupBox(BuildExport)
        self.groupBox_PasteBin.setObjectName(u"groupBox_PasteBin")
        self.groupBox_PasteBin.setEnabled(True)
        self.groupBox_PasteBin.setGeometry(QRect(10, 110, 461, 81))
        self.lineEdit_DevKey = QLineEdit(self.groupBox_PasteBin)
        self.lineEdit_DevKey.setObjectName(u"lineEdit_DevKey")
        self.lineEdit_DevKey.setGeometry(QRect(90, 18, 361, 22))
        self.lineEdit_DevKey.setInputMask(u"")
        self.lineEdit_DevKey.setText(u"")
        self.lineEdit_DevKey.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.label_DevKey = QLabel(self.groupBox_PasteBin)
        self.label_DevKey.setObjectName(u"label_DevKey")
        self.label_DevKey.setGeometry(QRect(10, 20, 71, 16))
        self.label_DevKey.setLayoutDirection(Qt.RightToLeft)
        self.lineEdit_UserKey = QLineEdit(self.groupBox_PasteBin)
        self.lineEdit_UserKey.setObjectName(u"lineEdit_UserKey")
        self.lineEdit_UserKey.setGeometry(QRect(90, 48, 361, 22))
        self.lineEdit_UserKey.setInputMask(u"")
        self.lineEdit_UserKey.setText(u"")
        self.lineEdit_UserKey.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.label_UserKey = QLabel(self.groupBox_PasteBin)
        self.label_UserKey.setObjectName(u"label_UserKey")
        self.label_UserKey.setGeometry(QRect(10, 50, 71, 16))
        self.label_UserKey.setLayoutDirection(Qt.RightToLeft)
#if QT_CONFIG(shortcut)
        self.label_DevKey.setBuddy(self.lineEdit_DevKey)
        self.label_UserKey.setBuddy(self.lineEdit_UserKey)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(BuildExport)
        self.buttonBox.accepted.connect(BuildExport.accept)
        self.buttonBox.rejected.connect(BuildExport.reject)

        QMetaObject.connectSlotsByName(BuildExport)
    # setupUi

    def retranslateUi(self, BuildExport):
        BuildExport.setWindowTitle(QCoreApplication.translate("BuildExport", u"Export current character. Generate a code to share this build with other Path of Building users.", None))
        self.label_Info.setText(QCoreApplication.translate("BuildExport", u"Code", None))
        self.label_Share.setText(QCoreApplication.translate("BuildExport", u"Note: this code can be very long; you can use 'Share' to shrink it.", None))
        self.btn_Copy.setText(QCoreApplication.translate("BuildExport", u"Copy", None))
        self.btn_Share.setText(QCoreApplication.translate("BuildExport", u"&Share", None))
        self.label_Export.setText(QCoreApplication.translate("BuildExport", u"Character Export Status :", None))
        self.label_Status.setText(QCoreApplication.translate("BuildExport", u"Idle", None))
        self.groupBox_PasteBin.setTitle(QCoreApplication.translate("BuildExport", u"PasteBin parameters", None))
        self.lineEdit_DevKey.setPlaceholderText(QCoreApplication.translate("BuildExport", u"<default>", None))
        self.label_DevKey.setText(QCoreApplication.translate("BuildExport", u"Dev API KEY", None))
        self.label_UserKey.setText(QCoreApplication.translate("BuildExport", u"User API KEY", None))
    # retranslateUi

