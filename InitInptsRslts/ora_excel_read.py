#-------------------------------------------------------------------------------
# Name:        ora_excel_read.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     26/12/2019
# Licence:     <your licence>
# Definitions:
#   spin_up
#
# Description:
#
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_excel_read.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os
from copy import copy
from openpyxl import load_workbook
from pandas import Series, read_excel, DataFrame
from zipfile import BadZipFile
from glob import glob
from calendar import monthrange
from pandas import DataFrame
from numpy import nan, isnan

from ora_water_model import add_pet_to_weather
from ora_cn_fns import plant_inputs_crops_distribution
from ora_low_level_fns import average_weather

METRIC_LIST = list(['precip', 'tair'])
MNTH_NAMES_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

ANML_PRODN_SHEET = 'Typical animal production'   # Herrero table
REQUIRED_SHEET_NAMES = list(['N constants', 'Crop parms', 'Org Waste parms', ANML_PRODN_SHEET])
FARM_WTHR_SHEET_NAMES = {'lctn': 'Farm location', 'wthr':'Weather'}

RUN_SHT_NAMES = {'sign': 'Signature', 'lctn': 'Farm location', 'wthr': 'Weather', 'sbas': 'Subareas'}
SOIL_METRICS = list(['t_depth', 't_clay', 't_sand', 't_silt', 't_carbon', 't_bulk', 't_pH', 't_salinity'])
MNGMNT_SHT_HDRS = ['period', 'year', 'month', 'crop_name', 'yld', 'fert_type', 'fert_n', 'ow_type', 'ow_amnt', 'irrig']
T_DEPTH = 30

FNAME_RUN = 'FarmWthrMgmt.xlsx'

ERR_MESS = '*** Error *** '
ERR_MESS_SHEET = ERR_MESS + 'reading sheet\t'
WARNING_STR = '*** Warning ***\t'

from string import ascii_uppercase
ALPHABET = list(ascii_uppercase)
MAX_SUB_AREAS = 8

def _create_ow_fert(df):
    '''
'   create fertiliser and organic waste lists from series
    '''
    fert_ns = []
    for fert_type, fert_n in zip(df['fert_type'].values, df['fert_n'].values):
        if fert_type is None:
            fert_ns.append(None)
        else:
            fert_ns.append({'fert_type': fert_type, 'fert_n': fert_n})

    org_ferts = []
    for ow_type, ow_amnt in zip(df['ow_type'].values, df['ow_amnt'].values):
        if ow_type is None:
            org_ferts.append(None)
        else:
            org_ferts.append({'ow_type': ow_type, 'amount': ow_amnt})

    irrigs_tmp = list(df['irrig'].values)
    irrigs = []
    for irrig in irrigs_tmp:
        if irrig is None:
            irrigs.append(0)
        else:
            if isnan(irrig):
                irrigs.append(0)
            else:
                irrigs.append(irrig)

    return fert_ns, org_ferts, irrigs

def _add_tgdd_to_weather(tair_list):
    '''
    growing degree days indicates the cumulative temperature when plant growth is assumed to be possible (above 5Â°C)
    '''
    imnth = 1
    grow_dds = []
    for tair in tair_list:

        dummy, ndays = monthrange(2011, imnth)
        n_grow_days = max(0, ndays * (tair - 5))    #  (eq.3.2.2)
        grow_dds.append(round(n_grow_days,3))

        imnth += 1
        if imnth > 12:
            imnth = 1

    return grow_dds

