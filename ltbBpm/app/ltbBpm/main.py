#! /usr/bin/env python

import os
import sys
import PyQt4.Qwt5
import webbrowser
import tau.core.utils
import PyTango
from PyQt4 import QtCore, QtGui
from ui_ltb import *
from optparse import OptionParser
from subprocess import Popen

#Default plot scales and limits
XAXIS = PyQt4.Qwt5.QwtPlot.xBottom
XMIN  = 0
XMAX  = 1024
YAXIS = PyQt4.Qwt5.QwtPlot.yLeft
YMIN  = -10
YMAX  =  10

#Acquire command names
ADCSTART = "ADCAcquire"
ADCSTOP  = "ADCStop"
DDSTART  = "DDAcquire"
DDSTOP   = "DDStop"

#Documentation url address
DOC_URL = "http://www.cells.es/Intranet/Divisions/Computing/Controls/Help/LT/DI/BPM/index_html"

#This will be the default polling period in case we are told not to use events
POLL_PERIOD = 1000

#Python devices to connect to
pyDevices = [
        "li/di/bpm-acq-01",
        "lt/di/bpm-acq-01",
        "lt/di/bpm-acq-02",
        "lt/di/bpm-acq-03"
        ]

#C++ devices to connect to
cppDevices = [
        "li/di/bpm-01",
        "lt/di/bpm-01",
        "lt/di/bpm-02",
        "lt/di/bpm-03",
        ]

pyDevices = [
        "lab02/di/bpm-acq-01",
        "lab02/di/bpm-acq-02",
        "lab02/di/bpm-acq-03",
        "lab02/di/bpm-acq-04"
        ]

cppDevices = [
        "lab02/di/bpm-01",
        "lab02/di/bpm-02",
        "lab02/di/bpm-03",
        "lab02/di/bpm-04",
        ]

ADCattr = [ "ADCChannelA", "ADCChannelB", "ADCChannelC", "ADCChannelD" ]
DDattr  = [ "XPosDD", "ZPosDD" ]


