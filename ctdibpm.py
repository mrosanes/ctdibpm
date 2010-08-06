#!/usr/bin/env python

#############################################################################
##
## Copyright (C) 2004-2005 Trolltech AS. All rights reserved.
##
## This file is part of the example classes of the Qt Toolkit.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following information to ensure GNU
## General Public Licensing requirements will be met:
## http://www.trolltech.com/products/qt/opensource.html
##
## If you are unsure which license is appropriate for your use, please
## review the following information:
## http://www.trolltech.com/products/qt/licensing.html or contact the
## sales department at sales@trolltech.com.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
#############################################################################

# Alba imports
import PyTango
import tau

# UI imports
from ui_libera import Ui_MainWindow
from ui_settime import Ui_SetTime
from ui_synchronize import Ui_Synchronize
from ui_statusbar import Ui_StatusBar
from ui_gainscheme import Ui_GainScheme
from ui_about import Ui_About
from ui_log import Ui_Log
from liberatab import *
from screenshot import Screenshot

# Standard python imports
import sys
import time
import string
import calendar
import os
import webbrowser
from datetime import datetime
from optparse import OptionParser


# Enumeration Values
SWITCHES_DIRECT         = 0
SWITCHES_AUTO           = 1

SWITCH_DIRECT           = 15
SWITCH_AUTO             = 255

CLOCK_SOURCE_INTERNAL   = 0
CLOCK_SOURCE_EXTERNAL   = 1

DSC_OFF                 = 0
DSC_UNITY               = 1
DSC_AUTO                = 2
DSC_SAVE                = 3

INTERLOCK_MODE_OFF      = 0
INTERLOCK_MODE_ON       = 1
INTERLOCK_MODE_ON_GAIN  = 2

OVERF_DUR_MAX           = 1050
ACTIVE_WIDGET           = 1

# Constants
SERVER_NAME   = "LiberaAcquisator/*"
CLASS_NAME    = "LiberaAcquisator"

#Default save/load paths and files
DEFAULT_PATH = "/tmp/bootservertmp/operator/"
GAIN_FILENAME = DEFAULT_PATH + "gain.conf"

DOC_URL = "http://www.cells.es/Intranet/Divisions/Computing/Controls/Help/DI/BPM/"