def read_run_xlxs_file(run_xls_fn, crop_vars, latitude):
    '''
    check required sheets are present
     '''
    ret_var = None
    wb_obj = load_workbook(run_xls_fn, data_only=True)

    # check required sheets are present
    # =================================
    integrity_flag = True
    for rqrd_sheet in RUN_SHT_NAMES.values():
        if rqrd_sheet not in wb_obj.sheetnames:
            print('Sheet ' + rqrd_sheet + ' not present in ' + run_xls_fn)
            integrity_flag = False

    if integrity_flag:

        # Farm location - not used
        # =============
        lctn_sht = wb_obj[RUN_SHT_NAMES['lctn']]
        df = DataFrame(lctn_sht.values, columns=['Attribute', 'Values'])
        lctn_var = list(df['Values'][:])

        # Weather
        # =======
        pettmp_ss = {'precip': [], 'tair': []}
        pettmp_fwd = {'precip': [], 'tair': []}

        wthr_sht = wb_obj[RUN_SHT_NAMES['wthr']]
        df = DataFrame(wthr_sht.values, columns=['period', 'year', 'month', 'precip', 'tair'])
        for mode, precip, tair in zip(df['period'].values[1:], df['precip'].values[1:], df['tair'].values[1:]):
            if mode == 'steady state':
                pettmp_ss['precip'].append(precip)
                pettmp_ss['tair'].append(tair)
            else:
                pettmp_fwd['precip'].append(precip)
                pettmp_fwd['tair'].append(tair)

        ora_weather = ReadWeather(pettmp_ss, pettmp_fwd, latitude)

        # Subareas - read subareas lookup sheet which includes soil definition
        # ====================================================================
        sbas_sht = wb_obj[RUN_SHT_NAMES['sbas']]
        rows_generator = sbas_sht.values
        header_row = next(rows_generator)
        data_rows = [list(row) for (_, row) in zip(range(MAX_SUB_AREAS), rows_generator)]

        ora_subareas = {}
        for rec in data_rows:
            descr = rec[1]

            # if subarea description is present then make sure the corresponding subarea sheet is present
            # ===========================================================================================
            if descr is not None:
                sba = rec[0]
                if sba not in wb_obj:
                    print(WARNING_STR + 'Management sheet ' + sba + ' not in run file')
                    continue

                area_ha = rec[4]

                # soils
                # =====
                soil_defn = {}
                for val, metric in zip([T_DEPTH] + rec[5:], SOIL_METRICS):
                    if val is None:
                        print(ERR_MESS + 'Soil for subarea ' + sba + ' not defined in run file')
                        integrity_flag = False
                        break
                    soil_defn[metric] = val

                if integrity_flag:
                    # read subarea sheet
                    # ==================
                    soil_for_area = Soil(soil_defn)
                    ora_subareas[sba] = ReadMngmntSubareas(wb_obj, sba, soil_for_area, crop_vars, area_ha)
                else:
                    break

        if integrity_flag:
            ret_var = (ora_weather, ora_subareas)
        else:
            ret_var = None

    wb_obj.close()

    return ret_var

def _make_current_crop_list(crop_names):
    '''
    fill in crops for entire period
    '''
    crop_currs = copy(crop_names)
    prev_crop = crop_names[0]
    for indx, crop in enumerate(crop_names):
        if crop is None:

            # if remaining entries are all None then fill with previous crop
            # ==============================================================
            rmn_set = set(crop_names[indx:])
            if len(rmn_set) == 1:
                if list(rmn_set)[0] is None:
                    crop_currs[indx] = prev_crop

            # find next crop in future months
            # ===============================
            for crop_fwd in crop_names[indx + 1:]:
                if crop_fwd is not None:
                    crop_currs[indx] = crop_fwd
                    break
        else:
            # remember last crop
            # ==================
            prev_crop = crop

    return crop_currs

def _homologate_list(base_list, inp_list, func_name, padding_val = 0):
    '''
    check input list against base list and, if necessary adjust input list
    '''
    nelems = len(base_list)

    if len(inp_list) != nelems:
        print(WARNING_STR + 'repaired inconsistent list lengths in ' + func_name)
        ndiff = len(inp_list) - nelems
        if ndiff > 0:
            inp_list = inp_list[:nelems]
        else:
            inp_list = inp_list + abs(ndiff)*[padding_val]

    return inp_list

def _make_pi_props_tonnes(crop_names, indx_mode, crop_vars):
    '''
    accumulate growing months for each crop
    '''
    func_name = __prog__ + '\t_make_pi_props_tonnes'

    crops_ss = []
    crops_fwd = []
    pi_props = []
    pi_tonnes = []
    prev_crop = None

    indx_pi = 0
    for indx, crop in enumerate(crop_names):
        if crop is None:
            pi_tonnes.append(0)
            pi_props.append(0)
            indx_pi += 1
        elif crop != prev_crop:
            # consider contiguous perennial crops - grassland, scrubland, coffee
            # ==================================================================
            pi_tonnes += crop_vars[crop]['pi_tonnes']
            pi_props += crop_vars[crop]['pi_prop']
            indx_pi += crop_vars[crop]['t_grow']

            yield_typ = crop_vars[crop]['max_yld']      # TODO: should get yield from run file
            if indx < indx_mode:
                crops_ss.append(Crop(crop, yield_typ))
            else:
                crops_fwd.append(Crop(crop, yield_typ))

        prev_crop = crop

    # check list length consistency - should not be necessary
    # =======================================================
    pi_tonnes = _homologate_list(crop_names, pi_tonnes, func_name)
    pi_props  = _homologate_list(crop_names, pi_props, func_name)

    return pi_props, pi_tonnes, crops_ss, crops_fwd

