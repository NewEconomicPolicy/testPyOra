#-------------------------------------------------------------------------------
# Name:        ora_classes_excel_write.py
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

__prog__ = 'ora_classes_excel_write.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from operator import add, mul
from string import ascii_uppercase
ALPHABET = list(ascii_uppercase)

class pyoraId():
    """
    define unique program identifiers which will be used for setup and configuration files etc.
    """

    def __init__(self):

        NSUBAREAS = 8

        self.SUBAREAS = ALPHABET[:NSUBAREAS]
        self.glbl_ecsse_str = 'glbl_ecss_site_specif_'
        self.applic_str = 'glbl_ecss_site_spec_mk'

def _setup_sheet_data_dict(pettmp, var_format_dict):
    """
    all classes require sheet_data dictionary to be initiated
    """
    sheet_data = {}
    var_name_list = list(var_format_dict.keys())
    for var_name in var_name_list:
        sheet_data[var_name] = []

    sheet_data['period'] = pettmp['period']  # steady state or forward

    ntsteps = len(pettmp['tair'])
    nyears = int(ntsteps/12)

    sheet_data['month'] = nyears * [tstep + 1 for tstep in range(12)]

    sheet_data['year'] = []
    this_year = -10
    for tstep in range(ntsteps):
        if int(tstep / 12) * 12 == tstep:
            if tstep > 0:
                this_year += 1

        sheet_data['year'].append(this_year)

    exclusion_list = list(['period', 'year', 'month', 'days_month'])

    return sheet_data, var_name_list, exclusion_list

class B1CropProduction(object, ):
    """
    C
    """
    def __init__(self, pettmp, soil_water, mngmnt_ss, mngmnt_fwd):
        """
        B1      TODO: removed 'days_month': 'd' from var_format_dict - don't know why it was there
        """
        self.title = 'Crop Production'

        var_format_dict = {'period': 's',  'year':'d', 'month': 'd', 'crop_name': 's',
                        'wat_soil': '2f', 'tair': '2f', 'npp_miami':'2f', 'prodn_miami':'2f', 'yld_miami':'2f',
                        'grow_dds':'2f', 'aet':'2f', 'pet':'2f', 'npp_zaks':'2f', 'prodn_zaks':'2f', 'yld_zaks':'2f'}

        sheet_data, var_name_list, exclusion_list = _setup_sheet_data_dict(pettmp, var_format_dict)

        sheet_data['crop_name'] = mngmnt_ss.crop_names + mngmnt_fwd.crop_names
        sheet_data['aet'] = soil_water.data['aet']
        sheet_data['pet'] = pettmp['pet']

        sheet_data['wat_soil'] = soil_water.data['wat_soil']
        sheet_data['tair'] = pettmp['tair']

        sheet_data['grow_dds'] = pettmp['grow_dds']
        sheet_data['npp_miami'] = len(pettmp['period'])*[0]
        sheet_data['npp_zaks'] = mngmnt_ss.npp_zaks + mngmnt_fwd.npp_zaks

        self.sheet_data = sheet_data
        self.var_name_list = var_name_list
        self.var_formats = var_format_dict

class B1cNlimitation(object, ):

    def __init__(self, pettmp, carbon_change, nitrogen_change, soil_water, mngmnt_ss, mngmnt_fwd):
        """
        B1c
        """
        self.title = 'Nitrogen limitation'


        var_format_dict = {'period': 's',  'year':'d', 'month': 'd', 'crop_name': 's',
                           'plant_n_avail':'2f', 'nut_n_fert':'2f',   # TODO: was 'soil_n_sply':'2f', 'nut_n_fert':'2f',
                           'n_sply_scld':'2f', 'yld_scld':'2f', 'yld_scld_adj':'2f', 'yld_n_lim':'2f', 'prodn_ss':'2f' }

        sheet_data, var_name_list, exclusion_list = _setup_sheet_data_dict(pettmp, var_format_dict)

        for key_name in var_format_dict:
            if key_name in exclusion_list:
                continue

            if key_name in nitrogen_change.data:
                sheet_data[key_name] = nitrogen_change.data[key_name]

        # use operator module for clarity and reduce code
        # =======================================================================
        sheet_data['plant_n_avail'] = list(map(add, nitrogen_change.data['no3_avail'],
                                                                                    nitrogen_change.data['nh4_avail']))
        self.sheet_data = sheet_data
        self.var_name_list = var_name_list
        self.var_formats = var_format_dict

