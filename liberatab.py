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

import sys, time
from PyQt4 import QtCore, QtGui, Qt
import PyTango
from os import sep


class LiberaTab:
        def __init__(self, p):
                self.p = p
                self.tabName = p["tabname"]

                # 4-Spectrum Widgets -> Tango Attrs
                self.plot1 = p["plot1"][0]
                self.plot2 = p["plot2"][0]

                self.plot1Attrs = p["plot1"][1:]
                self.plot2Attrs = p["plot2"][1:]

                # Single loop for adc or dd captures
                self.singleLoop = p["singleLoop"][0]

                # Attr for 'save' proposes
                self.timestamp = p["timestamp"][0]

                # Buttons -> Click signal+ method
                self.configureButton("start",self.start)
                self.configureButton("stop",self.stop)
                self.configureButton("save",self.save)
                self.configureButton("resetPM",self.resetPM)

        def configureButton(self, lbl, method):
                if(self.p[lbl][1] != None):
                        QtCore.QObject.connect(self.p[lbl][0], QtCore.SIGNAL("clicked()"), method)

        def connectTangoAttribute(self, dsName, lbl):
                #if attribute is not found, then don't try to connect it
                try:
                    tangoWidget = self.p[lbl][0]
                    tangoAttr = self.p[lbl][1]
                except KeyError:
                    print "Attribute %s not found in device %s" % (lbl,dsName)
                    return

                if(tangoAttr == None):
                    return

                try:
                        if tangoAttr:
                            attrName = dsName +'/'+ tangoAttr
                            tangoWidget.setModel(attrName)

                except Exception, e:
                        print "connectTangoAttribute Exception        -->   ", str(e)
                        raise


        def connectLibera(self, dsName):
                try:
                        self.dsName  = dsName
                        self.dp = PyTango.DeviceProxy(self.dsName)
                        self.connectLiberaTab()

                        self.connectTangoAttribute(dsName, "samples")
                        self.connectTangoAttribute(dsName, "samplesRB")
                        self.connectTangoAttribute(dsName, "loops")
                        self.connectTangoAttribute(dsName, "loopsRB")
                        self.connectTangoAttribute(dsName, "triggercounts")
                        self.connectTangoAttribute(dsName, "peakA")
                        self.connectTangoAttribute(dsName, "peakB")
                        self.connectTangoAttribute(dsName, "peakC")
                        self.connectTangoAttribute(dsName, "peakD")
                        self.connectTangoAttribute(dsName, "timesleep")
                        self.connectTangoAttribute(dsName, "timesleepRB")
                        self.connectTangoAttribute(dsName, "timestamp")
                        self.connectTangoAttribute(dsName, "timestampRB")
                        self.connectTangoAttribute(dsName, "firstcount")
                        self.connectTangoAttribute(dsName, "lastcount")
                        self.connectTangoAttribute(dsName, "decimation")
                        self.connectTangoAttribute(dsName, "decimationRB")
                except Exception, e:
                        print "connectLibera Exception        -->   ", str(e)
                        raise

        def save(self):
            try:
                # Get file name from Save dialog
                defaultName = PyTango.DeviceProxy(self.dsName).read_attribute("SAFileName").value
                fileName, ok = QtGui.QInputDialog.getText(None, "File name", "File name:", QtGui.QLineEdit.Normal, defaultName)
                if (not ok or fileName.isEmpty()):
                    return False
                fileName = str(fileName.toAscii()) #convert to normal string

                # Call to DS save function
                if(self.dsName):
                    self.dp.write_attribute(self.p["filename"][1],str(fileName))
                    # Check if timestamp has to be saved and inform it to the Device server
                    if ( self.timestamp != None ):
                        if(self.timestamp.isChecked()):
                            timeStamp = True
                        else:
                            timeStamp = False
                        self.dp.write_attribute(self.p["timestamp"][1],timeStamp)

                    if (self.p["savefunc"][1] != None): #we're not in SA mode
                        self.dp.command_inout(self.p["savefunc"][1])
            except Exception, e:
                QtGui.QMessageBox.critical(None, self.tabName , repr(e))
                return False

            return True


        def connectLiberaTab(self):
                try:
                        plot1 = []
                        plot2 = []

                        #connect tab1 attributes
                        for i in range(len(self.plot1Attrs)):
                            plot1.append(self.dsName +'/'+ self.plot1Attrs[i])
                        self.plot1.setModel(QtCore.QStringList(plot1))

                        #connect tab2 (if it exists) attributes
                        if self.plot2 != None:
                            for i in range(len(self.plot2Attrs)):
                                plot2.append(self.dsName +'/'+ self.plot2Attrs[i])
                            self.plot2.setModel(QtCore.QStringList(plot2))
                except Exception, e:
                        print "connectLiberaTab Exception        -->   ", str(e)
                        raise

        def start(self):
                if(self.dsName):
                        try:
                                #if ADC or DD acquire, we must say if we want it to stop after
                                #one reading cycle
                                if (self.p["tabname"].startswith("ADC") or
                                    self.p["tabname"].startswith("DD")):
                                    singleLoop = self.singleLoop.isChecked()
                                    prevTimeout = self.dp.get_timeout_millis()
                                    self.dp.set_timeout_millis(10000)
                                    #if (self.dp.command_inout(self.p["start"][1],singleLoop) == False):
                                        #QtGui.QMessageBox.warning(None, self.p["tabname"],
                                            #"Cannot start acquisition. Maybe already running?")
                                        #self.dp.set_timeout_millis(prevTimeout)
                                        #return False
                                    #else:
                                        #self.dp.set_timeout_millis(prevTimeout)
                                        #return True
                                    retries = 0
                                    while (not self.dp.command_inout(self.p["start"][1],singleLoop)):
                                        self.dp.command_inout(self.p["stop"][1])
                                        time.sleep(0.2)
                                        retries += 1
                                        if retries > 10:
                                            QtGui.QMessageBox.warning(None, self.p["tabname"],
                                                "Cannot start acquisition. Max retries reached")
                                            self.dp.set_timeout_millis(prevTimeout)
                                            return False
                                    self.dp.set_timeout_millis(prevTimeout)
                                    return True
                                # if we are in SA mode
                                if (self.p["tabname"].startswith("SA")):
                                    if not self.save():
                                        return False
                                #if we're treating with FA data, we must increase timeout before executing
                                #the command, since we can easily reach it depending on the length
                                if (self.p["tabname"].startswith("FA")):
                                    prevTimeout = self.dp.get_timeout_millis()
                                    self.dp.set_timeout_millis(60000)
                                    self.dp.command_inout(self.p["start"][1])
                                    self.dp.set_timeout_millis(prevTimeout)
                                    return True
                                #finally, run standard acquire command on device (only PM is standard).
                                #timeout must be increased since the command may take long
                                self.dp.command_inout(self.p["start"][1])
                                return True
                        except PyTango.DevFailed, e:
                                QtGui.QMessageBox.critical(None, self.tabName , repr(e))

        def stop(self):
                if(self.dsName):
                        try:
                                self.dp.command_inout(self.p["stop"][1])
                        except PyTango.DevFailed, e:
                                QtGui.QMessageBox.critical(None, self.tabName , repr(e))

        def resetPM(self):
            if(self.dsName):
                try:
                    self.dp.command_inout(self.p["resetPM"][1])
                except PyTango.DevFailed, e:
                    QtGui.QMessageBox.critical(None, self.tabName , repr(e))

        def freeze(self):
            pass

        def restart(self):
            pass