class ReadMngmntSubareas(object, ):

    def __init__(self, wb_obj, sba, soil_for_area, crop_vars, area_ha):
        '''

        '''
        print('Reading management sheet ' + sba)

        mgmt_sht = wb_obj[sba]
        ntsteps = mgmt_sht.max_row - 1
        rows_generator = mgmt_sht.values
        header_row = next(rows_generator)
        data_rows = [list(row) for (_, row) in zip(range(ntsteps), rows_generator)]

        df = DataFrame(data_rows, columns = MNGMNT_SHT_HDRS)
        period_list = list(df['period'].values)
        try:
            indx_mode = period_list.index('forward run')
        except ValueError as err:
            print(ERR_MESS + 'bad subarea sheet ' + sba)
            return

        crop_names = list(df['crop_name'].values)

        crop_currs = _make_current_crop_list(crop_names)
        fert_n_list, org_fert_list, irrigs = _create_ow_fert(df)
        pi_props, pi_tonnes, crops_ss, crops_fwd = _make_pi_props_tonnes(crop_names, indx_mode, crop_vars)

        # TODO: crude and unpythonic
        # ==========================
        crop_mngmnt_fwd = {}
        crop_mngmnt_ss = {}

        crop_mngmnt_ss['crop_name'] = crop_names[:indx_mode]
        crop_mngmnt_ss['crop_curr'] = crop_currs[:indx_mode]
        crop_mngmnt_ss['crop_mngmnt'] = crops_ss
        crop_mngmnt_ss['fert_n'] = fert_n_list[:indx_mode]
        crop_mngmnt_ss['org_fert'] = org_fert_list[:indx_mode]
        crop_mngmnt_ss['pi_prop'] = pi_props[:indx_mode]
        crop_mngmnt_ss['pi_tonne'] = pi_tonnes[:indx_mode]
        crop_mngmnt_ss['irrig'] = irrigs[:indx_mode]

        crop_mngmnt_fwd['crop_name'] = crop_names[indx_mode:]
        crop_mngmnt_fwd['crop_curr'] = crop_currs[indx_mode:]
        crop_mngmnt_fwd['crop_mngmnt'] = crops_fwd
        crop_mngmnt_fwd['fert_n'] = fert_n_list[indx_mode:]
        crop_mngmnt_fwd['org_fert'] = org_fert_list[indx_mode:]
        crop_mngmnt_fwd['pi_prop'] = pi_props[indx_mode:]
        crop_mngmnt_fwd['pi_tonne'] = pi_tonnes[indx_mode:]
        crop_mngmnt_fwd['irrig'] = irrigs[indx_mode:]

        self.soil_for_area = soil_for_area
        self.crop_mngmnt_ss = crop_mngmnt_ss

        self.crop_mngmnt_fwd = crop_mngmnt_fwd
        self.area_ha = area_ha

class ReadWeather(object, ):

    def __init__(self, pettmp_ss, pettmp_fwd, latitude):
        '''
        read parameters from ORATOR inputs Excel file
        '''
        # generate PET from weather
        # =========================
        self.pettmp_ss = add_pet_to_weather(latitude, pettmp_ss)
        self.pettmp_fwd = add_pet_to_weather(latitude, pettmp_fwd)

        # growing degree days
        # ==================
        self.pettmp_ss['grow_dds'] = _add_tgdd_to_weather(pettmp_ss['tair'])
        self.pettmp_fwd['grow_dds'] = _add_tgdd_to_weather(pettmp_fwd['tair'])

        # average monthly precip and temp is required for spin up
        # =======================================================
        self.ave_precip_ss, self.ave_temp_ss, self.ave_pet_ss = \
                            average_weather(latitude, self.pettmp_ss['precip'], self.pettmp_ss['tair'])

        # get average annual rain and temperature of first 10 years
        # =========================================================
        nmnths = len(pettmp_ss['precip'])
        nyrs = nmnths/12
        self.ann_ave_precip_ss = sum(pettmp_ss['precip'])/nyrs
        self.ann_ave_temp_ss = sum(pettmp_ss['tair'])/nmnths

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

        salinity = soil_defn['t_salinity']
        if salinity is None:
            self.t_salinity = 0.0
        else:
            self.t_salinity = salinity

        tot_soc_meas = (10 ** 4) * (t_depth / 100) * t_bulk * (t_carbon / 100)  # tonnes/ha

        self.t_depth = t_depth
        self.t_carbon = t_carbon
        self.t_bulk = t_bulk
        self.tot_soc_meas = tot_soc_meas

