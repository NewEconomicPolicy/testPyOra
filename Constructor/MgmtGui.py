# -------------------------------------------------------------------------------
# Name:        MgmtGui.py
# Purpose:     enables user to define management data
# Author:      Mike Martin
# Created:     14/04/2021
# Licence:     <your licence>
# Description:
#
# -------------------------------------------------------------------------------
# !/usr/bin/env python

__prog__ = 'MgmtGui.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from os.path import join, isfile
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, QWidget, QGridLayout, QPushButton, QLineEdit, QLabel,
                             QMessageBox, QComboBox, QAction, QScrollArea, QMainWindow)

from ora_gui_misc_fns import simulation_yrs_validate, rotation_yrs_validate
from ora_utils_write_mgmt_sheet import write_mgmt_sht
from ora_excel_read_misc import get_mnth_yr_names
from ora_excel_read import read_subarea_sheet

WARN_STR = '*** Warning *** '
VAR_DESCRIPTIONS = ['Crop:', 'Typical yield\n(t/ha)', 'Inorganic\nfertiliser', 'Amount Nitrogen\napplied (kg/ha)',
                    'Organic\nfertiliser', 'Amount typically\napplied (t/ha)', ' ', 'Irrigation\n(mm)']
MNGMNT_HDRS = ['period', 'crop_name', 'yld_typcl', 'fert_typ', 'fert_n', 'ow_typ', 'ow_amnt', 'irrig']
NO_CROP = 'No crop'
NONE_STR = 'None'

def display_subarea(form, sba_indx):
    """
    check to see if subarea sheet already exists - if so read it
    create arguments
    """
    inorg_ferts = [NONE_STR] + [inorg_fert for inorg_fert in form.ora_parms.syn_fert_parms]
    org_wastes = [NONE_STR] + [ow_typ for ow_typ in form.ora_parms.ow_parms if ow_typ != 'Organic waste type']

    sba_descr = form.w_sba_descrs[sba_indx].text()
    # irrig = form.w_typ_irri[sba_indx].text()
    irrig = str(50)
    crop_vars = form.ora_parms.crop_vars
    nyrs_rota = rotation_yrs_validate(form.w_nrota_ss[sba_indx])
    nyrs_ss, nyrs_fwd = simulation_yrs_validate(form.w_nyrs_ss, form.w_nyrs_fwd)

    # construct name of farm run file as management sheets will need to be added
    # ==========================================================================
    fname_run = join(form.settings['study_area_dir'], form.w_combo00.currentText(), form.w_farm_name.text(),
                                                                                            form.settings['fname_run'])
    if not isfile(fname_run):
        print(WARN_STR + 'Farm run file ' + fname_run + ' must exist')
        return

    mgmt_ss = read_subarea_sheet(fname_run, sba_indx, nyrs_rota, MNGMNT_HDRS)

    arg_list = (fname_run, sba_indx, sba_descr, crop_vars, org_wastes, inorg_ferts, irrig,
                                                               nyrs_rota, nyrs_ss, nyrs_fwd, mgmt_ss)
    form.managment = DispSubareaMgmt(arg_list)
    return

