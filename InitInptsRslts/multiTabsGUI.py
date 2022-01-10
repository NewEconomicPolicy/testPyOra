#-------------------------------------------------------------------------------
# Name:        multiTabsGUI.py
# Purpose:     GUI front end to enable checking of Fortran modules
# Author:      Mike Martin
# Created:     25/7/2016
# Licence:     <your licence>
# Description:
#   tab2UI  AOI from shape
#   tab3UI  Clean Ecosse study
#-------------------------------------------------------------------------------
#
__prog__ = 'multiTabsGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QWidget, QTabWidget, QFileDialog, QGridLayout, QLineEdit, \
                                                                                    QComboBox, QPushButton, QCheckBox

from subprocess import Popen, DEVNULL
from os.path import normpath, join

# from ora_classes_excel_write import pyoraId as oraId

from ora_low_level_fns import gui_optimisation_cycle
from ora_economics_model import test_economics_algorithms
from livestock_output_data import calc_livestock_data
from ora_cn_model import run_soil_cn_algorithms, recalc_fwd_soil_cn
from ora_excel_read import ReadStudy
from ora_json_read import check_json_xlsx_inp_files, disp_ow_parms, check_mngmnt_ow
from display_gui_charts import display_metric
from ora_lookup_df_fns import fetch_defn_units_from_pyora_display, fetch_pyora_varname_from_pyora_display

STD_FLD_SIZE = 60
STD_BTN_SIZE = 100
STD_CMBO_SIZE = 150
FNAME_RUN = 'FarmWthrMgmt.xlsx'

