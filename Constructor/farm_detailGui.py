"""
#-------------------------------------------------------------------------------
# Name:        farm_detailGui.py
# Purpose:     invoked by main GUI to great weather related widgets
# Author:      Mike Martin
# Created:     23/02/2021
# Licence:     <your licence>
# Description:
#
#-------------------------------------------------------------------------------
#
"""
__prog__ = 'farm_detailGui.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

from os.path import join, normpath, isfile

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QComboBox, QLineEdit

from ora_excel_read import read_farm_wthr_xls_file
from ora_excel_read_misc import identify_farms_for_study, read_farm_wthr_sbsa_xls_file
from ora_gui_misc_fns import format_sbas

ERROR_STR = '*** Error *** '
STD_FLD_SIZE_40 = 40
STD_FLD_SIZE_60 = 60
STD_FLD_SIZE_80 = 80
STD_FLD_SIZE_100 = 100
STD_CMBO_SIZE = 150

RUN_MODE_HDRS = {'Steady state': '', 'Forward run': ''}
FIELD_NAMES = {'Description': '',
               'Area\n(ha)': '',
               'Rotation SS\n(yrs)': 'Number of years of a crop rotation cycle for this subarea',
               'Mgmt SS': '',
               'Copy Mgmt': '',
               'Rotation Fwd\n(yrs)': '',
               'Mgmt Fwd': ''
               }

def post_sbas_hdrs(grid, irow):
    '''
    called once from main GUI at startup
    '''

    for icol, fld_name in enumerate(RUN_MODE_HDRS):
        hdr_lbl = QLabel(fld_name)
        hdr_lbl.setToolTip(RUN_MODE_HDRS[fld_name])
        hdr_lbl.setAlignment(Qt.AlignCenter)
        grid.addWidget(hdr_lbl, irow, icol*4, 1, 3)

    irow += 1
    for icol, fld_name in enumerate(FIELD_NAMES):
        hdr_lbl = QLabel(fld_name)
        hdr_lbl.setToolTip(FIELD_NAMES[fld_name])
        hdr_lbl.setAlignment(Qt.AlignCenter)
        grid.addWidget(hdr_lbl, irow, icol)

    return irow

def farm_detail_gui(form, grid, irow):
    '''
    construct that section of the GUI dedicated to farm detail
    '''

    # ========
    lbl00 = QLabel('Study area:')
    lbl00.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl00, irow, 0)

    w_combo00 = QComboBox()
    for study in form.settings['studies']:
        w_combo00.addItem(study)
    w_combo00.setFixedWidth(STD_CMBO_SIZE)
    grid.addWidget(w_combo00, irow, 1, 1, 3)
    w_combo00.currentIndexChanged[str].connect(form.changeStudy)
    form.w_combo00 = w_combo00

    # ===================
    lbl00b = QLabel('Existing farms:')
    lbl00b.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl00b, irow, 4)

    w_combo02 = QComboBox()
    grid.addWidget(w_combo02, irow, 5)
    w_combo02.currentIndexChanged[str].connect(form.postFarmDetail)
    form.w_combo02 = w_combo02

    # ===================
    irow += 1
    lbl00a = QLabel('Farm:')
    lbl00a.setAlignment(Qt.AlignRight)
    helpText = 'list of farms'
    lbl00a.setToolTip(helpText)
    grid.addWidget(lbl00a, irow, 0)

    w_farm_name = QLineEdit()
    w_farm_name.setFixedWidth(STD_FLD_SIZE_80)
    grid.addWidget(w_farm_name, irow, 1)
    w_farm_name.textChanged[str].connect(form.changeFarmName)
    form.w_farm_name = w_farm_name

    sys_lbl = QLabel('Farming system:')
    sys_lbl.setAlignment(Qt.AlignRight)
    grid.addWidget(sys_lbl, irow, 2)

    w_systems = QComboBox()
    w_systems.setFixedWidth(STD_FLD_SIZE_60)
    for prod_sys in form.anml_prodn.africa_systems:
        w_systems.addItem(prod_sys)
    helpText = 'farming systems'
    w_systems.setToolTip(helpText)
    grid.addWidget(w_systems, irow, 3)
    w_systems.currentIndexChanged[str].connect(form.changeSystem)

    sys_descr_lbl = QLabel('')
    grid.addWidget(sys_descr_lbl, irow, 4, 1, 3)

    form.w_systems = w_systems
    form.sys_descr_lbl = sys_descr_lbl

    # lon/lat
    # =======
    irow += 1
    lbl03a = QLabel('Latitude:')
    lbl03a.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl03a, irow, 0)

    w_lat = QLineEdit()
    w_lat.setFixedWidth(STD_FLD_SIZE_60)
    grid.addWidget(w_lat, irow, 1)
    form.w_lat = w_lat

    form.w_lat = w_lat
    lbl03b = QLabel('Longitude:')
    lbl03b.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl03b, irow, 2)

    w_lon = QLineEdit()
    w_lon.setFixedWidth(STD_FLD_SIZE_60)
    grid.addWidget(w_lon, irow, 3)
    form.w_lon = w_lon

    region_lbl = QLabel('Region:')
    region_lbl.setAlignment(Qt.AlignRight)
    grid.addWidget(region_lbl, irow, 4)

    w_regions = QComboBox()
    for region in form.anml_prodn.africa_regions:
        w_regions.addItem(region)
    helpText = 'world region'
    w_regions.setToolTip(helpText)
    grid.addWidget(w_regions, irow, 5, alignment=Qt.AlignHCenter)
    form.w_regions = w_regions

    # additional farm related
    # =======================
    irow += 1

    lbl02a = QLabel('Description:')
    lbl02a.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl02a, irow, 0)

    w_farm_desc = QLineEdit()
    grid.addWidget(w_farm_desc, irow, 1, 1, 3)
    form.w_farm_desc = w_farm_desc

    lbl02b = QLabel('Area (ha):')
    lbl02b.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl02b, irow, 4)

    w_area = QLineEdit()
    w_area.setFixedWidth(STD_FLD_SIZE_60)
    grid.addWidget(w_area, irow, 5)
    form.w_area = w_area

    # ===================
    lbl01 = QLabel('Sub-district:')
    helpText = 'Sub-district or kebele (Ethiopia) or tehsil (India) in which farm is located'
    lbl01.setToolTip(helpText)
    lbl01.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl01, irow, 6)

    w_subdist = QLineEdit()
    w_subdist.setFixedWidth(STD_FLD_SIZE_100)
    grid.addWidget(w_subdist, irow, 7)
    form.w_subdist = w_subdist

    # ===================
    lbl02c = QLabel('% of sub-district:')
    lbl02c.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl02c, irow, 8)

    w_prcnt = QLineEdit()
    w_prcnt.setFixedWidth(STD_FLD_SIZE_40)
    grid.addWidget(w_prcnt, irow, 9)
    form.w_prcnt = w_prcnt

    return irow

