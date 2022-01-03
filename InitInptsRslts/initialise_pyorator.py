'''
#-------------------------------------------------------------------------------
# Name:        initialise_funcs.py
# Purpose:     script to read read and write the setup and configuration files
# Author:      Mike Martin
# Created:     31/07/2020
# Licence:     <your licence>
# Description:#
#   Notes:
#       entries for drop-down menus are populated after GUI has been created and config file has been read
#-------------------------------------------------------------------------------
'''

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
from ora_excel_read import check_params_excel_file, ReadStudy, ReadCropOwNitrogenParms
from ora_json_read import check_json_xlsx_inp_files
from ora_cn_classes import CarbonChange, NitrogenChange, CropModel, EconoLvstckModel
from ora_water_model import  SoilWaterChange
from ora_lookup_df_fns import read_lookup_excel_file, fetch_display_names_from_metrics

PROGRAM_ID = 'pyorator'
EXCEL_EXE_PATH = 'C:\\Program Files\\Microsoft Office\\root\\Office16'
ERROR_STR = '*** Error *** '
sleepTime = 5

FNAME_RUN = 'FarmWthrMgmt.xlsx'
MNTH_NAMES_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def initiation(form):
    '''
    this function is called to initiate the programme to process all settings
    '''
    # retrieve settings
    # =================
    form.settings = _read_setup_file(PROGRAM_ID)

    # initialise bridges across economics, livestock and carbon-nitrogen-water models
    # ===============================================================================
    form.all_runs_output = {}
    form.all_runs_crop_model = {}

    # Set flags to show if crop and livestock models have run
    # ===============================================================================
    form.crop_run = False
    form.livestock_run = False
    set_up_logging(form, PROGRAM_ID)

    return

def _read_setup_file(program_id):
    '''
    read settings used for programme from the setup file, if it exists,
    or create setup file using default values if file does not exist
    '''
    func_name = __prog__ + ' _read_setup_file'

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
    settings_list = ['config_dir', 'fname_png', 'log_dir', 'fname_lookup', 'excel_dir', 'weather_dir', 'params_xls']
    for key in settings_list:
        if key not in settings:
            print(ERROR_STR + 'setting {} is required in setup file {} '.format(key, setup_file))
            sleep(sleepTime)
            exit(0)

    # TODO: consider situation when user uses Apache OpenOffice
    # =========================================================
    excel_flag = False
    if os.path.isdir(settings['excel_dir']):

        excel_path = os.path.join(settings['excel_dir'], 'EXCEL.EXE')
        if os.path.isfile(excel_path):
            excel_flag = True
        else:
            print(ERROR_STR + 'Excel progam must exist - should be here: ' + excel_path)

    else:
        print(ERROR_STR + 'Excel directory must exist - usually here: ' + EXCEL_EXE_PATH)

    if not excel_flag:
        sleep(sleepTime)
        exit(0)

    settings['excel_path'] = excel_path

    # lookup Excel and parameters files are required
    # ==============================================
    if read_lookup_excel_file(settings) is None:
        sleep(sleepTime)
        exit(0)

    params_xls = os.path.normpath(settings['params_xls'])
    if check_params_excel_file(params_xls) is None:
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

    settings['study'] = ''

    return settings

