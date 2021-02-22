#-------------------------------------------------------------------------------
# Name:        ora_json_read.py
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

__prog__ = 'ora_json_read.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os
import json
from glob import glob
from copy import copy

from ora_low_level_fns import get_imnth

ERROR_STR = '*** Error *** '
METRIC_LIST = list(['precip', 'tair'])
JSON_TYPES = {'mgmt': 'management', 'lvstck': 'livestock'}
CLIMATE_TYPES = {'A':'Arid/semi-arid', 'H': 'humid/sub-humid', 'T':'Tropical highlands or temperate'}
FARMING_TYPES = {'LG':'Livestock grazing', 'MR':'Mixed rotation'}
STRATEGIES = list(['On farm production', 'Buy/sell'])

'''
=========== Livestock ==============
'''
def _region_validate(site_defn, anml_prodn_obj):
    '''
    TODO: improve - issue error
    '''
    region = site_defn['region']
    if region not in anml_prodn_obj.africa_regions:
        region = anml_prodn_obj.africa_regions[-1]

    return region

def _farming_system(site_defn):
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
                    value = None
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
            if not os.path.isfile(lvstck_fname):
                continue

            with open(lvstck_fname, 'r') as flvstck:
                lvstck_content = json.load(flvstck)

            site_defn = lvstck_content['site definition']
            area = site_defn['area name']
            region = _region_validate(site_defn, anml_prodn_obj)
            system = _farming_system(site_defn)

            lvstck_grp = []
            for key in site_defn:
                if key.find('livestock') > -1:
                    lvstck_grp.append(LivestockEntity(site_defn[key], anml_prodn_obj))

            subareas[area] = {'region': region, 'system': system, 'lvstck_grp': lvstck_grp}

        self.subareas = subareas
        print()     # cosmetic

'''
=========== Management ==============
'''
def _add_months(crop_obj_inp, add_month):
    '''
    modify crop object by adding months, usually a factor of 12
    '''
    crop_obj = copy(crop_obj_inp)
    if add_month == 0:
        return crop_obj

    crop_obj.sowing_mnth += add_month
    crop_obj.harvest_mnth += add_month
    crop_obj.fert_mnth += add_month
    crop_obj.ow_mnth += add_month

    # irrigation up to 12 months max
    # ==============================
    irrig = {}
    for imnth in crop_obj.irrig:
        amount = crop_obj.irrig[imnth]
        irrig[imnth + add_month] = amount

    crop_obj.irrig = irrig

    return crop_obj

def _read_crop_mngmnt(mgmt_defn, crop_vars):
    '''
    create crops, typically two crops per year over 10, 20, 30, 40 etc. years
    '''

    # TODO: replace with validation function
    # ======================================
    mandatory_key = 'management1'
    if mandatory_key not in mgmt_defn:
        print('mandatory key ' + mandatory_key + ' not present in management file')
        return None

    nyears = mgmt_defn['nyears']
    this_mgmt = mgmt_defn[mandatory_key]

    # create list of crops for one year
    # =================================
    crop_objs = []
    for crop_name in this_mgmt['crops']:
        crop_objs.append(Crop(this_mgmt, crop_name))

    # create list of crops for all years
    # ==================================
    crop_list = []
    add_month = 0
    for year in range(nyears):
        for crop_obj in crop_objs:
            crop_list.append(_add_months(crop_obj, add_month))

        add_month += 12

    return crop_list

class ReadMngmntJsonSubareas(object, ):

    def __init__(self, mgmt_files, crop_vars):
        '''
        management files have been validated
        gather soil params and management for each subarea
        '''
        print('Reading management JSON files...')

        crop_mngmnt_fwd = {}
        crop_mngmnt_ss = {}
        soil_all_areas = {}

        for mgmt_fname in mgmt_files:

            # avoid error when user has removed a management file during a session
            # ====================================================================
            if not os.path.isfile(mgmt_fname):
                continue

            with open(mgmt_fname, 'r') as fmgmt:
                mgmt_content = json.load(fmgmt)

            site_defn = mgmt_content['site definition']
            area = site_defn['area name']
            soil_all_areas[area] = Soil(site_defn['soil'])
            crop_mngmnt_ss[area] = _read_crop_mngmnt(mgmt_content['steady state'], crop_vars)
            crop_mngmnt_fwd[area] = _read_crop_mngmnt(mgmt_content['forward run'], crop_vars)

        self.soil_all_areas = soil_all_areas
        self.crop_mngmnt_ss = crop_mngmnt_ss
        self.crop_mngmnt_fwd = crop_mngmnt_ss
        print()     # cosmetic