class MainWindow(QtGui.QMainWindow):
        def __init__(self, parent=None,liberaDeviceName=None):
                QtGui.QWidget.__init__(self, parent)

                # Get graphical information
                self.ui = Ui_MainWindow()
                self.ui.setupUi(self)

                # Add statusbar info to toolbar to save space. Insted of adding this to the toolBar,
                # you can add it to the status bar. You'll have to modify the main ui file to include
                # a status bar and then substitute self.ui.toolBar.addWidget(self.LiberaStatusBar) by:
                #self.ui.statusbar.addPermanentWidget(self.LiberaStatusBar)
                self.LiberaStatusBar = LiberaStatusBar(self)
                self.ui.toolBar.addWidget(self.LiberaStatusBar)

                # Initialize devices and devices names
                self.dp = None
                self.dsPyName = None
                self.dsCppName = None

                # 'File' Menu Actions
                QtCore.QObject.connect(self.ui.actionLiberaStart,   QtCore.SIGNAL("triggered()"), self.actionLiberaStart)
                QtCore.QObject.connect(self.ui.actionLiberaStop ,   QtCore.SIGNAL("triggered()"), self.actionLiberaStop)
                QtCore.QObject.connect(self.ui.actionLiberaRestart, QtCore.SIGNAL("triggered()"), self.actionLiberaRestart)
                QtCore.QObject.connect(self.ui.actionLiberaReboot,  QtCore.SIGNAL("triggered()"), self.actionLiberaReboot)
                QtCore.QObject.connect(self.ui.actionLiberaDSInit,  QtCore.SIGNAL("triggered()"), self.actionLiberaDSInit)
                QtCore.QObject.connect(self.ui.actionOpen,          QtCore.SIGNAL("triggered()"), self.actionOpen)
                QtCore.QObject.connect(self.ui.actionSave,          QtCore.SIGNAL("triggered()"), self.actionSave)
                QtCore.QObject.connect(self.ui.actionPrint,         QtCore.SIGNAL("triggered()"), self.actionPrint)
                QtCore.QObject.connect(self.ui.actionScreenshot,    QtCore.SIGNAL("triggered()"), self.actionScreenshot)
                QtCore.QObject.connect(self.ui.actionQuit,          QtCore.SIGNAL("triggered()"), self.actionQuit)

                # 'Unit' Menu Actions
                QtCore.QObject.connect(self.ui.actionConnectToLibera, QtCore.SIGNAL("triggered()"), self.actionConnectToLibera)
                QtCore.QObject.connect(self.ui.actionSynchronize, QtCore.SIGNAL("triggered()"), self.actionSynchronize)

                # 'Mode' Menu Actions
                QtCore.QObject.connect(self.ui.actionADCTab, QtCore.SIGNAL("triggered()"), self.actionADCTab)
                QtCore.QObject.connect(self.ui.actionDDTab1, QtCore.SIGNAL("triggered()"), self.actionDDTab1)
                QtCore.QObject.connect(self.ui.actionDDTab2,   QtCore.SIGNAL("triggered()"), self.actionDDTab2)
                QtCore.QObject.connect(self.ui.actionPMTab1, QtCore.SIGNAL("triggered()"), self.actionPMTab1)
                QtCore.QObject.connect(self.ui.actionPMTab2,   QtCore.SIGNAL("triggered()"), self.actionPMTab2)
                QtCore.QObject.connect(self.ui.actionSATab1, QtCore.SIGNAL("triggered()"), self.actionSATab1)
                QtCore.QObject.connect(self.ui.actionSATab2,   QtCore.SIGNAL("triggered()"), self.actionSATab2)
                QtCore.QObject.connect(self.ui.actionFATab1, QtCore.SIGNAL("triggered()"), self.actionFATab1)
                QtCore.QObject.connect(self.ui.actionFATab2,   QtCore.SIGNAL("triggered()"), self.actionFATab2)
                QtCore.QObject.connect(self.ui.actionGain,    QtCore.SIGNAL("triggered()"), self.actionGain)
                QtCore.QObject.connect(self.ui.actionLog,    QtCore.SIGNAL("triggered()"), self.actionLog)

                # 'Help' Menu Actions
                QtCore.QObject.connect(self.ui.actionHelp, QtCore.SIGNAL("triggered()"), self.actionHelp)
                QtCore.QObject.connect(self.ui.actionAbout, QtCore.SIGNAL("triggered()"), self.actionAbout)

                # 'EP' Buttons
                QtCore.QObject.connect(self.ui.EPget    , QtCore.SIGNAL("clicked()"), self.EPget)
                QtCore.QObject.connect(self.ui.EPset    , QtCore.SIGNAL("clicked()"), self.EPset)
                QtCore.QObject.connect(self.ui.EPsettime, QtCore.SIGNAL("clicked()"), self.EPsettime)
                QtCore.QObject.connect(self.ui.EPagc    , QtCore.SIGNAL("clicked()"), self.EPsetgain)

                # EP Get and Set buttons will become red when any EP value changed.
                QtCore.QObject.connect(self.ui.EPzhigh, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPxoffset, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPzoffset, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPqoffset, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPkx, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPkz, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPswitches, QtCore.SIGNAL("activated(const int)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPdsc, QtCore.SIGNAL("activated(const int)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPgain, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPagc, QtCore.SIGNAL("clicked()"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPmode, QtCore.SIGNAL("activated(const int)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPgainlimit, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPxhigh, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPxlow, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPzhigh, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPzlow, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPoverflim, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPoverfdur, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPclocksource, QtCore.SIGNAL("activated(const int)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPswitchdelay, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPofftunemode, QtCore.SIGNAL("activated(const int)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPofftuneunits, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPpmoffset, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPtrigdelay, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPmaflength, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)
                QtCore.QObject.connect(self.ui.EPmafdelay, QtCore.SIGNAL("textChanged(const QString &)"), self.EPActivateWarning)

                #Keep DD single acquisition check boxes synchronized
                QtCore.QObject.connect(self.ui.DDcheckSingle1, QtCore.SIGNAL("toggled(bool)"), self.ui.DDcheckSingle2, QtCore.SLOT("setChecked(bool)") )
                QtCore.QObject.connect(self.ui.DDcheckSingle2, QtCore.SIGNAL("toggled(bool)"), self.ui.DDcheckSingle1, QtCore.SLOT("setChecked(bool)") )

                #Keep DD Decimation acquisition check boxes synchronized
                #QtCore.QObject.connect(self.ui.DDDecimation1, QtCore.SIGNAL("toggled(bool)"), self.ui.DDDecimation2, QtCore.SLOT("setChecked(bool)") )
                #QtCore.QObject.connect(self.ui.DDDecimation2, QtCore.SIGNAL("toggled(bool)"), self.ui.DDDecimation1, QtCore.SLOT("setChecked(bool)") )

                # Add Gain Scheme tab
                self.gainScheme = GainScheme(self)
                self.ui.tabWidget.insertTab(self.ui.tabWidget.count(),self.gainScheme,self.tr("Gain Scheme"))

                # Add log tab
                self.log = Log(self)
                self.ui.tabWidget.insertTab(self.ui.tabWidget.count(),self.log,self.tr("Log"))

                # 'EP' Buttons
                QtCore.QObject.connect(self.ui.EPget, QtCore.SIGNAL("clicked()"), self.EPget)

                # Initialize time window
                self.settime = SetTime(self)
                # Initialize time synchronization window
                self.synctime = SyncTime(self)
                # Initialize screenshot window
                self.screenshot = Screenshot()

                self.setTab()

                #Connect to libera number or libera device (if any specified)
                if liberaDeviceName:
                    self.connectLibera(liberaDeviceName)
                else:
                    pass

        def setTab(self):

                # Set ADC tab
                ADCTabWidgets = {
                "tabname"       : "ADC",
                "plot1"         : [self.ui.ADCplot, "ADCChannelA","ADCChannelB","ADCChannelC","ADCChannelD"],
                "plot2"         : [None, None],
                "start"         : [self.ui.ADCstart, "ADCAcquire"],
                "stop"          : [self.ui.ADCstop, "ADCStop"],
                "save"          : [None, None],
                "resetPM"       : [None, None],
                "samples"       : [self.ui.ADCsamples, "ADCNSamples"],
                "samplesRB"     : [self.ui.ADCsamplesRB, 'ADCNSamples'],
                "loops"         : [self.ui.ADCloops, "ADCNLoops"],
                "loopsRB"       : [self.ui.ADCloopsRB, 'ADCNLoops'],
                "triggercounts" : [self.ui.ADCtriggers, "ADCLoopCounter"],
                "peakA"         : [self.ui.ADCPeakA, "ADCChannelAPeak"],
                "peakB"         : [self.ui.ADCPeakB, "ADCChannelBPeak"],
                "peakC"         : [self.ui.ADCPeakC, "ADCChannelCPeak"],
                "peakD"         : [self.ui.ADCPeakD, "ADCChannelDPeak"],
                "singleLoop"    : [self.ui.ADCcheckSingle, None],
                "timestamp"     : [None, None],
#                "version"       : [None, None],
#                "ontrigger"     : [None, None],
#                "raw"           : [None, None],
#                "decimation"    : [None, None],
#                "decimationRB"  : [None, None],
#                "timesleep"     : [None, None],
#                "firstcount"    : [None, None],
#                "lastcount"     : [None, None],
#                "savefunc"      : [None, "ADCSave"]
                }
                self.ADCTab = LiberaTab(ADCTabWidgets)

                # Set DDrate tab
                DDTab1Widgets = {
                "tabname"       : "DDXZVolt",
                "plot1"         : [self.ui.DDplotA1,"XPosDD","ZPosDD"],
                "plot2"         : [self.ui.DDplotA2,"VaDD","VbDD","VcDD","VdDD"],
                "start"         : [self.ui.DDstart1, 'DDAcquire'],
                "stop"          : [self.ui.DDstop1, "DDStop"],
                "save"          : [None, None],
                "samples"       : [self.ui.DDNSamples1, 'DDNSamples'],
                "samplesRB"     : [self.ui.DDNSamplesRB1, 'DDNSamples'],
                "loops"         : [self.ui.DDloops1, 'DDNLoops'],
                "loopsRB"       : [self.ui.DDloopsRB1, 'DDNLoops'],
                "triggercounts" : [self.ui.DDTriggers1, 'DDLoopCounter'],
                "resetPM"       : [None, None],
                "decimation"    : [self.ui.DDDecimation1, 'DDDecimationFactor'],
                "decimationRB"  : [self.ui.DDDecimationRB1, 'DDDecimationFactor'],
                "singleLoop"    : [self.ui.DDcheckSingle1, None],
                "timestamp"     : [None, None],
                }
                self.DDTab1 = LiberaTab(DDTab1Widgets)

                # Set DDrate tab
                DDTab2Widgets = {
                "tabname"       : "DDQSum",
                "plot1"         : [self.ui.DDplotB1, "QuadDD"],
                "plot2"         : [self.ui.DDplotB2, "SumDD"],
                "start"         : [self.ui.DDstart2, "DDAcquire"],
                "singleLoop"    : [self.ui.DDcheckSingle2, None],
                "stop"          : [self.ui.DDstop2, "DDStop"],
                "save"          : [None, None],
                "resetPM"       : [None, None],
                "samples"       : [self.ui.DDNSamples2, 'DDNSamples'],
                "samplesRB"     : [self.ui.DDNSamplesRB2, 'DDNSamples'],
                "loops"         : [self.ui.DDloops2, 'DDNLoops'],
                "loopsRB"       : [self.ui.DDloopsRB2, 'DDNLoops'],
                "triggercounts" : [self.ui.DDTriggers2, 'DDLoopCounter'],
                "decimation"    : [self.ui.DDDecimation2, 'DDDecimationFactor'],
                "decimationRB"  : [self.ui.DDDecimationRB2, 'DDDecimationFactor'],
                "singleLoop"    : [self.ui.DDcheckSingle1, None],
                "timestamp"     : [None, None],
                }
                self.DDTab2 = LiberaTab(DDTab2Widgets)

                # Set PM tab
                PMTab1Widgets = {
                "tabname"       : "PMXZVolt",
                "plot1"         : [self.ui.PMplotA1,"XPosPM","ZPosPM"],
                "plot2"         : [self.ui.PMplotA2,"VaPM","VbPM","VcPM","VdPM"],
                "start"         : [self.ui.PMstart1, "PMAcquire"],
                "stop"          : [None, None],
                "save"          : [None, None],
                "resetPM"       : [None, None],
                #"save"          : [self.ui.save_4, ACTIVE_WIDGET],
                "samples"       : [self.ui.PMNSamples1, "PMNSamples"],
                "samplesRB"     : [self.ui.PMNSamplesRB1, "PMNSamples"],
                "loops"         : [None, None],
#                "triggercounts" : [None, None],
                "resetPM"       : [self.ui.PMreset1, "PMResetFlag"],
                "singleLoop"    : [None, None],
                "timestamp"     : [None, None],
#                "version"       : [None, None],
                #"ontrigger"     : [None, None],
                #"peakA"         : [None, None],
                #"peakB"         : [None, None],
                #"peakC"         : [None, None],
                #"peakD"         : [None, None],
                #"raw"           : [None, None],
                #"decimation"    : [None, None],
                #"decimationRB"    : [None, None],
                #"temperaturestamp"   : [None, None],
                #"timesleep"     : [None, None],
                #"firstcount"    : [None, None],
                #"lastcount"     : [None, None],
                #"filename"      : [None, "PMFileName"],
                #"savefunc"      : [None, "PMSave"]
                }
                self.PMTab1 = LiberaTab(PMTab1Widgets)

                # Set PM tab
                PMTab2Widgets = {
                "tabname"       : "PMQSum",
                "plot1"         : [self.ui.PMplotB1, "QuadPM"],
                "plot2"         : [self.ui.PMplotB2, "SumPM"],
                "start"         : [self.ui.PMstart2, "PMAcquire"],
                "stop"          : [None, None],
                "save"          : [None, None],
                "resetPM"       : [None, None],
#                "save"          : [self.ui.save_5, ACTIVE_WIDGET],
#                "version"       : [self.ui.version_5, None],
                "samples"       : [self.ui.PMNSamples2, "PMNSamples"],
                "samplesRB"     : [self.ui.PMNSamplesRB2, "PMNSamples"],
#                "loops"         : [None, None],
                "singleLoop"    : [None, None],
                "timestamp"     : [None, None],
#                "version"       : [None, None],
#                "triggercounts" : [None, None],
#                "resetPM"       : [self.ui.PMreset2, "PMResetFlag"],
#                "ontrigger"     : [None, None],
#                "peakA"         : [None, None],
#                "peakB"         : [None, None],
#                "peakC"         : [None, None],
#                "peakD"         : [None, None],
#                "raw"           : [None, None],
#                "decimation"    : [None, None],
#                "decimationRB"    : [None, None],
#                "temperaturestamp"   : [None, None],
#                "timesleep"     : [None, None],
#                "firstcount"    : [None, None],
#                "lastcount"     : [None, None],
#                "filename"      : [None, "PMFileName"],
#                "savefunc"      : [None, "PMSave"]
                }
                self.PMTab2 = LiberaTab(PMTab2Widgets)

                # Set SA tab
                SATab1Widgets = {
                "tabname"       : "SAXZVolt",
                "plot1"         : [self.ui.SAplotA1, "XPosSA","ZPosSA"],
                "plot2"         : [self.ui.SAplotA2, "VaSA","VbSA","VcSA","VdSA"],
                "start"         : [self.ui.SAstart1, "SAAcquire"], 
                "stop"          : [self.ui.SAstop1, "SAStop"],
                "save"          : [None, None],
                "resetPM"       : [None, None],
#                "save"          : [self.ui.save_6, ACTIVE_WIDGET],
#                "version"       : [self.ui.version_6, None],   

                "samples"       : [self.ui.SANSamples1, "SANSamples"],
                "samplesRB"     : [self.ui.SANSamplesRB1, "SANSamples"],
#                "loops"         : [None, None],
#                "triggercounts" : [None, None],
                "singleLoop"    : [None, None],
                "timestamp"     : [self.ui.SAtimestamp1, "SATimestamp"],
                "timestampRB"   : [self.ui.SAtimestampRB1, "SATimestamp"],
#                "version"       : [None, None],
#                "ontrigger"     : [None, None],
#                "peakA"         : [None, None],
#                "peakB"         : [None, None],
#                "peakC"         : [None, None],
#                "peakD"         : [None, None],
#                "raw"           : [None, None],
#                "decimation"    : [None, None],
#                "decimationRB"    : [None, None],
#                "temperaturestamp"   : [None, None],
                "timesleep"     : [self.ui.SAtimesleep1, "SASleep"],
                "timesleepRB"   : [self.ui.SAtimesleepRB1, "SASleep"],
#                "firstcount"    : [None, None],
#                "lastcount"     : [None, None],
                "filename"      : [None, "SAFileName"],
                "savefunc"      : [None, None]
                }
                self.SATab1 = LiberaTab(SATab1Widgets)

                # Set SA tab
                SATab2Widgets = {
                "tabname"       : "SAQSum",
                "plot1"         : [self.ui.SAplotB1, "QuadSA"],
                "plot2"         : [self.ui.SAplotB2, "SumSA"],
                "start"         : [self.ui.SAstart2, "SAAcquire"], 
                "stop"          : [self.ui.SAstop2, "SAStop"],
                "save"          : [None, None],
                "resetPM"       : [None, None],
                "singleLoop"    : [None, None],
                "timestamp"     : [None, None],
#                "version"       : [None, None],
#                "timestamp"     : [self.ui.timestamp_7, "SATimestamp"],
                "samples"       : [self.ui.SANSamples2, "SANSamples"],
                "samplesRB"     : [self.ui.SANSamplesRB2, "SANSamples"],
#                "loops"         : [None, None],
#                "triggercounts" : [None, None],
#                "ontrigger"     : [None, None],
#                "peakA"         : [None, None],
#                "peakB"         : [None, None],
#                "peakC"         : [None, None],
#                "peakD"         : [None, None],
#                "raw"           : [None, None],
#                "decimation"    : [None, None],
#                "decimationRB"  : [None, None],
#                "temperaturestamp"   : [None, None],
                "timestamp"     : [self.ui.SAtimestamp2, "SATimestamp"],
                "timestampRB"   : [self.ui.SAtimestampRB2, "SATimestamp"],
                "timesleep"     : [self.ui.SAtimesleep2, "SASleep"],
                "timesleepRB"   : [self.ui.SAtimesleepRB2, "SASleep"],
#                "firstcount"    : [None, None],
#                "lastcount"     : [None, None],
                "filename"      : [None, "SAFileName"],
                "savefunc"      : [None, None]
                }
                self.SATab2 = LiberaTab(SATab2Widgets)

                # Set FA tab
                FATab1Widgets = {
                "tabname"       : "FAXZVolt",
                "plot1"         : [self.ui.FAplotA1, "XPosFA","ZPosFA"],
                "plot2"         : [self.ui.FAplotA2, "VaFA","VbFA","VcFA","VdFA"],
                "start"         : [self.ui.FAstart1, "FAAcquire"], 
                "stop"     	    : [None, None],
                "save"          : [self.ui.FAsave1, ACTIVE_WIDGET],
                "resetPM"       : [None, None],
                "timestamp"     : [None, None],
                "samples"       : [self.ui.FANSamples1, "FANSamples"],
                "samplesRB"     : [self.ui.FANSamplesRB1, "FANSamples"],
                "singleLoop"    : [None, None],
#                "loops"         : [None, None],
#                "triggercounts" : [None, None],
#                "resetPM"       : [None, None],
#                "ontrigger"     : [None, None],
#                "peakA"         : [None, None],
#                "peakB"         : [None, None],
#                "peakC"         : [None, None],
#                "peakD"         : [None, None],
#                "raw"           : [None, None],
#                "decimation"    : [None, None],
#                "decimationRB"  : [None, None],
#                "temperaturestamp"   : [None, None],
#                "timesleep"     : [None, None],
#                "firstcount"    : [self.ui.firstcount_8, None],
#                "lastcount"     : [self.ui.lastcount_8, None],
#                "filename"      : [None, "FAFileName"],
#                "savefunc"      : [None, "FASave"]
                }
                self.FATab1 = LiberaTab(FATab1Widgets)

                FATab2Widgets = {
                "tabname"       : "FAQSum",
                "plot1"         : [self.ui.FAplotB1, "QuadFA"],
                "plot2"         : [self.ui.FAplotB2, "SumFA"],
                "start"         : [self.ui.FAstart2, "FAAcquire"],
                "stop"          : [None, None],
                "save"          : [self.ui.FAsave2, ACTIVE_WIDGET],
                "resetPM"       : [None, None],
                "timestamp"     : [None, None],
                "samples"       : [self.ui.FANSamples2, "FANSamples"],
                "samplesRB"     : [self.ui.FANSamplesRB2, "FANSamples"],
                "singleLoop"    : [None, None],
#                "loops"         : [None, None],
#                "triggercounts" : [None, None],
#                "resetPM"       : [None, None],
#                "ontrigger"     : [None, None],
#                "peakA"         : [None, None],
#                "peakB"         : [None, None],
#                "peakC"         : [None, None],
#                "peakD"         : [None, None],
#                "raw"           : [None, None],
#                "decimation"    : [None, None],
#                "decimationRB"  : [None, None],
#                "temperaturestamp"   : [None, None],
#                "timesleep"     : [None, None],
#                "firstcount"    : [None, None],
#                "lastcount"     : [None, None],
#                "filename"      : [None, "FAFileName"],
#                "savefunc"      : [None, "FASave"]
                }
                self.FATab2 = LiberaTab(FATab2Widgets)

        def connectLibera(self, dev_name):
            """This function will connect all the window components to the libera received as
            parameter. This parameter may be an integer (hence meaning a libera number, from
            which we'll get the underlying device server) or a string (meaning we want to
            connect directly to the python device server)"""

            db = PyTango.Database()
            libnumCppRelation = db.get_property("BPM",["DeviceParameters"])
            cppPyRelation     = db.get_class_property("LiberaAcquisator",["CppDS"])

            def getCppFromNumber(liberaNumber):
                """This function will get the cpp ds name from the libera number"""
                dsCppName = ""
                for relation in libnumCppRelation["DeviceParameters"]:
                    tokens = relation.split(":")
                    if str("Libera%03d" % liberaNumber).lower() == (tokens[2]).lower():
                        dsCppName = tokens[0]
                        break
                return dsCppName

            def getCppFromPy(pyDsName):
                """This function will get the cpp ds name from the py ds name"""
                cppPyName = ""
                for relation in cppPyRelation["CppDS"]:
                    tokens = relation.split("@")
                    if tokens[0].lower().endswith(pyDsName.lower()):
                        cppPyName = tokens[1]
                        break
                return cppPyName


            def getPyFromCpp(cppDsName):
                """This function will get the py ds name from the cpp ds name"""
                dsPyName = ""
                for relation in cppPyRelation["CppDS"]:
                    tokens = relation.split("@")
                    if tokens[1].lower().endswith(cppDsName.lower()):
                        dsPyName = tokens[0]
                        break
                return dsPyName

            #Function start
            dsCppNameBack = self.dsCppName
            dsPyNameBack = self.dsPyName
            self.dsCppName = ""
            self.dsPyName  = ""
#            if type(numberOrDS) == int:
#                numberSpecified = True
#            elif type(numberOrDS) == str:
#                numberSpecified = False
#            else:
#                raise ValueError, "Expected int or str parameter. Got: " + repr(type(numberOrDS))

            try:
                # For each Libera there are two ds. We have to get this information from tango db
                # We have three important entities:
                # - libera number (which will also be used as libera ip hostname)
                # - python ds that corresponds to this libera number
                # - cpp ds that is used by the python ds
                # The relationship between them is stored in a quite messy way in the database. We have
                # libera number <-> cpp ds relationship in "DeviceParameters" property of "BPM" db
                # property. On the other hand, we have cpp <--> python relationship in "CppDS" property
                # of class property of LiberaAcquisator class

                self.dsPyName = dev_name
                self.dsCppName = getCppFromPy(self.dsPyName)
                windowTitle = self.dsPyName
                if self.dsCppName == "":
                    QtGui.QMessageBox.warning(self,
                        self.tr("Device server not located"),
                        self.tr("Unable to find out which underlying cpp device server is serving this python device server. Please, check \"CppDS\" class property on tango database for \"LiberaAcquisator\" class for " + "\"" + self.dsPyName + "\""))
                    return False


                # Connect to the Device Server and check its state, keep backup of the previous dp; in
                # case of any problem, we'll keep connected to it.
                dpBack = self.dp
                self.dp = PyTango.DeviceProxy(self.dsPyName)
                if (self.dp.state() != PyTango.DevState.ON):
                    a = QtGui.QMessageBox.question(self, 
                            self.tr("Device server failed"),
                            self.tr("The status of the device server for this libera is NOT ON."
                            " Are you sure you want to continue?"),
                            QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                    if (a == QtGui.QMessageBox.No):
                        self.dsCppName = dsCppNameBack
                        self.dsPyName = dsPyNameBack
                        self.dp = dpBack
                        return False

                # Connect Tango Values for Environmental Parameters (Warning! This may raise exception)
                self.EPget()

                # Connect hardware values for StatusBar
                self.LiberaStatusBar.connectLibera(self.dsCppName, self.dsPyName)

                # Clear gain schem tab contents and inform it of the ds change
                self.gainScheme.reset(self.dp)

                # Clear log and inform it of the ds change
                self.log.reset(self.dsCppName)

                # Connect tango values for each tab
                print 80*"*", self.dsPyName
                self.ADCTab.connectLibera(self.dsPyName)
                self.DDTab1.connectLibera(self.dsPyName)
                self.DDTab2.connectLibera(self.dsPyName)
                self.PMTab1.connectLibera(self.dsPyName)
                self.PMTab2.connectLibera(self.dsPyName)
                self.SATab1.connectLibera(self.dsPyName)
                self.SATab2.connectLibera(self.dsPyName)
                self.FATab1.connectLibera(self.dsPyName)
                self.FATab2.connectLibera(self.dsPyName)

                # Set main window's title
                self.setWindowTitle(windowTitle)

            except PyTango.DevFailed, e:
                QtGui.QMessageBox.critical(None, "Connect to libera" , repr(e))
                self.dsCppName = dsCppNameBack
                self.dsPyName = dsPyNameBack
                self.dp = dpBack
                return False

        def EPsetgain(self):
                if(self.ui.EPagc.isChecked()):
                        self.ui.EPgain.setEnabled(False)
                else:
                        self.ui.EPgain.setEnabled(True)

        def EPcheckIncompatibility(self):
                # FB: storage or boost?
                if(float(self.ui.EPoverfdur.text()) > OVERF_DUR_MAX):
                        a = QtGui.QMessageBox.warning(self, 
                                self.tr("Incompatible setting"),
                                self.tr("Interlock OverF Dur is greater than 1050.\nCheck it!"))
                        if(a == QtGui.QMessageBox.Ok):
                                return

                if(self.ui.EPdsc.currentIndex() == DSC_AUTO) and (self.ui.EPswitches.currentIndex() != SWITCHES_AUTO):
                        a = QtGui.QMessageBox.question(self, 
                                self.tr("Incompatible setting"),
                                self.tr("DSC is set to AUTO\nSwitch has to be set to AUTO"),
                                QtGui.QMessageBox.Yes,
                                QtGui.QMessageBox.No)
                        if(a == QtGui.QMessageBox.Yes):
                                self.ui.EPswitches.setCurrentIndex(SWITCHES_AUTO)

                if(self.ui.EPswitches.currentIndex() == SWITCHES_DIRECT) and (self.ui.EPdsc.currentIndex() != DSC_OFF):
                        a = QtGui.QMessageBox.question(self, 
                                self.tr("Incompatible setting"),
                                self.tr("Switches is set to DIRECT\nDSC has to be set to OFF"),
                                QtGui.QMessageBox.Yes,
                                QtGui.QMessageBox.No)
                        if(a == QtGui.QMessageBox.Yes):
                                self.ui.EPdsc.setCurrentIndex(DSC_OFF)

        def setSwitches(self, v):
                if v == SWITCH_AUTO:
                        self.ui.EPswitches.setCurrentIndex(1)
                else:
                        self.ui.EPswitches.setCurrentIndex(0)

        def getSwitches(self):
                i = self.ui.EPswitches.currentIndex()
                if i==1:
                        return SWITCH_AUTO
                else:
                        return SWITCH_DIRECT

        def setInterlockMode(self, v):
                if v == 0:
                        self.ui.EPmode.setCurrentIndex(0)
                elif v == 1:
                        self.ui.EPmode.setCurrentIndex(1)
                elif v == 3:
                        self.ui.EPmode.setCurrentIndex(2)
                else:
                        self.ui.EPmode.setCurrentIndex(0)

        def getInterlockMode(self):
                i = self.ui.EPmode.currentIndex()
                if i==0:
                        return 0
                elif i==1:
                        return 1
                elif i==2:
                        return 3
                else:
                        return 0

        def EPget(self):
            """This function gets environment parameters from the hardware. It calls ParamGet of PyDS,
            which will get parameters from CppDS from hardware. This may cause EPGet to throw exceptions,
            so be sure you know how to handle them"""
            try:
                    attrs_name = [ "Xoffset","Zoffset", "Qoffset", "Kx", "Kz", "Switches", "Gain",
                            "AGCEnabled", "DSCMode","InterlockMode", "GainLimit", "Xhigh", "Xlow",
                            "Zhigh", "Zlow", "OverflowLimit","OverflowDuration","ExternalSwitching",
                            "SwitchingDelay", "CompensateTune", "OffsetTune", "PMOffset", "ExternalTriggerDelay"]
                    self.hasMAFSupport = self.dp.read_attribute("HasMAFSupport").value
                    if self.hasMAFSupport:
                        attrs_name.extend(["MAFLength", "MAFDelay"])
                        self.ui.EPmaflength.setEnabled(True)
                        self.ui.EPmafdelay.setEnabled(True)
                    else:
                        self.ui.EPmaflength.clear()
                        self.ui.EPmaflength.setEnabled(False)
                        self.ui.EPmafdelay.clear()
                        self.ui.EPmafdelay.setEnabled(False)

                    self.dp.command_inout("ParamGet")
                    attrs_value_objects = self.dp.read_attributes(attrs_name)
                    attrs_values = [ av.value for av in attrs_value_objects ]
                    pairs = dict(zip(attrs_name, attrs_values))
                    self.ui.EPxoffset.setText(str(pairs["Xoffset"]))
                    self.ui.EPzoffset.setText(str(pairs["Zoffset"]))
                    self.ui.EPqoffset.setText(str(pairs["Qoffset"]))
                    self.ui.EPkx.setText(str(pairs["Kx"]))
                    self.ui.EPkz.setText(str(pairs["Kz"]))
                    self.setSwitches(int(pairs["Switches"]))
                    if int(pairs["AGCEnabled"]):
                        self.ui.EPagc.setCheckState(Qt.Qt.Checked)
                    else:
                        self.ui.EPagc.setCheckState(Qt.Qt.Unchecked)
                    self.ui.EPgain.setText(str(pairs["Gain"]))
                    self.EPsetgain() #enable/disable gain depending on agc
                    self.ui.EPdsc.setCurrentIndex(int(pairs["DSCMode"]))
                    self.ui.EPclocksource.setCurrentIndex(int(pairs["ExternalSwitching"]))
                    self.ui.EPclocksource.setEnabled(True)
                    self.ui.EPswitchdelay.setText(str(pairs["SwitchingDelay"]))
                    self.ui.EPswitchdelay.setEnabled(True)
                    self.ui.EPofftunemode.setCurrentIndex(int(pairs["CompensateTune"]))
                    self.ui.EPofftunemode.setEnabled(True)
                    self.ui.EPofftuneunits.setText(str(pairs["OffsetTune"]))
                    self.ui.EPofftuneunits.setEnabled(True)
                    self.ui.EPpmoffset.setText(str(pairs["PMOffset"]))
                    self.ui.EPpmoffset.setEnabled(True)
                    self.ui.EPtrigdelay.setText(str(pairs["ExternalTriggerDelay"]))
                    self.ui.EPtrigdelay.setEnabled(True)
                    if self.hasMAFSupport:
                        self.ui.EPmaflength.setText(str(pairs["MAFLength"]))
                        self.ui.EPmaflength.setEnabled(True)
                        self.ui.EPmafdelay.setText(str(pairs["MAFDelay"]))
                        self.ui.EPmafdelay.setEnabled(True)
                    self.setInterlockMode(int(pairs["InterlockMode"]))
                    self.ui.EPgainlimit.setText(str(pairs["GainLimit"]))
                    self.ui.EPxhigh.setText(str(pairs["Xhigh"]))
                    self.ui.EPxlow.setText(str(pairs["Xlow"]))
                    self.ui.EPzhigh.setText(str(pairs["Zhigh"]))
                    self.ui.EPzlow.setText(str(pairs["Zlow"]))
                    self.ui.EPoverflim.setText(str(pairs["OverflowLimit"]))
                    self.ui.EPoverfdur.setText(str(pairs["OverflowDuration"]))

                    self.EPResetWarning()
            except PyTango.DevFailed, e:
                    QtGui.QMessageBox.critical(None, "EPget" , repr(e))
                    raise

        def EPset(self):
            if (self.dp == None):
                QtGui.QMessageBox.warning(self,self.tr("Set environment parameters"),
                                               self.tr("No connection to any libera"))
                return
            answer = QtGui.QMessageBox.question(self,
                    self.tr("Set environment parameters"),
                    self.tr("This will stop any running acquisition. It will also reinitialize underlying"\
                            "C++ device server.\nAre you sure you want to continue?"),
                    QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if (answer == QtGui.QMessageBox.No):
                return False
            try:
                attrs_name_sw = [ "Xoffset","Zoffset","Qoffset","Kx", "Kz","InterlockMode","GainLimit","Xhigh","Xlow","Zhigh","Zlow","OverflowLimit","OverflowDuration" ]
                attrs_name_hw = ["Switches","AGCEnabled","Gain","DSCMode","ExternalSwitching", "SwitchingDelay", "CompensateTune","OffsetTune", "PMOffset", "ExternalTriggerDelay"]
                if self.hasMAFSupport:
                    attrs_name_hw.extend(["MAFLength","MAFDelay"])

                write_values_sw = [
                self.ui.EPxoffset.displayText(),
                self.ui.EPzoffset.displayText(),
                self.ui.EPqoffset.displayText(),
                self.ui.EPkx.displayText(),
                self.ui.EPkz.displayText(),
                self.getInterlockMode(),
                self.ui.EPgainlimit.displayText(),
                self.ui.EPxhigh.displayText(),
                self.ui.EPxlow.displayText(),
                self.ui.EPzhigh.displayText(),
                self.ui.EPzlow.displayText(),
                self.ui.EPoverflim.displayText(),
                self.ui.EPoverfdur.displayText()
                ]

                write_values_hw = [
                self.getSwitches(),
                (self.ui.EPagc.checkState()==Qt.Qt.Checked),
                self.ui.EPgain.displayText(),
                self.ui.EPdsc.currentIndex(),
                ]

                #if requesting to activate AGC, gain must not be set or an error will occur
                if (self.ui.EPagc.checkState()==Qt.Qt.Checked):
                    write_values_hw.remove(self.ui.EPgain.displayText())
                    attrs_name_hw.remove("Gain")

                write_values_hw.extend(
                    [
                    bool(self.ui.EPclocksource.currentIndex()),
                    self.ui.EPswitchdelay.displayText(),
                    self.ui.EPofftunemode.currentIndex(),
                    self.ui.EPofftuneunits.displayText(),
                    self.ui.EPpmoffset.displayText(),
                    self.ui.EPtrigdelay.displayText()
                    ])

                if self.hasMAFSupport:
                    write_values_hw.extend(
                        [
                        self.ui.EPmaflength.displayText(),
                        self.ui.EPmafdelay.displayText()
                        ])

                self.dp.command_inout("ADCStop")
                self.dp.command_inout("DDStop")

                #read attributes (will be reused to write_attributes)
                attrs_value_objects_sw = self.dp.read_attributes(attrs_name_sw)
                attrs_value_objects_hw = self.dp.read_attributes(attrs_name_hw)

                sw_changed = False #if no changes, nothing will be done

                #---------------------------------------------------------------
                #first step: set sw attributes
                #first of all, determine if something changed and prepare 
                for i in range(len(write_values_sw)):
                    oldValue = attrs_value_objects_sw[i].value
                    tipo = type(oldValue)
                    newValue = tipo(write_values_sw[i])
                    if oldValue != newValue:
                        attrs_value_objects_sw[i].value = newValue
                        sw_changed = True

                if sw_changed:
                    self.dp.write_attributes([[attrs_name_sw[i],attrs_value_objects_sw[i].value] for i in range(len(attrs_name_sw))])
                    self.dp.command_inout("ParamSet") #this forces the writing to cpp ds

                #---------------------------------------------------------------
                #second step: set hw attributes (if we reached here, there were no exception, so OK.
                for i in range (len(write_values_hw)):
                    oldAttr = attrs_value_objects_hw[i]
                    tipo = type(oldAttr.value)
                    newValue = tipo(write_values_hw[i])
                    #write attribute only if really changed
                    if oldAttr.value != newValue:
                        self.dp.write_attribute(attrs_name_hw[i],newValue)

                #everything seems to have worked correctly, so reset warning
                self.EPResetWarning()

            except PyTango.DevFailed, e:
                QtGui.QMessageBox.critical(None, "EPset" , repr(e))
            finally:
                    self.EPget()
            return

        def EPsettime(self):
                self.settime.connect(self.dp)
                self.settime.show()

        def EPActivateWarning(self):
            palette = QtGui.QPalette()

            brush = QtGui.QBrush(QtGui.QColor(255,0,0))
            brush.setStyle(QtCore.Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Button,brush)

            brush = QtGui.QBrush(QtGui.QColor(255,0,0))
            brush.setStyle(QtCore.Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Button,brush)

            brush = QtGui.QBrush(QtGui.QColor(255,0,0))
            brush.setStyle(QtCore.Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Button,brush)
            self.ui.EPget.setPalette(palette)
            self.ui.EPset.setPalette(palette)

        def EPResetWarning(self):
            palette = QtGui.QPalette()

            brush = QtGui.QBrush(QtGui.QColor(238,238,238))
            brush.setStyle(QtCore.Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Button,brush)

            brush = QtGui.QBrush(QtGui.QColor(238,238,238))
            brush.setStyle(QtCore.Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Button,brush)

            brush = QtGui.QBrush(QtGui.QColor(238,238,238))
            brush.setStyle(QtCore.Qt.SolidPattern)
            palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Button,brush)
            self.ui.EPget.setPalette(palette)
            self.ui.EPset.setPalette(palette)

        def actionADCTab(self):
                self.ui.tabWidget.setCurrentIndex(0)

        def actionDDTab1(self):
                self.ui.tabWidget.setCurrentIndex(1)

        def actionDDTab2(self):
                self.ui.tabWidget.setCurrentIndex(2)

        def actionPMTab1(self):
                self.ui.tabWidget.setCurrentIndex(3)

        def actionPMTab2(self):
                self.ui.tabWidget.setCurrentIndex(4)

        def actionSATab1(self):
                self.ui.tabWidget.setCurrentIndex(5)

        def actionSATab2(self):
                self.ui.tabWidget.setCurrentIndex(6)

        def actionFATab1(self):
                self.ui.tabWidget.setCurrentIndex(7)

        def actionFATab2(self):
                self.ui.tabWidget.setCurrentIndex(8)

        def actionGain(self):
                self.ui.tabWidget.setCurrentIndex(9)

        def actionLog(self):
                self.ui.tabWidget.setCurrentIndex(10)

        def actionConnectToLibera(self):
            db = PyTango.Database()
            deviceList = list(db.get_device_name(SERVER_NAME,CLASS_NAME).value_string)
            name, ok = QtGui.QInputDialog.getItem(self, self.tr("Libera Selection"),
                                            self.tr("Libera device name:"),deviceList)
            if ok:
                self.connectLibera(str(name.toAscii()))

        def actionSynchronize(self):
            self.synctime.show()

        def actionLiberaStart(self):
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Libera Start"),
                        self.tr("Are you sure?"),
                        QtGui.QMessageBox.Yes,
                        QtGui.QMessageBox.No)
                if(a == QtGui.QMessageBox.Yes):
                        self.dp.command_inout("LiberaStart")

        def actionLiberaStop(self):
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Libera Stop"),
                        self.tr("Are you sure?"),
                        QtGui.QMessageBox.Yes,
                        QtGui.QMessageBox.No)
                if(a == QtGui.QMessageBox.Yes):
                        self.dp.command_inout("LiberaStop")
                elif(a == QtGui.QMessageBox.No):
                        print "Libera Stop No"

        def actionLiberaRestart(self):
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Libera Restart"),
                        self.tr("Are you sure?"),
                        QtGui.QMessageBox.Yes,
                        QtGui.QMessageBox.No)
                if(a == QtGui.QMessageBox.Yes):
                        self.dp.command_inout("LiberaRestart")
                elif(a == QtGui.QMessageBox.No):
                        print "Libera Restart No"

        def actionLiberaReboot(self):
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Libera Reboot. This will take some time"),
                        self.tr("Are you sure?"),
                        QtGui.QMessageBox.Yes,
                        QtGui.QMessageBox.No)
                if(a == QtGui.QMessageBox.Yes):
                        self.dp.command_inout("LiberaReboot")
                elif(a == QtGui.QMessageBox.No):
                        print "Libera Reboot No"

        def actionLiberaDSInit(self):
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Libera Device server init."),
                        self.tr("Are you sure?"),
                        QtGui.QMessageBox.Yes,
                        QtGui.QMessageBox.No)
                if(a == QtGui.QMessageBox.Yes):
                        self.dp.command_inout("RunDSCommand","init")
                elif(a == QtGui.QMessageBox.No):
                        print "Libera Init No"

        def actionOpen(self):
                fileName = QtGui.QFileDialog.getOpenFileName(self,
                    self.tr("Open Environmental Parameters"), DEFAULT_PATH,
                    self.tr("DAT (*.dat)"))
                if fileName.isEmpty():
                    return

                textEdit = self.openFile(fileName)
                aa = string.split(str(textEdit.toPlainText()))
                column0 = list()
                column1 = list()
                for i in range(len(aa)):
                        if((i%2)==0):
                                column0.append(aa[i])
                        if((i%2)==1):
                                column1.append(aa[i])

                numParam = 25
                if (len(column0) != numParam):
                    QtGui.QMessageBox.warning(self, self.tr("Opening File ..."),
                            self.tr("The number of parameters has to be " + repr(numParam)) )
                    return

                # Set data (from File) in the Environmental Parameters Box 
                self.ui.EPxoffset.setText(str(column1[0]))
                self.ui.EPzoffset.setText(str(column1[1]))
                self.ui.EPqoffset.setText(str(column1[2]))
                self.ui.EPkx.setText(str(column1[3]))
                self.ui.EPkz.setText(str(column1[4]))
                self.setSwitches(int(column1[5]))
                self.ui.EPgain.setText(str(column1[6]))
                if( int(column1[7]) == 1):
                        self.ui.EPagc.setCheckState(Qt.Qt.Checked)
                else:
                        self.ui.EPagc.setCheckState(Qt.Qt.Unchecked)
                self.EPsetgain() #disable/enable gain depending on agc
                self.ui.EPdsc.setCurrentIndex(int(column1[8]))
                self.ui.EPmode.setCurrentIndex(int(column1[9]))
                self.ui.EPgainlimit.setText(str(column1[10]))
                self.ui.EPxhigh.setText(str(column1[11]))
                self.ui.EPxlow.setText(str(column1[12]))
                self.ui.EPzhigh.setText(str(column1[13]))
                self.ui.EPzlow.setText(str(column1[14]))
                self.ui.EPoverflim.setText(str(column1[15]))
                self.ui.EPoverfdur.setText(str(column1[16]))
                self.ui.EPclocksource.setCurrentIndex(int(column1[17]))
                self.ui.EPswitchdelay.setText(str((column1[18])))
                self.ui.EPofftunemode.setCurrentIndex(int(column1[19]))
                self.ui.EPofftuneunits.setText(str(column1[20]))
                self.ui.EPpmoffset.setText(str(column1[21]))
                self.ui.EPtrigdelay.setText(str(column1[22]))
                self.ui.EPmaflength.setText(str(column1[23]))
                self.ui.EPmafdelay.setText(str(column1[24]))
                self.EPActivateWarning()

        def openFile(self, fileName):
                fileEnv = QtCore.QFile(fileName)
                if not fileEnv.open( QtCore.QFile.ReadOnly | QtCore.QFile.Text):
                    QtGui.QMessageBox.warning(self, self.tr("Recent Files"),
                            self.tr("Cannot read file %1:\n%2.").arg(fileName).arg(file.errorString()))
                    return
                instr = QtCore.QTextStream(fileEnv)
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                textEdit = QtGui.QTextEdit()
                textEdit.setPlainText(instr.readAll())
                QtGui.QApplication.restoreOverrideCursor()

                return textEdit 


        def actionSave(self):
                # Get file name from Save dialog
                fileName = QtGui.QFileDialog.getSaveFileName(self,
                    self.tr("Save Environmental Parameters"), DEFAULT_PATH + "EP.dat",
                    self.tr("DAT (*.dat)"))
                if fileName.isEmpty():
                    return False

                return self.saveFile(fileName)


        def saveFile(self, fileName):
                """Save configuration of the Libera to a file."""
                confFile = QtCore.QFile(fileName)
                ## I think that is all....
                if not confFile.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
                    QtGui.QMessageBox.warning(self, self.tr("Application"),
                                self.tr("Cannot write file %1:\n%2.").arg(fileName).arg(confFile.errorString()))
                    return False

                outf = QtCore.QTextStream(confFile)
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

                # Save (to File) all data shown in the Environmental Parameters Box
                outf << "xoffset        \t"  << self.ui.EPxoffset.text()                << "\n"
                outf << "zoffset        \t"  << self.ui.EPzoffset.text()                << "\n"
                outf << "qoffset        \t"  << self.ui.EPqoffset.text()                << "\n"
                outf << "kx             \t"  << self.ui.EPkx.text()                     << "\n"
                outf << "kz             \t"  << self.ui.EPkz.text()                     << "\n"
                outf << "switches       \t"  << self.getSwitches()                      << "\n"
                outf << "gain           \t"  << self.ui.EPgain.text()                  << "\n"
                outf << "agc            \t"  << self.ui.EPagc.isChecked()               << "\n" 
                outf << "dsc            \t"  << self.ui.EPdsc.currentIndex()            << "\n"
                outf << "mode           \t"  << self.ui.EPmode.currentIndex()           << "\n"
                outf << "gainlimit      \t"  << self.ui.EPgainlimit.text()              << "\n"
                outf << "xhigh          \t"  << self.ui.EPxhigh.text()                  << "\n"
                outf << "xlow           \t"  << self.ui.EPxlow.text()                   << "\n"
                outf << "zhigh          \t"  << self.ui.EPzhigh.text()                  << "\n"
                outf << "zlow           \t"  << self.ui.EPzlow.text()                   << "\n"
                outf << "overflim       \t"  << self.ui.EPoverflim.text()               << "\n"
                outf << "overfdur       \t"  << self.ui.EPoverfdur.text()               << "\n"
                outf << "clocksource    \t"  << self.ui.EPclocksource.currentIndex()    << "\n"
                outf << "switchdelay    \t"  << self.ui.EPswitchdelay.text()            << "\n"
                outf << "offtunemode    \t"  << self.ui.EPofftunemode.currentIndex()    << "\n"
                outf << "offtuneunits   \t"  << self.ui.EPofftuneunits.text()           << "\n"
                outf << "pmoffset       \t"  << self.ui.EPpmoffset.text()               << "\n"
                outf << "trigdelay      \t"  << self.ui.EPtrigdelay()                   << "\n"
                outf << "maflength      \t"  << self.ui.EPmaflength()                   << "\n"
                outf << "mafdelay       \t"  << self.ui.EPmafdelay()                    << "\n"

                QtGui.QApplication.restoreOverrideCursor()

                return True

        def actionPrint(self):
                index = self.ui.tabWidget.currentIndex()
                fileName = self.ui.tabWidget.tabText(index).toAscii()

                if index == 0:
                    self.ui.ADCplot.exportPrint()
                elif index == 1:
                    self.ui.DDplotA1.exportPrint()
                    self.ui.DDplotA2.exportPrint()
                elif index == 2:
                    self.ui.DDplotB1.exportPrint()
                    self.ui.DDplotB2.exportPrint()
                elif index == 3:
                    self.ui.PMplotA1.exportPrint()
                    self.ui.PMplotA2.exportPrint()
                elif index == 4:
                    self.ui.PMplotB1.exportPrint()
                    self.ui.PMplotB2.exportPrint()
                elif index == 5:
                    self.ui.SAplotA1.exportPrint()
                    self.ui.SAplotA2.exportPrint()
                elif index == 6:
                    self.ui.SAplotB1.exportPrint()
                    self.ui.SAplotB2.exportPrint()
                elif index == 7:    
                    self.ui.FAplotA1.exportPrint()
                    self.ui.FAplotA2.exportPrint()
                elif index == 8:
                    self.ui.FAplotB1.exportPrint()
                    self.ui.FAplotB2.exportPrint()
                elif index == 9:
                    self.gainScheme.print_()
                elif index == 10:
                    self.log.print_()
                    pass
                else:
                    QtGui.QMessageBox.warning(self, self.tr("Application"),"Invalid tab")

                return

        def actionScreenshot(self):
                self.screenshot.show()

        def actionHelp(self):
            webbrowser.open(DOC_URL)

        def actionAbout(self):
            self.aboutDialog = QtGui.QDialog()
            self.about = Ui_About()
            self.about.setupUi(self.aboutDialog)
            self.aboutDialog.exec_()

        def actionQuit(self):
            self.close()


class LiberaStatusBar(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.ui = Ui_StatusBar()
        self.ui.setupUi(self)

    def connectLibera(self, cppDevice, pyDevice):
        try:
                attrName = cppDevice +"/HWTemperature"
                self.ui.HwTempLabel.setModel(attrName)
                attrName = cppDevice +"/HWTemperature?configuration=label"
                self.ui.HwTempConfigLabel.setModel(attrName)

                attrName = cppDevice +"/Fan1Speed"
                self.ui.Fan1Label.setModel(attrName)
                attrName = cppDevice +"/Fan1Speed?configuration=label"
                self.ui.Fan1ConfigLabel.setModel(attrName)

                attrName = cppDevice +"/Fan2Speed"
                self.ui.Fan2Label.setModel(attrName)
                attrName = cppDevice +"/Fan2Speed?configuration=label"
                self.ui.Fan2ConfigLabel.setModel(attrName)

                attrName = cppDevice +"/SCPLLStatus"
                self.ui.SCPLLLabel.setModel(attrName)
                attrName = cppDevice +"/SCPLLStatus?configuration=label"
                self.ui.SCPLLConfigLabel.setModel(attrName)

                attrName = cppDevice +"/MCPLLStatus"
                self.ui.MCPLLLabel.setModel(attrName)
                attrName = cppDevice +"/MCPLLStatus?configuration=label"
                self.ui.MCPLLConfigLabel.setModel(attrName)

                attrName = cppDevice +'/PMNotified'
                self.ui.PMFlagLed.setModel(attrName)
                attrName = cppDevice + '/PMNotified?configuration=label'
                self.ui.PMConfigLabel.setModel(attrName)

                attrName = cppDevice +'/State'
                self.ui.LiberaCppStateLED.setModel(attrName)
                attrName = cppDevice + '/State?configuration=label'
                self.ui.LiberaStateConfigLabel.setModel(attrName)

                #connect PyDevice state
                attrName = pyDevice +'/State'
                self.ui.LiberaPyStateLED.setModel(attrName)

                #finally, connect state label and widget
                self.ui.liberaStateLabel.setText(cppDevice)

        except Exception, e:
                raise

    ## The minimum size of the widget (a limit for the user)
    #def minimumSizeHint(self):
        #return QtCore.QSize(950, 40)

    ## The default size of the widget
    #def sizeHint(self):
        #return QtCore.QSize(950, 40)



class SetTime(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)

        self.ui = Ui_SetTime()
        self.ui.setupUi(self)

        # FB cambiar
        self.ui.MachineTimeLineEdit.setText(str(11))
        self.ui.MachinePhaseLineEdit.setText(str(22))

        QtCore.QObject.connect(self.ui.SetButton, QtCore.SIGNAL("clicked()"), self.Set)

        QtCore.QObject.connect(self.ui.MachineTimeLineEdit , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MachineTimeLineEdit , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MachineTimeLineEdit , QtCore.SIGNAL("textChanged()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MachineTimeLineEdit , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MachinePhaseLineEdit, QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MachinePhaseLineEdit, QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.YearLineEdit     , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.YearLineEdit     , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MonthLineEdit    , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MonthLineEdit    , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.DayLineEdit      , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.DayLineEdit      , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.HourLineEdit     , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.HourLineEdit     , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MinuteLineEdit   , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.MinuteLineEdit   , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.SecondLineEdit   , QtCore.SIGNAL("returnPressed()"), self.UpdateMessage)
        QtCore.QObject.connect(self.ui.SecondLineEdit   , QtCore.SIGNAL("editingFinished()"), self.UpdateMessage)

    def connect(self, dp):
        self.dp = dp

    def UpdateMessage(self):
        # MT:MP:YYYYMMDDhhmm.ss
        v1 = self.ui.MachineTimeLineEdit.text()
        v2 = self.ui.MachinePhaseLineEdit.text()
        v3 = self.ui.YearLineEdit.text()
        v4 = self.ui.MonthLineEdit.text() 
        v5 = self.ui.DayLineEdit.text()
        v6 = self.ui.HourLineEdit.text()
        v7 = self.ui.MinuteLineEdit.text() 
        v8 = self.ui.SecondLineEdit.text() 

        msg = v1+'.'+v2+':'+v3+v4+v5+v6+v7+'.'+v8 

        self.ui.LiberaMessageLineEdit.setText(str(msg)) 

    def Set(self):
        v1 = self.ui.MachineTimeLineEdit.text()
        v2 = self.ui.MachinePhaseLineEdit.text()
        v3 = self.ui.YearLineEdit.text()
        v4 = self.ui.MonthLineEdit.text() 
        v5 = self.ui.DayLineEdit.text()
        v6 = self.ui.HourLineEdit.text()
        v7 = self.ui.MinuteLineEdit.text() 
        v8 = self.ui.SecondLineEdit.text() 
        msg = str( (v1+'.'+v2+':'+v3+v4+v5+v6+v7+'.'+v8).toAscii() )
        self.ui.LiberaMessageLineEdit.setText(msg)

        # Check parameters
        answer = QtGui.QMessageBox.Yes
        if ((int(v2)<0) or (int(v2)>95)):
            answer = QtGui.QMessageBox.question(self,
                    self.tr("Machine Phase"),
                    self.tr("Machine Phase exceeds booster units. Are you sure you want to proceed?"),
                    QtGui.QMessageBox.Yes,
                    QtGui.QMessageBox.No)
        try:
            datetime(int(v3),int(v4),int(v4),int(v6),int(v7),int(v8))
        except ValueError:
            answer = QtGui.QMessageBox.warning(self,
                    self.tr("Invalid date"),
                    self.tr("The date is invalid. Please enter it again."),
                    QtGui.QMessageBox.Ok)

        #If the answer is Ok or the validation passed, then set libera time
        if (answer == QtGui.QMessageBox.Yes):
            try:
                self.dp.command_inout("SetTimeOnNextTrigger",msg)
                self.hide()
            except PyTango.DevFailed, e:
                QtGui.QMessageBox.critical(None, "EPget" , repr(e))

    def GetGMtime(self):
        t = time.gmtime()

        self.ui.YearLineEdit.setText(str("%04.0f" %t.tm_year)) 
        self.ui.MonthLineEdit.setText(str("%02.0f" %t.tm_mon))
        self.ui.DayLineEdit.setText(str("%02.0f" %t.tm_mday))
        self.ui.HourLineEdit.setText(str("%02.0f" %t.tm_hour))
        self.ui.MinuteLineEdit.setText(str("%02.0f" %t.tm_min))
        self.ui.SecondLineEdit.setText(str("%02.0f" %t.tm_sec))

        self.UpdateMessage()

    def showEvent(self, event):
        self.GetGMtime()

class SyncTime(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_Synchronize()
        self.ui.setupUi(self)
        self.setup()
        QtCore.QObject.connect(self.ui.setButton,      QtCore.SIGNAL("clicked()"), self.setTimes)
        QtCore.QObject.connect(self.ui.clearButton,    QtCore.SIGNAL("clicked()"), self.clearContents)
        QtCore.QObject.connect(self.ui.loadConfButton, QtCore.SIGNAL("clicked()"), self.loadConf)
        QtCore.QObject.connect(self.ui.saveConfButton, QtCore.SIGNAL("clicked()"), self.saveConf)
        QtCore.QObject.connect(self.ui.doneButton,     QtCore.SIGNAL("clicked()"), self.hide)

    def setup(self):
        self.liberaCount = 120  # number of libera units (now hardcoded, but may be useful)
        self.tableCount = 5     # number of available tables to display libera units (now hardcoded)
        if ((self.liberaCount % self.tableCount) != 0):
            QtGui.QMessageBox.critical(None,"SyncTime" , "Num of liberas must be divisible by num of tables")
            return False

        # Set the headers of the tables
        for i in range(1,self.tableCount+1):
            header1 = QtGui.QTableWidgetItem()
            header1.setText("Machine Time")
            getattr(self.ui,"tableWidget"+str(i)).setColumnCount(2)
            getattr(self.ui,"tableWidget"+str(i)).setHorizontalHeaderItem(0,header1)
            header2 = QtGui.QTableWidgetItem()
            header2.setText("Machine Phase")
            getattr(self.ui,"tableWidget"+str(i)).setHorizontalHeaderItem(1,header2)

        # Fill the rows with libera unit number (header) and empty items for cells
        rowsPerTable = self.liberaCount/self.tableCount
        liberaNumber = 1
        for i in range(1,self.tableCount+1):
            for j in range(0,rowsPerTable):
                item = QtGui.QTableWidgetItem()
                item.setText("%03d" % liberaNumber)
                liberaNumber += 1
                getattr(self.ui,"tableWidget"+str(i)).insertRow(j)
                getattr(self.ui,"tableWidget"+str(i)).setVerticalHeaderItem(j,item)
                item = QtGui.QTableWidgetItem()
                item.setCheckState(QtCore.Qt.Unchecked)
                getattr(self.ui,"tableWidget"+str(i)).setItem(j,0,item)
                item = QtGui.QTableWidgetItem()
                getattr(self.ui,"tableWidget"+str(i)).setItem(j,1,item)

        # Force repaint of the tables to adjust sizes
        for i in range(1,self.tableCount+1):
            getattr(self.ui,"tableWidget"+str(i)).resizeRowsToContents()
            getattr(self.ui,"tableWidget"+str(i)).resizeColumnsToContents()

        # Set current time in the system time line edits
        t = time.gmtime()
        self.ui.YearLineEdit.setText(str("%04.0f" %t.tm_year))
        self.ui.MonthLineEdit.setText(str("%02.0f" %t.tm_mon))
        self.ui.DayLineEdit.setText(str("%02.0f" %t.tm_mday))
        self.ui.HourLineEdit.setText(str("%02.0f" %t.tm_hour))
        self.ui.MinuteLineEdit.setText(str("%02.0f" %t.tm_min))
        self.ui.SecondLineEdit.setText(str("%02.0f" %t.tm_sec))

    def setTimeOnNextTrigger(self,dp,MT,MP):
        v1 = self.ui.YearLineEdit.text()
        v2 = self.ui.MonthLineEdit.text() 
        v3 = self.ui.DayLineEdit.text()
        v4 = self.ui.HourLineEdit.text()
        v5 = self.ui.MinuteLineEdit.text() 
        v6 = self.ui.SecondLineEdit.text() 
        dateTime = str( (v1+v2+v3+v4+v5+v6).toAscii() )

        try:
            timeInEpoch = float(calendar.timegm(time.strptime(dateTime, '%Y%m%d%H%M%S')))
        except:
            QtGui.QMessageBox.critical(None,"SyncTime","Invalid date")
            return False

        if (timeInEpoch < 0):
            QtGui.QMessageBox.critical(None,"SyncTime","Invalid date. Min date is 19700101000000")
            return False

        try:
            #write attributes and execute command
            dp.write_attribute("MachineTime", float(MT))
            dp.write_attribute("TimePhase",   int(MP))
            dp.write_attribute("SystemTime",  timeInEpoch)
            dp.command_inout("SetTimeOnNextTrigger")
        except PyTango.DevFailed, e:
            QtGui.QMessageBox.critical(None, "SyncTime" , repr(e))
            return False
        except Exception, e:
            QtGui.QMessageBox.critical(None,"SyncTime","Device server failed to execute command SetTimeOnNextTrigger. Unknown reason: " + repr(e))
            return False

        return True #if we reach this point, everything was OK


    def setTimes(self):
        rowsPerTable = self.liberaCount/self.tableCount
        for i in range(1,self.tableCount+1):
            for j in range(0,rowsPerTable):
                if (getattr(self.ui,"tableWidget"+str(i)).item(j,0).checkState() == QtCore.Qt.Checked):
                    liberaNumber = ((i-1) * rowsPerTable) + (j+1)
                    # try to get MachineTime and MachinePhase values for this libera. If error, paint in red
                    try:
                        MachineTime  = int(getattr(self.ui,"tableWidget"+str(i)).item(j,0).text())
                        MachinePhase = int(getattr(self.ui,"tableWidget"+str(i)).item(j,1).text())
                    except ValueError:
                        QtGui.QMessageBox.critical(None,"SyncTime","setTimes: MachineTime or MachinePhase not valid for libera " + str(liberaNumber))
                        getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.red)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.red)
                        continue
                    # try to get connection to the libera device server
                    try:
                        dsCppName = str("WS/DI-LI/%03d" % liberaNumber)
                        # Connect to the Device Server and check its state
                        dp = PyTango.DeviceProxy(dsCppName)
                        if (dp.state() != PyTango.DevState.ON):
                            QtGui.QMessageBox.warning(self,
                                self.tr("Device server failed"),
                                self.tr("The status of the device server " + dsCppName + " is not ON"))
                            getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.red)
                            getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.red)
                    except PyTango.DevFailed:
                        QtGui.QMessageBox.critical(None,"SyncTime","setTimes: unable to connect to libera device server " + dsCppName)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.red)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.red)
                        continue
                    # and finally try to issue the command to the libera device server
                    if (self.setTimeOnNextTrigger(dp,MachineTime, MachinePhase)):
                        getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.green)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.green)
                    else:
                        getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.red)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.red)
                else: #it may be in red due to previous set try (the user may have unchecked it)
                    if (getattr(self.ui,"tableWidget"+str(i)).item(j,0).backgroundColor() == Qt.Qt.red):
                        getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.white)
                        getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.white)

    def clearContents(self):
        rowsPerTable = self.liberaCount/self.tableCount
        for i in range(1,self.tableCount+1):
            for j in range(0,rowsPerTable):
                getattr(self.ui,"tableWidget"+str(i)).item(j,0).setCheckState(QtCore.Qt.Unchecked)
                getattr(self.ui,"tableWidget"+str(i)).item(j,0).setText("")
                getattr(self.ui,"tableWidget"+str(i)).item(j,0).setBackgroundColor(Qt.Qt.white)
                getattr(self.ui,"tableWidget"+str(i)).item(j,1).setText("")
                getattr(self.ui,"tableWidget"+str(i)).item(j,1).setBackgroundColor(Qt.Qt.white)

    def saveConf(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self,
            self.tr("Save liberas times configuration"),  DEFAULT_PATH + "LiberasTimes.dat",
            self.tr("DAT (*.dat)"))
        if fileName.isEmpty():
            return False
        file = open(fileName,'w')
        line = "# Liberas time configuration file. Format is:\n"
        file.write(line)
        line = "# liberaUnitNumber setOrNot [MachineTime] [MachinePhase]\n"
        file.write(line)
        line = "# setOrNot specifies if the values will finally be set or not to the libera unit. The\n"
        file.write(line)
        line = "# values admitted are 0 (don't set) or 2 (set)\n"
        file.write(line)
        liberaNumber=1
        try:
            for i in range(1,self.tableCount+1):
                for j in range(0,getattr(self.ui,"tableWidget"+str(i)).rowCount()):
                    line =  str(liberaNumber)
                    line += (" " + str(getattr(self.ui,"tableWidget"+str(i)).item(j,0).checkState()))
                    line += (" " + str(getattr(self.ui,"tableWidget"+str(i)).item(j,0).text()))
                    line += (" " + str(getattr(self.ui,"tableWidget"+str(i)).item(j,1).text()) + "\n")
                    liberaNumber += 1
                    file.write(line)
        finally:
            file.close()

    def loadConf(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,
            self.tr("Open liberas times file"), DEFAULT_PATH,
            self.tr("DAT (*.dat)"))
        if fileName.isEmpty():
            return
        file = open(fileName,'r')
        try:
            rowsPerTable  = (self.liberaCount/self.tableCount)
            for line in file:
                tokens = line.split()
                if (tokens[0].startswith("#")): #if it's a comment, go for next loop
                    continue
                liberaNumber = int(tokens[0])
                if (liberaNumber > self.liberaCount):
                    QtGui.QMessageBox.critical(None,"SyncTime" , "LoadConf: libera number read from file (" + str(liberaNumber) +") is greater than max number (" + str(self.liberaCount) + ")")
                    return False
                #determine in which table to insert
                insertInTableNum = ((liberaNumber-1) / rowsPerTable) + 1
                #determine in which row to insert
                row = (liberaNumber-1) % rowsPerTable
                getattr(self.ui,"tableWidget"+str(insertInTableNum)).item(row,0).setCheckState(QtCore.Qt.CheckState(int(tokens[1])))
                if (len(tokens) == 4):
                    getattr(self.ui,"tableWidget"+str(insertInTableNum)).item(row,0).setText(tokens[2])
                    getattr(self.ui,"tableWidget"+str(insertInTableNum)).item(row,1).setText(tokens[3])
        except:
            QtGui.QMessageBox.critical(None,"SyncTime","Unable to load configuration file. Please check that it has a valid format.")
            return False
        finally:
            file.close()