class A2fNitrification(object, ):

    def __init__(self, pettmp, nitrogen_change):
        """
        A2f
        """
        self.title = 'Nitrification'

        var_format_dict = {'period': 's',  'year':'d', 'month': 'd', 'crop_name': 's',
                           'nh4_start':'2f', 'nh4_total_inp':'2f', 'nh4_nitrif':'2f', 'nh4_nitrif_adj':'2f'}

        sheet_data, var_name_list, exclusion_list = _setup_sheet_data_dict(pettmp, var_format_dict)

        for key_name in var_format_dict:
            if key_name in exclusion_list:
                continue

            sheet_data[key_name] = nitrogen_change.data[key_name]

        self.sheet_data = sheet_data
        self.var_name_list = var_name_list
        self.var_formats = var_format_dict

class A2eVolatilisedNloss(object, ):

    def __init__(self, pettmp, nitrogen_change):
        """
        A2e
        """
        self.title = 'Volatilised N loss'

        var_format_dict = {'period': 's', 'year':'d', 'month': 'd', 'crop_name': 's', 'precip': '2f',
                           'nh4_ow_fert': '2f', 'nh4_inorg_fert': '2f', 'total_n_appld': '2f',
                           'nh4_volat': '2f', 'nh4_volat_adj': '2f'}

        sheet_data, var_name_list, exclusion_list = _setup_sheet_data_dict(pettmp, var_format_dict) # adds period, year and month

        sheet_data['precip'] = pettmp['precip']

        for key_name in var_format_dict:
            if key_name in exclusion_list:
                continue

            if key_name in nitrogen_change.data:
                sheet_data[key_name] = nitrogen_change.data[key_name]

        # use operator module for clarity and reduce code
        # =======================================================================
        sheet_data['total_n_appld'] = list(map(add, sheet_data['nh4_ow_fert'], sheet_data['nh4_inorg_fert']))
        sheet_data['nh4_volat_adj'] = list(map(mul, nitrogen_change.data['loss_adj_rat_nh4'], sheet_data['nh4_volat']))

        self.sheet_data = sheet_data
        self.var_name_list = var_name_list
        self.var_formats = var_format_dict

class A2dDenitrifiedNloss(object, ):

    def __init__(self, pettmp, carbon_change, nitrogen_change, soil_water):
        """
        A2d
        """
        self.title = 'Denitrified N loss'

        var_format_dict = {'period': 's', 'year':'d', 'month': 'd', 'crop_name': 's',
               'no3_avail': '2f', 'n_denit_max': '2f', 'rate_denit_no3': '2f',
               'wc_pwp': '2f', 'wat_soil': '2f', 'wc_fld_cap': '2f', 'rate_denit_moist': '2f',
               'co2_emiss': '2f', 'rate_denit_bio': '2f', 'no3_denit': '2f', 'no3_denit_adj': '2f',
               'prop_n2_wat': '2f', 'prop_n2_no3': '2f', 'n2o_emiss_denit': '2f'}

        sheet_data, var_name_list, exclusion_list = _setup_sheet_data_dict(pettmp, var_format_dict)

        # Hydrologically effective rainfall to depth, drainage from soil depth (mm)
        # ========================================================================
        for var_name in var_name_list:
            if var_name in exclusion_list:
                continue
            elif var_name in list(['wc_pwp', 'wat_soil', 'wc_fld_cap', 'wat_drain']):     # soil water list
                sheet_data[var_name] = soil_water.data[var_name]

            elif var_name == 'co2_emiss':
                sheet_data[var_name] = carbon_change.data[var_name]
            else:
                sheet_data[var_name] = nitrogen_change.data[var_name]

        self.sheet_data = sheet_data
        self.var_name_list = var_name_list
        self.var_formats = var_format_dict

