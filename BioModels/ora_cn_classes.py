#-------------------------------------------------------------------------------
# Name:        ora_cn_classes.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     26/12/2019
# Licence:     <your licence>
# Definitions:
#
#
# Description:
#   classes defined: EnsureContinuity, MngmntSubarea, CarbonChange, NitrogenChange
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_cn_classes.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from math import ceil
from operator import add, mul
from ora_low_level_fns import populate_org_fert
from ora_cn_fns import init_ss_carbon_pools


def _record_values(self, indx, this_crop_name, cumul_n_uptake, cumul_n_uptake_adj):
    '''

    '''
    self.data['crop_name'].append(this_crop_name)
    self.data['cumul_n_uptake'].append(cumul_n_uptake)
    self.data['cumul_n_uptake_adj'].append(cumul_n_uptake_adj)
    yld_typ = self.data['yld_typ'][indx]
    yld_n_lim = yld_typ * (cumul_n_uptake_adj / cumul_n_uptake)  # n limited yield
    self.data['yld_n_lim'].append(yld_n_lim)

    indx += 1
    return indx

class CropModel(object, ):
    '''
    ensure continuity during equilibrium phase then between steady state and forward run
    '''
    def __init__(self, complete_run, mngmnt_ss, mngmnt_fwd):
        '''
        construct a crop model object suitable for livestock model
        '''
        self.title = 'CropModel'
        self.data = {}

        var_name_list = list(['crop_name', 'npp_zaks', 'npp_miami', 'cumul_n_uptake', 'cumul_n_uptake_adj',
                              'yld_typ', 'yld_n_lim'])
        for var_name in var_name_list:
            self.data[var_name] = []

        self.var_name_list = var_name_list

        self.data['npp_zaks'] = mngmnt_ss.npp_zaks_grow + mngmnt_fwd.npp_zaks_grow
        self.data['npp_miami'] = mngmnt_ss.npp_miami_grow + mngmnt_fwd.npp_miami_grow
        for crop_obj in (mngmnt_ss.crop_mngmnt + mngmnt_fwd.crop_mngmnt):
            self.data['yld_typ'].append(crop_obj.yield_typ)     # typical yield

        num_grow_seasons = len(self.data['npp_miami'])

        # cumulative N uptake
        # ===================
        c_change, n_change, soil_water = complete_run
        cumul_n_uptake = 0
        cumul_n_uptake_adj = 0
        this_crop_name = None
        indx = 0
        for crop_name, n_crop_dem, n_crop_dem_adj in zip(n_change.data['crop_name'],
                                                    n_change.data['n_crop_dem'], n_change.data['n_crop_dem_adj']):

            if crop_name is None:
                if cumul_n_uptake > 0:
                    indx = _record_values(self, indx, this_crop_name, cumul_n_uptake, cumul_n_uptake_adj)

                cumul_n_uptake = 0
                cumul_n_uptake_adj = 0
            else:
                this_crop_name = crop_name
                cumul_n_uptake += n_crop_dem
                cumul_n_uptake_adj += n_crop_dem_adj


        # catch situation when December is a growing month
        # ================================================
        if (len(self.data['cumul_n_uptake']) < num_grow_seasons):
            indx = _record_values(self, indx, this_crop_name, cumul_n_uptake, cumul_n_uptake_adj)


