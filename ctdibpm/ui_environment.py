#!/usr/bin/env python


from taurus.external.qt import QtGui
from taurus.qt.qtgui.util.ui import UILoadable


@UILoadable
class Ui_Environment(QtGui.QDockWidget):
    """A specialized QLineEdit"""

    def __init__(self, parent=None):

        # call the parent class init
        QtGui.QDockWidget.__init__(self, parent=parent)

        # load the UI
        self.loadUi("ui_environment.ui")