class A2cLeachedNloss(object, ):

    def __init__(self, pettmp, soil_water, nitrogen_change):
        """
        A2c
        """
        self.title = 'Leached N loss'

        var_format_dict = {'period': 's',  'year':'d', 'month': 'd', 'crop_name': 's',
                           'wat_soil': '2f', 'wat_hydro_eff': '2f', 'no3_start': '2f',
                           'wat_drain': '2f', 'no3_leach': '2f', 'no3_leach_adj': '2f'}

        sheet_data, var_name_list, exclusion_list = _setup_sheet_data_dict(pettmp, var_format_dict)

        # Hydrologically effective rainfall to depth, drainage from soil depth (mm)
        # ========================================================================
        for var_name in list(['wat_soil', 'wat_hydro_eff', 'wat_drain']):
            sheet_data[var_name] = soil_water.data[var_name]
        
        for var_name in list(['crop_name', 'no3_start', 'no3_leach', 'no3_leach_adj']):
            sheet_data[var_name] = nitrogen_change.data[var_name]

        self.sheet_data = sheet_data
        self.var_name_list = var_name_list
        self.var_formats = var_format_dict

class A2bCropNuptake(object, ):

    def __init__(self, pettmp, nitrogen_change):
        """
        A2b
        """
        self.title = 'Crop N uptake'

        var_format_dict = {'period': 's', 'year':'d', 'month': 'd', 'crop_name': 's',
                           'prop_yld_opt': '2f', 'n_crop_dem': '2f', 'n_crop_dem_adj': '2f',
                           'prop_yld_opt_adj': '2f', 'cml_n_uptk': '2f', 'cml_n_uptk_adj': '2f'}

        sheet_data, var_name_list, exclusion_list = _setup_sheet_data_dict(pettmp, var_format_dict)

        for key_name in var_format_dict:
            if key_name in exclusion_list:
                continue

            sheet_data[key_name] = nitrogen_change.data[key_name]

        self.sheet_data = sheet_data
        self.var_name_list = var_name_list
        self.var_formats = var_format_dict

class A2aSoilNsupply(object, ):

    def __init__(self, pettmp, nitrogen_change):
        """
        A2a
        """
        self.title = 'Soil N supply'

        var_format_dict = {'period':'s', 'year':'d', 'month':'d', 'crop_name': 's',
                           'c_n_rat_dpm': '2f', 'c_n_rat_rpm': '2f', 'c_n_rat_hum': '2f',
                           'n_release': '2f', 'n_adjust': '2f','soil_n_sply': '2f'}

        sheet_data, var_name_list, exclusion_list = _setup_sheet_data_dict(pettmp, var_format_dict)

        for key_name in var_format_dict:
            if key_name in exclusion_list:
                continue
            sheet_data[key_name] = nitrogen_change.data[key_name]

        self.sheet_data = sheet_data
        self.var_name_list = var_name_list
        self.var_formats = var_format_dict

class A2MineralN(object,):

    def __init__(self, pettmp, nitrogen_change):
        """
        A2
        """
        self.title = 'Mineral N'

        var_format_dict = {'period': 's', 'year':'d', 'month': 'd', 'crop_name': 's', 'tair': '2f',
                'no3_start':'2f', 'no3_atmos':'2f', 'no3_inorg_fert':'2f', 'no3_nitrif':'2f', 'no3_total_inp':'2f',
                'no3_immob':'2f', 'no3_leach':'2f', 'no3_denit':'2f', 'no3_crop_dem':'2f', 'no3_total_loss':'2f',
                'loss_adj_rat_no3':'2f', 'no3_end':'2f', 'nh4_start':'2f', 'nh4_atmos':'2f',
                'nh4_inorg_fert':'2f', 'nh4_miner':'2f', 'nh4_total_inp':'2f', 'nh4_immob':'2f',  'nh4_nitrif':'2f',
                'nh4_volat':'2f', 'nh4_crop_dem':'2f', 'nh4_total_loss':'2f', 'loss_adj_rat_nh4':'2f', 'nh4_end':'2f'}

        sheet_data, var_name_list, exclusion_list = _setup_sheet_data_dict(pettmp, var_format_dict)

        for key_name in var_format_dict:
            if key_name in exclusion_list + list(['tair']):
                continue

            sheet_data[key_name] = nitrogen_change.data[key_name]

        sheet_data['tair'] = pettmp['tair']
        self.sheet_data = sheet_data
        self.var_name_list = var_name_list
        self.var_formats = var_format_dict