class EnsureContinuity(object, ):
    '''
    ensure continuity during equilibrium phase then between steady state and forward run
    '''
    def __init__(self, tot_soc_meas = None):
        '''

        '''
        if tot_soc_meas is None:
            self.pool_c_dpm, self.pool_c_rpm, self.pool_c_bio, self.pool_c_hum, self.pool_c_iom = 5*[None]
        else:
            self.pool_c_dpm, self.pool_c_rpm, self.pool_c_bio, self.pool_c_hum, self.pool_c_iom = \
                                                                                    init_ss_carbon_pools(tot_soc_meas)
        self.wc_t0 = None
        self.no3_start = None
        self.nh4_start = None
        self.wat_strss_indx = 1.0
        self.c_n_rat_hum_prev = 8.5

    def adjust_soil_water(self, soil_water):
        '''

        '''
        self.wc_t0 = soil_water.data['wat_soil'][-1]  # carry forward to next iteration
        self.wat_strss_indx = soil_water.data['wat_strss_indx'][-1]

    def adjust_soil_n_change(self, nitrogen_change):
        '''

        '''
        self.no3_start = nitrogen_change.data['no3_end'][-1]
        self.nh4_start = nitrogen_change.data['nh4_end'][-1]
        self.c_n_rat_hum_prev = nitrogen_change.data['c_n_rat_hum'][-1]

    def sum_c_pools(self):
        '''

        '''
        tot_soc_simul = self.pool_c_dpm + self.pool_c_rpm + self.pool_c_bio + self.pool_c_hum + self.pool_c_iom
        return tot_soc_simul

    def write_c_pools(self, pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom):
        '''

        '''
        self.pool_c_dpm = pool_c_dpm
        self.pool_c_rpm = pool_c_rpm
        self.pool_c_bio = pool_c_bio
        self.pool_c_hum = pool_c_hum
        self.pool_c_iom = pool_c_iom

    def get_rothc_vars(self):
        '''

        '''

        return self.wc_t0, self.wat_strss_indx, self.pool_c_dpm, self.pool_c_rpm, \
                                                                self.pool_c_bio, self.pool_c_hum, self.pool_c_iom

    def get_n_change_vars(self):
        '''

        '''

        return self.no3_start, self.nh4_start, self.c_n_rat_hum_prev

class MngmntSubarea(object, ):
    '''

    '''
    def __init__(self, crop_mngmnt, ora_parms, pi_tonnes_ss = None):
        """
        determine temporal extent of the management
        should list indices correspond to the months?
        """
        self.crop_mngmnt = crop_mngmnt

        last_crop = crop_mngmnt[-1]

        nyears = ceil(last_crop.harvest_mnth/12)
        ntsteps = nyears * 12
        np1 = ntsteps + 1
        irrig = np1*[0]
        org_fert = np1*[None]
        fert_n_list = np1*[0]
        pi_prop_list = np1*[0]     # plant input proportions
        pi_tonnes_list = np1*[0]   # plant input - will be overwritten
        crop_names = np1 * [None]
        crop_currs = np1 * [None]
        npp_zaks = np1 * [0]
        npp_miami = np1 * [0]

        # populate list of current crops
        # ==============================
        imnth_last = len(crop_currs)
        for crop in reversed(crop_mngmnt):
            crop_current = crop.crop_lu
            imnth_sow = crop.sowing_mnth
            crop_currs[imnth_sow:imnth_last] = [crop_current for indx in range(imnth_sow, imnth_last)]
            imnth_last = imnth_sow

        crop_currs[0:imnth_sow] = [crop_current for indx in range(0, imnth_sow)]      # make sure no gaps

        for crop in crop_mngmnt:
            crop_name = crop.crop_lu  # e.g. Maize
            pi_tonnes = ora_parms.crop_vars[crop_name]['pi_tonnes']
            pi_prop = ora_parms.crop_vars[crop_name]['pi_prop']
            sow_mnth = crop.sowing_mnth
            harv_mnth = crop.harvest_mnth

            # TODO: this does not seem Pythonic
            # =================================
            for indx, imnth in enumerate(range(sow_mnth, harv_mnth + 1)):

                crop_names[imnth] = crop_name
                pi_prop_list[imnth] = pi_prop[indx]
                pi_tonnes_list[imnth] = pi_tonnes[indx]

            for imnth in crop.irrig:
                irrig[imnth] = crop.irrig[imnth]

            org_fert[crop.ow_mnth] = {'ow_type': crop.ow_type, 'amount': crop.ow_amount}
            fert_n_list[crop.fert_mnth] = {'fert_type': crop.fert_type, 'fert_n': crop.fert_n}

        self.nyears = nyears
        self.ntsteps = ntsteps
        self.irrig = irrig[1:]
        self.crop_names = crop_names[1:]
        self.fert_n = fert_n_list[1:]

        # TODO: important for RothC calculations see function : get_values_for_tstep
        # ==========================================================================
        self.org_fert = populate_org_fert(org_fert[1:])

        if pi_tonnes_ss is None:
            self.pi_tonnes = pi_tonnes_list[1:]      # required for seeding steady state
        else:
            self.pi_tonnes = pi_tonnes_ss   # use plant inputs from steady state

        self.pi_props  = pi_prop_list[1:]
        self.crop_currs = crop_currs[1:]
        self.npp_zaks = npp_zaks[1:]
        self.npp_zaks_grow = []
        self.npp_miami = npp_miami[1:]
        self.npp_miami_grow = []

