"""
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
"""

__prog__ = 'ora_cn_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import sys
from math import exp, atan
from time import sleep
from PyQt5.QtWidgets import QApplication

GDDS_SCLE_FACTR = 11500
IWS_SCLE_FACTR = 2720

def add_npp_zaks_by_month(management, pettmp, soil_water, tstep):
    """
    called from fn run_rothc only
    This differs from the  calculation presented by Zaks et al. (2007) in that the net primary production was
    calculated monthly using the water stress index for the previous month.
    """
    if management.pi_props[tstep] > 0.0:
        wat_strss_indx = soil_water.data['wat_strss_indx'][tstep]
        tgdd = pettmp['grow_dds'][tstep]
        npp = (0.0396 / (1 + exp(6.33 - 1.5 * (tgdd / GDDS_SCLE_FACTR)))) * (39.58 * wat_strss_indx - 14.52)
        npp_month = IWS_SCLE_FACTR * max(0, npp)  # (eq.3.2.1)
    else:
        npp_month = 0.0

    management.npp_zaks[tstep] = npp_month

    return npp_month

def get_crop_vars(management, crop_vars, tstep):
    """
    C
    """
    crop_curr = management.crop_currs[tstep]
    crop_name = management.crop_names[tstep]
    if crop_name is None:
        n_crop_dem = 0
    else:
        t_grow = crop_vars[crop_curr]['t_grow']
        n_crop_dem = crop_vars[crop_curr]['n_sply_opt'] / t_grow  # per month - was nut_n_opt

    nut_n_min = crop_vars[crop_curr]['n_sply_min']
    n_respns_coef = crop_vars[crop_curr]['n_respns_coef']
    c_n_rat_pi = crop_vars[crop_curr]['c_n_rat_pi']

    return crop_name, nut_n_min, n_crop_dem, n_respns_coef, c_n_rat_pi

def npp_zaks_grow_season(management):
    """
    calculate npp for each growing season by summing monthly npp for that season
    """
    ntsteps = management.ntsteps
    npp_cumul = 0.0
    tgrow = 0
    for tstep, crop_name in enumerate(management.crop_names):

        # second condition covers last month of last year
        # ===============================================
        if crop_name is None or tstep == (ntsteps - 1):
            if tgrow > 0:
                # fetch npp for this growing season and backfill monthly NPPs
                # ===========================================================
                management.npp_zaks_grow.append(npp_cumul)

                tgrow = 0
                npp_cumul = 0.0
        else:
            npp_cumul += management.npp_zaks[tstep]
            tgrow += 1

    return

def _miami_dyce_growing_season(precip, tair, land_cover_type='ara'):
    """
    tair     mean annual temperature
    precip   mean total annual precipitation

    from section 3.1 Net primary production from average temperature and total rainfall during the growing season
    modification of the well-established Miami model (Leith, 1972)

    units are tonnes
    """
    nppp = 15 * (1 - exp(-0.000664 * precip))  # precipitation-limited npp
    nppt = 15 / (1 + exp(1.315 - 0.119 * tair))  # temperature-limited npp
    npp = min(nppt, nppp)  # (eq.3.1.1)

    return npp

def generate_miami_dyce_npp(pettmp, management, management_ss=None):
    """
    return list of miami dyce npp estimates based on rainfall and temperature for growing months only
    modifies management only
    """
    if management_ss is None:
        ngrow_seasons = len(management.crop_defns)
    else:
        ngrow_seasons = len(management_ss.crop_defns)

    ntsteps = management.ntsteps
    precip_cumul, tair_cumul, tgrow = 3*[0]
    strt_indx = None
    icrp = 0
    for tstep in range(ntsteps):

        # second condition covers last month of last year
        # ===============================================
        if management.pi_props[tstep] == 0 or tstep == (ntsteps - 1):
            management.npp_miami.append(0.0)
            if tgrow > 0:

                # fetch npp for this growing season and backfill monthly NPPs
                # ===========================================================
                tair_ave = tair_cumul / tgrow
                npp = _miami_dyce_growing_season(precip_cumul, tair_ave)
                management.npp_miami_grow.append(npp)
                if management_ss is None:
                    management.npp_miami_rats.append(1.0)
                else:
                    try:
                        npp_typ = management_ss.npp_miami_grow[icrp]       # fetch ss val
                    except IndexError as err:
                        management.npp_miami_rats.append(1)
                    else:
                        management.npp_miami_rats.append(npp/npp_typ)
                tgrow = 0
                precip_cumul = 0
                tair_cumul = 0
                icrp += 1
                if icrp >= ngrow_seasons:
                    icrp = 0

                strt_indx = None
        else:
            try:
                precip = pettmp['precip'][tstep]
            except IndexError as err:
                precip = 0.0
            try:
                tair = pettmp['tair'][tstep]
            except IndexError as err:
                tair = 15.0
            npp = _miami_dyce_growing_season(precip, tair)
            management.npp_miami.append(npp)

            if strt_indx is None:
                strt_indx = tstep
            precip_cumul += precip
            tair_cumul += tair
            tgrow += 1

    return

