"""
#-------------------------------------------------------------------------------
# Name:        climateGui.py
# Purpose:     invoked by main GUI to create weather related widgets
# Author:      Mike Martin
# Created:     23/02/2021
# Licence:     <your licence>
# Description:
#
#-------------------------------------------------------------------------------
#
"""
__prog__ = 'climateGui.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QComboBox, QLineEdit, QPushButton, QCheckBox

def climate_gui(form, grid, irow):
    '''
    construct that section of the GUI which is dedicated to climate
    drop-down widgets used: w_combo29s, w_combo30w, w_combo30, w_combo31s
    '''
    if form.wthr_sets is None:
        start_year = 1921
        end_year = 1923
    else:
        start_year = form.wthr_sets['CRU_hist']['year_start']
        end_year = form.wthr_sets['CRU_hist']['year_end']

    hist_syears = list(range(start_year, end_year))

    if form.wthr_sets is None:
        start_year = 1921
        end_year = 1923
    else:
        start_year = form.wthr_sets['ClimGen_A1B']['year_start']
        end_year = form.wthr_sets['ClimGen_A1B']['year_end']

    fut_syears = list(range(start_year, end_year))

    scenarios = list(['A1B','A2','B1','B2'])  # these have been replaced by RCPs

    # Climate dataset resources
    # =========================
    w_lbl30w = QLabel('Weather resource:')
    w_lbl30w.setAlignment(Qt.AlignRight)
    helpText = 'permissable weather dataset resources are limited to CRU only'
    w_lbl30w.setToolTip(helpText)
    grid.addWidget(w_lbl30w, irow, 0)

    w_combo30w = QComboBox()
    for wthr_rsrc in form.wthr_rsrces_gnrc:
        w_combo30w.addItem(wthr_rsrc)
    w_combo30w.setFixedWidth(80)
    grid.addWidget(w_combo30w, irow, 1)

    # first line - scenarios
    # ======================
    w_lbl30 = QLabel('Climate Scenario:')
    w_lbl30.setAlignment(Qt.AlignRight)
    helpText = 'Ecosse requires future average monthly precipitation and temperature derived from climate models.\n' \
        + 'The data used here is ClimGen v1.02 created on 16.10.08 developed by the Climatic Research Unit\n' \
        + ' and the Tyndall Centre. See: http://www.cru.uea.ac.uk/~timo/climgen/'

    w_lbl30.setToolTip(helpText)
    grid.addWidget(w_lbl30, irow, 2)

    w_combo30 = QComboBox()
    for scen in scenarios:
        w_combo30.addItem(str(scen))
    w_combo30.setFixedWidth(60)
    grid.addWidget(w_combo30, irow, 3)

    if form.wthr_sets is None:
        w_combo30.setEnabled(False)
        w_combo30w.setEnabled(False)
    else:
        w_combo30.setEnabled(True)
        w_combo30w.setEnabled(True)

    form.w_combo30w = w_combo30w
    form.w_combo30 = w_combo30

    # second line - steady state
    # ==========================
    irow += 1
    w_lbl29s = QLabel('Steady state start:')
    w_lbl29s.setAlignment(Qt.AlignRight)
    helpText = 'Ecosse requires long term average monthly precipitation and temperature\n' \
            + 'which is derived from datasets managed by Climatic Research Unit (CRU).\n' \
            + ' See: http://www.cru.uea.ac.uk/about-cru'
    w_lbl29s.setToolTip(helpText)
    grid.addWidget(w_lbl29s, irow, 0)

    w_combo29s = QComboBox()
    for year in hist_syears:
        w_combo29s.addItem(str(year))
    w_combo29s.setFixedWidth(80)
    form.w_combo29s = w_combo29s
    grid.addWidget(w_combo29s, irow, 1)
    form.w_combo29s = w_combo29s

    # second line - end year and number of years
    # ==========================================
    w_lbl29e = QLabel('# years:')
    w_lbl29e.setAlignment(Qt.AlignRight)
    grid.addWidget(w_lbl29e, irow, 2)
    form.w_lbl29e = w_lbl29e

    w_nyrs_ss = QLineEdit()
    w_nyrs_ss.setFixedWidth(40)
    # w_nyrs_ss.setEnabled(False)
    grid.addWidget(w_nyrs_ss, irow, 3)
    form.w_nyrs_ss  = w_nyrs_ss

    # third line - forward run
    # ========================
    irow += 1
    w_lbl31s = QLabel('Forward run start:')
    helpText = 'Simulation start and end years determine the number of growing seasons to simulate\n'
    w_lbl31s.setToolTip(helpText)
    w_lbl31s.setAlignment(Qt.AlignRight)
    grid.addWidget(w_lbl31s, irow, 0)

    w_combo31s = QComboBox()
    for year in fut_syears:
        w_combo31s.addItem(str(year))
    form.w_combo31s = w_combo31s
    w_combo31s.setFixedWidth(80)
    grid.addWidget(w_combo31s, irow, 1)
    form.w_combo31s = w_combo31s

    # third line - end year and number of years
    # =========================================
    w_lbl31e = QLabel('# years:')
    w_lbl31e.setAlignment(Qt.AlignRight)
    grid.addWidget(w_lbl31e, irow, 2)
    form.w_lbl31e = w_lbl31e

    w_nyrs_fwd = QLineEdit()
    w_nyrs_fwd.setFixedWidth(40)
    # w_nyrs_fwd.setEnabled(False)
    grid.addWidget(w_nyrs_fwd, irow, 3)
    form.w_nyrs_fwd = w_nyrs_fwd

    irow += 1
    grid.addWidget(QLabel(), irow, 0)  # spacer

    # ============
    irow += 1
    w_csv_psh = QPushButton('CSV weather set')
    helpText = 'Comma Separated Values (CSV) file comprising monthly weather - precipitation (mm) and air temperature at surface (deg C)'
    w_csv_psh.setToolTip(helpText)
    grid.addWidget(w_csv_psh, irow, 0)
    w_csv_psh.clicked.connect(form.fetchCsvFile)

    w_csv_fn = QLabel('')
    grid.addWidget(w_csv_fn, irow, 1, 1, 5)
    form.w_csv_fn = w_csv_fn

    # CSV description
    # ===============
    irow += 1
    w_csv_dscr = QLabel('')
    grid.addWidget(w_csv_dscr, irow, 0, 1, 5)
    form.w_csv_dscr = w_csv_dscr

    w_view_csv = QPushButton('View CSV file')
    helpText = 'View CSV file comprising monthly weather'
    w_view_csv.setToolTip(helpText)
    grid.addWidget(w_view_csv, irow, 6)
    w_view_csv.clicked.connect(form.viewCsvFile)
    form.w_view_csv = w_view_csv

    # =============
    w_use_csv = QCheckBox('Use CSV')
    helpText = 'Use CSV in preference to CRU data'
    w_use_csv.setToolTip(helpText)
    w_view_csv.clicked.connect(form.checkWthrSrces)
    grid.addWidget(w_use_csv, irow, 7)
    form.w_use_csv = w_use_csv


    return irow

