#-------------------------------------------------------------------------------
# Name:        ora_gui_misc_fns.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     26/10/2020
# Licence:     <your licence>
# Definitions:
#   spin_up
#
# Description:
#
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_gui_misc_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import json
from csv import reader
from os.path import isfile, join

WARN_STR = '*** Warning *** '
ERROR_STR = '*** Error *** '
METRIC_LIST = list(['precip', 'tair'])
FNAME_RUN = 'FarmWthrMgmt.xlsx'
JSON_TYPES = {'lvstck': 'livestock'}
CLIMATE_TYPES = {'A':'Arid/semi-arid', 'H': 'humid/sub-humid', 'T':'Tropical highlands or temperate'}
FARMING_TYPES = {'LG':'Livestock grazing', 'MR':'Mixed rotation'}
STRATEGIES = list(['On farm production', 'Buy/sell'])

'''
=========== BioModels ==============
'''
def rotation_yrs_validate(w_nrota_ss):
    '''
    check number of rotation years
    '''
    try:
        nyrs_rota  = int(w_nrota_ss.text())
    except ValueError as err:
        nyrs_rota = 1
        print(WARN_STR + 'number of rotation years years must be an integer')

    return nyrs_rota


def simulation_yrs_validate(w_nyrs_ss, w_nyrs_fwd):
    '''
    number of steady state and forward run years must be integers - subsitute defaults in event of non-compliance
    '''
    try:
        nyrs_ss = int(w_nyrs_ss.text())
    except ValueError as err:
        nyrs_ss = 10
        print(WARN_STR + 'number of steady state years must be an integer')

    try:
        nyrs_fwd = int(w_nyrs_fwd.text())
    except ValueError as err:
        nyrs_fwd = 10
        print(WARN_STR + 'number of forward run years must be an integer')

    return nyrs_ss, nyrs_fwd
'''
=========== Livestock ==============
'''
def region_validate(site_defn, anml_prodn_obj):
    '''
    TODO: improve - issue error
    '''
    region = site_defn['region']
    if region not in anml_prodn_obj.africa_regions:
        region = anml_prodn_obj.africa_regions[-1]

    return region

def farming_system(site_defn):
    '''
    should be 3 characters, capitals
    '''
    system = site_defn['system'].upper()
    if len(system) < 3:
        system = 'MRA'  # TODO: issue warning

    else:
        farming_type = system[0:2]
        if farming_type not in FARMING_TYPES:
            farming_type = 'MR'  # TODO: issue warning

        climate_type = system[2]
        if climate_type not in CLIMATE_TYPES:
            climate_type = 'A'

        system = farming_type + climate_type

    return system

class LivestockEntity:

    def __init__(self, lvstck_content, anml_prodn_obj):
        '''
        TODO: improve
        '''
        type = lvstck_content['type']
        if type not in anml_prodn_obj.africa_anml_types:
            type = anml_prodn_obj.africa_anml_types[-1]

        number = float(lvstck_content['number'])    # TODO: trap error
        strategy = lvstck_content['strategy']
        if strategy not in STRATEGIES:
            strategy = STRATEGIES[-1]

        feeds = []
        for key in lvstck_content:
            if key.find('feed') > -1:
                feed_type = lvstck_content[key]['type']
                if feed_type ==  'bought in':
                    value = lvstck_content[key]['value']
                else:
                    if feed_type not in anml_prodn_obj.crop_names:
                        feed_type = anml_prodn_obj.crop_names[-1]

                    try:
                        value = lvstck_content[key]['value']
                    except KeyError as err:
                        value = None

                feeds.append({'type':feed_type, 'value': value})

        self.type = type
        self.number = number
        self.statgey = strategy
        self.feeds = feeds
        self.manure = None
        self.n_excrete = None
        self.meat = None
        self.milk = None

class ReadLvstckJsonSubareas(object, ):

    def __init__(self, lvstck_files, anml_prodn_obj):
        '''
        read and validate livestock JSON file
        '''
        print('Reading livestock JSON files...')

        subareas = {}

        for lvstck_fname in lvstck_files:

            # avoid error when user has removed a management file during a session
            # ====================================================================
            if not isfile(lvstck_fname):
                continue

            with open(lvstck_fname, 'r') as flvstck:
                lvstck_content = json.load(flvstck)

            site_defn = lvstck_content['site definition']
            area = site_defn['area name']
            region = region_validate(site_defn, anml_prodn_obj)
            system = farming_system(site_defn)

            lvstck_grp = []
            for key in site_defn:
                if key.find('livestock') > -1:
                    lvstck_grp.append(LivestockEntity(site_defn[key], anml_prodn_obj))

            subareas[area] = {'region': region, 'system': system, 'lvstck_grp': lvstck_grp}

        self.subareas = subareas
        print()     # cosmetic

def disp_ow_parms(form):
    '''
    display summary of selected organic waste type
    '''
    ow_parms = form.ora_parms.ow_parms

    # build message
    # =============
    ow_type = form.w_combo13.currentText()
    pcnt_c = round(ow_parms[ow_type]['pcnt_c']*100, 3)
    pcnt_urea = round(ow_parms[ow_type]['pcnt_urea']*100, 3)
    ann_c_input = round(ow_parms[ow_type]['ann_c_input']*100, 3)

    mess = 'Organic waste parameters:\t% Carbon: {}\t'.format(pcnt_c)
    mess += '\t%C wrt untreated waste: {}\t\t% Ammonia or urea-N in manure: {}'.format(ann_c_input, pcnt_urea)

    return mess

def check_mngmnt_ow(form):
    '''
    display summary of selected organic waste type
    '''

    # TODO - delete if unnecessary

    '''
    # check first 12 months
    # =====================
    if hasattr(form, 'ora_subareas'):
        subareas = form.ora_subareas
        for sba in subareas:
            for imnth in range(12):
    '''

    # build message
    # =============
    ow_type = form.w_combo13.currentText()
    mnth_appl = form.w_mnth_appl.currentText()

    mess = 'Extra {} will be applied in {}'.format(ow_type, mnth_appl)

    return mess

def format_sbas(prefix, subareas, mess = ''):
    '''
     add list of subareas to message
     '''
    mess += prefix
    for sba in subareas:
        mess += sba + ', '
    mess = mess.rstrip(', ')

    return mess