class Crop(object,):
    '''

    '''
    def __init__(self, crop_name, yield_typ):
        """
        Assumptions:
        """
        self.crop_lu = crop_name
        self.yield_typ = yield_typ

def check_params_excel_file(params_xls_fn):
    '''
    validate selected Excel parameters file and disable CN model push button if not valid
    '''
    retcode = None

    if not os.path.isfile(params_xls_fn):
        print(ERR_MESS + 'Excel parameters file ' + params_xls_fn + ' must exist - check setup file')
        return None

    print('ORATOR parameters file: ' + params_xls_fn)
    try:
        wb_obj = load_workbook(params_xls_fn, data_only = True)
        sheet_names = wb_obj.sheetnames
    except (PermissionError, BadZipFile) as err:
        print(ERR_MESS + str(err))
        return retcode

    wb_obj.close()

    # all required sheets must be present
    # ===================================
    for sheet in REQUIRED_SHEET_NAMES:
        if sheet not in sheet_names:
            print(ERR_MESS + 'Required sheet ' + sheet + ' is not present - please check file')
            return retcode

    return 0

def _read_n_constants_sheet(xls_fname, sheet_name, skip_until):
    '''
    r_dry is an environmental constant
    '''

    n_parm_names = list(['atmos_n_depos', 'prop_atmos_dep_no3', 'no3_min', 'k_nitrif',
                      'n_denit_max', 'n_d50', 'prop_n2o_fc', 'prop_nitrif_gas', 'prop_nitrif_no',
                      'precip_critic', 'prop_volat', 'prop_atmos_dep_nh4', 'c_n_rat_soil', 'r_dry', 'k_c_rate'])

    data = read_excel(xls_fname, sheet_name, skiprows=range(0, skip_until), usecols=range(1,3))
    n_parms_df = data.dropna(how='all')
    n_parms = {}
    for indx, defn in enumerate(n_parm_names):
        n_parms[defn]  = n_parms_df['Value'].values[indx]

    return n_parms

def _read_crop_vars(xls_fname, sheet_name):
    '''
    read maximum rooting depths etc. for each crop from sheet A1c
    '''
    crop_parm_names = Series(list(['lu_code', 'rat_dpm_rpm', 'harv_indx', 'prop_npp_to_pi', 'max_root_dpth',
                    'max_root_dpth_orig', 'sow_mnth', 'harv_mnth', 'max_yld', 'dummy1',
                    'c_n_rat_pi', 'n_sply_min', 'n_sply_opt', 'n_respns_coef', 'fert_use_eff',
                    'dummy3', 'n_rcoef_a', 'n_rcoef_b', 'n_rcoef_c', 'n_rcoef_d', 'gdds_scle_factr','iws_scle_factr']))

    data = read_excel(xls_fname, sheet_name)
    data = data.dropna(how='all')
    try:
        crop_dframe = data.set_index(crop_parm_names)
        crop_vars = crop_dframe.to_dict()
    except ValueError as err:

        print(ERR_MESS_SHEET + sheet_name + ' ' + str(err))
        return None

    # discard unwanted entries
    # ========================
    for crop in ['Crop', 'None', 'Null']:
        del(crop_vars[crop])

    for crop_name in crop_vars:

        # clean data
        # ==========
        for var in ['harv_mnth', 'sow_mnth', 'lu_code']:
            crop_vars[crop_name][var] = int(crop_vars[crop_name][var])

        # number of months in the growing season
        # ======================================
        harv_mnth = crop_vars[crop_name]['harv_mnth']
        sow_mnth = crop_vars[crop_name]['sow_mnth']
        if sow_mnth > harv_mnth:
            harv_mnth += 12
        t_grow = harv_mnth - sow_mnth + 1
        crop_vars[crop_name]['pi_tonnes'], crop_vars[crop_name]['pi_prop'] = plant_inputs_crops_distribution(t_grow)
        crop_vars[crop_name]['t_grow'] = t_grow

    return crop_vars

