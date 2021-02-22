"""
#-------------------------------------------------------------------------------
# Name:        initialise_funcs.py
# Purpose:     script to read read and write the setup and configuration files
# Author:      Mike Martin
# Created:     31/07/2020
# Licence:     <your licence>
#
#   Notes:
#       entries for drop-down menus are populated after GUI has been created and config file has been read
#-------------------------------------------------------------------------------
"""

__prog__ = 'initialise_pyorator.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
import os
import json
from time import sleep
import sys
from win32api import GetLogicalDriveStrings

from set_up_logging import set_up_logging
from ora_excel_read import check_excel_input_file, ReadStudy
from ora_excel_write import retrieve_output_xls_files
from ora_low_level_fns import extend_out_dir
from ora_json_read import check_json_input_files
from ora_cn_classes import CarbonChange, NitrogenChange
from ora_water_model import  SoilWaterChange
from ora_lookup_df_fns import read_lookup_excel_file, fetch_display_names_from_metrics

PROGRAM_ID = 'pyorator'
EXCEL_EXE_PATH = 'C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE'
ERROR_STR = '*** Error *** '
sleepTime = 5

def initiation(form):
    '''
    this function is called to initiate the programme to process all settings
    '''
    # retrieve settings
    # =================
    form.settings = _read_setup_file(PROGRAM_ID)
    form.settings['studies'] = []

    # initialise bridges across economics, livestock and carbon-nitrogen-water models
    # ===============================================================================
    form.all_runs_output = {}
    form.all_runs_crop_model = {}

    set_up_logging(form, PROGRAM_ID)

    return

def _read_setup_file(program_id):
    """
    read settings used for programme from the setup file, if it exists,
    or create setup file using default values if file does not exist
    """
    func_name = __prog__ + ' _read_setup_file'

    # TODO: this is an unsafe assumption, e.g. if user uses Apache OpenOffice
    # =======================================================================
    if not os.path.isfile(EXCEL_EXE_PATH):
        print(ERROR_STR + 'Excel must be installed - usually here: ' + EXCEL_EXE_PATH)
        sleep(sleepTime)
        exit(0)

    # validate setup file
    # ===================
    fname_setup = program_id + '_setup.json'

    setup_file = os.path.join(os.getcwd(), fname_setup)
    if os.path.exists(setup_file):
        try:
            with open(setup_file, 'r') as fsetup:
                setup = json.load(fsetup)

        except (OSError, IOError) as e:
            sleep(sleepTime)
            exit(0)
    else:
        setup = _write_default_setup_file(setup_file)
        print('Read default setup file ' + setup_file)

    # initialise vars
    # ===============
    settings = setup['setup']
    settings_list = ['config_dir', 'fname_png', 'log_dir', 'fname_lookup']
    for key in settings_list:
        if key not in settings:
            print(ERROR_STR + 'setting {} is required in setup file {} '.format(key, setup_file))
            sleep(sleepTime)
            exit(0)

    # lookup Excel file is required
    # =============================
    if read_lookup_excel_file(settings) is None:
        sleep(sleepTime)
        exit(0)

    # make sure directories exist for configuration and log files
    # ===========================================================
    log_dir = settings['log_dir']
    if not os.path.lexists(log_dir):
        os.makedirs(log_dir)

    config_dir = settings['config_dir']
    if not os.path.lexists(config_dir):
        os.makedirs(config_dir)

    # only one configuration file for this application
    # ================================================
    config_file = os.path.normpath(settings['config_dir'] + '/' + program_id + '_config.json')
    settings['config_file'] = config_file
    # print('Using configuration file: ' + config_file)

    settings['inp_dir'] = ''  # this will be reset after valid Excel inputs file has been identified
    settings['excel_path'] = EXCEL_EXE_PATH

    return settings