def get_soil_vars(soil_vars, subarea=None, write_flag=False):
    """
    required by nitrogen model, RothC and steady state function
    """
    t_bulk = soil_vars.t_bulk
    t_clay = soil_vars.t_clay
    t_depth = soil_vars.t_depth
    t_pH_h2o = soil_vars.t_pH_h2o
    t_salinity = soil_vars.t_salinity
    tot_soc_meas = soil_vars.tot_soc_meas

    # C lost from each pool due to aerobic decomposition is partitioned into HUM, BIO and CO2
    # =======================================================================================
    denom = 1 + 1.67 * (1.85 + 1.6 * exp(-0.0786 * t_clay))
    prop_hum = (1 / denom) / (1 + 0.85)  # (eq.2.1.7)
    prop_bio = (1 / denom) - prop_hum  # (eq.2.1.8)
    prop_co2 = 1 - prop_bio - prop_hum  # (eq.2.1.9)

    if write_flag:
        mess = 'Proportions of C lost from each pool in sub area: ' + subarea
        print(mess + '\tHUM: {}\tBIO: {}\tCO2: {}'.format(round(prop_hum, 3), round(prop_bio, 3), round(prop_co2, 3)))

    return t_depth, t_bulk, t_pH_h2o, t_salinity, tot_soc_meas, prop_hum, prop_bio, prop_co2

def init_ss_carbon_pools(tot_soc_meas):
    """
    initialise carbon pools in tonnes
    use Falloon equation for amount of C in the IOM pool (eq.2.1.15)
    """

    # initialise carbon pools
    # =======================
    pool_c_iom = 0.049 * (tot_soc_meas ** 1.139)  # Falloon
    pool_c_dpm = 1
    pool_c_rpm = 1
    pool_c_bio = 1
    pool_c_hum = 1

    return pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom


def get_fert_vals_for_tstep(management, parameters, tstep):
    """
    see manual on fertiliser inputs. Urea fertiliser (the main form of fertiliser used in
    Africa and India, decomposes on application to the soil to produce ammonium. Therefore, the
    proportion of nitrate added in the fertiliser is zero and hence the fertiliser inputs to the nitrate pool are zero
    """
    func_name = __prog__ + ' get_fert_vals_for_tstep'

    org_fert = management.org_fert[tstep]
    if org_fert is None:
        ow_type = 'Fresh waste'
        amount = 0
    else:
        ow_type = org_fert['ow_type']
        amount = org_fert['amount']

    # inorganic fertiliser
    # ====================
    inorg_fert = management.fert_n[tstep]
    if inorg_fert is None:
        nut_n_fert = 0
    else:
        nut_n_fert = inorg_fert['fert_n']

    # organic fertiliser
    # ==================
    ow_parms = parameters.ow_parms
    nh4_ow_fert = amount * ow_parms[ow_type]['pcnt_urea']

    # inputs of inorganic N fertiliser
    # ================================
    nh4_inorg_fert, no3_inorg_fert = [nut_n_fert, 0.0]  # see eq.2.4.3

    ow_parms = parameters.ow_parms
    c_n_rat_ow = ow_parms[ow_type]['c_n_rat']

    pi_tonnes = management.pi_tonnes[tstep]
    return nh4_ow_fert, nh4_inorg_fert, no3_inorg_fert, c_n_rat_ow, pi_tonnes

