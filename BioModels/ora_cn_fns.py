#-------------------------------------------------------------------------------
# Name:        ora_low_level_fns.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     26/12/2019
# Licence:     <your licence>
# Definitions:
#   spin_up
#
# Description:#
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_low_level_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import sys
from math import exp, atan
from time import sleep

sleepTime = 5
MNTH_NAMES_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def add_npp_zaks_by_month(management, pettmp, soil_water, tstep, t_grow):
    '''
    This differs from the  calculation presented by Zaks et al. (2007) in that the net primary production was
    calculated monthly using the water stress index for the previous month.
    '''
    frig_factor = 100/t_grow   # TODO
    if management.pi_props[tstep] > 0:
        wat_stress_index = soil_water.data['wat_stress_index'][tstep]
        tgdd = pettmp['grow_dds'][tstep]
        npp = (0.0396/(1 + exp(6.33 - 1.5*(tgdd/11500))))*(39.58*wat_stress_index - 14.52)
        npp_month = frig_factor*(27.20 * max(0, npp))    # TODO
    else:
        npp_month = 0

    management.npp_zaks[tstep] = npp_month

    return

def _miami_dyce_growing_season(precip, tair, land_cover_type='ara'):
    '''
    tair     mean annual temperature
    precip   mean total annual precipitation

    from section 3.1 Net primary production from average temperature and total rainfall during the growing season
    modification of the well-established Miami model (Leith, 1972)

    units are tonnes
    '''
    nppp = 15 * (1 - exp(-0.000664 * precip))  # precipitation-limited npp
    nppt = 15 / (1 + exp(1.315 - 0.119 * tair))  # temperature-limited npp
    npp = min(nppt, nppp)  # (eq.3.1.1)

    return npp

def generate_miami_dyce_npp(pettmp, management):
    '''
    return list of miami dyce npp estimates based on rainfall and temperature for growing months only
    '''
    ntsteps = management.ntsteps
    npp_annual = []
    npp_mnthly = []
    precip_cumul = 0
    tair_cumul = 0
    tgrow = 0
    imnth = 1
    for tstep in range(ntsteps):

        if management.pi_props[tstep] > 0:
            precip_cumul += pettmp['precip'][tstep]
            tair_cumul += pettmp['tair'][tstep]
            tgrow += 1

        imnth += 1
        if imnth > 12:
            tair_ave = tair_cumul / tgrow
            npp = _miami_dyce_growing_season(precip_cumul, tair_ave)
            npp_annual.append(npp)
            npp_mnthly.append(npp/tgrow)
            tgrow = 0
            precip_cumul = 0
            tair_cumul = 0
            imnth = 1

    # populate monthly npp
    # ====================
    imnth = 1
    iyr = 0
    for tstep in range(ntsteps):
        if management.pi_props[tstep] > 0:
            management.npp_miami[tstep] = npp_mnthly[iyr]
        else:
            management.npp_miami[tstep] = 0

        imnth += 1
        if imnth > 12:
            iyr += 1
            imnth = 1

    return npp_annual

def get_soil_vars(soil_vars):
    '''

    '''
    t_bulk = soil_vars.t_bulk
    t_clay = soil_vars.t_clay
    t_depth = soil_vars.t_depth
    t_pH_h2o = soil_vars.t_pH_h2o
    t_salinity = soil_vars.t_salinity
    tot_soc_meas = soil_vars.tot_soc_meas

    # C lost from each pool due to aerobic decomposition is partitioned into HUM, BIO and CO2
    # =======================================================================================
    denom = 1 + 1.67 * (1.85 + 1.6 * exp(-0.0786 * t_clay))
    prop_hum = (1 / denom) / (1 + 0.85)     # (eq.2.1.7)
    prop_bio = (1 / denom) - prop_hum       # (eq.2.1.8)
    prop_co2 = 1 - prop_bio - prop_hum      # (eq.2.1.9)

    return t_depth, t_bulk, t_pH_h2o, t_salinity, tot_soc_meas, prop_hum, prop_bio, prop_co2

def init_ss_carbon_pools(tot_soc_meas):
    '''
    initialise carbon pools in tonnes
    use Falloon equation for amount of C in the IOM pool (eq.2.1.15)
    '''

    # initialise carbon pools
    # =======================
    pool_c_iom = 0.049 * (tot_soc_meas ** 1.139)    # Falloon
    pool_c_dpm = 1
    pool_c_rpm = 1
    pool_c_bio = 1
    pool_c_hum = 1

    return pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom

