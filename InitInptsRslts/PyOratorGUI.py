#-------------------------------------------------------------------------------
# Name:
# Purpose:     Creates a GUI with five adminstrative levels plus country
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
# Decription:
#       if climate weather sets and HWSD data are not found then use spreadsheet only for input data
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'PyOratorGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

import sys
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QWidget, QApplication, QHBoxLayout, QVBoxLayout, QGridLayout, QLineEdit, \
                                                                        QComboBox, QPushButton, QCheckBox, QFileDialog
from subprocess import Popen, DEVNULL

from initialise_pyorator import read_config_file, initiation, write_config_file
from ora_economics_model import test_economics_algorithms
from ora_livestock_model import test_livestock_algorithms
from ora_cn_model import run_soil_cn_algorithms
from ora_excel_read import check_excel_input_file
from ora_json_read import check_json_input_files
from display_gui_charts import display_metric
from ora_lookup_df_fns import fetch_variable_definition, fetch_pyora_varname_from_pyora_display
from ora_low_level_fns import optimisation_cycle

class Form(QWidget):

    def __init__(self, parent=None):

        super(Form, self).__init__(parent)

        self.version = 'PyOrator_v2'
        initiation(self)
        # define two vertical boxes, in LH vertical box put the painter and in RH put the grid
        # define horizon box to put LH and RH vertical boxes in
        hbox = QHBoxLayout()
        hbox.setSpacing(10)

        # left hand vertical box consists of png image
        # ============================================
        lh_vbox = QVBoxLayout()

        # LH vertical box contains image only
        lbl20 = QLabel()
        pixmap = QPixmap(self.settings['fname_png'])
        lbl20.setPixmap(pixmap)

        lh_vbox.addWidget(lbl20)

        # add LH vertical box to horizontal box
        hbox.addLayout(lh_vbox)

        # right hand box consists of combo boxes, labels and buttons
        # ==========================================================
        rh_vbox = QVBoxLayout()

        # The layout is done with the QGridLayout
        grid = QGridLayout()
        grid.setSpacing(10)	# set spacing between widgets

        # line 0 for study details
        # ========================
        w_study = QLabel()
        grid.addWidget(w_study, 1, 0, 1, 5)
        self.w_study = w_study

        # rows 2 and 3
        # ============
        w_inp_xls = QPushButton("Parameters file")
        helpText = 'Select an Orator Excel inputs file comprising crop and nitrogen parameters, weather'
        w_inp_xls.setToolTip(helpText)
        grid.addWidget(w_inp_xls, 2, 0)
        w_inp_xls.clicked.connect(self.fetchInpExcel)

        w_lbl13 = QLabel('')
        grid.addWidget(w_lbl13, 2, 1, 1, 5)
        self.w_lbl13 = w_lbl13

        # for message from check_xls_fname
        # ================================
        w_lbl14 = QLabel('')
        grid.addWidget(w_lbl14, 3, 0, 1, 2)
        self.w_lbl14 = w_lbl14

        # rows 4 and 5
        # ============
        w_inp_json = QPushButton("Management files")
        helpText = 'Select a file location with JSON files comprising management data for steady state and forward run'
        w_inp_json.setToolTip(helpText)
        grid.addWidget(w_inp_json, 4, 0)
        w_inp_json.clicked.connect(self.fetchInpJson)

        w_lbl06 = QLabel('')
        grid.addWidget(w_lbl06, 4, 1, 1, 5)
        self.w_lbl06 = w_lbl06

        # line 5
        # ======
        w_use_json = QCheckBox('Use JSON files')
        helpText = 'Will use JSON files for management instead of Inputs3b and Inputs3d sheets in Excel inputs file'
        w_use_json.setToolTip(helpText)
        w_use_json.setChecked(True)
        grid.addWidget(w_use_json, 5, 0, 1, 2)
        self.w_use_json = w_use_json

        # for message from check_json_fname
        w_lbl07 = QLabel('')
        grid.addWidget(w_lbl07, 5, 1, 1, 5)
        self.w_lbl07 = w_lbl07

        # line 7: carbon
        # ==============
        w_disp_c = QPushButton('Display C metric')
        helpText = 'Display carbon chart'
        w_disp_c.setToolTip(helpText)
        w_disp_c.clicked.connect(lambda: self.displayMetric(self.w_combo07, 'carbon'))
        w_disp_c.setEnabled(False)
        self.w_disp_c = w_disp_c
        grid.addWidget(w_disp_c, 7, 0)

        w_combo07 = QComboBox()
        w_combo07.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo07))
        self.w_combo07 = w_combo07
        grid.addWidget(w_combo07, 7, 1, 1, 2)

        w_min_wat = QLineEdit()
        grid.addWidget(w_min_wat, 7, 3)
        w_min_wat.setFixedWidth(60)
        self.w_min_wat = w_min_wat

        w_max_wat = QLineEdit()
        grid.addWidget(w_max_wat, 7, 4)
        w_max_wat.setFixedWidth(60)
        self.w_max_wat = w_max_wat

        # line 8: nitrogen
        # ================
        w_disp_n = QPushButton('Display N metric')
        helpText = 'Display nitrogen chart'
        w_disp_n.setToolTip(helpText)
        w_disp_n.setEnabled(False)
        w_disp_n.clicked.connect(lambda: self.displayMetric(self.w_combo08, 'nitrogen'))
        self.w_disp_n = w_disp_n
        grid.addWidget(w_disp_n, 8, 0)

        w_combo08 = QComboBox()
        w_combo08.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo08))
        self.w_combo08 = w_combo08
        grid.addWidget(w_combo08, 8, 1, 1, 2)

        # line 9: water
        # =============
        w_disp_w = QPushButton('Display water metric')
        helpText = 'Display water chart'
        w_disp_w.setToolTip(helpText)
        w_disp_w.clicked.connect(lambda: self.displayMetric(self.w_combo09, 'soil_water'))
        w_disp_w.setEnabled(False)
        self.w_disp_w = w_disp_w
        grid.addWidget(w_disp_w, 9, 0)

        w_combo09 = QComboBox()
        w_combo09.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo09))
        self.w_combo09 = w_combo09
        grid.addWidget(w_combo09, 9, 1, 1, 2)

        grid.addWidget(QLabel(), 10, 0, )   # spacer

        # row 15
        # ======
        w_out_dir = QPushButton("Outputs directory")
        helpText = 'Select a file path for Excel outputs files'
        w_out_dir.setToolTip(helpText)
        grid.addWidget(w_out_dir, 15, 0)
        w_out_dir.clicked.connect(self.fetchOutDir)

        w_lbl15 = QLabel('')
        grid.addWidget(w_lbl15, 15, 1, 1, 5)
        self.w_lbl15 = w_lbl15

        # line 16: generate Excel files
        # =============================
        w_make_xls = QCheckBox('Write Excel output files')
        helpText = 'Writing Excel files is slow'
        w_make_xls.setToolTip(helpText)
        w_make_xls.setChecked(True)
        grid.addWidget(w_make_xls, 16, 0, 1, 2)
        self.w_make_xls = w_make_xls

        # line 17: display output
        # ========================
        w_disp_out = QPushButton('Display output')
        helpText = 'Display output Excel files'
        w_disp_out.setToolTip(helpText)
        w_disp_out.clicked.connect(self.displayXlsxOutput)
        self.w_disp_out = w_disp_out
        grid.addWidget(w_disp_out, 17, 0)

        w_combo17 = QComboBox()
        self.w_combo17 = w_combo17
        grid.addWidget(w_combo17, 17, 1, 1, 4)

        # user feedback
        # =============
        w_opt_cycle = QLabel(optimisation_cycle(self))
        # grid.addWidget(w_opt_cycle, 18, 2, 1, 2)
        self.w_opt_cycle = w_opt_cycle

        # line 19
        # =======
        w_economics = QPushButton('Economics')
        helpText = 'Runs ORATOR economics model'
        w_economics.setToolTip(helpText)
        # w_economics.setEnabled(False)
        w_economics.clicked.connect(self.runEconomicsClicked)
        grid.addWidget(w_economics, 19, 0)
        self.w_economics = w_economics

        w_livestock = QPushButton('Livestock')
        helpText = 'Runs ORATOR livestock model'
        w_livestock.setToolTip(helpText)
        # w_livestock.setEnabled(False)
        w_livestock.clicked.connect(self.runLivestockClicked)
        grid.addWidget(w_livestock, 19, 1)
        self.w_livestock = w_livestock

        w_soil_cn = QPushButton('Soil C and N')
        helpText = 'Runs ORATOR soil carbon and nitrogen code'
        w_soil_cn.setToolTip(helpText)
        w_soil_cn.setEnabled(False)
        w_soil_cn.clicked.connect(self.runSoilCnClicked)
        grid.addWidget(w_soil_cn, 19, 2)
        self.w_soil_cn = w_soil_cn

        w_optimise = QPushButton('Optimise')
        helpText = 'Optimisation - not ready'
        w_optimise.setToolTip(helpText)
        w_optimise.setEnabled(False)
        w_optimise.clicked.connect(self.runOptimiseClicked)
        grid.addWidget(w_optimise, 19, 3)
        self.w_optimise = w_optimise

        w_save = QPushButton("Save", self)
        helpText = 'save the configuration file'
        w_save.setToolTip(helpText)
        grid.addWidget(w_save, 19, 5)
        w_save.clicked.connect(self.saveClicked)

        w_exit = QPushButton("Exit", self)
        helpText = 'Close GUI - the configuration file will be saved'
        w_exit.setToolTip(helpText)
        grid.addWidget(w_exit, 19, 6)
        w_exit.clicked.connect(self.exitClicked)

        # add grid to RH vertical box
        # ===========================
        rh_vbox.addLayout(grid)

        # vertical box goes into horizontal box
        hbox.addLayout(rh_vbox)

        # the horizontal box fits inside the window
        self.setLayout(hbox)

        # posx, posy, width, height
        self.setGeometry(500, 100, 500, 400)
        self.setWindowTitle('Run ORATOR analysis')

        # reads and set values from last run
        # ==================================
        read_config_file(self)

    def fetchOutDir(self):

        dirname_cur = self.w_lbl15.text()
        dirname = QFileDialog.getExistingDirectory(self, 'Select directory', dirname_cur)
        if dirname != '' and dirname != dirname_cur:
            self.w_lbl15.setText(dirname)

    def fetchInpJson(self):

        dirname_cur = self.w_lbl06.text()
        dirname = QFileDialog.getExistingDirectory(self, 'Select directory', dirname_cur)
        if dirname != '' and dirname != dirname_cur:
            self.w_lbl06.setText(dirname)
            self.w_lbl07.setText(check_json_input_files(self, dirname))

    def changeHelpText(self, w_combo):
        '''
        modify help text according to metric
        '''
        metric = w_combo.currentText()
        defn, units = fetch_variable_definition(self.settings['lookup_df'], metric)
        helpText = 'Display ' + defn + ' chart'
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

        test_livestock_algorithms(self)

    def runSoilCnClicked(self):

        run_soil_cn_algorithms(self)

    def fetchInpExcel(self):
        """
        QFileDialog returns a tuple for Python 3.5, 3.6
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

        # sleep(2)
        self.close()

def main():
    """

    """
    app = QApplication(sys.argv)  # create QApplication object
    form = Form() # instantiate form
    # display the GUI and start the event loop if we're not running batch mode
    form.show()             # paint form
    sys.exit(app.exec_())   # start event loop

if __name__ == '__main__':
    main()