def repopulate_farms_dropdown(form):
    '''
    called at program start up or when user changes study area or if a farm is added or removed
    '''
    farms = identify_farms_for_study(form)

    if hasattr(form, 'w_combo02'):      # TODO tidy
        form.w_combo02.clear()
        for farm_name in farms:
            form.w_combo02.addItem(farm_name)
    else:
        form.w_tab_wdgt.w_combo02.clear()
        for farm_name in farms:
            form.w_tab_wdgt.w_combo02.addItem(farm_name)

    return

def post_farm_detail(form):
    '''
    called once from main GUI when farm changed
    if successful then return farm run file name
    '''
    ret_code = None
    farm_name = form.w_farm_name.text()
    if farm_name == '':
        return ret_code

    farms = identify_farms_for_study(form)
    if farm_name not in farms.keys():

        # overwrite farm name with one which exists
        # =========================================
        farm_name = list(farms.keys())[0]
        form.w_farm_name.setText(farm_name)

    farm_wthr_fname = farms[farm_name]
    study = form.w_combo00.currentText()
    study_dir = join(form.settings['study_area_dir'], study)

    farm_dir = join(normpath(study_dir), farm_name)
    form.w_run_dir0.setText(farm_dir)
    form.w_run_dir3.setText(farm_dir)

    if isfile(farm_wthr_fname):
        farm_vars = read_farm_wthr_xls_file(farm_wthr_fname)
        if farm_vars is None:
            print(ERROR_STR + ' check ' + farm_wthr_fname)
        else:
            subareas, sub_distr, dum, lat, lon, area, prnct, farm_desc, farm_system, region = farm_vars
            form.w_lbl_sbas.setText(format_sbas('Subareas: ', subareas))
            form.w_farm_desc.setText(farm_desc)
            form.w_prcnt.setText(str(prnct))
            form.w_subdist.setText(sub_distr)
            form.w_area.setText(str(area))
            form.w_lat.setText(str(lat))
            form.w_lon.setText(str(lon))
            systm_indx = form.w_systems.findText(farm_system)
            if systm_indx >= 0:
                form.w_systems.setCurrentIndex(systm_indx)
            rgn_indx = form.w_regions.findText(region)
            if rgn_indx >= 0:
                form.w_regions.setCurrentIndex(rgn_indx)
            ret_code = farm_wthr_fname
    else:
        print('Could not locate ' + farm_wthr_fname)

    return ret_code

def post_sbas_detail(form, run_xls_fn):
    '''
    called once from main GUI after a successful farm change
    '''
    ret_code = False

    if hasattr(form, 'w_nrota_ss'):
        read_farm_wthr_sbsa_xls_file(form, run_xls_fn)

    return ret_code

    return irow
