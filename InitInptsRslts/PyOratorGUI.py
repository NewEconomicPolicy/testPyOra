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
from PyQt5.QtWidgets import QLabel, QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, \
                                                    QComboBox, QPushButton, QCheckBox, QFileDialog, QTextEdit
from subprocess import Popen, DEVNULL

from initialise_pyorator import read_config_file, initiation, write_config_file

from ora_excel_write import retrieve_output_xls_files
from ora_economics_model import test_economics_algorithms
from livestock_output_data import write_livestock_charts
from ora_cn_model import run_soil_cn_algorithms
from ora_excel_read import check_excel_input_file
from ora_json_read import check_json_input_files
from display_gui_charts import display_metric
from ora_lookup_df_fns import fetch_defn_units_from_pyora_display, fetch_pyora_varname_from_pyora_display
from ora_low_level_fns import extend_out_dir, gui_optimisation_cycle
from set_up_logging import OutLog

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
        strt_line = 0   # main layout is a grid therefore line and row spacing is important

        # grid will be put in RH vertical box
        # ===================================
        grid = QGridLayout()
        grid.setSpacing(10)	    # set spacing between widgets

        # line 0 for study details
        # ========================
        w_study = QLabel()
        grid.addWidget(w_study, strt_line + 1, 0, 1, 5)
        self.w_study = w_study

        # rows 2 and 3
        # ============
        w_inp_xls = QPushButton("Parameters file")
        helpText = 'Select an Orator Excel inputs file comprising crop and nitrogen parameters, weather'
        w_inp_xls.setToolTip(helpText)
        grid.addWidget(w_inp_xls, strt_line + 2, 0)
        w_inp_xls.clicked.connect(self.fetchInpExcel)

        w_lbl13 = QLabel('')
        grid.addWidget(w_lbl13, strt_line + 2, 1, 1, 5)
        self.w_lbl13 = w_lbl13

        # for message from check_xls_fname
        # ================================
        w_lbl14 = QLabel('')
        grid.addWidget(w_lbl14, strt_line + 3, 0, 1, 2)
        self.w_lbl14 = w_lbl14

        # rows 4 and 5
        # ============
        w_inp_json = QPushButton("Management files")
        helpText = 'Select a file location with JSON files comprising management data for steady state and forward run'
        w_inp_json.setToolTip(helpText)
        grid.addWidget(w_inp_json, strt_line + 4, 0)
        w_inp_json.clicked.connect(self.fetchInpJson)

        w_lbl06 = QLabel('')
        grid.addWidget(w_lbl06, strt_line + 4, 1, 1, 5)
        self.w_lbl06 = w_lbl06

        # line 5 - for message from check_json_fname
        # ==========================================
        w_lbl07 = QLabel('')
        grid.addWidget(w_lbl07, strt_line + 5, 1, 1, 5)
        self.w_lbl07 = w_lbl07

        # line 7: carbon
        # ==============
        w_disp_c = QPushButton('Display C metric')
        helpText = 'Display carbon chart'
        w_disp_c.setToolTip(helpText)
        w_disp_c.clicked.connect(lambda: self.displayMetric(self.w_combo07, 'carbon'))
        w_disp_c.setEnabled(False)
        self.w_disp_c = w_disp_c
        grid.addWidget(w_disp_c, strt_line + 7, 0)

        w_combo07 = QComboBox()
        w_combo07.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo07))
        self.w_combo07 = w_combo07
        grid.addWidget(w_combo07, strt_line + 7, 1, 1, 2)

        # line 8: nitrogen
        # ================
        w_disp_n = QPushButton('Display N metric')
        helpText = 'Display nitrogen chart'
        w_disp_n.setToolTip(helpText)
        w_disp_n.setEnabled(False)
        w_disp_n.clicked.connect(lambda: self.displayMetric(self.w_combo08, 'nitrogen'))
        self.w_disp_n = w_disp_n
        grid.addWidget(w_disp_n, strt_line + 8, 0)

        w_combo08 = QComboBox()
        w_combo08.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo08))
        self.w_combo08 = w_combo08
        grid.addWidget(w_combo08, strt_line + 8, 1, 1, 2)

        # line 9: water
        # =============
        w_disp_w = QPushButton('Display water metric')
        helpText = 'Display water chart'
        w_disp_w.setToolTip(helpText)
        w_disp_w.clicked.connect(lambda: self.displayMetric(self.w_combo09, 'soil_water'))
        w_disp_w.setEnabled(False)
        self.w_disp_w = w_disp_w
        grid.addWidget(w_disp_w, strt_line + 9, 0)

        w_combo09 = QComboBox()
        w_combo09.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo09))
        self.w_combo09 = w_combo09
        grid.addWidget(w_combo09, strt_line + 9, 1, 1, 2)

        # line 10: crop model
        # ===================
        w_disp_cm = QPushButton('Display crop model metric')
        helpText = 'Display crop model chart'
        w_disp_cm.setToolTip(helpText)
        w_disp_cm.clicked.connect(lambda: self.displayMetric(self.w_combo10, 'crop_model'))
        w_disp_cm.setEnabled(False)
        self.w_disp_cm = w_disp_cm
        grid.addWidget(w_disp_cm, strt_line + 10, 0)

        w_combo10 = QComboBox()
        w_combo10.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo10))
        self.w_combo10 = w_combo10
        grid.addWidget(w_combo10, strt_line + 10, 1, 1, 2)

        grid.addWidget(QLabel(), strt_line + 11, 0, )   # spacer

        # row 15
        # ======
        w_out_dir = QPushButton("Outputs directory")
        helpText = 'Select a file path for Excel outputs files'
        w_out_dir.setToolTip(helpText)
        grid.addWidget(w_out_dir, strt_line + 15, 0)
        w_out_dir.clicked.connect(self.fetchOutDir)

        w_lbl15 = QLabel('')
        grid.addWidget(w_lbl15, strt_line + 15, 1, 1, 5)
        self.w_lbl15 = w_lbl15

        # line 16: generate Excel files
        # =============================
        w_make_xls = QCheckBox('Write Excel output files')
        helpText = 'Writing Excel files is slow'
        w_make_xls.setToolTip(helpText)
        w_make_xls.setChecked(True)
        grid.addWidget(w_make_xls, strt_line + 16, 0, 1, 2)
        self.w_make_xls = w_make_xls

        # line 17: display output
        # ========================
        w_disp_out = QPushButton('Display output')
        helpText = 'Display output Excel files'
        w_disp_out.setToolTip(helpText)
        w_disp_out.clicked.connect(self.displayXlsxOutput)
        self.w_disp_out = w_disp_out
        grid.addWidget(w_disp_out, strt_line + 17, 0)

        w_combo17 = QComboBox()
        self.w_combo17 = w_combo17
        grid.addWidget(w_combo17, strt_line + 17, 1, 1, 3)

        # user feedback
        # =============
        w_opt_cycle = QLabel(gui_optimisation_cycle(self))
        grid.addWidget(w_opt_cycle, strt_line + 18, 1, 1, 6)
        self.w_opt_cycle = w_opt_cycle

        # line 19
        # =======
        w_economics = QPushButton('Economics')
        helpText = 'Runs ORATOR economics model'
        w_economics.setToolTip(helpText)
        # w_economics.setEnabled(False)
        w_economics.clicked.connect(self.runEconomicsClicked)
        grid.addWidget(w_economics, strt_line + 19, 0)
        self.w_economics = w_economics

        w_livestock = QPushButton('Livestock')
        helpText = 'Runs ORATOR livestock model'
        w_livestock.setToolTip(helpText)
        w_livestock.clicked.connect(self.runLivestockClicked)
        grid.addWidget(w_livestock, strt_line + 19, 1)
        self.w_livestock = w_livestock

        w_soil_cn = QPushButton('Soil C and N')
        helpText = 'Runs ORATOR soil carbon and nitrogen code'
        w_soil_cn.setToolTip(helpText)
        w_soil_cn.setEnabled(False)
        w_soil_cn.clicked.connect(self.runSoilCnClicked)
        grid.addWidget(w_soil_cn, strt_line + 19, 2)
        self.w_soil_cn = w_soil_cn

        w_optimise = QPushButton('Optimise')
        helpText = 'Optimisation - not ready'
        w_optimise.setToolTip(helpText)
        w_optimise.setEnabled(False)
        w_optimise.clicked.connect(self.runOptimiseClicked)
        grid.addWidget(w_optimise, strt_line + 19, 3)
        self.w_optimise = w_optimise

        w_save = QPushButton("Save", self)
        helpText = 'save the configuration file'
        w_save.setToolTip(helpText)
        grid.addWidget(w_save, strt_line + 19, 6)
        w_save.clicked.connect(self.saveClicked)

        w_exit = QPushButton("Exit", self)
        helpText = 'Close GUI - the configuration file will be saved'
        w_exit.setToolTip(helpText)
        grid.addWidget(w_exit, strt_line + 19, 7)
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
        w_report.setMinimumHeight(175)
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

    def fetchOutDir(self):

        dirname_cur = self.w_lbl15.text()
        dirname = QFileDialog.getExistingDirectory(self, 'Select directory', dirname_cur)
        if dirname != '' and dirname != dirname_cur:
            self.w_lbl15.setText(dirname)

    def fetchInpJson(self):
        '''
        when the directory changes disable display push buttons
        '''
        dirname_cur = self.w_lbl06.text()
        dirname = QFileDialog.getExistingDirectory(self, 'Select directory', dirname_cur)
        if dirname != '' and dirname != dirname_cur:
            self.w_lbl06.setText(dirname)
            self.w_lbl07.setText(check_json_input_files(self, dirname, 'mgmt'))
            print(check_json_input_files(self, dirname, 'lvstck'))
            self.w_disp_c.setEnabled(False)
            self.w_disp_n.setEnabled(False)
            self.w_disp_w.setEnabled(False)
            self.w_disp_cm.setEnabled(False)
            self.w_disp_out.setEnabled(False)
            self.w_livestock.setEnabled(False)
            extend_out_dir(self)
            retrieve_output_xls_files(self)

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

        write_livestock_charts(self)

    def runSoilCnClicked(self):

        run_soil_cn_algorithms(self)

    def fetchInpExcel(self):
        """
        QFileDialog returns a tuple for Python 3.5 onwards
        """
        fname = self.w_lbl13.text()
        fname, dummy = QFileDialog.getOpenFileName(self, 'Open file', fname, 'Excel files (*.xlsx)')
        if fname != '':
            self.w_lbl13.setText(fname)
            self.w_lbl14.setText(check_excel_input_file(self, fname))

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
            self.lgr.handlers[0].close()
        except AttributeError:
            pass

        self.close()

def main():
    """
    program entry point
    """
    app = QApplication(sys.argv)  # create QApplication object
    form = Form() # instantiate form
    # display the GUI and start the event loop if we're not running batch mode
    form.show()             # paint form
    sys.exit(app.exec_())   # start event loop

if __name__ == '__main__':
    main()
