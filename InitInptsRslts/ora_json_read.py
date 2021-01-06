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
from time import sleep
from glob import glob
from copy import copy

from ora_low_level_fns import get_imnth

METRIC_LIST = list(['precip', 'tair'])
ERROR_STR = '*** Error *** '
sleepTime = 5

def check_json_input_files(form, mgmt_dirname):
    '''
    validate management files
    '''
    mgmt_files = []
    json_files = glob(mgmt_dirname + '/*mgmt.json')
    if len(json_files) > 0:
        for mgmt_fname in json_files:
            mgmt_fname = os.path.normpath(mgmt_fname)
            try:
                with open(mgmt_fname, 'r') as fmgmt:
                    mgmt_content = json.load(fmgmt)
                    # TODO: to log file?                print('Read management input file ' + mgmt_fname)
                    mgmt_files.append(mgmt_fname)

            except (json.JSONDecodeError, OSError, IOError) as err:
                print(str(err))
                print('Could not read management input file ' + mgmt_fname)

    nfiles = len(mgmt_files)
    if nfiles == 0 :
        mess = 'No management JSON files'
        form.w_use_json.setCheckState(0)  # adjust GUI to deny use of JSON files
    else:
        dummy, short_fname = os.path.split(mgmt_files[0])
        mess = '{} management JSON files eg: {}'.format(nfiles, short_fname)

    form.settings['mgmt_files'] = mgmt_files

    return mess

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

class ReadJsonSubareas(object, ):

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
            with open(mgmt_fname, 'r') as fmgmt:
                mgmt_content = json.load(fmgmt)
                # TODO: logging?         print('Read management input file ' + mgmt_fname)

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