class Ti(object):

    def __init__(self, noEvents=True):
        """This function will initialize all the components and show the dialog"""
        #Initialize graphical components
        app = QtGui.QApplication(sys.argv)
        self.Dialog = QtGui.QDialog()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self.Dialog)

        #Get connections to the devices
        self.devices = []
        for i in range(4):
            self.devices.append(PyTango.DeviceProxy(pyDevices[i]))

        #Make connections
        QtCore.QObject.connect(self.ui.expertButton1,   QtCore.SIGNAL("clicked()"), self.openExpert)
        QtCore.QObject.connect(self.ui.expertButton2,   QtCore.SIGNAL("clicked()"), self.openExpert)
        QtCore.QObject.connect(self.ui.expertButton3,   QtCore.SIGNAL("clicked()"), self.openExpert)
        QtCore.QObject.connect(self.ui.expertButton4,   QtCore.SIGNAL("clicked()"), self.openExpert)
        QtCore.QObject.connect(self.ui.startButton1,    QtCore.SIGNAL("clicked()"), self.start)
        QtCore.QObject.connect(self.ui.startButton2,    QtCore.SIGNAL("clicked()"), self.start)
        QtCore.QObject.connect(self.ui.startButton3,    QtCore.SIGNAL("clicked()"), self.start)
        QtCore.QObject.connect(self.ui.startButton4,    QtCore.SIGNAL("clicked()"), self.start)
        QtCore.QObject.connect(self.ui.stopButton1,     QtCore.SIGNAL("clicked()"), self.stop)
        QtCore.QObject.connect(self.ui.stopButton2,     QtCore.SIGNAL("clicked()"), self.stop)
        QtCore.QObject.connect(self.ui.stopButton3,     QtCore.SIGNAL("clicked()"), self.stop)
        QtCore.QObject.connect(self.ui.stopButton4,     QtCore.SIGNAL("clicked()"), self.stop)
        QtCore.QObject.connect(self.ui.saveButton1,     QtCore.SIGNAL("clicked()"), self.save)
        QtCore.QObject.connect(self.ui.saveButton2,     QtCore.SIGNAL("clicked()"), self.save)
        QtCore.QObject.connect(self.ui.saveButton3,     QtCore.SIGNAL("clicked()"), self.save)
        QtCore.QObject.connect(self.ui.saveButton4,     QtCore.SIGNAL("clicked()"), self.save)
        QtCore.QObject.connect(self.ui.comboDataSource, QtCore.SIGNAL("currentIndexChanged(const QString&)"),self.comboChanged)
        QtCore.QObject.connect(self.ui.singleCheckBox,  QtCore.SIGNAL("toggled (bool)"),self.toggled)
        QtCore.QObject.connect(self.ui.startAllButton,  QtCore.SIGNAL("clicked()"), self.startAll)
        QtCore.QObject.connect(self.ui.stopAllButton,   QtCore.SIGNAL("clicked()"), self.stopAll)
        QtCore.QObject.connect(self.ui.helpButton,      QtCore.SIGNAL("clicked()"), self.showHelp)

        #Fill combo box possible values
        self.ui.comboDataSource.insertItem(0,"ADC")
        self.ui.comboDataSource.insertItem(1,"DD")
        self.ui.comboDataSource.setCurrentIndex(1)

        #Make tau connections for those attributes to be shown
        for i in range(len(pyDevices)):
            #Connect XPosDD and ZPosDD and set default axis scale and value
            model = QtCore.QStringList([pyDevices[i]+"/XPosDD", pyDevices[i]+"/ZPosDD"])
            plot = getattr(self.ui,"tauPlot"+str(i+1))
            plot.setModel(model)
            if noEvents:
                plot.getCurve(pyDevices[i]+"/XPosDD").getModelObj().changePollingPeriod(POLL_PERIOD)
                plot.getCurve(pyDevices[i]+"/ZPosDD").getModelObj().changePollingPeriod(POLL_PERIOD)
            plot.setAxisScale(XAXIS,XMIN,XMAX)
            plot.setAxisScale(YAXIS,YMIN,YMAX)
            #Connect State of cpp device server to TauStateLed
            model = pyDevices[i]+"/State"
            attr  = getattr(self.ui,"TauStateLed"+str(i+1))
            attr.setModel(model)
            if noEvents:
                attr.getModelObj().changePollingPeriod(POLL_PERIOD)
            #Connect the means of XPos and Zpos
            model = pyDevices[i]+"/XPosDDMean?configuration=label"
            attr = getattr(self.ui,"tauConfigLabel"+str(i+1)+"a")
            attr.setModel(model)
            model = pyDevices[i]+"/XPosDDMean"
            attr = getattr(self.ui,"tauValueLabel"+str(i+1)+"a")
            attr.setModel(model)
            if noEvents:
                attr.getModelObj().changePollingPeriod(POLL_PERIOD)
            model = pyDevices[i]+"/ZPosDDMean?configuration=label"
            attr = getattr(self.ui,"tauConfigLabel"+str(i+1)+"b")
            attr.setModel(model)
            model = pyDevices[i]+"/ZPosDDMean"
            attr = getattr(self.ui,"tauValueLabel"+str(i+1)+"b")
            attr.setModel(model)
            if noEvents:
                attr.getModelObj().changePollingPeriod(POLL_PERIOD)

        #Show dialog
        self.Dialog.show()

        sys.exit(app.exec_())

    def start(self):
        """Start endless capture in the selected device (this is found out by checking which
        button wass clicked)
        """
        #Find out which button was clicked
        button = self.Dialog.sender()
        if button is None or not isinstance(button, QtGui.QPushButton):
            return
        if button.objectName() == "startButton1":
            deviceNum = 0
        elif button.objectName() == "startButton2":
            deviceNum = 1
        elif button.objectName() == "startButton3":
            deviceNum = 2
        elif button.objectName() == "startButton4":
            deviceNum = 3
        else:
            print "Unknow device: ", button.name()
            return

        #Find out the data source and set command accordingly
        if self.ui.comboDataSource.currentText() == "ADC":
            command = ADCSTART
        elif self.ui.comboDataSource.currentText() == "DD":
            command = DDSTART
        else:
            print "Unknow data source: ", self.ui.comboDataSource.currenText()
            return

        #Run start command
        try:
            self.devices[deviceNum].command_inout(command,False)
        except PyTango.DevFailed, e:
            QtGui.QMessageBox.critical(None, "Connect to libera" , repr(e))
        except:
            raise

    def stop(self):
        """Stop acquisition"""
        button = self.Dialog.sender()
        if button is None or not isinstance(button, QtGui.QPushButton):
            return
        if button.objectName() == "stopButton1":
            deviceNum = 0
        elif button.objectName() == "stopButton2":
            deviceNum = 1
        elif button.objectName() == "stopButton3":
            deviceNum = 2
        elif button.objectName() == "stopButton4":
            deviceNum = 3
        else:
            print "Unknow device: ", button.name()
            return

        #Find out the data source and set command accordingly
        if self.ui.comboDataSource.currentText() == "ADC":
            command = ADCSTOP
        elif self.ui.comboDataSource.currentText() == "DD":
            command = DDSTOP
        else:
            print "Unknow data source: ", self.ui.comboDataSource.currenText()
            return

        #Run stop command
        try:
            self.devices[deviceNum].command_inout(command,False)
        except PyTango.DevFailed, e:
            QtGui.QMessageBox.critical(None, "Connect to libera" , repr(e))
        except:
            raise

    def save(self):
        """Save dialog. Note that we are unable to save while an acquisition is running"""
        #Find out which button was clicked
        button = self.Dialog.sender()
        if button is None or not isinstance(button, QtGui.QPushButton):
            return
        if button.objectName() == "saveButton1":
            deviceNum = 0
        elif button.objectName() == "saveButton2":
            deviceNum = 1
        elif button.objectName() == "saveButton3":
            deviceNum = 2
        elif button.objectName() == "saveButton4":
            deviceNum = 3
        else:
            print "Unknow device: ", button.name()
            return

        #Find out the data source
        if self.ui.comboDataSource.currentText() == "ADC":
            dataSource = "ADC"
        elif self.ui.comboDataSource.currentText() == "DD":
            dataSource = "DD"
        else:
            print "Unknow data source: ", self.ui.comboDataSource.currenText()
            return

        fileName = QtGui.QFileDialog.getSaveFileName(None, "Save "+dataSource, dataSource+str(deviceNum)+".dat", "DAT (*.dat)")

        if fileName.isEmpty():
            return False
        fileName = str(fileName.toAscii()) #convert to normal string

        #Write FileName and Timestamp attributes and then Save data
        try:
            self.devices[deviceNum].write_attribute(dataSource+"FileName",str(fileName))
            self.devices[deviceNum].write_attribute(dataSource+"Timestamp",True)
            self.devices[deviceNum].command_inout(dataSource+"Save")
        except PyTango.DevFailed, e:
                QtGui.QMessageBox.critical(None, dataSource , repr(e))

    def openExpert(self):
        """Open expert window"""
        #Find out which button was clicked
        button = self.Dialog.sender()
        if button is None or not isinstance(button, QtGui.QPushButton):
            return
        if button.objectName() == "expertButton1":
            deviceNum = 0
        elif button.objectName() == "expertButton2":
            deviceNum = 1
        elif button.objectName() == "expertButton3":
            deviceNum = 2
        elif button.objectName() == "expertButton4":
            deviceNum = 3
        else:
            print "Unknow device: ", button.name()
            return
        cmd = [ "LiberaGUI", "-d", pyDevices[deviceNum] ]
        Popen(cmd)

    def comboChanged(self, itemSelected):
        """This will catch the combo box selection change and will display the corresponding
        values on the plot"""
        if itemSelected == "ADC":
            attrList = ADCattr
            startCommand = ADCSTART
            stopCommand = None
        elif itemSelected == "DD":
            attrList = DDattr
            startCommand = None
            stopCommand = ADCSTOP
        else:
            print "ltbBPM::comboChanged() -> Unknown data source"
            return
        #Change data source
        for i in range(len(pyDevices)):
            modelList=[]
            for attr in attrList:
                modelList.append(pyDevices[i]+"/"+attr)
            model = QtCore.QStringList(modelList)
            plot = getattr(self.ui,"tauPlot"+str(i+1))
            plot.setModel(model)
            plot.setAxisAutoScale(YAXIS)

    def toggled(self, toggled):
        """This will simply enable/disable nloops spin box when the single acquisition
        checkbox is toggled on/off"""
        self.ui.nloopsSpinBox.setEnabled(toggled)

    def startAll(self):
        """This will start the acquisition on all device servers. If \"single\" is checked, it
        will start a single set nloops to the value of the nloops spinbox and start the acquisition.
        Note that the acquisition will not start in case one is already running"""
        itemSelected = self.ui.comboDataSource.currentText()
        if itemSelected == "ADC":
            command = "ADCAcquire"
            attribute = "ADCNLoops"
        elif itemSelected == "DD":
            command = "DDAcquire"
            attribute = "DDNLoops"
        else:
            print "ltbBpm::startAll() -> Unknown data source"
            return

        #Only if single combo is checked, then set the nloops attribute
        if self.ui.singleCheckBox.isChecked():
            for i in range(len(self.devices)):
                self.devices[i].write_attribute(attribute,self.ui.nloopsSpinBox.value())

        #Finally, start the acquisition
        for i in range(len(self.devices)):
            try:
                self.devices[i].command_inout(command,self.ui.singleCheckBox.isChecked())
            except PyTango.DevFailed, e:
                QtGui.QMessageBox.critical(None, "Connect to libera" , repr(e))

    def stopAll(self):
        """This will stop the acquisition in all the servers"""
        itemSelected = self.ui.comboDataSource.currentText()
        if itemSelected == "ADC":
            command = "ADCStop"
        elif itemSelected == "DD":
            command = "DDStop"
        else:
            print "ltbBpm::stopAll() -> Unknown data source"
            return
        for i in range(len(self.devices)):
            self.devices[i].command_inout(command)

    def showHelp(self):
        webbrowser.open(DOC_URL)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-e", "--no-events", action="store_true", dest="noEvents",
                     help="do not use events")
    (options, args) = parser.parse_args()
    tau.core.utils.Logger.setLogLevel(tau.core.utils.Logger.Info)
    ti = Ti(options.noEvents)
