# -------------------------------------------------------------------------------
# Name:        CropGui.py
# Purpose:     enables user to adjust crop parameters
# Author:      Mike Martin
# Created:     05/07/2023
# Licence:     <your licence>
# Description:#
#
# -------------------------------------------------------------------------------
# !/usr/bin/env python

__prog__ = 'CropGui.py'
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

def edit_crop_parms(form):
    '''
    
    '''
    form.crop_vars_gui = DispCropVars(form.ora_parms.crop_vars)
    return

class DispCropVars(QMainWindow):
    '''

    '''
    submitted = pyqtSignal(str, str)  # will send 2 strings

    def __init__(self, crop_vars, parent=None):
        '''
         calls the __init__() method of the QMainWindow (or QWidget) class, allowing
         the DispCropParms class to be used without repeating code
        '''
        super(DispCropVars, self).__init__(parent)

        self.crop_vars = crop_vars

        self.setWindowTitle('Adjust Crop Parameters')

        self.UiGridWdgts()

        self.UiControlPanel()

        self.UiScrllLayout()

        self.setGeometry(150, 50, 400, 240)  # posx, posy, width, height
        self.show()  # showing all the widgets


    def UiGridWdgts(self):
        '''
        method for grid components
        '''
        crop_names = [crop_name for crop_name in self.crop_vars]

        # grid will be put in RH vertical box
        # ===================================
        lay_grid = QGridLayout()
        lay_grid.setSpacing(10)  # set spacing between widgets

        irow = 1
        w_lbl00s = QLabel('Crops:')
        w_lbl00s.setToolTip('list of crops')
        lay_grid.addWidget(w_lbl00s, irow, 0)

        w_combo00 = QComboBox()
        for crop_name in crop_names:
            w_combo00.addItem(str(crop_name))

        w_combo00.currentIndexChanged[str].connect(self.changeCrop)
        lay_grid.addWidget(w_combo00, irow, 1)
        self.w_combo00 = w_combo00

        irow += 1
        lay_grid.addWidget(QLabel(' '), irow, 0)

        w_lbl01s = QLabel('Number of growing months:')
        w_lbl01s.setToolTip('list of crops')
        lay_grid.addWidget(w_lbl01s, irow, 0)

        w_tgrow = QLineEdit()
        w_tgrow.setFixedWidth(STD_FLD_SIZE_40)
        w_tgrow.setAlignment(Qt.AlignRight)
        lay_grid.addWidget(w_tgrow, irow, 1, alignment=Qt.AlignHCenter)
        self.w_tgrow = w_tgrow

        # add space
        # =========
        for iline in range(2):
            irow += 1
            lay_grid.addWidget(QLabel(' '), irow, 0)

        self.lay_grid = lay_grid  # used in UiScrllLayout

        return

    def changeCrop(self):
        '''

        '''
        crop_name = self.w_combo00.currentText()

        t_grow = self.crop_vars[crop_name]['t_grow']
        self.w_tgrow.setText(str(t_grow))

        return

    def UiControlPanel(self):
        '''
        method for constructing control panel
        '''
        w_clr_crps = QPushButton("Clear crops")
        w_clr_crps.setFixedWidth(65)
        w_clr_crps.clicked.connect(self.resetClicked)

        w_reset = QPushButton("Reset")
        w_reset.setFixedWidth(65)
        w_reset.clicked.connect(self.resetClicked)

        w_submit = QPushButton("Save")
        helpText = 'Save management detail, write to file and close'
        w_submit.setToolTip(helpText)
        w_submit.setFixedWidth(65)
        w_submit.setEnabled(True)
        w_submit.clicked.connect(self.saveCropParsClicked)
        self.w_submit = w_submit

        w_dismiss = QPushButton("Dismiss")
        w_dismiss.setFixedWidth(65)
        w_dismiss.clicked.connect(self.dismissClicked)

        lay_hbox_cntrl = QHBoxLayout()
        lay_hbox_cntrl.addWidget(w_clr_crps)
        lay_hbox_cntrl.addWidget(w_submit)
        lay_hbox_cntrl.addWidget(w_reset)
        lay_hbox_cntrl.addWidget(w_dismiss)

        self.lay_hbox_cntrl = lay_hbox_cntrl

        return

    def saveCropParsClicked(self, dummy):
        '''
        gather all fields
        '''
        crop_name = self.w_combo00.currentText()
        t_grow = int(self.w_tgrow.text())

        pi_tonnes, pi_props = plant_inputs_crops_distribution(t_grow)
        self.crop_vars[crop_name]['pi_tonnes'] = pi_tonnes
        self.crop_vars[crop_name]['pi_prop'] = pi_props
        self.crop_vars[crop_name]['t_grow'] = t_grow

        print('Updated ' + crop_name)
        QApplication.processEvents()

        return

    def dismissClicked(self):

        self.close()

    def resetClicked(self):
        '''

        '''
        pass

    def UiScrllLayout(self):
        '''
        method for laying out UI
        '''
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
        '''

        '''
        close = QMessageBox()
        close.setText("You sure?")
        close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        close = close.exec()

        if close == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

        return
