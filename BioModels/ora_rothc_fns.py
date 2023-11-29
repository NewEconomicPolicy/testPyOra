# -------------------------------------------------------------------------------
# Name:        ora_rothc_fns.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     13/04/2017
# Licence:     <your licence>
##
# -------------------------------------------------------------------------------

__prog__ = 'ora_rothc_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from ora_water_model import get_soil_water, get_soil_water_constants
from ora_cn_fns import (get_rate_temp, inert_organic_carbon, carbon_lost_from_pool, add_npp_zaks_by_month,
                                                                            get_values_for_tstep, get_soil_vars)

K_DPM = 10/12; K_RPM = 0.3/12; K_BIO = 0.66/12; K_HUM = 0.02/12  # rate constants for decomposition of the pool per month

def run_rothc(parameters, pettmp, management, carbon_change, soil_vars, soil_water, continuity, npp_model=None):
    """
    C
    """

    # retrieve water content, stress index and C pool values for initial and first time step
    # ======================================================================================
    wc_t0, dummy, pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom = continuity.get_rothc_vars()
    t_depth, dum, t_pH_h2o, t_salinity, dum, prop_hum, prop_bio, prop_co2 = get_soil_vars(soil_vars)

    if len(carbon_change.data['pool_c_dpm']) == 0:
        c_input_bio, c_input_hum, c_loss_dpm, c_loss_rpm, c_loss_hum, c_loss_bio = 6*[0]
        tot_soc = soil_vars.tot_soc_meas     # use measured SOC initially for get_soil_water_constants
    else:
        # retrieve values from previous time step
        # =======================================
        vals_prev = carbon_change.get_last_tstep_pools()
        pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, \
            c_input_bio, c_input_hum, c_loss_dpm, c_loss_rpm, c_loss_hum, c_loss_bio, tot_soc = vals_prev

    ntsteps = management.ntsteps
    imnth = 1
    for tstep in range(ntsteps):

        vals_for_tstep = get_values_for_tstep(pettmp, management, parameters, t_depth, tstep)
        tair, precip, pet_prev, pet, irrig, c_pi_mnth, c_n_rat_ow, rat_dpm_rpm, cow, rat_dpm_hum_ow, prop_iom_ow, \
                                                                                max_root_dpth, t_grow = vals_for_tstep

        wc_fld_cap, wc_pwp, pcnt_c = get_soil_water_constants(soil_vars, parameters.n_parms, tot_soc)

        wc_t1 = get_soil_water(precip, pet, irrig, wc_fld_cap, wc_pwp, wc_t0)   # Zaks (2)

        soil_water.append_wvars(imnth, max_root_dpth, pcnt_c, precip, pet_prev, pet,
                                                                irrig, wc_pwp, wc_t1, wc_fld_cap) # Zaks (3) and (4)

        add_npp_zaks_by_month(management, pettmp, soil_water, tstep)       # add npp by Zaks to management

        # plant inputs and losses (t ha-1) passed to the DPM pool
        # =======================================================
        rate_mod = get_rate_temp(tair, t_pH_h2o, t_salinity, wc_fld_cap, wc_pwp, wc_t1)
        pi_to_dpm = c_pi_mnth * rat_dpm_rpm/(1.0 + rat_dpm_rpm)                       # (eq.2.1.10)
        cow_to_dpm = cow * rat_dpm_hum_ow * (1.0 - prop_iom_ow)/(1 + rat_dpm_hum_ow)  # (eq.2.1.12)
        pool_c_dpm += pi_to_dpm + cow_to_dpm - c_loss_dpm
        pool_c_dpm = max(0, pool_c_dpm)

        # RPM pool
        # ========
        pi_to_rpm = c_pi_mnth * 1.0 / (1.0 + rat_dpm_rpm)   # (eq.2.1.11)
        pool_c_rpm += pi_to_rpm - c_loss_rpm

        # BIO pool
        # ========
        pool_c_bio += c_input_bio - c_loss_bio

        # HUM pool
        # ========
        cow_to_hum = cow * (1 - prop_iom_ow)/(1 + rat_dpm_hum_ow)  # (eq.2.1.13)
        pool_c_hum += cow_to_hum + c_input_hum - c_loss_hum

        # IOM pool
        # ========
        cow_to_iom = inert_organic_carbon(prop_iom_ow, cow)  # add any inert carbon matter from organic waste to the soil
        pool_c_iom += cow_to_iom

        # carbon losses
        # =============
        c_loss_dpm = carbon_lost_from_pool(pool_c_dpm, K_DPM, rate_mod)
        c_loss_rpm = carbon_lost_from_pool(pool_c_rpm, K_RPM, rate_mod)
        c_loss_bio = carbon_lost_from_pool(pool_c_bio, K_BIO, rate_mod)
        c_loss_hum = carbon_lost_from_pool(pool_c_hum, K_HUM, rate_mod)
        c_loss_total = c_loss_dpm + c_loss_rpm + c_loss_hum + c_loss_bio

        c_input_bio = prop_bio * c_loss_total
        c_input_hum = prop_hum * c_loss_total
        co2_emiss = prop_co2 * c_loss_total        # co2 due to aerobic decomp - Loss as CO2 (t ha-1)

        carbon_change.append_cvars(imnth, rate_mod, c_pi_mnth, cow,
                                  pool_c_dpm, pi_to_dpm, cow_to_dpm, c_loss_dpm,
                                  pool_c_rpm, pi_to_rpm, c_loss_rpm,
                                  pool_c_bio, c_input_bio, c_loss_bio,
                                  pool_c_hum, cow_to_hum, c_input_hum, c_loss_hum,
                                  pool_c_iom, cow_to_iom, co2_emiss)

        tot_soc = pool_c_dpm + pool_c_rpm + pool_c_bio + pool_c_hum + pool_c_iom

        wc_t0 = wc_t1

        imnth += 1
        if imnth > 12:
            imnth = 1

    continuity.write_c_pools(pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom)

    return
