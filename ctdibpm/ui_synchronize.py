#!/usr/bin/env python


from taurus.external.qt import QtGui
from taurus.qt.qtgui.util.ui import UILoadable


@UILoadable
class Synchronize(QtGui.QDialog):
    """A specialized QLineEdit"""

    def __init__(self, parent=None):

        # call the parent class init
        QtGui.QDialog.__init__(self, parent=parent)

        # load the UI
        self.loadUi()