class A3SoilWater(object, ):

    def __init__(self, pettmp, nitrogen_change, soil_water):
        """
        Columns refer to sheet A3
        """
        self.title = 'Soil water'
        var_format_dict = {'period': 's', 'year':'d', 'month': 'd', 'crop_name': 's',        # cols C, D, E
                        'pet': '2f', 'pcnt_c': '2f',  'max_root_dpth': '2f',                 # cols F, G, H
                        'wc_pwp': '2f', 'wc_fld_cap': '2f', 'wat_soil_no_irri': '2f',        # cols I, J, K
                        'aet_no_irri': '2f', 'irrig': '2f', 'wat_soil': '2f', 'aet': '2f',   # cols L, M, N, 0
                             'wat_drain': '2f',  'wat_strss_indx': '2f'}         # TODO: cols P, Q

        sheet_data, var_name_list, exclusion_list = _setup_sheet_data_dict(pettmp, var_format_dict)

        for key_name in var_format_dict:
            if key_name in exclusion_list + list(['crop_name', 'pet']):
                continue

            sheet_data[key_name] = soil_water.data[key_name]

        sheet_data['crop_name'] = nitrogen_change.data['crop_name']
        sheet_data['pet'] = pettmp['pet']

        self.sheet_data = sheet_data
        self.var_name_list = var_name_list
        self.var_formats = var_format_dict

class A1SomChange(object, ):

    def __init__(self, pettmp, carbon_obj, soil_water, mngmnt_ss, mngmnt_fwd):
        """
        A1. Change in soil organic matter
        """
        self.title = 'SOM_change'
        # 'crop_name': 's',
        var_format_dict = {'period':'s', 'year':'d', 'month':'d', 'crop_name': 's', 'tair':'2f',
                   'wat_soil':'2f', 'rate_mod':'2f', 'c_pi_mnth':'2f', 'cow':'2f',
                   'pool_c_dpm':'2f', 'c_input_dpm':'2f', 'c_loss_dpm':'2f',
                   'pool_c_rpm':'2f', 'pi_to_rpm':'2f', 'c_loss_rpm':'2f',
                   'pool_c_bio':'2f', 'c_input_bio':'2f', 'c_loss_bio':'2f',
                   'pool_c_hum':'2f', 'cow_to_hum':'2f', 'c_input_hum':'2f', 'c_loss_hum':'2f',
                   'pool_c_iom':'2f', 'cow_to_iom':'2f', 'tot_soc_simul':'2f', 'co2_emiss':'2f'}

        sheet_data, var_name_list, exclusion_list = _setup_sheet_data_dict(pettmp, var_format_dict)

        for key_name in var_format_dict:
            if key_name in exclusion_list + list(['tair', 'wat_soil', 'c_input_dpm', 'crop_name']):
                continue

            sheet_data[key_name] = carbon_obj.data[key_name]

        # extra columns
        # =============
        sheet_data['crop_name'] = mngmnt_ss.crop_names + mngmnt_fwd.crop_names
        sheet_data['wat_soil'] = soil_water.data['wat_soil']  # col F
        sheet_data['tair'] = pettmp['tair']

        sheet_data['c_input_dpm'] = list(map(add, carbon_obj.data['pi_to_dpm'],carbon_obj.data['cow_to_dpm']))

        self.sheet_data = sheet_data
        self.var_name_list = var_name_list
        self.var_formats = var_format_dict