def _read_organic_waste_sheet(xls_fname, sheet_name, skip_until):
    '''
    read Organic waste parameters
    added  - see (eq.2.1.12) and (eq.2.1.13)
    TODO percentages are converted to fraction
    '''
    ow_parms_names = Series(list(['c_n_rat', 'prop_nh4', 'rat_dpm_hum_ow', 'prop_iom_ow', 'pcnt_c', 'min_e_pcnt_wd',
                                  'max_e_pcnt_wd', 'ann_c_input', 'pcnt_urea']))

    data = read_excel(xls_fname, sheet_name, skiprows=range(0, skip_until))
    data = data.dropna(how='all')
    try:
        ow_dframe = data.set_index(ow_parms_names)
        all_ow_parms = ow_dframe.to_dict()
    except ValueError as err:
        print(ERR_MESS_SHEET + sheet_name + ' ' + str(err))
        all_ow_parms = None

    return all_ow_parms

def read_econ_purch_sales_sheet(xls_fname, sheet_name, skip_until):
    '''
    Read data on purchases and sales, required for econ module
    '''

    data = read_excel(xls_fname, sheet_name, skiprows=range(0, skip_until))
    purch_sales_df = DataFrame(data)

    return purch_sales_df

def read_econ_labour_sheet(xls_fname, sheet_name, skip_until):
    '''
    Read data on labour, required for econ module
    '''

    data = read_excel(xls_fname, sheet_name, skiprows=range(0, skip_until))
    labour_df = DataFrame(data)

    return labour_df

def repopulate_excel_dropdown(form, study_name):
    '''
    repopulate Excel drop-down
    '''
    out_dir = form.settings['out_dir']
    xlsx_list = glob(out_dir + '/' + study_name + '*.xlsx')
    form.w_combo17.clear()
    if len(xlsx_list) > 0:
        form.w_disp_out.setEnabled(True)
        for out_xlsx in xlsx_list:
            dummy, short_fn = os.path.split(out_xlsx)
            form.w_combo17.addItem(short_fn)
    return

class ReadStudy(object, ):

    def __init__(self, form, mgmt_dir, run_xls_fname = None, output_excel = True):
        '''
        read location sheet from ORATOR inputs Excel file
        '''
        self.output_excel = output_excel

        if run_xls_fname is None:
            run_xls_fname = os.path.normpath(os.path.join(mgmt_dir, FNAME_RUN))

        if not os.path.isfile(run_xls_fname):
            print('No run file ' + FNAME_RUN + ' in directory ' + mgmt_dir)
            return None

        # split management directory
        # ==========================
        norm_path = os.path.normpath(mgmt_dir)
        path_cmpnts = norm_path.split(os.sep)
        study_area, farm = path_cmpnts[-2:]

        # Farm location
        # =============
        ret_var = read_farm_wthr_xlxs_file(run_xls_fname, study_flag = True)
        dum, sub_distr, farm_name, latitude, longitude, area, prnct, dum = ret_var

        # check consistency
        # =================
        if farm_name != farm:
            print('Inconsistent farm names: ' + farm + '\tname in run file: ' + farm_name)

        study_desc = 'Study area: ' + study_area + '\t\tFarm: ' + farm_name
        study_desc += '\t\tLatitude: {}'.format(latitude)
        study_desc += '\tLongitude: {}'.format(longitude)
        form.w_study.setText(study_desc)

        self.study_name = farm_name
        self.latitude = latitude
        self.longitude = longitude

        '''
         base outputs directory on inputs location, check and if necessary create
        '''
        out_dir = os.path.normpath(os.path.join(mgmt_dir, 'outputs'))
        if not os.path.isdir(out_dir):
            try:
                os.mkdir(out_dir)
                print('Created output directory: ' + out_dir)
            except:
                raise Exception('*** Error *** Could not create output directory: ' + out_dir)

        form.settings['out_dir'] = out_dir
        repopulate_excel_dropdown(form, farm_name)

