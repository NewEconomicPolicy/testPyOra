#-------------------------------------------------------------------------------
# Name:        PyOratorGUI.py
# Purpose:     main module for PyOrator
# Author:      Mike Martin
# Created:     11/12/2019
# Licence:     <your licence>
# Description:
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'PyOratorGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import QLabel, QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QLineEdit, \
                                                    QComboBox, QPushButton, QCheckBox, QFileDialog, QTextEdit
from subprocess import Popen, DEVNULL

from initialise_pyorator import read_config_file, initiation, write_config_file
from ora_economics_model import test_economics_algorithms
from livestock_output_data import calc_livestock_data
from ora_cn_model import run_soil_cn_algorithms, recalc_soil_cn
from ora_excel_read import ReadStudy
from ora_json_read import check_json_xlsx_inp_files, disp_ow_parms
from display_gui_charts import display_metric
from ora_lookup_df_fns import fetch_defn_units_from_pyora_display, fetch_pyora_varname_from_pyora_display
from ora_low_level_fns import gui_optimisation_cycle
from set_up_logging import OutLog

STD_FLD_SIZE = 60
STD_BTN_SIZE = 100
STD_CMBO_SIZE = 150

class Form(QWidget):
    '''
   define two vertical boxes - in LH vertical box put the painter and in RH put the grid
   define main horizontal box to put LH and RH vertical boxes in
   grid layout consists of combo boxes, labels and buttons
   '''
    def __init__(self, parent=None):

        super(Form, self).__init__(parent)

        self.version = 'PyOrator_v2'
        initiation(self)
        font = QFont(self.font())
        font.setPointSize(font.pointSize() + 2)
        self.setFont(font)
        irow = 0   # main layout is a grid therefore line and row spacing is important

        # grid will be put in RH vertical box
        # ===================================
        grid = QGridLayout()
        grid.setSpacing(10)	    # set spacing between widgets

        # line 0 for study details
        # ========================
        irow += 1
        w_study = QLabel()
        grid.addWidget(w_study, irow, 0, 1, 5)
        self.w_study = w_study

        # rows 4 and 5
        # ============
        irow += 1
        w_inp_json = QPushButton('Run file location')
        helpText = 'Location with a project file set comprising: livestock JSON file '
        helpText += 'and an Excel file with a farm location, management, soil and weather sheets'
        w_inp_json.setToolTip(helpText)
        grid.addWidget(w_inp_json, irow, 0)
        w_inp_json.clicked.connect(self.fetchInpJson)

        w_lbl06 = QLabel('')
        grid.addWidget(w_lbl06, irow, 1, 1, 5)
        self.w_lbl06 = w_lbl06

        # for message describing project files
        # ====================================
        irow += 1
        w_lbl07 = QLabel('')
        grid.addWidget(w_lbl07, irow, 0, 1, 5)
        self.w_lbl07 = w_lbl07

        # line 7: carbon
        # ==============
        irow += 1
        w_disp_c = QPushButton('Display C metric')
        helpText = 'Display carbon chart'
        w_disp_c.setToolTip(helpText)
        w_disp_c.clicked.connect(lambda: self.displayMetric(self.w_combo07, 'carbon'))
        w_disp_c.setEnabled(False)
        self.w_disp_c = w_disp_c
        grid.addWidget(w_disp_c, irow, 0)

        w_combo07 = QComboBox()
        w_combo07.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo07))
        self.w_combo07 = w_combo07
        grid.addWidget(w_combo07, irow, 1, 1, 2)

        # line 8: nitrogen
        # ================
        irow += 1
        w_disp_n = QPushButton('Display N metric')
        helpText = 'Display nitrogen chart'
        w_disp_n.setToolTip(helpText)
        w_disp_n.setEnabled(False)
        w_disp_n.clicked.connect(lambda: self.displayMetric(self.w_combo08, 'nitrogen'))
        self.w_disp_n = w_disp_n
        grid.addWidget(w_disp_n, irow, 0)

        w_combo08 = QComboBox()
        w_combo08.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo08))
        self.w_combo08 = w_combo08
        grid.addWidget(w_combo08, irow, 1, 1, 2)

        # line 9: water
        # =============
        irow += 1
        w_disp_w = QPushButton('Display water metric')
        helpText = 'Display water chart'
        w_disp_w.setToolTip(helpText)
        w_disp_w.clicked.connect(lambda: self.displayMetric(self.w_combo09, 'soil_water'))
        w_disp_w.setEnabled(False)
        self.w_disp_w = w_disp_w
        grid.addWidget(w_disp_w, irow, 0)

        w_combo09 = QComboBox()
        w_combo09.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo09))
        self.w_combo09 = w_combo09
        grid.addWidget(w_combo09, irow, 1, 1, 2)

        # crop model
        # ==========
        irow += 1
        w_disp_cm = QPushButton('Crop production')
        helpText = 'Display crop model charts'
        w_disp_cm.setToolTip(helpText)
        w_disp_cm.clicked.connect(lambda: self.displayMetric(self.w_combo10, 'crop_model'))
        w_disp_cm.setEnabled(False)
        self.w_disp_cm = w_disp_cm
        grid.addWidget(w_disp_cm, irow, 0)

        w_combo10 = QComboBox()
        w_combo10.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo10))
        self.w_combo10 = w_combo10
        grid.addWidget(w_combo10, irow, 1, 1, 2)

        # Livestock
        # ==========
        irow += 1
        w_disp_econ = QPushButton('Livestock, Economics')
        helpText = 'Display Livestock and Economics related charts'
        w_disp_econ.setToolTip(helpText)
        w_disp_econ.clicked.connect(lambda: self.displayMetric(self.w_combo11, 'livestock'))
        w_disp_econ.setEnabled(False)
        self.w_disp_econ = w_disp_econ
        grid.addWidget(w_disp_econ, irow, 0)

        w_combo11 = QComboBox()
        w_combo11.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo11))
        self.w_combo11 = w_combo11
        grid.addWidget(w_combo11, irow, 1, 1, 2)

        irow += 1
        grid.addWidget(QLabel(), irow, 0)  # spacer

        # extra organic waste
        # ===================
        irow += 1
        w_recalc = QPushButton('Recalculate')
        helpText = 'Examine the impact of changing the rate of organic waste applied to the foward run after ' + \
                                                                                    'steady state has been reached.'
        w_recalc.setToolTip(helpText)
        w_recalc.clicked.connect(self.recalcClicked)
        w_recalc.setEnabled(False)
        self.w_recalc = w_recalc
        grid.addWidget(w_recalc, irow, 0)

        lbl13a = QLabel('Extra organic waste applied - Min:')
        lbl13a.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl13a, irow, 1)

        w_owex_min = QLineEdit()
        # w_owex_min.textChanged[str].connect(self.studyTextChanged)
        w_owex_min.setFixedWidth(STD_FLD_SIZE)
        grid.addWidget(w_owex_min, irow, 2)
        self.w_owex_min = w_owex_min

        lbl13b = QLabel('Type of organic waste applied:')
        lbl13b.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl13b, irow, 3)

        w_combo13 = QComboBox()
        w_combo13.currentIndexChanged[str].connect(self.displayOwParms)
        self.w_combo13 = w_combo13
        grid.addWidget(w_combo13, irow, 4)

        # max application and month
        # =========================
        irow += 1
        lbl13a = QLabel(' (t ha-1 y-1) - Max:')
        lbl13a.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl13a, irow, 1)

        w_owex_max = QLineEdit()
        # w_owex_max.textChanged[str].connect(self.studyTextChanged)
        w_owex_max.setFixedWidth(STD_FLD_SIZE)
        grid.addWidget(w_owex_max, irow, 2)
        self.w_owex_max = w_owex_max

        lbl13c = QLabel('Month of application:')
        lbl13c.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl13c, irow, 3)

        w_mnth_appl = QComboBox()
        # w_mnth_appl.textChanged[str].connect(self.studyTextChanged)
        w_mnth_appl.setFixedWidth(STD_FLD_SIZE)
        grid.addWidget(w_mnth_appl, irow, 4)
        self.w_mnth_appl = w_mnth_appl

        # display organic waste summary
        # =============================
        irow += 1
        w_lbl_ow = QLabel('')
        grid.addWidget(w_lbl_ow, irow, 0, 1, 6)
        self.w_lbl_ow = w_lbl_ow

        irow += 1
        grid.addWidget(QLabel(), irow, 0)  # spacer

        # line 16: generate Excel files
        # =============================
        irow += 1
        w_make_xls = QCheckBox('Write Excel output files')
        helpText = 'Writing Excel files is slow'
        w_make_xls.setToolTip(helpText)
        w_make_xls.setChecked(True)
        grid.addWidget(w_make_xls, irow, 0, 1, 2)
        self.w_make_xls = w_make_xls

        # line 17: display output
        # ========================
        irow += 1
        w_disp_out = QPushButton('Display output')
        helpText = 'Display output Excel files'
        w_disp_out.setToolTip(helpText)
        w_disp_out.clicked.connect(self.displayXlsxOutput)
        self.w_disp_out = w_disp_out
        grid.addWidget(w_disp_out, irow, 0)

        w_combo17 = QComboBox()
        self.w_combo17 = w_combo17
        grid.addWidget(w_combo17, irow, 1)

        # user feedback
        # =============
        irow += 1
        w_opt_cycle = QLabel(gui_optimisation_cycle(self))
        grid.addWidget(w_opt_cycle, irow, 1, 1, 6)
        self.w_opt_cycle = w_opt_cycle

        # line 19
        # =======
        irow += 1
        w_economics = QPushButton('Economics')
        helpText = 'Runs ORATOR economics model'
        w_economics.setToolTip(helpText)
        # w_economics.setEnabled(False)
        w_economics.setFixedWidth(STD_BTN_SIZE)
        w_economics.clicked.connect(self.runEconomicsClicked)
        grid.addWidget(w_economics, irow, 0)
        self.w_economics = w_economics

        w_livestock = QPushButton('Livestock')
        helpText = 'Runs ORATOR livestock model'
        w_livestock.setToolTip(helpText)
        w_livestock.setEnabled(False)
        w_livestock.setFixedWidth(STD_BTN_SIZE)
        w_livestock.clicked.connect(self.runLivestockClicked)
        grid.addWidget(w_livestock, irow, 1)
        self.w_livestock = w_livestock

        w_soil_cn = QPushButton('Soil C and N')
        helpText = 'Runs ORATOR soil carbon and nitrogen code'
        w_soil_cn.setToolTip(helpText)
        w_soil_cn.setEnabled(False)
        w_soil_cn.setFixedWidth(STD_BTN_SIZE)
        w_soil_cn.clicked.connect(self.runSoilCnClicked)
        grid.addWidget(w_soil_cn, irow, 2)
        self.w_soil_cn = w_soil_cn

        w_optimise = QPushButton('Optimise')
        helpText = 'Optimisation - not ready'
        w_optimise.setToolTip(helpText)
        w_optimise.setEnabled(False)
        w_optimise.setFixedWidth(STD_BTN_SIZE)
        w_optimise.clicked.connect(self.runOptimiseClicked)
        grid.addWidget(w_optimise, irow, 3)
        self.w_optimise = w_optimise

        w_save = QPushButton('Save', self)
        helpText = 'save the configuration file'
        w_save.setToolTip(helpText)
        w_save.setFixedWidth(STD_BTN_SIZE)
        grid.addWidget(w_save, irow, 6)
        w_save.clicked.connect(self.saveClicked)

        w_exit = QPushButton('Exit', self)
        helpText = 'Close GUI - the configuration file will be saved'
        w_exit.setToolTip(helpText)
        grid.addWidget(w_exit, irow, 7)
        w_exit.clicked.connect(self.exitClicked)

        # LH vertical box consists of png image
        # =====================================
        lh_vbox = QVBoxLayout()

        lbl20 = QLabel()
        lbl20.setPixmap(QPixmap(self.settings['fname_png']))
        lh_vbox.addWidget(lbl20)

        # add grid consisting of combo boxes, labels and buttons to RH vertical box
        # =========================================================================
        rh_vbox = QVBoxLayout()
        rh_vbox.addLayout(grid)

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

        # add LH and RH vertical boxes to main horizontal box
        # ===================================================
        main_hbox = QHBoxLayout()
        main_hbox.setSpacing(10)
        main_hbox.addLayout(lh_vbox)
        main_hbox.addLayout(rh_vbox, stretch = 1)

        # feed horizontal boxes into the window
        # =====================================
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(main_hbox)
        outer_layout.addLayout(bot_hbox)
        self.setLayout(outer_layout)

        # posx, posy, width, height
        self.setGeometry(500, 100, 750, 400)
        self.setWindowTitle('Run ORATOR analysis')

        # reads and set values from last run
        # ==================================
        read_config_file(self)
        sys.stdout = OutLog(self.w_report, sys.stdout)
        # sys.stderr = OutLog(self.w_report, sys.stderr, QColor(255, 0, 0))

    def recalcClicked(self):

        recalc_soil_cn(self)

        return

    def displayOwParms(self):

        self.w_lbl_ow.setText(disp_ow_parms(self))

        return

    def fetchInpJson(self):
        '''
        when the directory changes disable display push buttons
        '''
        mgmt_dir_cur = self.w_lbl06.text()
        mgmt_dir = QFileDialog.getExistingDirectory(self, 'Select directory', mgmt_dir_cur)
        if mgmt_dir != '' and mgmt_dir != mgmt_dir_cur:
            self.w_lbl06.setText(mgmt_dir)
            self.w_lbl07.setText(check_json_xlsx_inp_files(self, mgmt_dir))
            self.w_disp_c.setEnabled(False)
            self.w_disp_n.setEnabled(False)
            self.w_disp_w.setEnabled(False)
            self.w_disp_cm.setEnabled(False)
            self.w_disp_econ.setEnabled(False)
            self.w_recalc.setEnabled(False)
            self.w_disp_out.setEnabled(False)
            self.w_livestock.setEnabled(False)
            self.settings['study'] = ReadStudy(self, mgmt_dir)

    def changeHelpText(self, w_combo):
        '''
        modify help text according to metric
        '''
        metric = w_combo.currentText()
        defn, units = fetch_defn_units_from_pyora_display(self.settings['lookup_df'], metric)
        helpText = 'Display ' + defn
        w_combo.setToolTip(helpText)

    def displayMetric(self, w_combo, group):

        display_name = w_combo.currentText()
        metric = fetch_pyora_varname_from_pyora_display(self.settings['lookup_df'], display_name)
        if metric is not None:
            display_metric(self, group, metric)

    def displayXlsxOutput(self):

        excel_file = self.settings['out_dir'] + '\\' + self.w_combo17.currentText()
        excel_path = self.settings['excel_path']
        junk = Popen(list([excel_path, excel_file]), stdout = DEVNULL)
        '''
        import signal
        os.kill(junk.pid, signal.SIGTERM)
        '''

    def runEconomicsClicked(self):

        test_economics_algorithms(self)

    def runOptimiseClicked(self):

        pass

    def runLivestockClicked(self):

        calc_livestock_data(self)

    def runSoilCnClicked(self):

        run_soil_cn_algorithms(self)

    def cancelClicked(self):

        self.close_down()

    def saveClicked(self):

        write_config_file(self)  # write last GUI selections

    def exitClicked(self):

        write_config_file(self)  # write last GUI selections
        self.close_down()

    def close_down(self):
        '''
        exit cleanly
        '''

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
    '''
    program entry point
    '''
    app = QApplication(sys.argv)  # create QApplication object
    form = Form() # instantiate form
    # display the GUI and start the event loop if we're not running batch mode
    form.show()             # paint form
    sys.exit(app.exec_())   # start event loop

if __name__ == '__main__':
    main()