class GainScheme(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_GainScheme()
        self.ui.setupUi(self)
        self.ui.textEdit.setUndoRedoEnabled(True)
        self.dp = None
        self.textModified = False
        QtCore.QObject.connect(self.ui.newButton,          QtCore.SIGNAL("clicked()"), self.new)
        QtCore.QObject.connect(self.ui.openButton,         QtCore.SIGNAL("clicked()"), self.open)
        QtCore.QObject.connect(self.ui.saveButton,         QtCore.SIGNAL("clicked()"), self.save)
        QtCore.QObject.connect(self.ui.printButton,        QtCore.SIGNAL("clicked()"), self.print_)
        QtCore.QObject.connect(self.ui.downloadGainButton, QtCore.SIGNAL("clicked()"), self.downloadGain)
        QtCore.QObject.connect(self.ui.uploadGainButton,   QtCore.SIGNAL("clicked()"), self.uploadGain)
        QtCore.QObject.connect(self.ui.textEdit,           QtCore.SIGNAL("textChanged()"), self.textChanged)

    def reset(self, dp):
        self.dp = dp
        self.ui.textEdit.clear()
        self.textModified = False

    def textChanged(self):
        self.textModified = True

    def new(self):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        if self.textModified:
            answer = QtGui.QMessageBox.question(self,
                    self.tr("New gain scheme"),
                    self.tr("Gain scheme has been changed. Are you sure?"),
                    QtGui.QMessageBox.Yes,
                    QtGui.QMessageBox.No)
            if(answer == QtGui.QMessageBox.No):
                return False
        self.ui.textEdit.clear()
        self.textModified = False

    def open(self):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        if self.textModified:
            answer = QtGui.QMessageBox.question(self,
                    self.tr("Open gain scheme"),
                    self.tr("Gain scheme has been changed. Are you sure?"),
                    QtGui.QMessageBox.Yes,
                    QtGui.QMessageBox.No)
            if(answer == QtGui.QMessageBox.No):
                return False
        fileName = QtGui.QFileDialog.getOpenFileName(self,
            self.tr("Open gain scheme"), ".", self.tr("CONF (*.conf)"))
        if fileName.isEmpty():
            return False

        gainFile = QtCore.QFile(fileName)
        if not gainFile.open( QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, self.tr("Open gain scheme"),
                    self.tr("Cannot read file %1:\n%2.").arg(fileName).arg(gainFile.errorString()))
            return False
        inStream = QtCore.QTextStream(gainFile)
        self.ui.textEdit.setPlainText(inStream.readAll())
        self.textModified = False
        gainFile.close()

    def save(self, fileName=None):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        # Get file name from Save dialog
        if fileName == None:
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                self.tr("Save gain configuration"), GAIN_FILENAME,
                self.tr("CONF (*.conf)"))
            if fileName.isEmpty():
                return False

        # Save contents to file
        gainFile = QtCore.QFile(fileName)
        if not gainFile.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, self.tr("Application"),
                        self.tr("Cannot write file %1:\n%2.").arg(fileName).arg(gainFile.errorString()))
            return False

        outStream = QtCore.QTextStream(gainFile)
        outStream << self.ui.textEdit.toPlainText()
        self.textModified = False
        gainFile.close()

    def downloadGain(self):
        #check if we have connection to the libera
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        #check if the file contents have been changed
        if self.textModified:
            answer = QtGui.QMessageBox.question(self,
                    self.tr("Load gain scheme"),
                    self.tr("Gain scheme has been changed. Are you sure?"),
                    QtGui.QMessageBox.Yes,
                    QtGui.QMessageBox.No)
            if(answer == QtGui.QMessageBox.No):
                return False
        #get gain.conf file from the libera
        try:
            self.ui.textEdit.setPlainText(self.dp.command_inout("GainDownload"))
            self.textModified = False
        except PyTango.DevFailed, e:
            QtGui.QMessageBox.critical(None, "downloadGain" , repr(e))
            return False

    def uploadGain(self):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False

        try:
            txt = str(self.ui.textEdit.toPlainText())
            if txt == "":
                a = QtGui.QMessageBox.question(self, 
                        self.tr("Empty gain contents"),
                        self.tr("The gain gain config you try to upload is empty."
                        " Are you sure you want to continue?"),
                        QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if (a == QtGui.QMessageBox.No):
                    return
            self.dp.command_inout("GainUpload",txt)
        except PyTango.DevFailed, e:
            QtGui.QMessageBox.critical(None, "uploadGain" , repr(e))
            return False

    def print_(self,title="Gain"):
        printer = Qt.QPrinter(Qt.QPrinter.HighResolution)
        dialog = Qt.QPrintDialog(printer)
        if dialog.exec_():
            self.ui.textEdit.print_(printer)


class Log(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Log()
        self.ui.setupUi(self)
        self.dp = None
        QtCore.QObject.connect(self.ui.updateButton,QtCore.SIGNAL("clicked()"), self.update)
        QtCore.QObject.connect(self.ui.saveButton,QtCore.SIGNAL("clicked()"), self.save)
        QtCore.QObject.connect(self.ui.printButton,QtCore.SIGNAL("clicked()"), self.print_)

    def reset(self, deviceName):
        self.dp = PyTango.DeviceProxy(deviceName)
        self.ui.textEdit.clear()

    def update(self):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        self.ui.textEdit.clear()
        log = self.dp.read_attribute("logs").value
        if log is None: log = []
        for logLine in log:
            self.ui.textEdit.append(logLine)

    def save(self, fileName=None):
        if (self.dp == None):
            QtGui.QMessageBox.warning(self,self.tr("No connection"),self.tr("No connection to any libera"))
            return False
        # Get file name from Save dialog
        if fileName == None:
            fileName = QtGui.QFileDialog.getSaveFileName(self,
                self.tr("Save log into a file"), "libera.log", self.tr("LOG (*.log)"))
            if fileName.isEmpty():
                return False

        # Save contents to file
        logFile = QtCore.QFile(fileName)
        if not logFile.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, self.tr("Application"),
                        self.tr("Cannot write file %1:\n%2.").arg(fileName).arg(logFile.errorString()))
            return False

        outStream = QtCore.QTextStream(logFile)
        outStream << self.ui.textEdit.toPlainText()
        self.textModified = False
        logFile.close()

    def print_(self,title="Log"):
        printer = Qt.QPrinter(Qt.QPrinter.HighResolution)
        dialog = Qt.QPrintDialog(printer)
        if dialog.exec_():
            self.ui.textEdit.print_(printer)



def main():
    #parse posible arguments
    parser = OptionParser()
    parser.add_option("-d", "--device-name", action="store", dest="liberaDsName",
                     type="string", help="Libera device name to connect to")
    (options, args) = parser.parse_args()
    #start the application
    app = QtGui.QApplication(args)
    mainUI = MainWindow(None,options.liberaDsName)
    mainUI.show()
    #tau.core.utils.Logger.setLogLevel(tau.core.utils.Logger.Debug)
    tau.setLogLevel(tau.Debug)
    sys.exit(app.exec_())



if __name__ == "__main__":
    main()