def get_fert_vals_for_tstep(management, parameters, tstep):
    '''
    see manual on fertiliser inputs. Urea fertiliser (the main form of fertiliser used in
    Africa and India, decomposes on application to the soil to produce ammonium. Therefore, the
    proportion of nitrate added in the fertiliser is zero and hence the fertiliser inputs to the nitrate pool are zero
    '''
    func_name = __prog__ + ' get_fert_vals_for_tstep'

    org_fert = management.org_fert[tstep]
    ow_type = org_fert['ow_type']

    # inorganic fertiliser
    # ====================
    inorg_fert = management.fert_n[tstep]
    if inorg_fert == 0:
        nut_n_fert = 0
    else:
        nut_n_fert = inorg_fert['fert_n']

    # organic fertiliser
    # ==================
    ow_parms = parameters.ow_parms
    nh4_ow_fert = org_fert['amount']*ow_parms[ow_type]['pcnt_urea']

    # TODO: greater clarity required
    nh4_inorg_fert, no3_inorg_fert = 2*[nut_n_fert]

    org_fert = management.org_fert[tstep]
    ow_type = org_fert['ow_type']

    ow_parms = parameters.ow_parms
    c_n_rat_ow = ow_parms[ow_type]['c_n_rat']

    pi_tonnes = management.pi_tonnes[tstep]
    return nh4_ow_fert, nh4_inorg_fert, no3_inorg_fert, c_n_rat_ow, pi_tonnes

def get_values_for_tstep(pettmp, management, parameters, tstep):

    func_name = __prog__ + ' get_values_for_tstep'

    try:
        tair = pettmp['tair'][tstep]
    except IndexError as err:
        print('*** Error *** ' + str(err) + ' in ' + func_name)
        sleep(sleepTime)
        sys.exit(0)

    precip = pettmp['precip'][tstep]
    pet = pettmp['pet'][tstep]

    if tstep == 0:
        pet_prev = pet
    else:
        pet_prev = pettmp['pet'][tstep - 0]

    irrig = management.irrig[tstep]
    c_pi_mnth = management.pi_tonnes[tstep]
    crop_name = management.crop_currs[tstep]
    rat_dpm_rpm = parameters.crop_vars[crop_name]['rat_dpm_rpm']
    max_root_dpth = parameters.crop_vars[crop_name]['max_root_dpth']
    t_grow = parameters.crop_vars[crop_name]['t_grow']

    org_fert = management.org_fert[tstep]
    ow_type = org_fert['ow_type']

    ow_parms = parameters.ow_parms
    c_n_rat_ow = ow_parms[ow_type]['c_n_rat']
    prop_iom_ow = ow_parms[ow_type]['prop_iom_ow']       # proportion of inert organic matter in added organic waste
    rat_dpm_hum_ow = ow_parms[ow_type]['rat_dpm_hum_ow'] # ratio of DPM:HUM in the active organic waste added
    cow = org_fert['amount']*ow_parms[ow_type]['pcnt_c']     # proportion of plant input is carbon (t ha-1)

    return tair, precip, pet_prev, pet, irrig, c_pi_mnth, c_n_rat_ow, rat_dpm_rpm, cow, rat_dpm_hum_ow, prop_iom_ow, \
                                                                                                max_root_dpth, t_grow

def get_rate_temp(tair, pH, salinity, wc_fld_cap, wc_pwp, wc_tstep):
    '''
    wc_tstep: water content in this timestep
    '''
    rate_temp = 47.91/(1.0 + exp(106.06/(tair + 18.27)))    # (eq.2.1.3)

    rate_moisture = min(1.0, 1.0 - (0.8 * (wc_fld_cap - wc_tstep))/(wc_fld_cap - wc_pwp))   # (eq.2.1.4)

    rate_ph = 0.56+(atan(3.14*0.45*(pH - 5.0)))/3.14    # (eq.2.1.5)

    rate_salinity = exp(-0.09 * salinity)    # (eq.2.1.6)

    # rmod is the product of rate modifiers that account for changes
    # in temperature, soil moisture, acidity and salinity
    # ===================================================
    rate_mod = rate_temp*rate_moisture*rate_ph*rate_salinity

    return rate_mod

def carbon_lost_from_pool(c_in_pool, k_rate_constant, rate_mod):

    c_loss = c_in_pool*(1.0 - exp(-k_rate_constant*rate_mod))    # (eq.2.1.2)

    return c_loss

def plant_inputs_crops_distribution(c_pi_yr, t_sow, t_harv, annual_flag = True):
    '''
    plant inputs for annual crops are distributed over the growing season between sowing and harvest using
    the equation for C inputs provided by Bradbury et al. (1993);
    '''
    k_pi_c = 0.6    # constant describing the shape of the exponential curve for C input

    if annual_flag:
        # annual crops - (14)
        # ==================
        c_pi_mnths = [0]*12     # initiate

        for t_mnth in range(t_sow, t_harv + 1):
            numer = exp(-k_pi_c*(t_harv - t_mnth))      # (eq.2.1.14)
            denom = 0
            for imnth in range(t_sow, t_harv + 1):
                denom += numer

            c_pi_mnths[t_mnth - 1] = c_pi_yr*(numer/denom)
    else:
        # perennial crops
        # ===============
        c_pi_mnth = c_pi_yr/12
        c_pi_mnths = [c_pi_mnth]*12

    return c_pi_mnths

def inert_organic_carbon(prop_iom_in_ow, cow):
    '''
    calculates the amount of organic waste passed to the IOM pool in this time-step (t ha-1)

    carbon in the IOM is assumed to be inert, and does not change unless organic waste containing IOM is added to the
    soil
    '''
    cow_to_iom = prop_iom_in_ow*cow   # (eq.2.1.16)

    return cow_to_iom


