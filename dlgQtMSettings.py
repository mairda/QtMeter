# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'qtmSettingsXDgRVl.ui'
##
## Created by: Qt User Interface Compiler version 6.6.0
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractSpinBox, QApplication, QCheckBox,
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QGraphicsView, QGroupBox, QHBoxLayout, QLabel,
    QLayout, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QSpinBox, QTabWidget, QTextBrowser,
    QVBoxLayout, QWidget)

class Ui_dlgSettings(object):
    def setupUi(self, dlgSettings):
        if not dlgSettings.objectName():
            dlgSettings.setObjectName(u"dlgSettings")
        dlgSettings.setWindowModality(Qt.ApplicationModal)
        dlgSettings.resize(501, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(dlgSettings.sizePolicy().hasHeightForWidth())
        dlgSettings.setSizePolicy(sizePolicy)
        dlgSettings.setAutoFillBackground(False)
        dlgSettings.setSizeGripEnabled(False)
        dlgSettings.setModal(True)
        self.buttonBox = QDialogButtonBox(dlgSettings)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(30, 558, 341, 32))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.horizontalLayoutWidget = QWidget(dlgSettings)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(0, 0, 501, 551))
        self.hlSettings = QHBoxLayout(self.horizontalLayoutWidget)
        self.hlSettings.setObjectName(u"hlSettings")
        self.hlSettings.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.hlSettings.setContentsMargins(10, 10, 10, 1)
        self.twSettings = QTabWidget(self.horizontalLayoutWidget)
        self.twSettings.setObjectName(u"twSettings")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.twSettings.sizePolicy().hasHeightForWidth())
        self.twSettings.setSizePolicy(sizePolicy1)
        self.twSettings.setMinimumSize(QSize(0, 0))
        self.twSettings.setTabShape(QTabWidget.Rounded)
        self.tabLatLon = QWidget()
        self.tabLatLon.setObjectName(u"tabLatLon")
        self.verticalLayoutWidget = QWidget(self.tabLatLon)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(0, 0, 481, 463))
        self.vlLatLon = QVBoxLayout(self.verticalLayoutWidget)
        self.vlLatLon.setObjectName(u"vlLatLon")
        self.vlLatLon.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.vlLatLon.setContentsMargins(5, 5, 5, 5)
        self.tbLatLonInfo = QTextBrowser(self.verticalLayoutWidget)
        self.tbLatLonInfo.setObjectName(u"tbLatLonInfo")
        sizePolicy2 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.tbLatLonInfo.sizePolicy().hasHeightForWidth())
        self.tbLatLonInfo.setSizePolicy(sizePolicy2)
        self.tbLatLonInfo.setMaximumSize(QSize(16777215, 16777215))

        self.vlLatLon.addWidget(self.tbLatLonInfo)

        self.gbLatLonFormat = QGroupBox(self.verticalLayoutWidget)
        self.gbLatLonFormat.setObjectName(u"gbLatLonFormat")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.gbLatLonFormat.sizePolicy().hasHeightForWidth())
        self.gbLatLonFormat.setSizePolicy(sizePolicy3)
        self.gbLatLonFormat.setMinimumSize(QSize(0, 67))
        self.horizontalLayoutWidget_6 = QWidget(self.gbLatLonFormat)
        self.horizontalLayoutWidget_6.setObjectName(u"horizontalLayoutWidget_6")
        self.horizontalLayoutWidget_6.setGeometry(QRect(0, 20, 471, 51))
        self.horizontalLayout_5 = QHBoxLayout(self.horizontalLayoutWidget_6)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(10, 2, 10, 2)
        self.rbDMS = QRadioButton(self.horizontalLayoutWidget_6)
        self.rbDMS.setObjectName(u"rbDMS")
        self.rbDMS.setChecked(True)

        self.horizontalLayout_5.addWidget(self.rbDMS)

        self.rbFloat = QRadioButton(self.horizontalLayoutWidget_6)
        self.rbFloat.setObjectName(u"rbFloat")

        self.horizontalLayout_5.addWidget(self.rbFloat)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_8)


        self.vlLatLon.addWidget(self.gbLatLonFormat)

        self.gbLatitude = QGroupBox(self.verticalLayoutWidget)
        self.gbLatitude.setObjectName(u"gbLatitude")
        sizePolicy1.setHeightForWidth(self.gbLatitude.sizePolicy().hasHeightForWidth())
        self.gbLatitude.setSizePolicy(sizePolicy1)
        self.gbLatitude.setMinimumSize(QSize(0, 88))
        self.horizontalLayoutWidget_2 = QWidget(self.gbLatitude)
        self.horizontalLayoutWidget_2.setObjectName(u"horizontalLayoutWidget_2")
        self.horizontalLayoutWidget_2.setGeometry(QRect(0, 20, 731, 71))
        self.hlLatitude = QHBoxLayout(self.horizontalLayoutWidget_2)
        self.hlLatitude.setSpacing(2)
        self.hlLatitude.setObjectName(u"hlLatitude")
        self.hlLatitude.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.hlLatitude.setContentsMargins(10, 4, 10, 4)
        self.sbLatDegrees = QSpinBox(self.horizontalLayoutWidget_2)
        self.sbLatDegrees.setObjectName(u"sbLatDegrees")
        self.sbLatDegrees.setMaximum(90)

        self.hlLatitude.addWidget(self.sbLatDegrees)

        self.lblLatDegrees = QLabel(self.horizontalLayoutWidget_2)
        self.lblLatDegrees.setObjectName(u"lblLatDegrees")

        self.hlLatitude.addWidget(self.lblLatDegrees)

        self.sbLatMinutes = QSpinBox(self.horizontalLayoutWidget_2)
        self.sbLatMinutes.setObjectName(u"sbLatMinutes")
        self.sbLatMinutes.setMaximum(59)

        self.hlLatitude.addWidget(self.sbLatMinutes)

        self.lblLatMinutes = QLabel(self.horizontalLayoutWidget_2)
        self.lblLatMinutes.setObjectName(u"lblLatMinutes")

        self.hlLatitude.addWidget(self.lblLatMinutes)

        self.sbLatSeconds = QSpinBox(self.horizontalLayoutWidget_2)
        self.sbLatSeconds.setObjectName(u"sbLatSeconds")
        self.sbLatSeconds.setMaximum(59)

        self.hlLatitude.addWidget(self.sbLatSeconds)

        self.lblLatSeconds = QLabel(self.horizontalLayoutWidget_2)
        self.lblLatSeconds.setObjectName(u"lblLatSeconds")

        self.hlLatitude.addWidget(self.lblLatSeconds)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.hlLatitude.addItem(self.horizontalSpacer)

        self.dsbLatFloat = QDoubleSpinBox(self.horizontalLayoutWidget_2)
        self.dsbLatFloat.setObjectName(u"dsbLatFloat")
        self.dsbLatFloat.setDecimals(8)
        self.dsbLatFloat.setMaximum(90.000000000000000)

        self.hlLatitude.addWidget(self.dsbLatFloat)

        self.lblLatFloat = QLabel(self.horizontalLayoutWidget_2)
        self.lblLatFloat.setObjectName(u"lblLatFloat")

        self.hlLatitude.addWidget(self.lblLatFloat)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.hlLatitude.addItem(self.horizontalSpacer_2)

        self.vlLatitude = QVBoxLayout()
        self.vlLatitude.setSpacing(2)
        self.vlLatitude.setObjectName(u"vlLatitude")
        self.vlLatitude.setContentsMargins(-1, -1, -1, 0)
        self.rbLatNorth = QRadioButton(self.horizontalLayoutWidget_2)
        self.rbLatNorth.setObjectName(u"rbLatNorth")
        self.rbLatNorth.setChecked(True)

        self.vlLatitude.addWidget(self.rbLatNorth)

        self.rbLatSouth = QRadioButton(self.horizontalLayoutWidget_2)
        self.rbLatSouth.setObjectName(u"rbLatSouth")

        self.vlLatitude.addWidget(self.rbLatSouth)


        self.hlLatitude.addLayout(self.vlLatitude)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.hlLatitude.addItem(self.horizontalSpacer_9)


        self.vlLatLon.addWidget(self.gbLatitude)

        self.gbLongitude = QGroupBox(self.verticalLayoutWidget)
        self.gbLongitude.setObjectName(u"gbLongitude")
        sizePolicy1.setHeightForWidth(self.gbLongitude.sizePolicy().hasHeightForWidth())
        self.gbLongitude.setSizePolicy(sizePolicy1)
        self.gbLongitude.setMinimumSize(QSize(0, 88))
        self.horizontalLayoutWidget_3 = QWidget(self.gbLongitude)
        self.horizontalLayoutWidget_3.setObjectName(u"horizontalLayoutWidget_3")
        self.horizontalLayoutWidget_3.setGeometry(QRect(0, 20, 740, 71))
        self.hlLongitude = QHBoxLayout(self.horizontalLayoutWidget_3)
        self.hlLongitude.setSpacing(2)
        self.hlLongitude.setObjectName(u"hlLongitude")
        self.hlLongitude.setContentsMargins(10, 4, 10, 4)
        self.sbLonDegrees = QSpinBox(self.horizontalLayoutWidget_3)
        self.sbLonDegrees.setObjectName(u"sbLonDegrees")
        self.sbLonDegrees.setMaximum(180)

        self.hlLongitude.addWidget(self.sbLonDegrees)

        self.lblLonDegrees = QLabel(self.horizontalLayoutWidget_3)
        self.lblLonDegrees.setObjectName(u"lblLonDegrees")

        self.hlLongitude.addWidget(self.lblLonDegrees)

        self.sbLonMinutes = QSpinBox(self.horizontalLayoutWidget_3)
        self.sbLonMinutes.setObjectName(u"sbLonMinutes")
        self.sbLonMinutes.setMaximum(59)

        self.hlLongitude.addWidget(self.sbLonMinutes)

        self.lblLonMinutes = QLabel(self.horizontalLayoutWidget_3)
        self.lblLonMinutes.setObjectName(u"lblLonMinutes")

        self.hlLongitude.addWidget(self.lblLonMinutes)

        self.sbLonSeconds = QSpinBox(self.horizontalLayoutWidget_3)
        self.sbLonSeconds.setObjectName(u"sbLonSeconds")
        self.sbLonSeconds.setMaximum(59)

        self.hlLongitude.addWidget(self.sbLonSeconds)

        self.lblLonSeconds = QLabel(self.horizontalLayoutWidget_3)
        self.lblLonSeconds.setObjectName(u"lblLonSeconds")

        self.hlLongitude.addWidget(self.lblLonSeconds)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.hlLongitude.addItem(self.horizontalSpacer_3)

        self.dsbLonFloat = QDoubleSpinBox(self.horizontalLayoutWidget_3)
        self.dsbLonFloat.setObjectName(u"dsbLonFloat")
        self.dsbLonFloat.setLayoutDirection(Qt.LeftToRight)
        self.dsbLonFloat.setDecimals(8)
        self.dsbLonFloat.setMaximum(180.000000000000000)
        self.dsbLonFloat.setSingleStep(0.000278000000000)
        self.dsbLonFloat.setValue(0.000000000000000)

        self.hlLongitude.addWidget(self.dsbLonFloat)

        self.lblLonFloat = QLabel(self.horizontalLayoutWidget_3)
        self.lblLonFloat.setObjectName(u"lblLonFloat")

        self.hlLongitude.addWidget(self.lblLonFloat)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.hlLongitude.addItem(self.horizontalSpacer_4)

        self.vlLongitude = QVBoxLayout()
        self.vlLongitude.setSpacing(2)
        self.vlLongitude.setObjectName(u"vlLongitude")
        self.vlLongitude.setContentsMargins(-1, -1, 0, -1)
        self.rbLonEast = QRadioButton(self.horizontalLayoutWidget_3)
        self.rbLonEast.setObjectName(u"rbLonEast")
        self.rbLonEast.setChecked(True)

        self.vlLongitude.addWidget(self.rbLonEast)

        self.rbLonWest = QRadioButton(self.horizontalLayoutWidget_3)
        self.rbLonWest.setObjectName(u"rbLonWest")

        self.vlLongitude.addWidget(self.rbLonWest)


        self.hlLongitude.addLayout(self.vlLongitude)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.hlLongitude.addItem(self.horizontalSpacer_10)


        self.vlLatLon.addWidget(self.gbLongitude)

        self.twSettings.addTab(self.tabLatLon, "")
        self.tabColors = QWidget()
        self.tabColors.setObjectName(u"tabColors")
        self.verticalLayoutWidget_2 = QWidget(self.tabColors)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.verticalLayoutWidget_2.setGeometry(QRect(-1, -1, 461, 501))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)
        self.tbColors = QTextBrowser(self.verticalLayoutWidget_2)
        self.tbColors.setObjectName(u"tbColors")
        sizePolicy1.setHeightForWidth(self.tbColors.sizePolicy().hasHeightForWidth())
        self.tbColors.setSizePolicy(sizePolicy1)
        self.tbColors.setMaximumSize(QSize(655360, 16777215))
        font = QFont()
        font.setPointSize(8)
        self.tbColors.setFont(font)

        self.verticalLayout.addWidget(self.tbColors)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.groupBox = QGroupBox(self.verticalLayoutWidget_2)
        self.groupBox.setObjectName(u"groupBox")
        self.horizontalLayoutWidget_4 = QWidget(self.groupBox)
        self.horizontalLayoutWidget_4.setObjectName(u"horizontalLayoutWidget_4")
        self.horizontalLayoutWidget_4.setGeometry(QRect(0, 20, 461, 91))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget_4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout.setContentsMargins(10, 2, 10, 2)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(2)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(2, 2, 2, 2)
        self.label = QLabel(self.horizontalLayoutWidget_4)
        self.label.setObjectName(u"label")

        self.horizontalLayout_3.addWidget(self.label)

        self.gvMinColor = QGraphicsView(self.horizontalLayoutWidget_4)
        self.gvMinColor.setObjectName(u"gvMinColor")
        sizePolicy.setHeightForWidth(self.gvMinColor.sizePolicy().hasHeightForWidth())
        self.gvMinColor.setSizePolicy(sizePolicy)
        self.gvMinColor.setMaximumSize(QSize(56, 56))

        self.horizontalLayout_3.addWidget(self.gvMinColor)

        self.pbChangeMinColor = QPushButton(self.horizontalLayoutWidget_4)
        self.pbChangeMinColor.setObjectName(u"pbChangeMinColor")

        self.horizontalLayout_3.addWidget(self.pbChangeMinColor)


        self.horizontalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(2)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(2, 2, 2, 2)
        self.label_2 = QLabel(self.horizontalLayoutWidget_4)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_4.addWidget(self.label_2)

        self.gvMaxColor = QGraphicsView(self.horizontalLayoutWidget_4)
        self.gvMaxColor.setObjectName(u"gvMaxColor")
        sizePolicy.setHeightForWidth(self.gvMaxColor.sizePolicy().hasHeightForWidth())
        self.gvMaxColor.setSizePolicy(sizePolicy)
        self.gvMaxColor.setMaximumSize(QSize(56, 56))

        self.horizontalLayout_4.addWidget(self.gvMaxColor)

        self.pbChangeMaxColor = QPushButton(self.horizontalLayoutWidget_4)
        self.pbChangeMaxColor.setObjectName(u"pbChangeMaxColor")

        self.horizontalLayout_4.addWidget(self.pbChangeMaxColor)


        self.horizontalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_5)


        self.verticalLayout_2.addWidget(self.groupBox)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(10, 10, 10, 10)
        self.groupBox_2 = QGroupBox(self.verticalLayoutWidget_2)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy4 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy4)
        self.horizontalLayoutWidget_5 = QWidget(self.groupBox_2)
        self.horizontalLayoutWidget_5.setObjectName(u"horizontalLayoutWidget_5")
        self.horizontalLayoutWidget_5.setGeometry(QRect(0, 19, 441, 81))
        self.horizontalLayout_2 = QHBoxLayout(self.horizontalLayoutWidget_5)
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_7)

        self.gvSpectrumColor = QGraphicsView(self.horizontalLayoutWidget_5)
        self.gvSpectrumColor.setObjectName(u"gvSpectrumColor")
        self.gvSpectrumColor.setMaximumSize(QSize(64, 64))

        self.horizontalLayout_2.addWidget(self.gvSpectrumColor)

        self.pbChangeSpecColor = QPushButton(self.horizontalLayoutWidget_5)
        self.pbChangeSpecColor.setObjectName(u"pbChangeSpecColor")

        self.horizontalLayout_2.addWidget(self.pbChangeSpecColor)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_6)


        self.verticalLayout_3.addWidget(self.groupBox_2)


        self.verticalLayout_2.addLayout(self.verticalLayout_3)


        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.twSettings.addTab(self.tabColors, "")
        self.tabSpectrum = QWidget()
        self.tabSpectrum.setObjectName(u"tabSpectrum")
        self.verticalLayoutWidget_3 = QWidget(self.tabSpectrum)
        self.verticalLayoutWidget_3.setObjectName(u"verticalLayoutWidget_3")
        self.verticalLayoutWidget_3.setGeometry(QRect(-1, -1, 481, 491))
        self.verticalLayout_4 = QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(5, 5, 5, 5)
        self.gbAudioFilter = QGroupBox(self.verticalLayoutWidget_3)
        self.gbAudioFilter.setObjectName(u"gbAudioFilter")
        self.gbAudioFilter.setCheckable(True)
        self.verticalLayoutWidget_4 = QWidget(self.gbAudioFilter)
        self.verticalLayoutWidget_4.setObjectName(u"verticalLayoutWidget_4")
        self.verticalLayoutWidget_4.setGeometry(QRect(9, 29, 451, 164))
        self.verticalLayout_5 = QVBoxLayout(self.verticalLayoutWidget_4)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.lblFilterType = QLabel(self.verticalLayoutWidget_4)
        self.lblFilterType.setObjectName(u"lblFilterType")

        self.horizontalLayout_6.addWidget(self.lblFilterType)

        self.cbFilterType = QComboBox(self.verticalLayoutWidget_4)
        self.cbFilterType.addItem("")
        self.cbFilterType.addItem("")
        self.cbFilterType.addItem("")
        self.cbFilterType.addItem("")
        self.cbFilterType.setObjectName(u"cbFilterType")

        self.horizontalLayout_6.addWidget(self.cbFilterType)

        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_11)


        self.verticalLayout_5.addLayout(self.horizontalLayout_6)

        self.lblFrequency = QLabel(self.verticalLayoutWidget_4)
        self.lblFrequency.setObjectName(u"lblFrequency")

        self.verticalLayout_5.addWidget(self.lblFrequency)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.lblLowF = QLabel(self.verticalLayoutWidget_4)
        self.lblLowF.setObjectName(u"lblLowF")
        self.lblLowF.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_7.addWidget(self.lblLowF)

        self.sbLowF = QSpinBox(self.verticalLayoutWidget_4)
        self.sbLowF.setObjectName(u"sbLowF")
        self.sbLowF.setMinimum(1)
        self.sbLowF.setMaximum(24000)
        self.sbLowF.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        self.sbLowF.setValue(1)

        self.horizontalLayout_7.addWidget(self.sbLowF)

        self.lblHighF = QLabel(self.verticalLayoutWidget_4)
        self.lblHighF.setObjectName(u"lblHighF")
        self.lblHighF.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_7.addWidget(self.lblHighF)

        self.sbHighF = QSpinBox(self.verticalLayoutWidget_4)
        self.sbHighF.setObjectName(u"sbHighF")
        self.sbHighF.setMinimum(2)
        self.sbHighF.setMaximum(24000)
        self.sbHighF.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        self.sbHighF.setValue(2)

        self.horizontalLayout_7.addWidget(self.sbHighF)

        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_12)


        self.verticalLayout_5.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_3 = QLabel(self.verticalLayoutWidget_4)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_8.addWidget(self.label_3)

        self.sbOrder = QSpinBox(self.verticalLayoutWidget_4)
        self.sbOrder.setObjectName(u"sbOrder")
        self.sbOrder.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.sbOrder.setMinimum(1)
        self.sbOrder.setStepType(QAbstractSpinBox.DefaultStepType)

        self.horizontalLayout_8.addWidget(self.sbOrder)

        self.horizontalSpacer_13 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_13)


        self.verticalLayout_5.addLayout(self.horizontalLayout_8)


        self.verticalLayout_4.addWidget(self.gbAudioFilter)

        self.gbWindowing = QGroupBox(self.verticalLayoutWidget_3)
        self.gbWindowing.setObjectName(u"gbWindowing")
        self.gbWindowing.setCheckable(True)
        self.horizontalLayoutWidget_7 = QWidget(self.gbWindowing)
        self.horizontalLayoutWidget_7.setObjectName(u"horizontalLayoutWidget_7")
        self.horizontalLayoutWidget_7.setGeometry(QRect(9, 29, 451, 41))
        self.horizontalLayout_9 = QHBoxLayout(self.horizontalLayoutWidget_7)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_4 = QLabel(self.horizontalLayoutWidget_7)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_9.addWidget(self.label_4)

        self.cbWindowFn = QComboBox(self.horizontalLayoutWidget_7)
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.addItem("")
        self.cbWindowFn.setObjectName(u"cbWindowFn")

        self.horizontalLayout_9.addWidget(self.cbWindowFn)

        self.horizontalSpacer_14 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_14)


        self.verticalLayout_4.addWidget(self.gbWindowing)

        self.cbFastViewUpdates = QCheckBox(self.verticalLayoutWidget_3)
        self.cbFastViewUpdates.setObjectName(u"cbFastViewUpdates")

        self.verticalLayout_4.addWidget(self.cbFastViewUpdates)

        self.twSettings.addTab(self.tabSpectrum, "")

        self.hlSettings.addWidget(self.twSettings)


        self.retranslateUi(dlgSettings)
        self.buttonBox.accepted.connect(dlgSettings.accept)
        self.buttonBox.rejected.connect(dlgSettings.reject)

        self.twSettings.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(dlgSettings)
    # setupUi

    def retranslateUi(self, dlgSettings):
        dlgSettings.setWindowTitle(QCoreApplication.translate("dlgSettings", u"QtMeter Settings", None))