class ReadAfricaAnmlProdn(object, ):

    def __init__(self, xls_fname, crop_vars):
        '''
        read values from sheet C1a: Typical animal production in Africa provided Herrero et al. (2016)
        '''
        func_name =  __prog__ +  ' oratorExcelDetail __init__'

        self.retcode = None
        self.header_mappings = {'Type': 'Livestock type', 'ProdSystem': 'Livestock production system',
             'Region': 'Region', 'System': 'System', 'Milk': 'Milk', 'Meat': 'Meat',
             'FSgraze': 'Feedstock dry matter from grazing',
             'FSstovers': 'Feedstock dry matter from stovers',
             'FSoccas': 'Feedstock dry matter from occasional sources',
             'FSgrain': 'Feedstock dry matter from grain',
             'Manure': 'Manure dry matter', 'ExcreteN': 'Excreted N'}

        print('Reading Africa animal production data from sheet: ' + ANML_PRODN_SHEET)
        column_names = 	list(self.header_mappings.keys())
        data = read_excel(xls_fname, header=None, names= column_names, sheet_name=ANML_PRODN_SHEET,
                                                                        usecols=range(1,13), skiprows=range(0,13))
        africa_anml_prodn = data.dropna(how='all')
        self.africa_anml_prodn = africa_anml_prodn

        # allowable values required for validation
        # ========================================
        self.africa_anml_types = list(africa_anml_prodn['Type'].unique()) + list(['Pigs','Poultry'])
        self.africa_prodn_systms = list(africa_anml_prodn['ProdSystem'].unique())
        self.africa_regions = list(africa_anml_prodn['Region'].unique())
        self.africa_systems = list(africa_anml_prodn['System'].unique())
        self.crop_names = list(crop_vars.keys())

        self.retcode = 0

def read_subarea_sheet(wthr_xls, sba_indx, nyrs_rota, mngmnt_hdrs):
    '''
    read first rotation period of management sheet
    '''
    df = None
    data_rows = None

    nmnths = 12*nyrs_rota
    wb_obj = load_workbook(wthr_xls, data_only=True)
    if sba_indx in wb_obj.sheetnames:
        sba_sht = wb_obj[sba_indx]
        rows_generator = sba_sht.values
        header_row = next(rows_generator)
        data_rows = [list(row) for (_, row) in zip(range(nmnths), rows_generator)]

        # df = DataFrame(data_rows, columns=mngmnt_hdrs)

    wb_obj.close()

    if data_rows is None:
        return data_rows

    if len(data_rows[0]) < 9:
        print(ERR_MESS_SHEET + sba_indx + ' must have at least 9 values per line')
        return None

    # condition data so yield, Fert N amount, OW amount and	irrigation are mapped from None to zero
    # =============================================================================================
    data_recs = []
    for row in data_rows:
        new_row = copy(row)
        for icol in list([4, 5, 8, 9]):     # corresponds to columns E, G, I and J
            if row[icol] is None:
                new_row[icol] = '0'

        data_recs.append(new_row)

    return data_recs

def read_farm_wthr_xlxs_file(wthr_xls, study_flag = False):
    '''
    check required sheets are present
    '''
    wb_obj = load_workbook(wthr_xls, data_only=True)

    if study_flag:
        rqrd_sheet = FARM_WTHR_SHEET_NAMES['lctn']
        if rqrd_sheet in wb_obj.sheetnames:
            farm_sht = wb_obj[rqrd_sheet]
            df = DataFrame(farm_sht.values, columns=['Attribute', 'Values'])
            ret_var = list(df['Values'][:])
        else:
            print('Sheet ' + rqrd_sheet + ' not present in ' + wthr_xls)
            ret_var = None
    else:
        pettmp_ss = {'precip': [], 'tair': []}
        pettmp_fwd = {'precip': [], 'tair': []}

        wthr_sht = wb_obj['Weather']
        df = DataFrame(wthr_sht.values, columns=['period', 'year', 'month', 'precip', 'tair'])
        for mode, precip, tair in zip(df['period'].values[1:], df['precip'].values[1:], df['tair'].values[1:]):
            if mode == 'steady state':
                pettmp_ss['precip'].append(precip)
                pettmp_ss['tair'].append(tair)
            else:
                pettmp_fwd['precip'].append(precip)
                pettmp_fwd['tair'].append(tair)

        ret_var = (pettmp_ss, pettmp_fwd)

    wb_obj.close()

    return ret_var

class ReadCropOwNitrogenParms(object, ):

    def __init__(self, params_xls_fn):
        '''
        read parameters from ORATOR inputs Excel file
        '''

        print('Reading crop, organic waste and Nitrogen parameter sheets...')

        # Nitrogen params plus r_dry, drying potential
        # ============================================
        self.n_parms = _read_n_constants_sheet(params_xls_fn, 'N constants', 0)

        # Organic Waste and Crop params e.g. max rooting depths
        # =====================================================
        self.ow_parms = _read_organic_waste_sheet(params_xls_fn, 'Org Waste parms', 0)
        self.crop_vars = _read_crop_vars(params_xls_fn, 'Crop parms')
