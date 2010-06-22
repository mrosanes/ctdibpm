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
from tau.core.utils import Logger
import tau

# UI imports
from PyQt4 import QtCore, QtGui, Qt, Qwt5
from ui_tune import Ui_MainWindow

# Standard python imports
import sys

ORD = "tango://ctdi1:10000/BO/DI/SMES/FFTord"
ABS = "tango://ctdi1:10000/BO/DI/SMES/FFTabs"

AXIS = Qwt5.QwtPlot.yLeft
SCALE_TYPE = Qwt5.QwtScaleTransformation.Log10


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        # Get graphical information
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.initConnections()

    def initConnections(self):
        model = ABS+"|"+ORD
        self.ui.tauPlotFFT.setAxisScaleType(AXIS,SCALE_TYPE)
        self.ui.tauPlotFFT.setModel([model])
        attr = self.ui.tauPlotFFT.getCurve(ORD)
        attr.getModelObj().changePollingPeriod(500)


if __name__ == "__main__":
    #start the application
#    Logger.setLogLevel(Logger.Debug)
    tau.setLogLevel(tau.Debug)
    app = QtGui.QApplication(sys.argv)
    mainUI = MainWindow()
    mainUI.show()
    Logger.setLogLevel(Logger.Trace)
    sys.exit(app.exec_())
