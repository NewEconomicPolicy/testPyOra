#-------------------------------------------------------------------------------
# Name:        ora_nitrogen_model.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     06/09/2020
# Licence:     <your licence>
#
# Description:
#   Nitrogen (N) is assumed to be held in 6 pools in the soil; mineral N (nitrate and ammonium) and organic
#   N (DPM, RPM, BIO and HUM-N). The release or uptake of N by organic matter is adjusted to maintain
#   a stable C:N ratio, as described in section 3.3
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_nitrogen_model.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from ora_cn_fns import get_fert_vals_for_tstep, get_soil_vars, get_crop_vars
from ora_no3_nh4_fns import soil_nitrogen_supply, no3_nh4_crop_uptake, get_n_parameters, no3_immobilisation, no3_denitrific, \
                    no3_leaching, loss_adjustment_ratio, prop_n_opt_from_soil_n_supply, \
                    nh4_mineralisation, nh4_immobilisation, nh4_nitrification, nh4_volatilisation, n2o_lost_nitrif

def soil_nitrogen(carbon_obj, soil_water_obj, parameters, pettmp, management, soil_vars, nitrogen_change, continuity):
    '''
    The soil organic matter pools (BIO and HUM-N) are assumed to have a constant C:N ratio (8.5 after Bradbury et al., 1993)
    also default for c_n_rat_hum_prev
    '''
    no3_start, nh4_start, c_n_rat_hum_prev = continuity.get_n_change_vars()
    n_parms = parameters.n_parms
    crop_vars = parameters.crop_vars

    # determine if using Neem
    # =======================
    rate_inhibit = 1.0
    applics = [val for val in management.fert_n if val is not None]
    if len(applics) > 0:
        if applics[0]['fert_type'] == 'Neem':
            rate_inhibit = 0.5

    # initialise the zeroth timestep
    # ==============================
    no3_atmos, nh4_atmos, k_nitrif, min_no3_nh4, n_d50, c_n_rat_soil, precip_critic, prop_volat = \
                                                                                            get_n_parameters(n_parms)
    if no3_start is None:
        no3_start = no3_atmos
        nh4_start = nh4_atmos

    t_depth, dum, dum, dum, dum, prop_hum, prop_bio, prop_co2 = get_soil_vars(soil_vars)

    len_n_change = len(nitrogen_change.data['no3_end'])
    if len_n_change > 0:
        # forward run: ensure continuity with steady state
        # ================================================
        indx_prev = len_n_change - 1
        c_n_rat_dpm_prev = nitrogen_change.data['c_n_rat_dpm'][-1]
        c_n_rat_rpm_prev = nitrogen_change.data['c_n_rat_rpm'][-1]
    else:
        # steady state initialisation
        # ===========================
        indx_prev = 0
        dum, dum, dum, dum, c_n_rat_pi = get_crop_vars(management, crop_vars, indx_prev)
        c_n_rat_dpm_prev, c_n_rat_rpm_prev = 2 * [c_n_rat_pi]

    # use first value for steady state or value for previous time step for forward run
    # ================================================================================
    dum, dum, dum, dum, pool_c_dpm_prev, dum, dum, dum, pool_c_hum_prev, \
                                    dum, dum, pool_c_rpm_prev, dum, dum = carbon_obj.get_cvals_for_tstep(indx_prev)
    wc_start, dum, dum = soil_water_obj.get_wvals_for_tstep(indx_prev)

    # main temporal loop
    # ==================
    imnth = 1   # may not always be January
    for tstep in range(management.ntsteps):
        precip = pettmp['precip'][tstep]
        pet = pettmp['pet'][tstep]
        crop_name, nut_n_min, n_crop_dem, n_respns_coef, c_n_rat_pi = get_crop_vars(management, crop_vars, tstep)

        # for no3_inorg_fert see manual under Inputs of nitrate, fertiliser inputs under 2.4. Soil nitrogen
        # =================================================================================================
        nh4_ow_fert, nh4_inorg_fert, no3_inorg_fert, c_n_rat_ow, pi_tonnes = \
                                                                get_fert_vals_for_tstep(management, parameters, tstep)

        cow, rate_mod, co2_emiss, c_loss_bio, pool_c_dpm, pi_to_dpm, cow_to_dpm, c_loss_dpm, \
                            pool_c_hum, cow_to_hum, c_loss_hum, pool_c_rpm, pi_to_rpm, c_loss_rpm = \
                                                                carbon_obj.get_cvals_for_tstep(tstep + len_n_change)
        wat_soil, wc_pwp, wc_fld_cap = soil_water_obj.get_wvals_for_tstep(tstep + len_n_change)

        # equs 3.3.7 to 3.3.12
        # ====================
        soil_n_sply, n_release, n_adjust, c_n_rat_dpm, c_n_rat_rpm, c_n_rat_hum = \
            soil_nitrogen_supply(prop_hum, prop_bio, prop_co2, c_n_rat_pi, c_n_rat_ow, c_n_rat_soil,
                                    cow_to_dpm, pi_to_dpm, pool_c_dpm_prev, c_loss_dpm, c_n_rat_dpm_prev,
                                                pi_to_rpm, pool_c_rpm_prev, c_loss_rpm, c_n_rat_rpm_prev,
                                    cow_to_hum,            pool_c_hum_prev, c_loss_hum, c_n_rat_hum_prev, c_loss_bio)

        # proportion of the optimum supply of N in the soil
        # =================================================
        nut_n_fert = nh4_ow_fert + nh4_inorg_fert
        prop_n_opt = prop_n_opt_from_soil_n_supply(soil_n_sply, nut_n_fert, nut_n_min, n_crop_dem)   # (eq.3.3.1)

        # Ammonium N (kg/ha) NB required before nitrate due to nitrification
        # ==================================================================
        nh4_miner = nh4_mineralisation(soil_n_sply)
        nh4_immob = nh4_immobilisation(soil_n_sply, min_no3_nh4)

        nh4_total_inp = nh4_inorg_fert + nh4_miner + nh4_atmos
        nh4_nitrif = nh4_nitrification(nh4_total_inp, min_no3_nh4, rate_mod, k_nitrif, rate_inhibit)

        # Nitrate N (kg/ha)
        # =================
        no3_nitrif = nh4_nitrif  # nitrified ammonium is assumed to be added to the nitrate-N pool (eq.2.4.4)
        no3_total_inp = no3_atmos + no3_nitrif

        no3_avail = no3_start + no3_total_inp
        nh4_avail = nh4_start + nh4_total_inp
        n_crop_dem_adj, no3_crop_dem, nh4_crop_dem, prop_yld_opt = \
                            no3_nh4_crop_uptake(prop_n_opt, n_respns_coef, n_crop_dem, no3_avail, nh4_avail, pi_tonnes)

        # Nitrate N (kg/ha)
        # =================
        no3_immob = no3_immobilisation(soil_n_sply, nh4_immob, min_no3_nh4)
        no3_leach, wat_drain = no3_leaching(precip, wc_start, pet, wc_fld_cap, no3_start, no3_total_inp, min_no3_nh4)

        no3_denit, n_denit_max, rate_denit_no3, rate_denit_moist, rate_denit_bio, prop_n2_wat, prop_n2_no3  = \
                            no3_denitrific(imnth, t_depth, wat_soil, wc_pwp, wc_fld_cap, co2_emiss, no3_avail, n_d50)

        # crop uptake col M
        # =================
        no3_total_loss = no3_immob + no3_leach + no3_denit + no3_crop_dem
        loss_adj_rat_no3 = loss_adjustment_ratio(no3_start, no3_total_inp, no3_total_loss)
        no3_loss_adj = loss_adj_rat_no3 * no3_total_loss

        no3_denit_adj = no3_denit * loss_adj_rat_no3
        n2o_emiss_denit = (1.0 - (prop_n2_wat * prop_n2_no3)) * no3_denit_adj  # (eq.2.4.13)

        no3_end = no3_start + no3_total_inp - no3_loss_adj
        no3_leach_adj = no3_leach * no3_loss_adj   # A2c - Nitrate-N lost by leaching (kg ha-1)

        # back to Ammonium N
        # ==================
        nh4_volat = nh4_volatilisation(precip, nh4_ow_fert, nh4_inorg_fert, precip_critic, prop_volat)
        nh4_total_loss = nh4_immob + nh4_nitrif + nh4_volat + nh4_crop_dem
        loss_adj_rat_nh4 = loss_adjustment_ratio(nh4_start, nh4_total_inp, nh4_total_loss)
        nh4_loss_adj = loss_adj_rat_nh4 * nh4_total_loss
        nh4_end = nh4_start + nh4_total_inp - nh4_loss_adj
        nh4_volat_adj = nh4_volat * loss_adj_rat_nh4  # A2e - Volatilised N loss
        n2o_emiss_nitrif = n2o_lost_nitrif(nh4_nitrif, wat_soil, wc_fld_cap, n_parms)

        nitrogen_change.append_vars(imnth, crop_name, min_no3_nh4, soil_n_sply, prop_yld_opt, prop_n_opt,
                    no3_start, no3_atmos, no3_inorg_fert, no3_nitrif,
                    no3_avail, no3_total_inp, no3_immob, no3_leach, no3_leach_adj,
                    no3_denit, rate_denit_no3, n_denit_max, rate_denit_moist, rate_denit_bio,
                    no3_denit_adj, n2o_emiss_nitrif, prop_n2_no3, prop_n2_wat,
                    no3_crop_dem, no3_total_loss, no3_loss_adj, loss_adj_rat_no3, no3_end, n2o_emiss_denit,
                    nh4_start, nh4_ow_fert, nh4_inorg_fert, nh4_miner, nh4_atmos, nh4_avail, nh4_total_inp,
                                    nh4_immob, nh4_nitrif,
                    nh4_volat, nh4_volat_adj, nh4_crop_dem, nh4_loss_adj, loss_adj_rat_nh4, nh4_total_loss, nh4_end,
                                n_crop_dem, n_crop_dem_adj, n_release, n_adjust, c_n_rat_dpm, c_n_rat_rpm, c_n_rat_hum)

        pool_c_dpm_prev = pool_c_dpm
        pool_c_rpm_prev = pool_c_rpm
        pool_c_hum_prev = pool_c_hum
        c_n_rat_dpm_prev = c_n_rat_dpm
        c_n_rat_rpm_prev = c_n_rat_rpm
        c_n_rat_hum_prev = c_n_rat_hum

        wc_start = wat_soil
        no3_start = no3_end
        nh4_start = nh4_end
        
        imnth += 1
        if imnth > 12:
            imnth = 1

    return