class CarbonChange(object, ):

    def __init__(self):
        """
        A1. Change in soil organic matter
        """
        self.title = 'CarbonChange'
        self.data = {}

        var_name_list = list(['imnth', 'rate_mod', 'c_pi_mnth', 'cow',
                                        'pool_c_dpm', 'pi_to_dpm', 'cow_to_dpm', 'c_loss_dpm',
                                        'pool_c_rpm', 'pi_to_rpm', 'c_loss_rpm',
                                        'pool_c_bio', 'c_input_bio', 'c_loss_bio',
                                        'pool_c_hum', 'cow_to_hum', 'c_input_hum', 'c_loss_hum',
                                        'pool_c_iom', 'cow_to_iom', 'tot_soc_simul', 'co2_emiss'])
        for var_name in var_name_list:
            self.data[var_name] = []

        self.var_name_list = var_name_list

    def get_last_tstep_pools(self):
        '''

        '''
        pool_c_dpm = self.data['pool_c_dpm'][-1]
        pool_c_rpm = self.data['pool_c_rpm'][-1]
        pool_c_hum = self.data['pool_c_hum'][-1]
        pool_c_bio = self.data['pool_c_bio'][-1]
        pool_c_iom = self.data['pool_c_iom'][-1]

        c_input_bio = self.data['c_input_bio'][-1]
        c_input_hum = self.data['c_input_hum'][-1]
        c_loss_dpm = self.data['c_loss_dpm'][-1]
        c_loss_rpm = self.data['c_loss_rpm'][-1]
        c_loss_hum = self.data['c_loss_hum'][-1]
        c_loss_bio = self.data['c_loss_bio'][-1]
        tot_soc = self.data['tot_soc_simul'][-1]

        last_tstep_vars = (pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom,
                            c_input_bio , c_input_hum, c_loss_dpm, c_loss_rpm, c_loss_hum, c_loss_bio, tot_soc)

        return last_tstep_vars

    def get_cvals_for_tstep(self, tstep):
        '''

        '''
        rate_mod = self.data['rate_mod'][tstep]
        cow = self.data['cow'][tstep]

        co2_emiss = self.data['co2_emiss'][tstep]

        c_loss_bio = self.data['c_loss_bio'][tstep]

        pool_c_dpm = self.data['pool_c_dpm'][tstep]
        pi_to_dpm = self.data['pi_to_dpm'][tstep]
        cow_to_dpm = self.data['cow_to_dpm'][tstep]
        c_loss_dpm = self.data['c_loss_dpm'][tstep]

        pool_c_rpm = self.data['pool_c_rpm'][tstep]
        pi_to_rpm = self.data['pi_to_rpm'][tstep]
        c_loss_rpm = self.data['c_loss_rpm'][tstep]

        pool_c_hum = self.data['pool_c_hum'][tstep]

        cow_to_hum = self.data['cow_to_hum'][tstep]
        c_loss_hum = self.data['c_loss_hum'][tstep]

        return cow, rate_mod, co2_emiss, \
                            c_loss_bio, pool_c_dpm, pi_to_dpm, cow_to_dpm, c_loss_dpm,  \
                            pool_c_hum, cow_to_hum, c_loss_hum, pool_c_rpm, pi_to_rpm, c_loss_rpm

    def append_vars(self, imnth, rate_mod, c_pi_mnth, cow,
                                                pool_c_dpm, pi_to_dpm, cow_to_dpm, c_loss_dpm,
                                                pool_c_rpm, pi_to_rpm, c_loss_rpm,
                                                pool_c_bio, c_input_bio, c_loss_bio,
                                                pool_c_hum, cow_to_hum, c_input_hum, c_loss_hum,
                                                pool_c_iom, cow_to_iom, co2_emiss):
        '''
        add one set of values for this timestep to each of lists
        columns refer to A1. SOM change sheet
        '''

        # rate modifier start of each month cols D, G and H
        # ==================================================
        for var in ['imnth', 'rate_mod', 'c_pi_mnth', 'cow']:
            self.data[var].append(eval(var))

        # DPM pool cols K to M
        # ====================
        for var in ['pool_c_dpm', 'cow_to_dpm', 'pi_to_dpm', 'c_loss_dpm']:
            self.data[var].append(eval(var))

        # RPM pool cols N to P
        # ====================
        for var in ['pool_c_rpm', 'pi_to_rpm', 'c_loss_rpm']:
            self.data[var].append(eval(var))

        # BIO pool cols Q to S
        # ====================
        for var in ['pool_c_bio', 'c_input_bio', 'c_loss_bio']:
            self.data[var].append(eval(var))

        # HUM pool cols K to M
        # ====================
        for var in ['pool_c_hum', 'cow_to_hum', 'c_input_hum', 'c_loss_hum']:
            self.data[var].append(eval(var))

        # IOM pool cols X to AA
        # =====================
        tot_soc_simul = pool_c_dpm + pool_c_rpm + pool_c_bio + pool_c_hum + pool_c_iom
        for var in ['pool_c_iom', 'cow_to_iom', 'tot_soc_simul', 'co2_emiss']:
            self.data[var].append(eval(var))

