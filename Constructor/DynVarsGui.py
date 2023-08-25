# -------------------------------------------------------------------------------
# Name:        DynVarsGui.py
# Purpose:     enables user to adjust crop parameters
# Author:      Mike Martin
# Created:     05/07/2023
# Licence:     <your licence>
# Description:  unfinished
#
# -------------------------------------------------------------------------------
# !/usr/bin/env python

__prog__ = 'DynVarsGui.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, QWidget, QGridLayout, QPushButton, QLineEdit, QLabel,
                       QApplication, QMessageBox, QComboBox, QAction, QScrollArea, QMainWindow)

from ora_cn_fns import plant_inputs_crops_distribution

WARN_STR = '*** Warning *** '

STD_FLD_SIZE_40 = 40

def edit_dyn_vars(form):
    """
    
    """
    form.crop_vars_gui = DispCropVars(form.ora_parms)
    return

class DispCropVars(QMainWindow):
    """

    """
    submitted = pyqtSignal(str, str)  # will send 2 strings

    def __init__(self, ora_parms, parent=None):
        """
         calls the __init__() method of the QMainWindow (or QWidget) class, allowing
         the DispCropParms class to be used without repeating code
        """
        super(DispCropVars, self).__init__(parent)

        self.crop_vars = ora_parms.crop_vars
        self.syn_fert_parms = ora_parms.syn_fert_parms

        self.setWindowTitle('Adjust Crop Parameters')

        self.UiGridWdgts()

        self.UiControlPanel()

        self.UiScrllLayout()

        self.setGeometry(150, 50, 400, 240)  # posx, posy, width, height
        self.show()  # showing all the widgets

    def UiGridWdgts(self):
        """
        method for grid components
        """
        syn_fert_parms = [syn_fert for syn_fert in self.syn_fert_parms]

        # grid will be put in RH vertical box
        # ===================================
        lay_grid = QGridLayout()
        lay_grid.setSpacing(10)  # set spacing between widgets

        irow = 1
        w_lbl00s = QLabel('Inorganic fertiliser:')
        lay_grid.addWidget(w_lbl00s, irow, 0)

        w_combo00 = QComboBox()
        for syn_fert in syn_fert_parms:
            w_combo00.addItem(str(syn_fert))

        w_combo00.currentIndexChanged[str].connect(self.changeCrop)
        lay_grid.addWidget(w_combo00, irow, 1)
        self.w_combo00 = w_combo00

        irow += 1
        lay_grid.addWidget(QLabel(' '), irow, 0)

        w_lbl01s = QLabel('Inhibition rate modifier:')
        lay_grid.addWidget(w_lbl01s, irow, 0)

        w_inhibit = QLineEdit()
        w_inhibit.setFixedWidth(STD_FLD_SIZE_40)
        w_inhibit.setAlignment(Qt.AlignRight)
        lay_grid.addWidget(w_inhibit, irow, 1, alignment=Qt.AlignHCenter)
        w_inhibit.setText(str(1))
        self.w_inhibit = w_inhibit

        # add space
        # =========
        for iline in range(2):
            irow += 1
            lay_grid.addWidget(QLabel(' '), irow, 0)

        self.lay_grid = lay_grid  # used in UiScrllLayout

        return

    def changeCrop(self):
        """

        """
        syn_fert = self.w_combo00.currentText()

        rate_inhibit = self.syn_fert_parms[syn_fert]['rate_inhibit']
        self.w_inhibit.setText(str(rate_inhibit))

        return

    def UiControlPanel(self):
        """
        method for constructing control panel
        """
        w_reset = QPushButton("Reset")
        w_reset.setFixedWidth(65)
        w_reset.clicked.connect(self.resetClicked)

        w_submit = QPushButton("Save")
        helpText = 'Save management detail, write to file and close'
        w_submit.setToolTip(helpText)
        w_submit.setFixedWidth(65)
        w_submit.setEnabled(True)
        w_submit.clicked.connect(self.saveDynVarsClicked)
        self.w_submit = w_submit

        w_dismiss = QPushButton("Dismiss")
        w_dismiss.setFixedWidth(65)
        w_dismiss.clicked.connect(self.dismissClicked)

        lay_hbox_cntrl = QHBoxLayout()
        lay_hbox_cntrl.addWidget(w_submit)
        lay_hbox_cntrl.addWidget(w_reset)
        lay_hbox_cntrl.addWidget(w_dismiss)

        self.lay_hbox_cntrl = lay_hbox_cntrl

        return

    def saveDynVarsClicked(self, dummy):
        """
        gather all fields
        """
        syn_fert = self.w_combo00.currentText()
        try:
            rate_inhibit = float(self.w_inhibit.text())
        except ValueError as err:
            rate_inhibit = 1

        self.syn_fert_parms[syn_fert]['rate_inhibit'] = rate_inhibit

        print('Updated ' + syn_fert)
        QApplication.processEvents()

        return

    def dismissClicked(self):

        self.close()

    def resetClicked(self):
        """

        """
        pass

    def UiScrllLayout(self):
        """
        method for laying out UI
        """
        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)

        # Scroll Area Properties
        # ======================
        self.scroll_area = QScrollArea()  # Scroll Area which contains the widgets, set as the centralWidget
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)

        # create widget that contains the main Vertical Box
        # =================================================
        self.widget = QWidget()
        lay_vbox = QVBoxLayout()
        lay_vbox.setSpacing(15)
        self.widget.setLayout(lay_vbox)

        self.scroll_area.setWidget(self.widget)
        self.setCentralWidget(self.scroll_area)

        # vertical box consists of grid and control button lay outs
        # =========================================================
        lay_vbox.addLayout(self.lay_grid)
        lay_vbox.addLayout(self.lay_hbox_cntrl)  # the horizontal box fits inside the vertical layout

        return

    def closeEvent(self, event):
        """

        """
        close = QMessageBox()
        close.setText("You sure?")
        close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        close = close.exec()

        if close == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

        return
