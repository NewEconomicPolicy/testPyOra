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
from PyQt5.QtWidgets import (QLabel, QWidget, QTabWidget, QFileDialog, QGridLayout, QLineEdit, QMessageBox,
                                   QStyle, QRadioButton, QApplication, QComboBox, QPushButton, QCheckBox, QButtonGroup)
from PyQt5.QtGui import QPixmap, QFont
from subprocess import Popen, DEVNULL
from os.path import normpath, join, isdir, isfile, split

from shutil import rmtree, copyfile
# from ora_classes_excel_write import pyoraId as oraId

from climateGui import climate_gui
from farm_detailGui import farm_detail_gui, repopulate_farms_dropdown, post_farm_detail, post_sbas_detail, post_sbas_hdrs
from ora_excel_read_misc import identify_farms_for_study, clear_farm_fields, check_sheets_for_farms, validate_farm_var_fields
from ora_utils_write_farm_sheets import make_or_update_farm

from ora_low_level_fns import gui_optimisation_cycle
from ora_economics_model import test_economics_algorithms
from livestock_output_data import calc_livestock_data, check_livestock_run_data
from ora_cn_model import run_soil_cn_algorithms, recalc_fwd_soil_cn
from ora_excel_read import check_xls_run_file, ReadStudy
from ora_gui_misc_fns import disp_ow_parms, check_mngmnt_ow
from ora_wthr_misc_fns import read_csv_wthr_file, prod_system_to_descr
from display_gui_charts import display_metric
from ora_lookup_df_fns import fetch_defn_units_from_pyora_display, fetch_pyora_varname_from_pyora_display

from DynVarsGui import edit_dyn_vars
from MgmtGui import display_subarea

STD_FLD_SIZE_60 = 60
STD_FLD_SIZE_40 = 40
STD_BTN_SIZE_100 = 100
STD_CMBO_SIZE = 150

ANML_ABBREVS = ['catdry', 'catmt', 'rumdry', 'rummt', 'pigs', 'pltry']
STRATEGIES = ['On farm production', 'Buy/sell']
NFEED_TYPES = 5         # typically 5 feed types

FNAME_RUN = 'FarmWthrMgmt.xlsx'
FNAME_ECON = 'PurchasesSalesLabour.xlsx'

from string import ascii_uppercase
ALPHABET = list(ascii_uppercase)