#if QT_CONFIG(whatsthis)
        dlgSettings.setWhatsThis("")
#endif // QT_CONFIG(whatsthis)
#if QT_CONFIG(tooltip)
        self.buttonBox.setToolTip(QCoreApplication.translate("dlgSettings", u"Press OK to exit saving changes. Press Cancel to exit abandoning changes.", None))
#endif // QT_CONFIG(tooltip)
        self.tbLatLonInfo.setHtml(QCoreApplication.translate("dlgSettings", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Cantarell'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Set the location of the program on earth using latitude and longitude co-ordinates. This is used to calculate the times of sunrise and sunset to properly display the background of the long-time running meter by showing day/night sunrise/sunset parts in the correct places.</span></p></body></html>", None))
        self.gbLatLonFormat.setTitle(QCoreApplication.translate("dlgSettings", u"Latitude, longitude format", None))
#if QT_CONFIG(tooltip)
        self.rbDMS.setToolTip(QCoreApplication.translate("dlgSettings", u"Select to input Latitude/Longitude in degrees, minutes and seconds format", None))
#endif // QT_CONFIG(tooltip)
        self.rbDMS.setText(QCoreApplication.translate("dlgSettings", u"Degrees, Minutes, Seconds", None))
#if QT_CONFIG(tooltip)
        self.rbFloat.setToolTip(QCoreApplication.translate("dlgSettings", u"Select to input Latitude/Longitude in decimal degrees format", None))
#endif // QT_CONFIG(tooltip)
        self.rbFloat.setText(QCoreApplication.translate("dlgSettings", u"Floating Point", None))
        self.gbLatitude.setTitle(QCoreApplication.translate("dlgSettings", u"Latitude", None))
#if QT_CONFIG(tooltip)
        self.sbLatDegrees.setToolTip(QCoreApplication.translate("dlgSettings", u"Input the latitude whole degrees", None))
#endif // QT_CONFIG(tooltip)
        self.lblLatDegrees.setText(QCoreApplication.translate("dlgSettings", u"\u00b0", None))
#if QT_CONFIG(tooltip)
        self.sbLatMinutes.setToolTip(QCoreApplication.translate("dlgSettings", u"Input the latitude minutes of the degree value", None))
#endif // QT_CONFIG(tooltip)
        self.lblLatMinutes.setText(QCoreApplication.translate("dlgSettings", u"m", None))
#if QT_CONFIG(tooltip)
        self.sbLatSeconds.setToolTip(QCoreApplication.translate("dlgSettings", u"Input the latitude seconds of the minutes value", None))
#endif // QT_CONFIG(tooltip)
        self.lblLatSeconds.setText(QCoreApplication.translate("dlgSettings", u"s", None))
#if QT_CONFIG(tooltip)
        self.dsbLatFloat.setToolTip(QCoreApplication.translate("dlgSettings", u"Input the latitude as a decimal number of degrees", None))
#endif // QT_CONFIG(tooltip)
        self.lblLatFloat.setText(QCoreApplication.translate("dlgSettings", u"\u00b0", None))
#if QT_CONFIG(tooltip)
        self.rbLatNorth.setToolTip(QCoreApplication.translate("dlgSettings", u"Select to specify the latitude is North of the equator", None))
#endif // QT_CONFIG(tooltip)
        self.rbLatNorth.setText(QCoreApplication.translate("dlgSettings", u"North", None))
#if QT_CONFIG(tooltip)
        self.rbLatSouth.setToolTip(QCoreApplication.translate("dlgSettings", u"Select to specify the latitude is South of the equator", None))
#endif // QT_CONFIG(tooltip)
        self.rbLatSouth.setText(QCoreApplication.translate("dlgSettings", u"South", None))
        self.gbLongitude.setTitle(QCoreApplication.translate("dlgSettings", u"Longitude", None))
#if QT_CONFIG(tooltip)
        self.sbLonDegrees.setToolTip(QCoreApplication.translate("dlgSettings", u"Input the longitude whole degrees", None))
#endif // QT_CONFIG(tooltip)
        self.lblLonDegrees.setText(QCoreApplication.translate("dlgSettings", u"\u00b0", None))
#if QT_CONFIG(tooltip)
        self.sbLonMinutes.setToolTip(QCoreApplication.translate("dlgSettings", u"Input the longitude minutes of the degree value", None))
#endif // QT_CONFIG(tooltip)
        self.lblLonMinutes.setText(QCoreApplication.translate("dlgSettings", u"m", None))
#if QT_CONFIG(tooltip)
        self.sbLonSeconds.setToolTip(QCoreApplication.translate("dlgSettings", u"Input the longitude seconds of the minutes value", None))
#endif // QT_CONFIG(tooltip)
        self.lblLonSeconds.setText(QCoreApplication.translate("dlgSettings", u"s", None))
#if QT_CONFIG(tooltip)
        self.dsbLonFloat.setToolTip(QCoreApplication.translate("dlgSettings", u"Input the longitude as a decimal number of degrees", None))
#endif // QT_CONFIG(tooltip)
        self.lblLonFloat.setText(QCoreApplication.translate("dlgSettings", u"\u00b0", None))
#if QT_CONFIG(tooltip)
        self.rbLonEast.setToolTip(QCoreApplication.translate("dlgSettings", u"Select to specify the longitude is East of Greenwich", None))
#endif // QT_CONFIG(tooltip)
        self.rbLonEast.setText(QCoreApplication.translate("dlgSettings", u"East", None))
#if QT_CONFIG(tooltip)
        self.rbLonWest.setToolTip(QCoreApplication.translate("dlgSettings", u"Select to specify the longitude is West of Greenwich", None))
#endif // QT_CONFIG(tooltip)
        self.rbLonWest.setText(QCoreApplication.translate("dlgSettings", u"West", None))
        self.twSettings.setTabText(self.twSettings.indexOf(self.tabLatLon), QCoreApplication.translate("dlgSettings", u"Lat/Lon", None))
        self.tbColors.setHtml(QCoreApplication.translate("dlgSettings", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Cantarell'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Select the colors to be used in the data graphs. The maximum signal level line, the minimum signal level line and the color used to display the signal spectrum over time.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:11pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; "
                        "margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">For the signal spectrum, the color is used with the alpha channel (transparency) used to indicate the intensity of the signal at the given frequency position. So, the less transparent the point in the spectrum the more intense the signal at that frequency and time.</p></body></html>", None))
        self.groupBox.setTitle(QCoreApplication.translate("dlgSettings", u"Signal Level Lines:", None))
        self.label.setText(QCoreApplication.translate("dlgSettings", u"Minimum:", None))
        self.pbChangeMinColor.setText(QCoreApplication.translate("dlgSettings", u"Change", None))
        self.label_2.setText(QCoreApplication.translate("dlgSettings", u"Maximum:", None))
        self.pbChangeMaxColor.setText(QCoreApplication.translate("dlgSettings", u"Change", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("dlgSettings", u"Spectrum:", None))
        self.pbChangeSpecColor.setText(QCoreApplication.translate("dlgSettings", u"Change", None))
        self.twSettings.setTabText(self.twSettings.indexOf(self.tabColors), QCoreApplication.translate("dlgSettings", u"Colors", None))
#if QT_CONFIG(tooltip)
        self.gbAudioFilter.setToolTip(QCoreApplication.translate("dlgSettings", u"Enable and configure to filter the audio spectrum display", None))
#endif // QT_CONFIG(tooltip)
        self.gbAudioFilter.setTitle(QCoreApplication.translate("dlgSettings", u"Audio Filter:", None))
        self.lblFilterType.setText(QCoreApplication.translate("dlgSettings", u"Filter type:", None))
        self.cbFilterType.setItemText(0, QCoreApplication.translate("dlgSettings", u"Low pass", None))
        self.cbFilterType.setItemText(1, QCoreApplication.translate("dlgSettings", u"High pass", None))
        self.cbFilterType.setItemText(2, QCoreApplication.translate("dlgSettings", u"Band pass", None))
        self.cbFilterType.setItemText(3, QCoreApplication.translate("dlgSettings", u"Band stop", None))

#if QT_CONFIG(tooltip)
        self.cbFilterType.setToolTip(QCoreApplication.translate("dlgSettings", u"Select a filter type", None))
#endif // QT_CONFIG(tooltip)
        self.lblFrequency.setText(QCoreApplication.translate("dlgSettings", u"Frequencies:", None))
        self.lblLowF.setText(QCoreApplication.translate("dlgSettings", u"Low:", None))
#if QT_CONFIG(tooltip)
        self.sbLowF.setToolTip(QCoreApplication.translate("dlgSettings", u"<html><head/><body><p>Select a minimum cut-off frequency for the filter. Take care, if the value is too close to the band edge, the filter can fail.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.lblHighF.setText(QCoreApplication.translate("dlgSettings", u"High:", None))
#if QT_CONFIG(tooltip)
        self.sbHighF.setToolTip(QCoreApplication.translate("dlgSettings", u"<html><head/><body><p>Select a maximum frequecy for the filter. Take care, if the value is too close to the band edge, the filter can fail.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("dlgSettings", u"Order:", None))
#if QT_CONFIG(tooltip)
        self.sbOrder.setToolTip(QCoreApplication.translate("dlgSettings", u"<html><head/><body><p>Set the filter order. Higher numbers mean steeper roll-off.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.gbWindowing.setTitle(QCoreApplication.translate("dlgSettings", u"Windowing", None))
        self.label_4.setText(QCoreApplication.translate("dlgSettings", u"Window function:", None))
        self.cbWindowFn.setItemText(0, QCoreApplication.translate("dlgSettings", u"Boxcar", None))
        self.cbWindowFn.setItemText(1, QCoreApplication.translate("dlgSettings", u"Triangular", None))
        self.cbWindowFn.setItemText(2, QCoreApplication.translate("dlgSettings", u"Blackman", None))
        self.cbWindowFn.setItemText(3, QCoreApplication.translate("dlgSettings", u"Hamming", None))
        self.cbWindowFn.setItemText(4, QCoreApplication.translate("dlgSettings", u"Hann", None))
        self.cbWindowFn.setItemText(5, QCoreApplication.translate("dlgSettings", u"Bartlett", None))
        self.cbWindowFn.setItemText(6, QCoreApplication.translate("dlgSettings", u"Flat top", None))
        self.cbWindowFn.setItemText(7, QCoreApplication.translate("dlgSettings", u"Parzen", None))
        self.cbWindowFn.setItemText(8, QCoreApplication.translate("dlgSettings", u"Bohman", None))
        self.cbWindowFn.setItemText(9, QCoreApplication.translate("dlgSettings", u"Blackman-Harris", None))
        self.cbWindowFn.setItemText(10, QCoreApplication.translate("dlgSettings", u"Nuttall", None))
        self.cbWindowFn.setItemText(11, QCoreApplication.translate("dlgSettings", u"Bartlett-Hann", None))
        self.cbWindowFn.setItemText(12, QCoreApplication.translate("dlgSettings", u"Cosine (simple)", None))
        self.cbWindowFn.setItemText(13, QCoreApplication.translate("dlgSettings", u"Exponential", None))
        self.cbWindowFn.setItemText(14, QCoreApplication.translate("dlgSettings", u"Tukey", None))
        self.cbWindowFn.setItemText(15, QCoreApplication.translate("dlgSettings", u"Taylor", None))
        self.cbWindowFn.setItemText(16, QCoreApplication.translate("dlgSettings", u"Lanczos", None))

#if QT_CONFIG(tooltip)
        self.cbFastViewUpdates.setToolTip(QCoreApplication.translate("dlgSettings", u"<html><head/><body><p>With this unchecked, the duration of the horizontal updates of the signal level and spectrum views is one day. Sometimes it helps to see faster updates, check this checkbox to do that but the horizontal position no longer represents time-of-day. If fast updates are enabled then later disabled you can restore time-of-day position of the data by stopping and starting updates.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.cbFastViewUpdates.setText(QCoreApplication.translate("dlgSettings", u"Use fast view updates (background does not represet time-of-day)", None))
        self.twSettings.setTabText(self.twSettings.indexOf(self.tabSpectrum), QCoreApplication.translate("dlgSettings", u"Spectrum", None))
    # retranslateUi

