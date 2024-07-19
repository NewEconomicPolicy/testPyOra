# -------------------------------------------------------------------------------
# Name:        PyOratorGUI.py
# Purpose:     main module for PyOrator
# Author:      Mike Martin
# Created:     11/12/2019
# Licence:     <your licence>
# Description:
#
# -------------------------------------------------------------------------------
__prog__ = 'PyOratorGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

import sys
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtWidgets import (QLabel, QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout,
                                                                                        QPushButton, QTextEdit)
from multiTabsGUI import AllTabs

from initialise_pyorator import read_config_file, initiation, write_config_file

from set_up_logging import OutLog

STD_FLD_SIZE = 60
STD_BTN_SIZE = 75
STD_CMBO_SIZE = 150

class Form(QWidget):
    """
   define two vertical boxes - in LH vertical box put the painter and in RH put the grid
   define main horizontal box to put LH and RH vertical boxes in
   grid layout consists of combo boxes, labels and buttons
   """
    def __init__(self, parent=None):

        super(Form, self).__init__(parent)

        self.version = 'PyOrator_v2'
        initiation(self)
        font = QFont(self.font())
        font.setPointSize(font.pointSize() + 2)
        self.setFont(font)

        # grid will be put in RH vertical box
        # ===================================
        grid = QGridLayout()
        grid.setSpacing(10)	    # set spacing between widgets

        w_tab_wdgt = AllTabs(self.settings, self.lggr, self.ora_parms, self.wthr_sets, self.wthr_rsrces_gnrc,
                                                                                                    self.anml_prodn)
        grid.addWidget(w_tab_wdgt, 0, 0, 20, 8)  # row, column, rowSpan, columnSpan
        self.w_tab_wdgt = w_tab_wdgt

        irow = 20  # main layout is a grid therefore line and row spacing is important

        w_clr_psh = QPushButton('Clear', self)
        helpText = 'Clear reporting window'
        w_clr_psh.setToolTip(helpText)
        w_clr_psh.setFixedWidth(STD_BTN_SIZE)
        grid.addWidget(w_clr_psh, irow, 4)
        w_clr_psh.clicked.connect(self.clearReporting)

        w_cancel = QPushButton('Cancel', self)
        helpText = 'leave program without saving the configuration file'
        w_cancel.setToolTip(helpText)
        w_cancel.setFixedWidth(STD_BTN_SIZE)
        grid.addWidget(w_cancel, irow, 5)
        w_cancel.clicked.connect(self.cancelClicked)

        w_save = QPushButton('Save', self)
        helpText = 'save the configuration file'
        w_save.setToolTip(helpText)
        w_save.setFixedWidth(STD_BTN_SIZE)
        grid.addWidget(w_save, irow, 6)
        w_save.clicked.connect(self.saveClicked)

        w_exit = QPushButton('Exit', self)
        helpText = 'Close GUI - the configuration file will be saved'
        w_exit.setToolTip(helpText)
        w_exit.setFixedWidth(STD_BTN_SIZE)
        grid.addWidget(w_exit, irow, 7)
        w_exit.clicked.connect(self.exitClicked)

        # LH vertical box consists of png image
        # =====================================
        lh_vbox = QVBoxLayout()

        lbl20 = QLabel()
        lbl20.setPixmap(QPixmap(self.settings['fname_png']))
        lbl20.setScaledContents(True)
        lh_vbox.addWidget(lbl20)

        # add grid consisting of combo boxes, labels and buttons to RH vertical box
        # =========================================================================
        rh_vbox = QVBoxLayout()
        rh_vbox.addLayout(grid)

        # add LH and RH vertical boxes to main horizontal box
        # ===================================================
        main_hbox = QHBoxLayout()
        main_hbox.setSpacing(10)
        main_hbox.addLayout(lh_vbox)
        main_hbox.addLayout(rh_vbox, stretch = 1)

        # add reporting
        # =============
        bot_hbox = QHBoxLayout()
        w_report = QTextEdit()
        w_report.verticalScrollBar().minimum()
        w_report.setMinimumHeight(250)
        w_report.setMinimumWidth(1000)
        w_report.setStyleSheet('font: bold 10.5pt Courier')  # big jump to 11pt
        bot_hbox.addWidget(w_report, 1)
        self.w_report = w_report

        # feed horizontal boxes into the window
        # =====================================
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(main_hbox)
        outer_layout.addLayout(bot_hbox)
        self.setLayout(outer_layout)

        self.setGeometry(100, 50, 750, 400)     # posx, posy, width, height
        self.setWindowTitle('Run ORATOR analysis')

        # reads and set values from last run
        # ==================================
        read_config_file(self)
        sys.stdout = OutLog(self.w_report, sys.stdout)
        # sys.stderr = OutLog(self.w_report, sys.stderr, QColor(255, 0, 0))   # RGB

    def clearReporting(self):
        #
        self.w_report.clear()

    def cancelClicked(self):

        self.close_down()

    def saveClicked(self):

        write_config_file(self)  # write last GUI selections

    def exitClicked(self):
        write_config_file(self)  # write last GUI selections
        self.close_down()

    def close_down(self):
        """
        exit cleanly
        """

        # close various files
        # ===================
        if hasattr(self, 'fobjs'):
            for key in self.fobjs:
                self.fobjs[key].close()

        # close logging
        # =============
        try:
            self.lggr.handlers[0].close()
        except AttributeError:
            pass

        self.close()

def main():
    """
    program entry point
    The splash screen is controlled from within Python by the pyi_splash module, which can be imported at runtime.
    This module cannot be installed by a package manager because it is part of PyInstaller and is included as needed.
    """
    try:
        import pyi_splash

        # Update the text on the splash screen
        # ====================================
        pyi_splash.update_text("Loading PyOratorGUI exe file - this may take some seconds...")

        # the splash screen remains open until this function is called or the Python program is terminated.
        pyi_splash.close()
    except:
        pass

    app = QApplication(sys.argv)  # create QApplication object
    form = Form() # instantiate form
    # display the GUI and start the event loop if we're not running batch mode
    form.show()             # paint form
    sys.exit(app.exec_())   # start event loop

if __name__ == '__main__':
    main()