class AllTabs(QTabWidget):
    """
    create 3 tabs each of which use QGridLayout
    """
    def __init__(self, settings, lggr, ora_parms, wthr_sets, wthr_rsrces_gnrc, anml_prodn, parent = None):

        super(AllTabs, self).__init__(parent)

        self.settings = settings
        self.lggr = lggr
        self.wthr_sets = wthr_sets
        self.wthr_rsrces_gnrc = wthr_rsrces_gnrc
        self.ora_parms = ora_parms
        self.anml_prodn = anml_prodn
        self.all_runs_output = {}
        self.all_runs_crop_model = {}
        self.crop_run = False
        self.livestock_run = False
        self.livestock_list = False

        self.w_tab0 = QWidget()
        self.w_tab1 = QWidget()
        self.w_tab2 = QWidget()
        self.w_tab3 = QWidget()
        self.w_tab4 = QWidget()
        self.w_tab5 = QWidget()

        self.addTab(self.w_tab0, "Tab 0")
        self.addTab(self.w_tab1, "Tab 1")
        self.addTab(self.w_tab2, "Tab 2")
        self.addTab(self.w_tab3, "Tab 3")
        self.addTab(self.w_tab4, "Tab 4")
        self.addTab(self.w_tab5, "Tab 5")

        self.tab0UI()   # Farm tab
        self.tab1UI()   # Crop Management
        self.tab2UI()   # Livestock
        self.tab3UI()   # Run Model
        self.tab4UI()   # Sensitivity Analysis
        self.tab5UI()   # Catchment

    # ================================ end of AllTabs =========================

    def tab0UI(self):
        """
        tab for farm and weather details
        creates these QComboBox names for studies: w_combo00  farm detail: .w_combo02
                            weather:  w_combo29s, w_combo30, w_combo30w, w_combo31s
        """
        grid = QGridLayout()    # define layout
        grid.setSpacing(10)

        # post farm detail
        # ================
        irow = 1
        irow = farm_detail_gui(self, grid, irow)

        irow += 1
        grid.addWidget(QLabel(), irow, 3)  # spacer

        # run file
        # ========
        irow += 1
        w_run_lbl0 = QLabel('Run file path:')
        helpText = 'Location for the Excel run file consisting of farm details, weather, crop management and livestock'
        w_run_lbl0.setToolTip(helpText)
        w_run_lbl0.setAlignment(Qt.AlignRight)
        grid.addWidget(w_run_lbl0, irow, 0)

        w_run_dir = QLabel()
        grid.addWidget(w_run_dir, irow, 1, 1, 5)
        self.w_run_dir0 = w_run_dir

        w_lbl_sbas = QLabel()
        w_lbl_sbas.setAlignment(Qt.AlignRight)
        grid.addWidget(w_lbl_sbas, irow, 5, 1, 2)
        self.w_lbl_sbas = w_lbl_sbas

        w_view_run = QPushButton('View run file')
        helpText = 'View Excel run file with a farm location, management, soil and weather sheets'
        w_view_run.setToolTip(helpText)
        grid.addWidget(w_view_run, irow, 7)
        w_view_run.clicked.connect(self.viewRunFile0)

        # =================================
        irow += 1
        w_view_econ = QPushButton('View economics')
        helpText = 'View and edit economics Excel file with Purchases & Sales and Labour sheets'
        w_view_econ.setToolTip(helpText)
        w_view_econ.setFixedWidth(STD_BTN_SIZE_100 + 10)
        grid.addWidget(w_view_econ, irow, 7)
        w_view_econ.clicked.connect(self.viewEconFile)

        # create 3 lines relating to climate
        # ==================================
        irow += 1
        irow = climate_gui(self, grid, irow)

        irow += 1
        grid.addWidget(QLabel(), irow, 3)  # spacer

        # soil detail source
        # ==================
        irow += 1
        w_use_exstng_soil = QCheckBox('Use existing soil')
        helpText = 'Use existing soil if available in run file'
        w_use_exstng_soil.setToolTip(helpText)
        grid.addWidget(w_use_exstng_soil, irow, 0)
        self.w_use_exstng_soil = w_use_exstng_soil

        # line for soil
        # =============
        irow += 1
        w_lbl06b = QLabel('Soil resource:')
        w_lbl06b.setAlignment(Qt.AlignRight)
        grid.addWidget(w_lbl06b, irow, 0)

        w_use_isda = QRadioButton('iSDAsoil')
        helpText = 'Use the 30 meter resolution iSDAsoil mapping system for Africa'
        helpText += ' - see: https://www.isda-africa.com/isdasoil/'
        w_use_isda.setToolTip(helpText)
        grid.addWidget(w_use_isda, irow, 1)
        self.w_use_isda = w_use_isda

        w_use_hwsd = QRadioButton("HWSD")
        helpText = 'Harmonized World Soil Database has a 30 arc seconds resolution and is maintained by\n'
        helpText += 'the Food and Agriculture Organization (FAO), a specialized agency of the United Nations'
        w_use_hwsd.setToolTip(helpText)
        grid.addWidget(w_use_hwsd, irow, 2)
        self.w_use_hwsd = w_use_hwsd

        w_soil_choice = QButtonGroup()
        w_soil_choice.addButton(w_use_isda)
        w_soil_choice.addButton(w_use_hwsd)
        self.w_soil_choice = w_soil_choice

        irow += 1
        grid.addWidget(QLabel(), irow, 3)   # spacer

        # operations
        # ==========
        irow += 2
        w_save_farm0 = QPushButton('Save farm')
        helpText = 'Create a new or update an existing Excel file for a PyOrator run consisting of farm details, management and weather data'
        w_save_farm0.setToolTip(helpText)
        w_save_farm0.clicked.connect(self.saveFarmClicked)
        w_save_farm0.setFixedWidth(STD_BTN_SIZE_100)
        grid.addWidget(w_save_farm0, irow, 0)
        self.w_save_farm0 = w_save_farm0

        w_rmv_farm = QPushButton('Remove farm')
        helpText = 'Remove all files relating to selected farm'
        w_rmv_farm.setToolTip(helpText)
        w_rmv_farm.setEnabled(False)
        w_rmv_farm.clicked.connect(self.removeFarmClicked)
        w_rmv_farm.setFixedWidth(STD_BTN_SIZE_100)
        grid.addWidget(w_rmv_farm, irow, 1)
        self.w_rmv_farm = w_rmv_farm

        w_chk_farm = QPushButton('Check farms')
        helpText = 'Check Excel files for a PyOrator run consisting of farm details, management and weather data'
        w_chk_farm.setToolTip(helpText)
        w_chk_farm.clicked.connect(self.checkFarms)
        w_chk_farm.setFixedWidth(STD_BTN_SIZE_100)
        grid.addWidget(w_chk_farm, irow, 2)
        self.w_chk_farm = w_chk_farm

        # ====================================
        w_chk_farm_icon = QPushButton('Check run file')
        helpText = 'Check run file integrity, namely that weather and management subarea months are equal'  # temporary solution
        w_chk_farm_icon.setToolTip(helpText)
        w_chk_farm_icon.clicked.connect(self.checkFarm)
        w_chk_farm_icon.setFixedWidth(STD_BTN_SIZE_100)
        grid.addWidget(w_chk_farm_icon, irow, 3)
        self.w_chk_farm_icon = w_chk_farm_icon

        '''
        # Arkan: check timespan consistency for weather and subareas
        # ==========================================================
        w_chk_farm_icon = QPushButton()
        helpText = 'Check that weather and management subarea months are equal'  # temporary solution
        logo = getattr(QStyle, 'SP_DialogApplyButton')  # temporary solution
        w_chk_farm_icon.setToolTip(helpText)
        w_chk_farm_icon.setIcon(self.style().standardIcon(logo))
        w_chk_farm_icon.clicked.connect(self.checkFarm)
        grid.addWidget(w_chk_farm_icon, irow, 3)
        self.w_chk_farm_icon = w_chk_farm_icon
        '''

        # =====================
        w_chk_lvstck = QPushButton('Check livestock sheet')
        helpText = 'Check Excel files for a PyOrator run consisting of farm details, management and weather data'
        w_chk_lvstck.setToolTip(helpText)
        w_chk_lvstck.clicked.connect(self.checkLvstck)
        w_chk_lvstck.setFixedWidth(STD_BTN_SIZE_100 + 30)
        grid.addWidget(w_chk_lvstck, irow, 5, 1, 2)
        self.w_chk_lvstck = w_chk_lvstck

        ntab = 0
        self.lggr.info('Last row: {} for tab {}'.format(irow, ntab))

        # =======================
        self.setTabText(ntab,'Farm')
        self.w_tab0.setLayout(grid)

    def checkLvstck(self):
        """

        """
        ngroups = check_livestock_run_data(self, ntab = 0)
        print('Livestock animal types to process: {}'.format(ngroups))

    def viewEconFile(self):
        """
        view Excel economics file
        """
        mgmt_dir = self.w_run_dir0.text()
        econ_xls_fname = normpath(join(mgmt_dir, FNAME_ECON))
        if not isfile(econ_xls_fname):
            try:
                copyfile(self.settings['econ_xls_fn'], econ_xls_fname)
            except FileNotFoundError as err:
                print(err)
                return -1
            else:
                print('Copied economics Excel file ' + FNAME_ECON + ' from templates directory ')

        excel_path = self.settings['excel_path']
        Popen(list([excel_path, econ_xls_fname]), stdout = DEVNULL)

    def viewRunFile0(self):
        """
        view Excel run file
        """
        mgmt_dir = self.w_run_dir0.text()
        run_xls_fname = normpath(join(mgmt_dir, FNAME_RUN))

        excel_path = self.settings['excel_path']
        Popen(list([excel_path, run_xls_fname]), stdout = DEVNULL)

    def checkForInteger(self):
        """
        TODO: not used as yet
        """
        s = 1.2
        isinstance(s, float)
        isinstance(s, int)

    def checkWthrSrces(self):
        """
        invoked when user clicks use CSV checkbox
        """
        print('CSV checkbox status: {}'.format(self.w_use_csv.isChecked()))

    def fetchCsvFile(self):
        """

        """
        csv_fn_cur = self.w_csv_fn.text()
        csv_fn, dummy = QFileDialog.getOpenFileName(self, 'Open file', csv_fn_cur, 'CSV files (*.csv)')
        if csv_fn != '' and csv_fn != csv_fn_cur:
            csv_valid_flag, dum = read_csv_wthr_file(csv_fn, self.w_csv_dscr)
            if csv_valid_flag:
                self.w_csv_fn.setText(csv_fn)

    def viewCsvFile(self):
        """
        invoke notepad to display weather file and report details
        """
        csv_fn_cur = self.w_csv_fn.text()
        notepad_path = self.settings['notepad_path']
        Popen(list([notepad_path, csv_fn_cur]), stdout=DEVNULL)
        '''
        excel_path = self.settings['excel_path']
        Popen(list([excel_path, csv_fn_cur]), stdout=DEVNULL)
        '''

    def removeFarmClicked(self):
        """

        """
        w_close = QMessageBox()
        w_close.setText('You sure?')
        w_close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        w_close.setDefaultButton(QMessageBox.Cancel)
        w_close = w_close.exec()

        if w_close == QMessageBox.Yes:
            study_dir = join(self.settings['study_area_dir'], self.w_combo00.currentText())
            farm_name = self.w_farm_name.text()
            farm_dir = join(study_dir, farm_name)
            if isdir(farm_dir):
                try:
                    rmtree(farm_dir)
                except PermissionError as err:
                    print(err)
                else:
                    print('Removed farm: ' + farm_name)
                    repopulate_farms_dropdown(self)
        return

    def checkFarm(self):
        """

        """
        mgmt_dir = self.w_run_dir0.text()
        run_fn_dscr = check_xls_run_file(self.w_run_model, mgmt_dir)

        return

    def checkFarms(self):
        """

        """
        check_sheets_for_farms(self)

        return

    def changeStudy(self):
        """
        if study is changed then farm must also be changed
        """
        repopulate_farms_dropdown(self)

        return

    def changeFarmName(self):
        """
        at start up there are zero farms
        """
        clear_farm_fields(self)

        farms = identify_farms_for_study(self)
        farm_name = self.w_farm_name.text()
        if farm_name in farms:
            self.w_rmv_farm.setEnabled(True)
        else:
            self.w_rmv_farm.setEnabled(False)

        return

    def postFarmDetail(self):
        """
        when the farm changes disable action push buttons
        """
        farm_name = self.w_combo02.currentText()
        self.w_farm_name.setText(farm_name)

        run_xls_fn = post_farm_detail(self)
        if run_xls_fn is not None:
            post_sbas_detail(self, run_xls_fn)

            mgmt_dir, dum = split(run_xls_fn)
            run_fn_dscr = check_xls_run_file(self.w_run_model, mgmt_dir)
            self.w_run_dscr.setText(run_fn_dscr)
            self.w_disp1_c.setEnabled(False)
            self.w_disp1_n.setEnabled(False)
            self.w_disp1_w.setEnabled(False)
            self.w_disp_cm.setEnabled(False)
            self.w_disp_lvstck.setEnabled(False)
            self.w_disp_econ.setEnabled(False)
            self.w_recalc.setEnabled(False)
            self.w_disp_out.setEnabled(False)
            self.w_livestock.setEnabled(False)

            # repopulate combo in Sensitivity Analysis tab
            # ============================================
            study = ReadStudy(self, mgmt_dir)
            self.w_combo36.clear()
            for sba in study.subareas:
                self.w_combo36.addItem(sba)

    def saveFarmClicked(self):
        """

        """
        if validate_farm_var_fields(self):          # checks farm name and numeric fields
            print('Saving farm... ' + self.w_farm_name.text())
            QApplication.processEvents()

            retcode, new_runfile_flag = make_or_update_farm(self)
            if retcode == 0:
                if new_runfile_flag:
                    repopulate_farms_dropdown(self)     # refresh list of farms

            # integrity check for all farms for this study
            # ============================================
            check_sheets_for_farms(self)

        QApplication.processEvents()
        return

    def editDynVars(self):
        """

        """
        edit_dyn_vars(self)

        return

    # ================================ end of tab0UI =========================

    def tab1UI(self):
        """
        subareas crop management
        """
        grid = QGridLayout()  # define layout
        grid.setSpacing(10)

        # subareas section
        # ================
        irow = 0
        post_sbas_hdrs(grid, irow)

        # create subarea widget sets
        # ==========================
        irow += 1
        w_sba_descrs, w_areas, w_nrota_ss, w_ss_mgmt, w_cpy_mgmt, w_nrota_fwd, w_fwd_mgmt = {}, {}, {}, {}, {}, {}, {}
        for sba_indx in ALPHABET[:self.settings['nsubareas']]:
            irow += 1
            self.makeMngmntWidgets(sba_indx, grid, w_sba_descrs, w_areas, w_nrota_ss, w_ss_mgmt, w_cpy_mgmt,
                                   w_nrota_fwd, w_fwd_mgmt, irow)

        self.w_ss_mgmt = w_ss_mgmt
        self.w_sba_descrs = w_sba_descrs
        self.w_fwd_mgmt = w_fwd_mgmt
        self.w_nrota_ss = w_nrota_ss
        self.w_areas = w_areas
        self.w_cpy_mgmt = w_cpy_mgmt

        irow += 1
        grid.addWidget(QLabel(), irow, 3)  # spacer

        irow += 2
        icol = 0
        w_save_farm1 = QPushButton('Save farm')
        helpText = 'Create a new or update an existing Excel file for a PyOrator run consisting of farm details, management and weather data'
        w_save_farm1.setToolTip(helpText)
        w_save_farm1.clicked.connect(self.saveFarmClicked)
        grid.addWidget(w_save_farm1, irow, icol)
        self.w_save_farm1 = w_save_farm1       

        ntab = 1
        self.lggr.info('Last row: {} for tab {}'.format(irow, ntab))

        # =======================
        self.setTabText(ntab,'Crop Management')
        self.w_tab1.setLayout(grid)

    def makeMngmntWidgets(self, sba_indx, grid, w_sba_descrs,  w_areas, w_nrota_ss, w_ss_mgmt, w_cpy_mgmt,
                                                                                    w_nrota_fwd, w_fwd_mgmt, irow):
        """
        construct grid of widgets defining subareas
        """

        # descriptions
        # ============
        icol = 0
        w_sba_descrs[sba_indx] = QLineEdit()
        w_sba_descrs[sba_indx].setFixedWidth(100)
        grid.addWidget(w_sba_descrs[sba_indx], irow, icol)
        w_sba_descrs[sba_indx].textChanged[str].connect(lambda: self.sbaDescRotaTextChanged(sba_indx))

        # areas
        # =====
        icol += 1
        w_areas[sba_indx] = QLineEdit()
        w_areas[sba_indx].setFixedWidth(40)
        w_areas[sba_indx].setAlignment(Qt.AlignRight)
        grid.addWidget(w_areas[sba_indx], irow, icol, alignment=Qt.AlignHCenter)

        # steady state run - years of rotation
        # ====================================
        icol += 1
        w_nrota_ss[sba_indx] = QLineEdit()
        w_nrota_ss[sba_indx].setFixedWidth(40)
        w_nrota_ss[sba_indx].setAlignment(Qt.AlignRight)
        grid.addWidget(w_nrota_ss[sba_indx], irow, icol, alignment=Qt.AlignHCenter)
        w_nrota_ss[sba_indx].textChanged[str].connect(lambda: self.sbaDescRotaTextChanged(sba_indx))

        # management
        # ==========
        icol += 1
        w_ss_mgmt[sba_indx] = QPushButton(sba_indx)
        w_ss_mgmt[sba_indx].setFixedWidth(65)
        w_ss_mgmt[sba_indx].setEnabled(False)
        grid.addWidget(w_ss_mgmt[sba_indx], irow, icol, alignment=Qt.AlignHCenter)
        w_ss_mgmt[sba_indx].clicked.connect(lambda: self.displaySubarea(sba_indx))

        # forward run
        # ===========
        icol += 1
        w_cpy_mgmt[sba_indx] = QCheckBox()
        w_cpy_mgmt[sba_indx].setCheckState(0)
        grid.addWidget(w_cpy_mgmt[sba_indx], irow, icol, alignment=Qt.AlignHCenter)

        # years of rotation
        # =================
        icol += 1
        w_nrota_fwd[sba_indx] = QLineEdit()
        w_nrota_fwd[sba_indx].setFixedWidth(40)
        w_nrota_fwd[sba_indx].setAlignment(Qt.AlignRight)
        grid.addWidget(w_nrota_fwd[sba_indx], irow, icol, alignment=Qt.AlignHCenter)
        w_nrota_fwd[sba_indx].textChanged[str].connect(lambda: self.sbaDescRotaTextChanged(sba_indx))

        # management
        # ==========
        icol += 1
        w_fwd_mgmt[sba_indx] = QPushButton(sba_indx)
        w_fwd_mgmt[sba_indx].setFixedWidth(65)
        w_fwd_mgmt[sba_indx].setEnabled(False)
        grid.addWidget(w_fwd_mgmt[sba_indx], irow, icol, alignment=Qt.AlignHCenter)
        w_fwd_mgmt[sba_indx].clicked.connect(lambda: self.displaySubarea(sba_indx))

    def displaySubarea(self, sba_indx):

        display_subarea(self, sba_indx)     # w_lbl_res.setText(summary)

    def sbaDescRotaTextChanged(self, sba_indx):
        """
        adjust active subareas according to user input
        """
        mess = 'Number of rotation years '
        rota_flag = False

        nrota_yrs = self.w_nrota_ss[sba_indx].text()
        if len(nrota_yrs) == 0:
            print(mess + 'cannot be blank')
        else:
            if not nrota_yrs.isdigit():
                print(mess + 'must be an integer')
            else:
                nrota_yrs = int(nrota_yrs)
                if nrota_yrs < 1 or nrota_yrs > 10:
                    print(mess + 'must be at least 1 year and no more than 10 years')
                else:
                    rota_flag = True

        # adjust active subarea fields according to user input
        # ====================================================
        descr = self.w_sba_descrs[sba_indx].text()
        if rota_flag and len(descr) > 0:
            self.w_ss_mgmt[sba_indx].setEnabled(True)
        else:
            self.w_ss_mgmt[sba_indx].setEnabled(False)

    # ================================ end of tab1UI =========================

    def tab2UI(self):
        """
        Livestock - creates widgets: w_bought_in, w_feed_qties, w_feed_types, w_numbers, w_strtgs
        """
        grid = QGridLayout()  # define layout
        grid.setSpacing(10)

        # =========
        w_numbers = {}
        w_strtgs = {}
        w_feed_types = {}
        w_feed_qties = {}
        w_bought_in = {}

        """
        construct grid of widgets defining livestock values
        """
        irow = 0
        anml_typs = self.anml_prodn.gnrc_anml_types

        # headers
        # =======
        irow += 1
        icol = 1
        for anml in anml_typs:
            hdr_lbl = QLabel(anml_typs[anml])
            hdr_lbl.setAlignment(Qt.AlignCenter)
            grid.addWidget(hdr_lbl, irow, icol)
            icol += 1

            w_feed_types[anml] = {}  # each animal type can have up to 5 feed types
            w_feed_qties[anml] = {}

        # setup row descriptions
        # ======================
        lvstck_row_dscrs = ['']

        # row for numbers of livestock
        # ============================
        lvstck_row_dscrs.append('Number')
        irow += 1
        icol = 0
        for anml in anml_typs:
            icol += 1
            w_numbers[anml] = QLineEdit()
            w_numbers[anml].setFixedWidth(STD_FLD_SIZE_40)
            w_numbers[anml].setAlignment(Qt.AlignRight)
            w_numbers[anml].textChanged.connect(self.evaluateBoughtIn)
            grid.addWidget(w_numbers[anml], irow, icol, alignment=Qt.AlignHCenter)

        # =====
        irow += 1
        icol = 0
        lvstck_row_dscrs.append('Strategy')
        #                        ========
        helpText = 'Possible strategies for coping with changes in feed availability'

        for anml in anml_typs:
            icol += 1
            w_strtgs[anml] = QComboBox()
            for strategy in STRATEGIES:
                w_strtgs[anml].addItem(strategy)
            w_strtgs[anml].setToolTip(helpText)
            grid.addWidget(w_strtgs[anml], irow, icol, alignment=Qt.AlignHCenter)

        # loop for upto 5 feeds for each animal type
        # ==========================================
        for findx in range(NFEED_TYPES):
            irow += 1
            icol = 0
            fd_typ = str(findx + 1)
            lvstck_row_dscrs.append('Feed type ' + fd_typ)
            #                        =========
            for anml in anml_typs:
                icol += 1
                w_feed_type = QComboBox()
                for feed_typ in list(self.anml_prodn.crop_names):
                    w_feed_type.addItem(feed_typ)
                grid.addWidget(w_feed_type, irow, icol)

                w_feed_types[anml][fd_typ] = w_feed_type
                w_feed_types[anml][fd_typ].currentIndexChanged.connect(self.evaluateBoughtIn)

            irow += 1
            icol = 0
            lvstck_row_dscrs.append('Feed value (%)')
            #                        ==============
            for anml in anml_typs:
                icol += 1
                w_feed_qty = QLineEdit()
                w_feed_qty.setFixedWidth(STD_FLD_SIZE_40)
                w_feed_qty.setAlignment(Qt.AlignRight)
                grid.addWidget(w_feed_qty, irow, icol, alignment=Qt.AlignHCenter)

                w_feed_qties[anml][fd_typ] = w_feed_qty
                w_feed_qties[anml][fd_typ].textChanged[str].connect(self.evaluateBoughtIn)

        # =========
        irow += 1
        icol = 0
        lvstck_row_dscrs.append('Bought in (%)')
        #                        =============
        helpText = 'Feed value obtained from bought in feed (%)'
        for anml in anml_typs:
            icol += 1
            w_bought_in[anml] = QLabel('')
            w_bought_in[anml].setToolTip(helpText)
            grid.addWidget(w_bought_in[anml], irow, icol, alignment=Qt.AlignHCenter)

        # write row descriptions
        # ======================
        for irow, row_dscr in enumerate(lvstck_row_dscrs):
            grid.addWidget(QLabel(row_dscr), irow, 0, alignment=Qt.AlignRight)
        irow += 1
        grid.addWidget(QLabel(), irow, 0)  # spacer

        self.lvstck_row_dscrs = lvstck_row_dscrs
        self.w_numbers = w_numbers
        self.w_strtgs = w_strtgs
        self.w_feed_types = w_feed_types
        self.w_feed_qties = w_feed_qties
        self.w_bought_in = w_bought_in

        # =======================
        irow += 2
        w_save_farm2 = QPushButton('Save farm')
        helpText = 'Create a new or update an existing Excel file for a PyOrator run consisting of farm details, management and weather data'
        w_save_farm2.setToolTip(helpText)
        w_save_farm2.setFixedWidth(STD_BTN_SIZE_100)
        w_save_farm2.clicked.connect(self.saveFarmClicked)
        grid.addWidget(w_save_farm2, irow, 0)
        self.w_save_farm2 = w_save_farm2

        w_clear_data = QPushButton('Clear data')
        helpText = 'set livestock data to zeros'
        w_clear_data.setToolTip(helpText)
        w_clear_data.setFixedWidth(STD_BTN_SIZE_100)
        w_clear_data.clicked.connect(self.clearDataClicked)
        grid.addWidget(w_clear_data, irow, 1)
        self.w_clear_data = w_clear_data

        # =======================
        ntab = 2
        self.lggr.info('Last row: {} for tab {}'.format(irow, ntab))

        # =======================
        self.setTabText(ntab, 'Livestock')
        self.w_tab2.setLayout(grid)

    def clearDataClicked(self):
        """
        resets livestock widgets
        """
        for anml in ANML_ABBREVS:
            for findx in range(NFEED_TYPES):
                fd_typ = str(findx + 1)
                self.w_feed_qties[anml][fd_typ].setText('0')
                self.w_feed_types[anml][fd_typ].setCurrentIndex(0)

                self.w_numbers[anml].setText('0')
                self.w_strtgs[anml].setCurrentIndex(0)

        return

    def changeSystem(self):
        """
        if system is changed then expand 3 letter code
        """
        prod_system = self.w_systems.currentText()
        self.sys_descr_lbl.setText(prod_system_to_descr(prod_system))

        return

    def evaluateBoughtIn(self):
        """

        """
        anml_typs = self.anml_prodn.gnrc_anml_types
        for anml in anml_typs:
            try:
                val = float(self.w_numbers[anml].text())
            except ValueError as err:
                val = 0

            if val == 0:
               self.w_bought_in[anml].setText('')
            else:
                feed_val_sum = 0.0
                for findx in range(NFEED_TYPES):

                    fd_typ = str(findx + 1)
                    if self.w_feed_types[anml][fd_typ].currentIndex() == 0:
                        self.w_feed_qties[anml][fd_typ].setText('0')

                    try:
                        val = float(self.w_feed_qties[anml][fd_typ].text())
                    except ValueError as err:
                        pass
                    else:
                        feed_val_sum += val

                    self.w_bought_in[anml].setText(str(100 - feed_val_sum))

    # ================================ end of tab2UI =========================

    def tab3UI(self):
        """
        Enables user to run PyOrator operations
        creates these QComboBox names:  w_combo07, w_combo08, w_combo09, w_combo10, w_combo11, w_combo17
        """

        grid = QGridLayout()    # define layout
        grid.setSpacing(10)

        # study details
        # =============
        irow = 1  # main layout is a grid therefore line and row spacing is important
        w_study = QLabel()
        grid.addWidget(w_study, irow, 0, 1, 5)
        self.w_study = w_study

        # ============
        irow += 1
        w_run_lbl3 = QLabel('Run file path:')
        helpText = 'Location of Excel run file comprising farm location, management, soil and weather sheets'
        w_run_lbl3.setToolTip(helpText)
        w_run_lbl3.setAlignment(Qt.AlignRight)
        grid.addWidget(w_run_lbl3, irow, 0)

        w_run_dir = QLabel('')
        grid.addWidget(w_run_dir, irow, 1, 1, 4)
        self.w_run_dir3 = w_run_dir

        w_run_dscr = QLabel('')     # for message describing run file
        grid.addWidget(w_run_dscr, irow, 5, 1, 2)
        w_run_dscr.setAlignment(Qt.AlignRight)
        self.w_run_dscr = w_run_dscr

        w_view_run = QPushButton('View run file')
        helpText = 'View Excel run file with a farm location, management, soil and weather sheets'
        w_view_run.setToolTip(helpText)
        grid.addWidget(w_view_run, irow, 7)
        w_view_run.clicked.connect(self.viewRunFile)

        irow += 1
        grid.addWidget(QLabel(), irow, 0)  # spacer

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
        w_disp_lvstck = QPushButton('Livestock')
        helpText = 'Display Livestock related charts'
        w_disp_lvstck.setToolTip(helpText)
        w_disp_lvstck.clicked.connect(lambda: self.displayMetric(self.w_combo11, 'livestock'))
        w_disp_lvstck.setEnabled(False)
        self.w_disp_lvstck = w_disp_lvstck
        grid.addWidget(w_disp_lvstck, irow, 0)

        w_combo11 = QComboBox()
        w_combo11.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo11))
        self.w_combo11 = w_combo11
        grid.addWidget(w_combo11, irow, 1, 1, 2)

        # Livestock
        # ==========
        irow += 1
        w_disp_econ = QPushButton('Economics')
        helpText = 'Display Economics related charts'
        w_disp_econ.setToolTip(helpText)
        w_disp_econ.clicked.connect(lambda: self.displayMetric(self.w_combo12, 'economics'))
        w_disp_econ.setEnabled(False)
        self.w_disp_econ = w_disp_econ
        grid.addWidget(w_disp_econ, irow, 0)

        w_combo12 = QComboBox()
        w_combo12.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo12))
        self.w_combo12 = w_combo12
        grid.addWidget(w_combo12, irow, 1, 1, 2)

        irow += 1
        grid.addWidget(QLabel(), irow, 0)  # spacer

        # extra line for Neem
        # ===================
        syn_fert = 'Neem coated urea'
        if syn_fert in self.ora_parms.syn_fert_parms:
            rate_inhibit = self.ora_parms.syn_fert_parms[syn_fert]['rate_inhibit']
        else:
            rate_inhibit = 0.5

        irow += 1
        w_lbl32 = QLabel('Neem coated urea inhibition rate modifier:')
        w_lbl32.setAlignment(Qt.AlignRight)
        grid.addWidget(w_lbl32, irow, 0, 1, 2)

        w_inhibit = QLineEdit()
        w_inhibit.setFixedWidth(STD_FLD_SIZE_40)
        w_inhibit.setAlignment(Qt.AlignRight)
        w_inhibit.setToolTip('this field enables the default Neem coated urea inhibition rate modifier to be overridden')
        grid.addWidget(w_inhibit, irow, 2)
        # w_inhibit.clicked.connect(self.displayXlsxOutput)
        w_inhibit.setText(str(rate_inhibit))
        self.w_inhibit = w_inhibit

        # end of Neem
        # ===========
        irow += 1
        grid.addWidget(QLabel(), irow, 0)  # spacer

        # =============================
        irow += 1
        w_make_xls = QCheckBox('Write Excel output files')
        helpText = 'Writing Excel files is slow'
        w_make_xls.setToolTip(helpText)
        w_make_xls.setChecked(True)
        grid.addWidget(w_make_xls, irow, 0, 1, 2)
        self.w_make_xls = w_make_xls

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

        # actions
        # =======
        irow += 1
        icol = 1
        w_run_model = QPushButton('Run model')
        helpText = 'Runs ORATOR soil carbon and nitrogen, livestock and economics models'
        w_run_model.setToolTip(helpText)
        w_run_model.setEnabled(False)
        w_run_model.setFixedWidth(STD_BTN_SIZE_100)
        w_run_model.clicked.connect(self.runModelClicked)
        grid.addWidget(w_run_model, irow, icol)
        self.w_run_model = w_run_model

        icol += 2
        w_dyn_vars = QPushButton('Dynamic variables')
        helpText = 'Change dynamic variables e.g. default crop or fertiliser parameters'
        w_dyn_vars.setToolTip(helpText)
        w_dyn_vars.setFixedWidth(STD_BTN_SIZE_100 + 40)
        w_dyn_vars.clicked.connect(self.editDynVars)
        w_dyn_vars.setEnabled(False)
        grid.addWidget(w_dyn_vars, irow, icol)
        self.w_dyn_vars = w_dyn_vars

        icol += 2
        w_economics = QPushButton('Economics')
        helpText = 'Runs ORATOR economics model'
        w_economics.setToolTip(helpText)
        w_economics.setEnabled(True)
        w_economics.setFixedWidth(STD_BTN_SIZE_100)
        w_economics.clicked.connect(self.runEconomicsClicked)
        grid.addWidget(w_economics, irow, icol)
        self.w_economics = w_economics

        icol += 1
        w_livestock = QPushButton('Livestock')
        helpText = 'Runs ORATOR livestock model'
        w_livestock.setToolTip(helpText)
        w_livestock.setEnabled(False)
        w_livestock.setFixedWidth(STD_BTN_SIZE_100)
        w_livestock.clicked.connect(self.runLivestockClicked)
        grid.addWidget(w_livestock, irow, icol)
        self.w_livestock = w_livestock

        icol += 1
        w_soil_cn = QPushButton('Soil C and N')
        helpText = 'Runs ORATOR soil carbon and nitrogen code'
        w_soil_cn.setToolTip(helpText)
        w_soil_cn.setEnabled(False)
        w_soil_cn.setFixedWidth(STD_BTN_SIZE_100)
        w_soil_cn.clicked.connect(self.runSoilCnClicked)
        grid.addWidget(w_soil_cn, irow, icol)
        self.w_soil_cn = w_soil_cn

        icol += 1
        w_optimise = QPushButton('Optimise')
        helpText = 'Optimisation - not ready'
        w_optimise.setToolTip(helpText)
        w_optimise.setEnabled(False)
        w_optimise.setFixedWidth(STD_BTN_SIZE_100)
        w_optimise.clicked.connect(self.runOptimiseClicked)
        grid.addWidget(w_optimise, irow, icol)
        self.w_optimise = w_optimise

        ntab = 3
        self.lggr.info('Last row: {} for tab {}'.format(irow, ntab))

        self.setTabText(ntab,'Run Model')
        self.w_tab3.setLayout(grid)

    def viewRunFile(self):
        """
        view Excel run file
        """
        mgmt_dir = self.w_run_dir3.text()
        run_xls_fname = normpath(join(mgmt_dir, FNAME_RUN))

        excel_path = self.settings['excel_path']
        Popen(list([excel_path, run_xls_fname]), stdout = DEVNULL)

    def mnthApplicChanged(self):
        """
        C
        """
        self.w_ow_rprt.setText(check_mngmnt_ow(self))

        return

    def displayOwParms(self):
        """
        C
        """
        self.w_lbl_ow.setText(disp_ow_parms(self))

        return

    def changeHelpText(self, w_combo):
        """
        modify help text according to metric
        """
        metric = w_combo.currentText()
        defn, units = fetch_defn_units_from_pyora_display(self.settings['lookup_df'], metric)
        helpText = 'Display ' + defn
        w_combo.setToolTip(helpText)

    def displayMetric(self, w_combo, group, recalc_flag = False):
        """
        this function is used by the main and recalculation tabs
        """
        if recalc_flag:
            sba = self.w_combo36.currentText()
        else:
            sba = None

        display_name = w_combo.currentText()
        metric = fetch_pyora_varname_from_pyora_display(self.settings['lookup_df'], display_name)
        if metric is not None:
            display_metric(self, group, metric, sba, recalc_flag)

    def displayXlsxOutput(self):
        """
        C
        """
        excel_file = self.settings['out_dir'] + '\\' + self.w_combo17.currentText()
        excel_path = self.settings['excel_path']
        Popen(list([excel_path, excel_file]), stdout = DEVNULL)
        '''
        import signal
        from os import kill as kill_prcs
        kill_prcs(junk.pid, signal.SIGTERM)
        '''

    def runModelClicked(self):
        """

        """
        ret_code = run_soil_cn_algorithms(self)
        if ret_code == 0:
            calc_livestock_data(self)
            # test_economics_algorithms(self)

    def runEconomicsClicked(self):

        test_economics_algorithms(self)

    def runOptimiseClicked(self):

        pass

    def runLivestockClicked(self):
        """
        C
        """
        calc_livestock_data(self)

    def runSoilCnClicked(self):
        """
        C
        """
        run_soil_cn_algorithms(self)

    # ================================ end of tab3UI =========================

    def tab4UI(self):
        """
        tab for foward run sensitivity analysis
        creates these QComboBox names:  w_combo13 w_combo37, w_combo38, w_combo39, w_combo41s

        """
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
        w_owex_min.setFixedWidth(STD_FLD_SIZE_40)
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
        w_owex_max.setFixedWidth(STD_FLD_SIZE_40)
        grid.addWidget(w_owex_max, irow, 2)
        self.w_owex_max = w_owex_max

        lbl13c = QLabel('Month of application:')
        lbl13c.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl13c, irow, 3)

        w_mnth_appl = QComboBox()
        w_mnth_appl.currentIndexChanged[str].connect(self.mnthApplicChanged)
        w_mnth_appl.setFixedWidth(STD_FLD_SIZE_60)
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

        w_combo36 = QComboBox()
        w_combo36.setFixedWidth(80)
        grid.addWidget(w_combo36, irow, 1)
        self.w_combo36 = w_combo36

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
        w_disp2_c.clicked.connect(lambda: self.displayMetric(self.w_combo37, 'carbon', recalc_flag))
        w_disp2_c.setEnabled(False)
        self.w_disp2_c = w_disp2_c
        grid.addWidget(w_disp2_c, irow, 0)

        w_combo37 = QComboBox()
        w_combo37.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo37))
        self.w_combo37 = w_combo37
        grid.addWidget(w_combo37, irow, 1, 1, 2)

        # nitrogen
        # ========
        irow += 1
        w_disp2_n = QPushButton('Display N metric')
        helpText = 'Display nitrogen chart'
        w_disp2_n.setToolTip(helpText)
        w_disp2_n.setEnabled(False)
        w_disp2_n.clicked.connect(lambda: self.displayMetric(self.w_combo38, 'nitrogen', recalc_flag))
        self.w_disp2_n = w_disp2_n
        grid.addWidget(w_disp2_n, irow, 0)

        w_combo38 = QComboBox()
        w_combo38.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo38))
        self.w_combo38 = w_combo38
        grid.addWidget(w_combo38, irow, 1, 1, 2)

        # water
        # =====
        irow += 1
        w_disp2_w = QPushButton('Display water metric')
        helpText = 'Display water chart'
        w_disp2_w.setToolTip(helpText)
        w_disp2_w.clicked.connect(lambda: self.displayMetric(self.w_combo39, 'soil_water', recalc_flag))
        w_disp2_w.setEnabled(False)
        self.w_disp2_w = w_disp2_w
        grid.addWidget(w_disp2_w, irow, 0)

        w_combo39 = QComboBox()
        w_combo39.currentIndexChanged[str].connect(lambda: self.changeHelpText(self.w_combo39))
        self.w_combo39 = w_combo39
        grid.addWidget(w_combo39, irow, 1, 1, 2)

        irow += 1
        grid.addWidget(QLabel(), irow, 0)  # spacer

        ntab = 4
        self.lggr.info('Last row: {} for tab {}'.format(irow, ntab))

        self.setTabText(ntab,'Sensitivity Analysis')
        self.w_tab4.setLayout(grid)

    def recalcClicked(self):
        """

        """
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

        pass

    # ================================ end of tab4UI =========================

    def tab5UI(self):
        """
        tab for catchment
        creates these QComboBox names:

        """
        grid = QGridLayout()    # define layout
        grid.setSpacing(10)

        font = QFont(self.font())

        font.setPointSize(font.pointSize() + 2)
        self.setFont(font)

        # extra organic waste
        # ===================
        irow = 0
        irow += 1
        grid.addWidget(QLabel(), irow, 0)  # spacer

        irow += 1
        functional_spec = 'This would take in the type of intervention (eg exclosure, ditches etc (other soil water\n'\
                ' conservation measures). We would need a sub-model to simulate deposition or runoff\n'\
                'of soils / water and how those are reduced by the presence of the intervention and the distance\n'\
                          'and slope between the farm area and the intervention.'
        w_func_spec = QLabel(functional_spec)
        w_func_spec.setStyleSheet('font: bold 10.5pt Courier')  # big jump to 11pt
        grid.addWidget(w_func_spec, irow, 0, 2, 2)

        irow += 2
        grid.addWidget(QLabel(), irow, 0)  # spacer

        ntab = 5
        self.lggr.info('Last row: {} for tab {}'.format(irow, ntab))

        self.setTabText(ntab,'Catchment')
        self.w_tab5.setLayout(grid)

    # ================================ end of tab5UI =========================