def get_values_for_tstep(pettmp, management, parameters, t_depth, tstep):
    """
    C
    """
    tair = pettmp['tair'][tstep]
    precip = pettmp['precip'][tstep]
    pet = pettmp['pet'][tstep]

    if tstep == 0:
        if hasattr(management, 'pet_prev'):
            pet_prev = management.pet_prev
        else:
            pet_prev = pet
    else:
        pet_prev = pettmp['pet'][tstep]

    irrig = management.irrig[tstep]
    c_pi_mnth = management.pi_tonnes[tstep]
    crop_name = management.crop_currs[tstep]
    rat_dpm_rpm = parameters.crop_vars[crop_name]['rat_dpm_rpm']
    max_root_dpth = parameters.crop_vars[crop_name]['max_root_dpth']
    t_grow = parameters.crop_vars[crop_name]['t_grow']

    ow_parms = parameters.ow_parms
    org_fert = management.org_fert[tstep]
    if org_fert is None:
        ow_type = 'Fresh waste'
        amount = 0
    else:
        ow_type = org_fert['ow_type']
        amount = org_fert['amount']

    c_n_rat_ow = ow_parms[ow_type]['c_n_rat']
    prop_iom_ow = ow_parms[ow_type]['prop_iom_ow']  # proportion of inert organic matter in added organic waste
    rat_dpm_hum_ow = ow_parms[ow_type]['rat_dpm_hum_ow']  # ratio of DPM:HUM in the active organic waste added
    cow = amount * ow_parms[ow_type]['pcnt_c']  # proportion of plant input is carbon (t ha-1)

    # PET from selected soil depth (eq.2.2.13)
    # ========================================
    dpth_soil_root_rat = t_depth / max_root_dpth
    pet_dpth = min(pet, pet * dpth_soil_root_rat)
    pet_prev_dpth = min(pet_prev, pet_prev * dpth_soil_root_rat)

    return (tair, precip, pet_prev_dpth, pet_dpth, irrig, c_pi_mnth, c_n_rat_ow, rat_dpm_rpm,
                                        cow, rat_dpm_hum_ow, prop_iom_ow, max_root_dpth, t_grow)
def get_rate_temp(tair, pH, salinity, wc_fld_cap, wc_pwp, wc_tstep):
    """
    wc_tstep: water content in this timestep
    """
    tair = max(-15, tair)
    rate_temp = 47.91 / (1.0 + exp(106.06 / (tair + 18.27)))  # (eq.2.1.3)

    rate_moisture = min(1.0, 1.0 - (0.8 * (wc_fld_cap - wc_tstep)) / (wc_fld_cap - wc_pwp))  # (eq.2.1.4)

    rate_ph = 0.56 + (atan(3.14 * 0.45 * (pH - 5.0))) / 3.14  # (eq.2.1.5)

    rate_salinity = exp(-0.09 * salinity)  # (eq.2.1.6)

    # rmod is the product of rate modifiers that account for changes
    # in temperature, soil moisture, acidity and salinity
    # ===================================================
    rate_mod = rate_temp * rate_moisture * rate_ph * rate_salinity

    return rate_mod

def carbon_lost_from_pool(c_in_pool, k_rate_constant, rate_mod):
    """
    C
    """
    c_loss = c_in_pool * (1.0 - exp(-k_rate_constant * rate_mod))  # (eq.2.1.2)

    return c_loss

def plant_inputs_crops_distribution(t_grow, c_pi_yr=None):
    """
    plant inputs for annual crops are distributed over the growing season between sowing and harvest using
    the equation for C inputs provided by Bradbury et al. (1993);
    """
    k_pi_c = 0.6  # constant describing the shape of the exponential curve for C input

    if t_grow < 12:

        # annual crops e.g. wheat
        # =======================
        pi_tonnes = []
        denom = 0
        for imnth in range(t_grow):
            c_pi = exp(-k_pi_c * (t_grow - imnth))  # (eq.2.1.14)
            denom += c_pi
            pi_tonnes.append(c_pi)
    else:
        # perennial crops e.g. grass
        # ==========================
        if c_pi_yr is None:
            c_pi_yr = 12
        pi_tonnes = [c_pi_yr / 12] * 12

    pi_proportions = [c_pi / sum(pi_tonnes) for c_pi in pi_tonnes]
    return pi_tonnes, pi_proportions


def inert_organic_carbon(prop_iom_ow, cow):
    """
    calculates the amount of organic waste passed to the IOM pool in this time-step (t ha-1)

    carbon in the IOM is assumed to be inert, and does not change unless organic waste containing IOM is added to the
    soil
    """
    cow_to_iom = prop_iom_ow * cow  # (eq.2.1.16)

    return cow_to_iom