def _write_default_setup_file(setup_file):
    '''
    stanza if setup_file needs to be created
    '''

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

    # typically: 'fname_lookup': 'G:\\PyOraDev\\testPyOra\\OratorRun\\lookup\\Orator variables lookup table.xlsx'
    # ===========================================================================================================
    orator_dir += '\\'
    data_path += '\\'
    _default_setup = {
        'setup': {
            'config_dir': orator_dir + 'config',
            'fname_png': os.path.join(orator_dir + 'run\\Images', 'Tree_of_life.PNG'),
            'fname_lookup': '',
            'excel_dir': '',
            'log_dir': orator_dir + 'logs',
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
    '''

    '''
    _default_config = {
        'params_xls': '',
        'mgmt_dir': '',
        'write_excel': True,
        'out_dir': ''
    }
    # if config file does not exist then create it...
    with open(config_file, 'w') as fconfig:
        json.dump(_default_config, fconfig, indent=2, sort_keys=True)
        return _default_config

def read_config_file(form):
    '''
    read widget settings used in the previous programme session from the config file, if it exists,
    or create config file using default settings if config file does not exist
    '''
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

    for attrib in list(['mgmt_dir', 'write_excel']):
        if attrib not in config:
            print(ERROR_STR + 'attribute {} not present in configuration file: {}'.format(attrib, config_file))
            sleep(sleepTime)
            sys.exit(0)

    # required for extra organic waste
    # ================================
    parms_xls_fname = form.settings['params_xls']
    print('Reading: ' + parms_xls_fname)
    form.ora_parms = ReadCropOwNitrogenParms(parms_xls_fname)
    for ow_typ in form.ora_parms.ow_parms:
        if ow_typ != 'Organic waste type':
            form.w_combo13.addItem(ow_typ)

    for mnth in MNTH_NAMES_SHORT:
        form.w_mnth_appl.addItem(mnth)

    # stanza for extra org waste
    # ==========================
    for attrib in list(['owex_min', 'owex_max', 'ow_type_indx', 'mnth_appl_indx']):
        if attrib not in config:
            owex_min = 0.0
            owex_max = 0.0
            ow_type_indx = 0
            mnth_appl_indx = 0
            break
    else:
        owex_min = config['owex_min']
        owex_max = config['owex_max']
        ow_type_indx = config['ow_type_indx']
        mnth_appl_indx = config['mnth_appl_indx']

    form.w_owex_min.setText(str(owex_min))
    form.w_owex_max.setText(str(owex_max))
    form.w_combo13.setCurrentIndex(ow_type_indx)
    form.w_mnth_appl.setCurrentIndex(mnth_appl_indx)

    # this stanza relates to use of JSON files
    # ========================================
    mgmt_dir = os.path.normpath(config['mgmt_dir'])
    if not os.path.isdir(mgmt_dir):
        mess =  '\nManagement path: ' + mgmt_dir + ' does not exist\n\t- check configuration file ' + config_file
        return

    form.w_lbl06.setText(mgmt_dir)

    form.w_lbl07.setText(check_json_xlsx_inp_files(form, mgmt_dir))

    # check run file
    # =============
    run_xls_fname = os.path.join(mgmt_dir, FNAME_RUN)
    if not os.path.isfile(run_xls_fname):
        print(ERROR_STR + '\nRun file ' + run_xls_fname + ' does not exist\n\t- select another management path')
        return

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

    crop_model = CropModel()
    display_names = fetch_display_names_from_metrics(lookup_df, crop_model)
    for display_name in display_names:
        form.w_combo10.addItem(display_name)

    econ_model = EconoLvstckModel()
    display_names = fetch_display_names_from_metrics(lookup_df, econ_model)
    for display_name in display_names:
        form.w_combo11.addItem(display_name)

    # enable users to view outputs from previous run
    # ==============================================
    form.settings['study'] = ReadStudy(form, mgmt_dir, run_xls_fname)

    return True

def write_config_file(form, message_flag=True):
    '''
    write current selections to config file
    '''

    # only one config file
    # ====================
    config_file = form.settings['config_file']

    config = {
        'mgmt_dir': form.w_lbl06.text(),
        'write_excel': form.w_make_xls.isChecked(),
        'owex_min': form.w_owex_min.text(),
        'owex_max': form.w_owex_max.text(),
        'ow_type_indx': form.w_combo13.currentIndex(),
        'mnth_appl_indx': form.w_mnth_appl.currentIndex()
    }
    if os.path.isfile(config_file):
        descriptor = 'Updated existing'
    else:
        descriptor = 'Wrote new'

    with open(config_file, 'w') as fconfig:
        json.dump(config, fconfig, indent=2, sort_keys=True)
        if message_flag:
            print('\n' + descriptor + ' configuration file ' + config_file)
        else:
            print()

    return