class AllTabs(QTabWidget):
    '''
    create 3 tabs each of which use QGridLayout
    '''
    def __init__(self, settings, lgr, ora_parms, parent = None):

        super(AllTabs, self).__init__(parent)

        self.settings = settings
        self.lgr = lgr
        self.ora_parms = ora_parms
        self.all_runs_output = {}
        self.all_runs_crop_model = {}

        self.w_tab1 = QWidget()
        self.w_tab2 = QWidget()
        self.w_tab3 = QWidget()

        self.addTab(self.w_tab1,"Tab 1")
        self.addTab(self.w_tab2,"Tab 2")
        self.addTab(self.w_tab3,"Tab 3")
        self.tab1UI()
        self.tab2UI()
        self.tab3UI()
        self.setWindowTitle("tab demo")

    def tab1UI(self):
        '''
        uses widgets w_prj_dir, wt1_lbl04, wt1_lbl05, w_report_prjs
        '''

        grid = QGridLayout()    # define layout
        grid.setSpacing(10)

        # line 0 for study details
        # ========================
        irow = 0  # main layout is a grid therefore line and row spacing is important
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

        w_view_run = QPushButton('View run file')
        helpText = 'View Excel run file with a farm location, management, soil and weather sheets'
        w_view_run.setToolTip(helpText)
        grid.addWidget(w_view_run, irow, 6)
        w_view_run.clicked.connect(self.viewRunFile)

        # carbon
        # ======
        irow += 1
        w_disp1_c = QPushButton('Display C metric')
        helpText = 'Display carbon chart'
        w_disp1_c.setToolTip(helpText)
        w_disp1_c.clicked.connect(lambda: self.displayMetric(self.w_combo07, 'carbon'))
        w_disp1_c.setEnabled(False)
        self.w_disp1_c = w_disp1_c
        grid.addWidget(w_disp1_c, irow, 0)

        w_combo07 = QComboBox()
        w_combo07.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo07))
        self.w_combo07 = w_combo07
        grid.addWidget(w_combo07, irow, 1, 1, 2)

        # nitrogen
        # ========
        irow += 1
        w_disp1_n = QPushButton('Display N metric')
        helpText = 'Display nitrogen chart'
        w_disp1_n.setToolTip(helpText)
        w_disp1_n.setEnabled(False)
        w_disp1_n.clicked.connect(lambda: self.displayMetric(self.w_combo08, 'nitrogen'))
        self.w_disp1_n = w_disp1_n
        grid.addWidget(w_disp1_n, irow, 0)

        w_combo08 = QComboBox()
        w_combo08.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo08))
        self.w_combo08 = w_combo08
        grid.addWidget(w_combo08, irow, 1, 1, 2)

        # water
        # =====
        irow += 1
        w_disp1_w = QPushButton('Display water metric')
        helpText = 'Display water chart'
        w_disp1_w.setToolTip(helpText)
        w_disp1_w.clicked.connect(lambda: self.displayMetric(self.w_combo09, 'soil_water'))
        w_disp1_w.setEnabled(False)
        self.w_disp1_w = w_disp1_w
        grid.addWidget(w_disp1_w, irow, 0)

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

        self.setTabText(0,'Main')
        self.w_tab1.setLayout(grid)

    def viewRunFile(self):
        '''
        view Excel run file
        '''
        mgmt_dir = self.w_lbl06.text()
        run_xls_fname = normpath(join(mgmt_dir, FNAME_RUN))

        excel_path = self.settings['excel_path']
        Popen(list([excel_path, run_xls_fname]), stdout = DEVNULL)

    def mnthApplicChanged(self):

        self.w_ow_rprt.setText(check_mngmnt_ow(self))

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
            self.w_lbl07.setText(check_json_xlsx_inp_files(self.w_soil_cn, self.settings, mgmt_dir))
            self.w_disp1_c.setEnabled(False)
            self.w_disp1_n.setEnabled(False)
            self.w_disp1_w.setEnabled(False)
            self.w_disp_cm.setEnabled(False)
            self.w_disp_econ.setEnabled(False)
            self.w_recalc.setEnabled(False)
            self.w_disp_out.setEnabled(False)
            self.w_livestock.setEnabled(False)

            # repopulate combo
            # ================
            study = ReadStudy(self, mgmt_dir)
            self.w_combo31s.clear()
            for sba in study.subareas:
                self.w_combo31s.addItem(sba)

            self.settings['study'] = study

    def changeHelpText(self, w_combo):
        '''
        modify help text according to metric
        '''
        metric = w_combo.currentText()
        defn, units = fetch_defn_units_from_pyora_display(self.settings['lookup_df'], metric)
        helpText = 'Display ' + defn
        w_combo.setToolTip(helpText)

    def displayMetric(self, w_combo, group, recalc_flag = False):
        '''
        this function is used by the main and recalculation tabs
        '''
        if recalc_flag:
            sba = self.w_combo31s.currentText()
        else:
            sba = None

        display_name = w_combo.currentText()
        metric = fetch_pyora_varname_from_pyora_display(self.settings['lookup_df'], display_name)
        if metric is not None:
            display_metric(self, group, metric, sba, recalc_flag)

    def displayXlsxOutput(self):

        excel_file = self.settings['out_dir'] + '\\' + self.w_combo17.currentText()
        excel_path = self.settings['excel_path']
        Popen(list([excel_path, excel_file]), stdout = DEVNULL)
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

    # ================================ end of tab1UI =========================

    def tab2UI(self):
        '''
        uses widgets w_shp_fname, w_lbl02 (shape file name), w_lbl03a, w_lbl03 (# shapes and provinces),
        w_overwrite, w_gen_csv
        '''

        grid = QGridLayout()    # define layout
        grid.setSpacing(10)

        # extra organic waste
        # ===================
        irow = 0
        irow += 1
        grid.addWidget(QLabel(), irow, 0)  # spacer

        irow += 1
        w_recalc = QPushButton('Recalculate')
        helpText = 'Examine the impact of changing the rate of organic waste applied to the foward run after ' + \
                   'steady state has been reached.'
        w_recalc.setToolTip(helpText)
        w_recalc.clicked.connect(self.recalcClicked)
        w_recalc.setEnabled(False)
        self.w_recalc = w_recalc
        grid.addWidget(w_recalc, irow, 0)

        lbl13a = QLabel('Additional organic waste applied - Min:')
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
        w_mnth_appl.currentIndexChanged[str].connect(self.mnthApplicChanged)
        w_mnth_appl.setFixedWidth(STD_FLD_SIZE)
        grid.addWidget(w_mnth_appl, irow, 4)
        self.w_mnth_appl = w_mnth_appl

        # display organic waste summary and feedback
        # ==========================================
        irow += 1
        w_lbl_ow = QLabel('')
        grid.addWidget(w_lbl_ow, irow, 0, 1, 6)
        self.w_lbl_ow = w_lbl_ow

        irow += 1
        w_ow_rprt = QLabel('')
        grid.addWidget(w_ow_rprt, irow, 0, 1, 6)
        self.w_ow_rprt = w_ow_rprt

        irow += 1
        grid.addWidget(QLabel(), irow, 0)  # spacer

        # combo is populated each time user selects a run file
        # ====================================================
        irow += 1
        w_lbl31s = QLabel('Sub area selection:')
        helpText = 'Sub area selection'
        w_lbl31s.setToolTip(helpText)
        w_lbl31s.setAlignment(Qt.AlignRight)
        grid.addWidget(w_lbl31s, irow, 0)

        w_combo31s = QComboBox()
        w_combo31s.setFixedWidth(80)
        grid.addWidget(w_combo31s, irow, 1)
        self.w_combo31s = w_combo31s

        w_lbl31e = QLabel('')   # TODO: for area description
        grid.addWidget(w_lbl31e, irow, 2)
        self.w_lbl31e = w_lbl31e

        # carbon
        # ======
        irow += 1
        recalc_flag = True
        w_disp2_c = QPushButton('Display C metric')
        helpText = 'Display carbon chart'
        w_disp2_c.setToolTip(helpText)
        w_disp2_c.clicked.connect(lambda: self.displayMetric(self.w_combo27, 'carbon', recalc_flag))
        w_disp2_c.setEnabled(False)
        self.w_disp2_c = w_disp2_c
        grid.addWidget(w_disp2_c, irow, 0)

        w_combo27 = QComboBox()
        w_combo27.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo27))
        self.w_combo27 = w_combo27
        grid.addWidget(w_combo27, irow, 1, 1, 2)

        # nitrogen
        # ========
        irow += 1
        w_disp2_n = QPushButton('Display N metric')
        helpText = 'Display nitrogen chart'
        w_disp2_n.setToolTip(helpText)
        w_disp2_n.setEnabled(False)
        w_disp2_n.clicked.connect(lambda: self.displayMetric(self.w_combo28, 'nitrogen', recalc_flag))
        self.w_disp2_n = w_disp2_n
        grid.addWidget(w_disp2_n, irow, 0)

        w_combo28 = QComboBox()
        w_combo28.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo28))
        self.w_combo28 = w_combo28
        grid.addWidget(w_combo28, irow, 1, 1, 2)

        # water
        # =====
        irow += 1
        w_disp2_w = QPushButton('Display water metric')
        helpText = 'Display water chart'
        w_disp2_w.setToolTip(helpText)
        w_disp2_w.clicked.connect(lambda: self.displayMetric(self.w_combo29, 'soil_water', recalc_flag))
        w_disp2_w.setEnabled(False)
        self.w_disp2_w = w_disp2_w
        grid.addWidget(w_disp2_w, irow, 0)

        w_combo29 = QComboBox()
        w_combo29.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo29))
        self.w_combo29 = w_combo29
        grid.addWidget(w_combo29, irow, 1, 1, 2)

        irow += 1
        grid.addWidget(QLabel(), irow, 0)  # spacer

        self.setTabText(1,'Test forward run')
        self.w_tab2.setLayout(grid)

    def recalcClicked(self):
        '''

        '''
        recalc_runs_fwd = recalc_fwd_soil_cn(self)
        if recalc_runs_fwd is None:
            self.w_disp2_c.setEnabled(False)
            self.w_disp2_n.setEnabled(False)
            self.w_disp2_w.setEnabled(False)
        else:
            self.w_disp2_c.setEnabled(True)
            self.w_disp2_n.setEnabled(True)
            self.w_disp2_w.setEnabled(True)

        self.recalc_runs_fwd = recalc_runs_fwd

        return

    def displayFwdRunsClicked(self):

        func_name =  __prog__ + ' createFileClicked'

        # generate_csv_from_shape(self)
        pass

    # ================================ end of tab2UI =========================

    def tab3UI(self):
        '''
        uses widgets w_ref_dir, w_lbl04, w_lbl05, w_cnfrm_del, w_del_sims
        '''

        grid = QGridLayout()    # define layout
        grid.setSpacing(10)

        # line for directory
        # ==================
        w_ref_dir = QPushButton('Sims dir')
        grid.addWidget(w_ref_dir, 1, 0)
        w_ref_dir.clicked.connect(self._fetchRefDir)

        w_lbl04 = QLabel()
        grid.addWidget(w_lbl04, 1, 1, 1, 5)
        self.w_lbl04 = w_lbl04

        w_lbl05 = QLabel('')
        grid.addWidget(w_lbl05, 2, 1, 1, 5)
        self.w_lbl05 = w_lbl05

        # confirmation line
        # =================
        w_cnfrm_del = QCheckBox('Confirm deletion of sims and associated files')
        grid.addWidget(w_cnfrm_del, 3, 0, 1, 3)
        w_cnfrm_del.setChecked(False)
        self.w_cnfrm_del = w_cnfrm_del

        # action line
        # ===========
        w_del_sims = QPushButton('Remove sims')
        helpText = 'remove all folders in selected directory with names starting with "lat" and associated files'
        w_del_sims.setToolTip(helpText)
        w_del_sims.clicked.connect(self._removeSimsClicked)
        grid.addWidget(w_del_sims, 6, 0)

        w_del_wthr = QPushButton('Remove weather')
        helpText = 'remove all folders relating to weather'
        w_del_wthr.setToolTip(helpText)
        w_del_wthr.clicked.connect(self._removeWthrClicked)
        grid.addWidget(w_del_wthr, 6, 1)

        self.setTabText(2,'Run file')
        self.w_tab3.setLayout(grid)

    def _fetchRefDir(self):

        fname_existing = self.w_lbl04.text()
        fname = QFileDialog.getExistingDirectory(self, 'Select directory', fname_existing)   # QFileDialog is a pop up
        if fname == '':
            fname = fname_existing

        self.w_lbl04.setText(fname)
        # self.w_lbl05.setText(check_sims_direcs(self, fname))

    def _removeSimsClicked(self):

        # remove_sims_files(self)
        pass

    def _removeWthrClicked(self):

        # remove_weather_only(self)
        pass

    # ================================ end of tab3UI =========================