class DispSubareaMgmt(QMainWindow):
    """

    """
    submitted = pyqtSignal(str, str)  # will send 2 strings

    def __init__(self, arg_list, parent=None):
        """
         calls the __init__() method of the QMainWindow (or QWidget) class, allowing
         the DispSubareaMgmt class to be used without repeating code
        """
        super(DispSubareaMgmt, self).__init__(parent)

        self.fname_run, self.subarea, self.sba_descr, self.crop_vars, self.org_wastes, self.inorg_ferts, self.irrig, \
                                                    self.nyrs_rota, self.nyrs_ss, self.nyrs_fwd, mgmt_ss = arg_list

        self.setWindowTitle('Subarea: ' + self.subarea + '   Description: ' + self.sba_descr)

        self.UiGridCmpnts()
        self.ApplyPrvSttngs(mgmt_ss)

        self.UiControlPanel()

        self.UiScrllLayout()

        self.changeFert()
        self.changeOrgWaste()

        self.setGeometry(150, 50, 800, min(self.nyrs_rota, 2)*440)  # posx, posy, width, height
        self.show()  # showing all the widgets

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

    def UiGridCmpnts(self):
        """
        method for grid components
        """
        mnth_keys = get_mnth_yr_names(self.nyrs_rota)
        self.mnth_keys = mnth_keys
        self.rllvr_lim = len(mnth_keys)  # rollover limit

        # applies to crop combo boxes only
        # ================================
        helpText = 'assigning crops - select a perennial crop e.g. grassland, '

        crop_names = [NO_CROP] + [crop_name for crop_name in self.crop_vars]
        self.crop_sttngs_prev = self.rllvr_lim * [NO_CROP]

        # grid will be put in RH vertical box
        # ===================================
        lay_grid = QGridLayout()
        lay_grid.setSpacing(10)  # set spacing between widgets

        # field descriptions - horizontal layout
        # ======================================
        irow = 1
        for icol, desc in enumerate(VAR_DESCRIPTIONS):
            w_lbl = QLabel(desc)
            w_lbl.setAlignment(Qt.AlignCenter)
            lay_grid.addWidget(w_lbl, irow, icol + 1)

        # main loop - number of rows is a factor of 12, one row per month
        # ===============================================================
        irow += 1
        irow_strt = irow
        w_cmbo_crops, w_yld_typs, w_cmbo_ferts, w_n_appld, w_cmbo_ows, w_irri_amnts, w_ow_appld = [{},{},{},{},{},{},{}]
        for irow, mnth in enumerate(mnth_keys):

            # months
            # =======
            w_mnth = QLabel(mnth)
            w_mnth.setAlignment(Qt.AlignCenter)
            lay_grid.addWidget(w_mnth, irow_strt + irow, 0)

            # create row of crop menu drop downs
            # ==================================
            w_cmbo_crops[mnth] = QComboBox()
            for crop_name in crop_names:
                w_cmbo_crops[mnth].addItem(crop_name)

            w_cmbo_crops[mnth].currentIndexChanged[str].connect(self.changeCrop)
            w_cmbo_crops[mnth].setToolTip(helpText)
            lay_grid.addWidget(w_cmbo_crops[mnth], irow_strt + irow, 1)

            # create row of typical yields
            # ============================
            w_yld_typs[mnth] = QLineEdit()
            w_yld_typs[mnth].setFixedWidth(80)
            w_yld_typs[mnth].setAlignment(Qt.AlignRight)
            lay_grid.addWidget(w_yld_typs[mnth], irow_strt + irow, 2)

            # create row of inorganic fertiliser menu drop downs
            # ==================================================
            w_cmbo_ferts[mnth] = QComboBox()
            for fert_name in self.inorg_ferts:
                w_cmbo_ferts[mnth].addItem(fert_name)
            w_cmbo_ferts[mnth].currentIndexChanged[str].connect(self.changeFert)
            lay_grid.addWidget(w_cmbo_ferts[mnth], irow_strt + irow, 3)

            # create row of N applied
            # =======================
            w_n_appld[mnth] = QLineEdit()
            w_n_appld[mnth].setFixedWidth(80)
            w_n_appld[mnth].setAlignment(Qt.AlignRight)
            lay_grid.addWidget(w_n_appld[mnth], irow_strt + irow, 4)

            # create row of organic fertiliser menu drop downs
            # ================================================
            w_cmbo_ows[mnth] = QComboBox()
            for ow_name in self.org_wastes:
                w_cmbo_ows[mnth].addItem(ow_name)
            w_cmbo_ows[mnth].currentIndexChanged[str].connect(self.changeOrgWaste)
            lay_grid.addWidget(w_cmbo_ows[mnth], irow_strt + irow, 5)

            # create row of OW applied
            # ========================
            w_ow_appld[mnth] = QLineEdit()
            w_ow_appld[mnth].setFixedWidth(80)
            w_ow_appld[mnth].setAlignment(Qt.AlignRight)
            lay_grid.addWidget(w_ow_appld[mnth], irow_strt + irow, 6)

            # create row of irrigation amounts
            # ================================
            w_irri_amnts[mnth] = QLineEdit()
            w_irri_amnts[mnth].setFixedWidth(80)
            w_irri_amnts[mnth].setText(self.irrig)
            w_irri_amnts[mnth].setAlignment(Qt.AlignRight)
            lay_grid.addWidget(w_irri_amnts[mnth], irow_strt + irow, 8)

        self.w_cmbo_crops = w_cmbo_crops
        self.w_yld_typs = w_yld_typs
        self.w_cmbo_ferts = w_cmbo_ferts
        self.w_n_appld = w_n_appld
        self.w_cmbo_ows = w_cmbo_ows
        self.w_ow_appld = w_ow_appld
        self.w_irri_amnts = w_irri_amnts

        # add space
        # =========
        for iline in range(2):
            irow += 1
            lay_grid.addWidget(QLabel(' '), irow, 0)

        self.lay_grid = lay_grid  # used in UiScrllLayout

    def ApplyPrvSttngs(self, mgmt_ss):
        """
        method for populating managment GUI
        """
        if mgmt_ss is not None:
            mnth_keys = get_mnth_yr_names(self.nyrs_rota)
            for mnth, rec in zip(mnth_keys, mgmt_ss):
                try:
                    dum, dum, dum, crop_name, yld_typcl, fert_typ, fert_n, ow_typ, ow_amnt, irrig = rec
                except ValueError as err:
                    print(err)
                else:
                    self.w_cmbo_crops[mnth].setCurrentText(crop_name)
                    self.w_yld_typs[mnth].setText(str(yld_typcl))
                    self.w_cmbo_ferts[mnth].setCurrentText(fert_typ)
                    self.w_n_appld[mnth].setText(str(fert_n))
                    self.w_cmbo_ows[mnth].setCurrentText(ow_typ)
                    self.w_ow_appld[mnth].setText(str(ow_amnt))
                    self.w_irri_amnts[mnth].setText(str(irrig))

    def UiControlPanel(self):
        """
        method for constructing control panel
        """
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
        w_submit.clicked.connect(self.saveMgmtClicked)
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

    def UiScrllLayout(self):
        """
        method for laying out UI
        """
        quit = QAction("Quit", self)
        quit.triggered.connect(self.closeEvent)
        '''
        menubar = self.menuBar()
        fmenu = menubar.addMenu("File")
        fmenu.addAction(quit)
        '''
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
        lay_vbox.addLayout(self.lay_hbox_cntrl)  # the horizontal box fits inside the vertical layout
        lay_vbox.addLayout(self.lay_grid)

    def changeFert(self):
        """
        check each of 12 or 24 combos starting in January and working through the months.
        """
        for mnth_indx, mnth in enumerate(self.mnth_keys):

            fert_name = self.w_cmbo_ferts[mnth].currentText()
            if fert_name == NONE_STR:
                self.w_n_appld[mnth].setEnabled(False)
                self.w_n_appld[mnth].setText('0')
            else:
                self.w_n_appld[mnth].setEnabled(True)

    def changeOrgWaste(self):
        """
        check each of 12 or 24 combos starting in January and working through the months.
        """
        for mnth_indx, mnth in enumerate(self.mnth_keys):

            ow_name = self.w_cmbo_ows[mnth].currentText()
            if ow_name == NONE_STR:
                self.w_ow_appld[mnth].setEnabled(False)
                self.w_ow_appld[mnth].setText('0')
            else:
                self.w_ow_appld[mnth].setEnabled(True)

    def saveMgmtClicked(self, dummy):
        """
        gather all fields
        """
        rota_dict = {'mnth_keys': [], 'crop_names': [], 'yld_typcls': [], 'fert_typs': [], 'fert_n_amnts': [],
                                                                        'ow_typs': [], 'ow_amnts': [], 'irrigs': []}

        for irow, mnth in enumerate(self.mnth_keys):
            rota_dict['mnth_keys'].append(mnth)

            crop_name = self.w_cmbo_crops[mnth].currentText()
            rota_dict['crop_names'].append(crop_name)

            yld_typcl = self.w_yld_typs[mnth].text()
            rota_dict['yld_typcls'].append(yld_typcl)

            fert_typ = self.w_cmbo_ferts[mnth].currentText()
            rota_dict['fert_typs'].append(fert_typ)

            fert_n = self.w_n_appld[mnth].text()  # TODO: validate
            rota_dict['fert_n_amnts'].append(fert_n)

            ow_typ = self.w_cmbo_ows[mnth].currentText()
            rota_dict['ow_typs'].append(ow_typ)

            ow_amnt = self.w_ow_appld[mnth].text()  # TODO: validate
            rota_dict['ow_amnts'].append(ow_amnt)

            irrig = self.w_irri_amnts[mnth].text()
            rota_dict['irrigs'].append(irrig)

        nmnths_ss = 12 * self.nyrs_ss
        nmnths_fwd = 12 * self.nyrs_fwd

        write_mgmt_sht(self.fname_run, self.subarea, self.sba_descr, nmnths_ss, nmnths_fwd, rota_dict)

    def changeCrop(self):
        """
        TODO consider using lambda to reduce logic
        check each of 12 or 24 combos starting in January and working through the months on a "first come, first
        served" basis.  The guiding principal is to keep the logic simple and maintainable.
        """
        mnth_keys = self.mnth_keys
        rllvr_lim = self.rllvr_lim  # rollover limit

        mnth_skip_indx = 0
        for mnth_indx, mnth in enumerate(mnth_keys):

            # skip months which have been assigned to a crop
            # ==============================================
            if mnth_indx < mnth_skip_indx:
                continue

            crop_name = self.w_cmbo_crops[mnth].currentText()
            if crop_name == NO_CROP:
                self.w_yld_typs[mnth].setEnabled(False)
                self.w_yld_typs[mnth].setText('0')
                continue

            # check previous month
            # ====================
            if not self.w_cmbo_crops[mnth].isEnabled():
                if mnth_indx > 0:
                    mnth_prev = mnth_keys[mnth_indx - 1]
                    prev_crop_name = self.w_cmbo_crops[mnth_prev].currentText()
                    if prev_crop_name == NO_CROP or prev_crop_name != crop_name:
                        self.w_cmbo_crops[mnth].setCurrentIndex(0)
                        self.w_cmbo_crops[mnth].setEnabled(True)
                        continue

            # on finding a crop, set subsequent months to that crop
            # =====================================================
            crop_indx = self.w_cmbo_crops[mnth].currentIndex()
            t_grow = self.crop_vars[crop_name]['t_grow']
            max_yld = self.crop_vars[crop_name]['max_yld']

            strt_indx = mnth_keys.index(mnth)
            end_indx = strt_indx + t_grow
            if end_indx > rllvr_lim:
                self.w_cmbo_crops[mnth].setCurrentIndex(0)
                print('Insufficient free months for crop ' + crop_name)
            else:
                # assign subsequent months to this crop
                # =====================================
                for mnth2 in mnth_keys[strt_indx:end_indx]:
                    self.w_cmbo_crops[mnth2].setCurrentIndex(crop_indx)
                    self.w_yld_typs[mnth2].setEnabled(False)
                    self.w_yld_typs[mnth2].setText('0')
                    if mnth2 != mnth:
                        self.w_cmbo_crops[mnth2].setEnabled(False)

                # retrieve and display maximum yield
                # ==================================
                self.w_yld_typs[mnth2].setEnabled(True)
                self.w_yld_typs[mnth2].setText(str(max_yld))
                mnth_skip_indx = end_indx

    def dismissClicked(self):

        self.close()

    def resetClicked(self):
        """

        """
        for mnth in self.mnth_keys:
            self.w_cmbo_crops[mnth].setEnabled(True)
            self.w_cmbo_crops[mnth].setCurrentIndex(0)