def _write_default_setup_file(setup_file):
    """
    stanza if setup_file needs to be created
    """

    # Windows only for now
    # =====================
    os_system = os.name
    if os_system != 'nt':
        print('Operating system is ' + os_system + 'should be nt - cannot proceed with writing default setup file')
        sleep(sleepTime)
        sys.exit(0)

    # auto find ORATOR location from list of drive
    # ============================================
    err_mess = '*** Error creating setup file *** '
    drives = GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]

    orator_flag = False

    for drive in drives:
        orator_dir = os.path.join(drive, 'ORATOR')
        if os.path.isdir(orator_dir):
            print('Found ' + orator_dir)
            orator_flag = True
            break

    if not orator_flag:
        print(err_mess + 'Could not find ' + orator_dir + ' on any of the drives ' + str(drives).strip('[]'))
        sleep(sleepTime)
        sys.exit(0)

    data_path = os.path.join(drive, 'GlobalEcosseData')
    if not os.path.isdir(data_path):
        print(err_mess + 'Could not find ' + data_path)
        sleep(sleepTime)
        sys.exit(0)

    orator_dir += '\\'
    data_path += '\\'
    _default_setup = {
        'setup': {
            'config_dir': orator_dir + 'config',
            'fname_png': os.path.join(orator_dir + 'Images', 'Tree_of_life.PNG'),
            'hwsd_dir': data_path + 'HWSD_NEW',
            'log_dir': orator_dir + 'logs',
            'shp_dir': data_path + 'CountryShapefiles',
            'weather_dir': data_path
        }
    }
    # create setup file
    # =================
    with open(setup_file, 'w') as fsetup:
        json.dump(_default_setup, fsetup, indent=2, sort_keys=True)
        fsetup.close()
        return _default_setup

def _write_default_config_file(config_file):
    """

    """
    _default_config = {
        'inp_xls': '',
        'mgmt_dir': '',
        'write_excel': True,
        'out_dir': ''
    }
    # if config file does not exist then create it...
    with open(config_file, 'w') as fconfig:
        json.dump(_default_config, fconfig, indent=2, sort_keys=True)
        return _default_config

def read_config_file(form):
    """
    read widget settings used in the previous programme session from the config file, if it exists,
    or create config file using default settings if config file does not exist
    """
    func_name = __prog__ + ' read_config_file'

    config_file = form.settings['config_file']
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as fconfig:
                config = json.load(fconfig)
                print('Read config file ' + config_file)
        except (OSError, IOError) as e:
            print(e)
            return False
    else:
        config = _write_default_config_file(config_file)

    for attrib in list(['inp_xls', 'mgmt_dir', 'write_excel', 'out_dir']):
        if attrib not in config:
            print(ERROR_STR + 'attribute {} not present in configuration file: {}'.format(attrib, config_file))
            sleep(sleepTime)
            sys.exit(0)

    # must come first
    # ===============
    out_dir = os.path.normpath(config['out_dir'])
    form.settings['out_dir'] = out_dir
    form.w_lbl15.setText(out_dir)

    inp_xls = os.path.normpath(config['inp_xls'])
    form.w_lbl13.setText(inp_xls)
    form.w_lbl14.setText(check_excel_input_file(form, inp_xls))     # needs out_dir from form.settings

    # this stanza relates to use of JSON files
    # ========================================
    mgmt_dir = os.path.normpath(config['mgmt_dir'])
    form.w_lbl06.setText(mgmt_dir)

    form.w_lbl07.setText(check_json_input_files(form, mgmt_dir, 'mgmt'))
    print(check_json_input_files(form, mgmt_dir, 'lvstck'))

    if config['write_excel']:
        form.w_make_xls.setCheckState(2)
    else:
        form.w_make_xls.setCheckState(0)

    # populate popup lists
    # ====================
    lookup_df = form.settings['lookup_df']
    carbon_change = CarbonChange()
    display_names = fetch_display_names_from_metrics(lookup_df, carbon_change)
    for display_name in display_names:
        form.w_combo07.addItem(display_name)

    nitrogen_change = NitrogenChange()
    display_names = fetch_display_names_from_metrics(lookup_df, nitrogen_change)
    for display_name in display_names:
            form.w_combo08.addItem(display_name)

    soil_water = SoilWaterChange()
    display_names = fetch_display_names_from_metrics(lookup_df, soil_water)
    for display_name in display_names:
            form.w_combo09.addItem(display_name)

    # enable users to view outputs from previous run
    # ==============================================
    study = ReadStudy(inp_xls, out_dir)
    extend_out_dir(form)
    retrieve_output_xls_files(form, study.study_name)

    return True

def write_config_file(form, message_flag=True):
    """
    # write current selections to config file
    """
    study = form.w_study.text()

    # only one config file
    # ====================
    config_file = form.settings['config_file']

    config = {
        "inp_xls": form.w_lbl13.text(),
        "mgmt_dir": form.w_lbl06.text(),
        "write_excel": form.w_make_xls.isChecked(),
        "out_dir": form.w_lbl15.text()
    }
    if os.path.isfile(config_file):
        descriptor = 'Updated existing'
    else:
        descriptor = 'Wrote new'
    if study != '':
        with open(config_file, 'w') as fconfig:
            json.dump(config, fconfig, indent=2, sort_keys=True)
            if message_flag:
                print('\n' + descriptor + ' configuration file ' + config_file)
            else:
                print()
    return