class NitrogenChange(object, ):
    '''

    '''
    def __init__(self):
        """
        A2. Mineral N
        """
        self.title = 'NitrogenChange'
        self.data = {}

        # Nitrate and Ammonium N (kg/ha) inputs and losses
        # ================================================
        var_name_list = list(['imnth', 'crop_name',  'soil_n_sply', 'prop_yld_opt', 'prop_n_opt',
                        'no3_start', 'no3_atmos', 'no3_inorg_fert', 'no3_nitrif', 'rate_denit_no3',
                        'no3_avail', 'no3_total_inp', 'no3_immob', 'no3_leach', 'no3_leach_adj',
                        'no3_denit_adj', 'n2o_emiss_nitrif', 'prop_n2_no3', 'prop_n2_wat',
                        'no3_denit', 'no3_crop_dem', 'n_denit_max', 'rate_denit_moist', 'rate_denit_bio',
                        'no3_total_loss', 'no3_loss_adj', 'loss_adj_rat_no3', 'no3_end',  'n2o_emiss_denit',
                        'nh4_start', 'nh4_ow_fert', 'nh4_atmos', 'nh4_inorg_fert', 'nh4_miner', 'nh4_avail',
                        'nh4_total_inp', 'nh4_immob', 'nh4_nitrif', 'nh4_nitrif_adj', 'nh4_volat', 'nh4_volat_adj',
                        'nh4_crop_dem', 'nh4_total_loss', 'loss_adj_rat_nh4',
                        'nh4_loss_adj', 'nh4_end', 'n_crop_dem', 'n_crop_dem_adj', 'n_release', 'n_adjust',
                        'c_n_rat_dpm', 'c_n_rat_rpm', 'c_n_rat_hum',
                                        'prop_yld_opt_adj', 'cumul_n_uptake', 'cumul_n_uptake_adj', 'nut_n_fert'])

        for var_name in var_name_list:
            self.data[var_name] = []

        self.var_name_list = var_name_list

    def append_vars(self, imnth, crop_name, min_no3_nh4, soil_n_sply, prop_yld_opt, prop_n_opt,
                    no3_start, no3_atmos, no3_inorg_fert, no3_nitrif,
                    no3_avail, no3_total_inp, no3_immob, no3_leach, no3_leach_adj,
                    no3_denit, rate_denit_no3, n_denit_max, rate_denit_moist, rate_denit_bio,
                    no3_denit_adj, n2o_emiss_nitrif, prop_n2_no3, prop_n2_wat,
                    no3_crop_dem, no3_total_loss, no3_loss_adj, loss_adj_rat_no3, no3_end, n2o_emiss_denit,
                    nh4_start, nh4_ow_fert, nh4_inorg_fert, nh4_miner, nh4_atmos, nh4_avail, nh4_total_inp,
                    nh4_immob, nh4_nitrif,
                    nh4_volat, nh4_volat_adj, nh4_crop_dem, nh4_loss_adj, loss_adj_rat_nh4, nh4_total_loss, nh4_end,
                                n_crop_dem, n_crop_dem_adj, n_release, n_adjust, c_n_rat_dpm, c_n_rat_rpm, c_n_rat_hum):
        '''
        add one set of values for this timestep to each of lists
        soil_n_sply  soil N supply
        n_crop      crop N demand
        columns refer to A2. Mineral N sheet
        '''

        # Nitrate and Ammonium at start of each imnth cols D, E and Q
        # ===========================================================
        for var in ['imnth', 'crop_name', 'soil_n_sply', 'n_crop_dem', 'n_crop_dem_adj', 'prop_yld_opt', 'prop_n_opt']:
            self.data[var].append(eval(var))

        # Ammonium N (kg/ha) cols R to W
        # ==============================
        for var in ['nh4_atmos', 'nh4_inorg_fert', 'nh4_miner', 'nh4_avail', 'nh4_total_inp',
                                                                        'nh4_immob', 'nh4_nitrif', 'nh4_start']:
            self.data[var].append(eval(var))

        # Ammonium N cols X to AB
        # =======================
        for var in ['nh4_ow_fert', 'nh4_volat', 'nh4_volat_adj', 'nh4_crop_dem',
                                                                        'nh4_total_loss', 'nh4_loss_adj', 'nh4_end']:
            self.data[var].append(eval(var))

        # Nitrate N (kg/ha) cols F to L
        # =============================
        for var in ['no3_start', 'no3_atmos', 'no3_inorg_fert', 'no3_nitrif', 'no3_total_inp', 'n2o_emiss_denit',
                    'rate_denit_moist', 'rate_denit_bio', 'rate_denit_no3']:
            self.data[var].append(eval(var))

        # Nitrate N (kg/ha) cols H to L
        # =============================
        for var in [ 'no3_avail', 'no3_immob', 'no3_leach', 'no3_leach_adj', 'no3_denit', 'no3_end',
                     'no3_denit_adj', 'n2o_emiss_nitrif', 'prop_n2_no3', 'prop_n2_wat']:
            self.data[var].append(eval(var))

        # crop uptake
        # ===========
        for var in ['no3_crop_dem', 'n_denit_max', 'no3_total_loss', 'no3_loss_adj', 'loss_adj_rat_no3',
                                                                                            'loss_adj_rat_nh4']:
            self.data[var].append(eval(var))

        # crop uptake
        # ===========
        for var in ['n_release', 'n_adjust', 'c_n_rat_dpm', 'c_n_rat_rpm', 'c_n_rat_hum']:
            self.data[var].append(eval(var))

        return

    def additional_n_variables(self):
        '''
        populate additional fields from existing data
        '''

        # cumulative N uptake - sheets A2 and A2b
        # =======================================
        tmp_list = []
        cumul_n_uptake = 0
        cumul_n_uptake_adj = 0
        for crop_name, n_crop_dem, n_crop_dem_adj in zip(self.data['crop_name'], self.data['n_crop_dem'],
                                                         self.data['n_crop_dem_adj']):
            if n_crop_dem_adj > 0.0:
                tmp_list.append(n_crop_dem_adj / n_crop_dem)
            else:
                tmp_list.append(0)

            self.data['prop_yld_opt_adj'] = tmp_list  # Yield scaled wrt optimum adjusted for other losses

            if crop_name is None:
                cumul_n_uptake = 0
                cumul_n_uptake_adj = 0
            else:
                cumul_n_uptake += n_crop_dem
                cumul_n_uptake_adj += n_crop_dem_adj

            self.data['cumul_n_uptake'].append(cumul_n_uptake)
            self.data['cumul_n_uptake_adj'].append(cumul_n_uptake_adj)

        # nitrified N adjusted for other losses - sheet A2f
        # =================================================
        self.data['nh4_nitrif_adj'] = list(map(mul, self.data['nh4_nitrif'], self.data['loss_adj_rat_nh4']))
        self.data['nut_n_fert'] = list(map(add, self.data['nh4_ow_fert'], self.data['nh4_inorg_fert']))