class Crop(object,):
    '''

    '''
    def __init__(self, this_mgmt, crop_name):
        """
        Assumptions:
        """
        self.title = 'Crop'

        crop_defn = this_mgmt['crops'][crop_name]

        self.crop_lu = crop_name
        self.sowing_mnth = get_imnth(crop_defn['sowing'])
        self.harvest_mnth = get_imnth(crop_defn['harvest'])
        self.c_yield_typ = crop_defn['yield']

        # inorganic fertiliser application
        # ================================
        io_fert = crop_defn['inorganic fert']
        self.fert_type = io_fert['type']
        self.fert_n = io_fert['fertN']
        self.fert_p = None
        self.fert_mnth = get_imnth(io_fert['month'])

        # organic waste
        # =============
        ow_fert = crop_defn['organic fert']
        self.ow_type = ow_fert['type']
        self.ow_mnth = get_imnth(ow_fert['month'])
        self.ow_amount = ow_fert['amount']

        # irrigation up to 12 months max
        # ==============================
        irrig = {}
        irrig_defn = crop_defn['irrigation']
        for mnth in irrig_defn:
            amount = irrig_defn[mnth]
            if amount == 0:
                continue
            else:
                irrig[get_imnth(mnth)] = amount

        self.irrig = irrig

class Soil(object,):
    '''

    '''
    def __init__(self, soil_defn):
        """
        Assumptions:
        """
        self.title = 'Soil'

        t_depth = soil_defn['t_depth']
        self.t_clay = soil_defn['t_clay']
        self.t_silt = soil_defn['t_silt']
        self.t_sand = soil_defn['t_sand']
        t_carbon = soil_defn['t_carbon']
        t_bulk = soil_defn['t_bulk']
        self.t_pH_h2o = soil_defn['t_pH']
        self.t_salinity = soil_defn['t_salinity']

        tot_soc_meas = (10 ** 4) * (t_depth / 100) * t_bulk * (t_carbon / 100)  # tonnes/ha

        self.t_depth = t_depth
        self.t_carbon = t_carbon
        self.t_bulk = t_bulk
        self.tot_soc_meas = tot_soc_meas

'''
=========== called during initialisation or from GUI ==============
'''
def check_json_input_files(form, mgmt_dirname, jtype):
    '''
    validate management files
    jtype can be either 'mgmt' for crop management, 'lvstck' for livestock
    '''
    if jtype not in JSON_TYPES:
        return
    json_type = JSON_TYPES[jtype]

    ok_json_files = []
    json_files = glob(mgmt_dirname + '/*' + jtype + '.json')
    if len(json_files) > 0:
        for json_fname in json_files:
            json_fname = os.path.normpath(json_fname)
            try:
                with open(json_fname, 'r') as fmgmt:
                    mgmt_content = json.load(fmgmt)
                    # TODO: to log file?                print('Read management input file ' + json_fname)
                    ok_json_files.append(json_fname)

            except (json.JSONDecodeError, OSError, IOError) as err:
                print(str(err))
                print('Could not read ' + json_type + ' input file ' + json_fname)

    nfiles = len(ok_json_files)
    if nfiles == 0 :
        mess = 'No ' + json_type + ' JSON files'
    else:
        dummy, short_fname = os.path.split(ok_json_files[0])
        mess = '{} {} JSON files eg: {}'.format(nfiles, json_type, short_fname)

    form.settings[jtype + '_files'] = ok_json_files

    return mess
