# -------------------------------------------------------------------------------
# Name:        ora_cn_model.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     13/04/2017
# Licence:     <your licence>
#
#   The simulation starts using default SOC pools and plant inputs
#    The SOC pools can have any value as the steady state simulation will adjust the pool sizes according to the measured SOC
#    The value of the total annual plant inputs will also be determined by the steady state simulation, but the
#    distribution of the plant inputs should follow the cropping patterns observed in the field#
#
#    The simulation is continued for 100 years, after which time, the C in the DPM, RPM, BIO, HUM and IOM pools are summed and
#    compared to the measured soil C. The soil C pools are then re-initialised with the values
#    calculated after 100 years and the plant inputs, CPI, are adjusted according to the ratio of measured and simulated total soil C
#
# -------------------------------------------------------------------------------
# !/usr/bin/env python

__prog__ = 'ora_cn_model.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os

from ora_low_level_fns import summary_table_add, optimisation_cycle
from ora_cn_fns import get_soil_vars, init_ss_carbon_pools, generate_miami_dyce_npp
from ora_cn_classes import MngmntSubarea, CarbonChange, NitrogenChange
from ora_water_model import SoilWaterChange, fix_soil_water
from ora_nitrogen_model import soil_nitrogen
from ora_excel_write import retrieve_output_xls_files, generate_excel_outfiles, extend_out_dir
from ora_excel_write_cn_water import write_excel_all_subareas
from ora_excel_read import ReadCropOwNitrogenParms, ReadInputSubareas, ReadStudy, ReadWeather
from ora_json_read import ReadJsonSubareas
from ora_rothc_fns import run_rothc

MAX_ITERS = 1000
SOC_MIN_DIFF = 0.0000001  # convergence criteria tonne/hectare

def _cn_steady_state(form, parameters, weather, management, soil_vars, subarea):
    '''

    '''
    pettmp = weather.pettmp_ss
    annual_miami_npps = generate_miami_dyce_npp(pettmp, management)

    t_depth, t_bulk, t_pH_h2o, t_salinity, tot_soc_meas, prop_hum, prop_bio, prop_co2 = get_soil_vars(soil_vars)
    pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom = init_ss_carbon_pools(tot_soc_meas)

    summary_table = summary_table_add(pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, management.pi_tonnes)

    converge_flag = False
    for iteration in range(MAX_ITERS):
        carbon_change = CarbonChange()
        soil_water = SoilWaterChange()
        nitrogen_change = NitrogenChange()

        # run RothC
        # =========
        optimisation_cycle(form, iteration)
        pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom = \
                        run_rothc(parameters, pettmp, management, carbon_change, soil_vars, soil_water,
                                  pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom)
        fix_soil_water(soil_water)  # make sure data metrics have same length
        nitrogen_change = soil_nitrogen(carbon_change, soil_water, parameters, pettmp,
                                                                                management, soil_vars, nitrogen_change)

        # after steady state period has completed adjust plant inputs
        # ===========================================================
        tot_soc_simul = pool_c_dpm + pool_c_rpm + pool_c_bio + pool_c_hum + pool_c_iom      # sum carbon pools
        rat_meas_simul_soc = tot_soc_meas/tot_soc_simul                                     # ratio of measured vs simulated SOC
        management.pi_tonnes = [val*rat_meas_simul_soc for val in management.pi_tonnes]     # (eq.2.1.1) adjust PIs

        # check for convergence
        # =====================
        diff_abs = abs(tot_soc_meas - tot_soc_simul)
        if  diff_abs < SOC_MIN_DIFF:
            print('\nSub area: {}\t\tsimulated and measured SOC: {}\t*** converged *** after {} iterations'
                                                            .format(subarea, round(tot_soc_simul, 3), iteration + 1))
            summary_table_add(pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom,
                                                                                management.pi_tonnes, summary_table)
            converge_flag = True
            break

    if not converge_flag:
        carbon_change, nitrogen_change, soil_water = 3*[None]
        print('Simulated SOC: {}\tMeasured SOC: {}\t *** failed to converge *** after iterations: {}'
              .format(round(tot_soc_simul, 3), tot_soc_meas, iteration + 1))

    return carbon_change, nitrogen_change, soil_water

def _cn_forward_run(parameters, weather, management, soil_vars, carbon_change, nitrogen_change, soil_water):
    '''

    '''
    pettmp = weather.pettmp_fwd
    annual_miami_npps = generate_miami_dyce_npp(pettmp, management)

    pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, \
                                    c_input_bio, c_input_hum, c_loss_dpm, c_loss_rpm, c_loss_hum, c_loss_bio \
                                                                                = carbon_change.get_last_tstep_pools()
    # run RothC
    # =========
    pools_set = run_rothc(parameters, pettmp, management, carbon_change, soil_vars, soil_water,
                                                            pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom)

    nitrogen_change = soil_nitrogen(carbon_change, soil_water, parameters, pettmp, management,
                                                                                        soil_vars, nitrogen_change)
    return (carbon_change, nitrogen_change, soil_water)

def run_soil_cn_algorithms(form):
    """
    retrieve weather and soil
    """
    func_name = __prog__ + '\ttest_soil_cn_algorithms'

    excel_out_flag = form.w_make_xls.isChecked()
    use_json_flag = form.w_use_json.isChecked()
    xls_inp_fname = os.path.normpath(form.w_lbl13.text())
    if not os.path.isfile(xls_inp_fname):
        print('Excel input file ' + xls_inp_fname + 'must exist')
        return

    # read input Excel workbook
    # =========================
    print('Loading: ' + xls_inp_fname)
    study = ReadStudy(xls_inp_fname, form.settings['out_dir'])
    ora_parms = ReadCropOwNitrogenParms(xls_inp_fname)
    if ora_parms.ow_parms is None:
        return
    ora_weather = ReadWeather(xls_inp_fname, study.latitude)
    if use_json_flag:
        ora_subareas = ReadJsonSubareas(form.settings['mgmt_files'], ora_parms.crop_vars)
        extend_out_dir(form)     # extend outputs directory by mirroring inputs location
    else:
        ora_subareas = ReadInputSubareas(xls_inp_fname, ora_parms.crop_vars)

    lookup_df = form.settings['lookup_df']

    # process each subarea
    # ====================
    form.all_runs_output = {}   # clear previously recorded outputs
    all_runs = {}
    for subarea in ora_subareas.soil_all_areas:

        soil_vars = ora_subareas.soil_all_areas[subarea]

        mngmnt_ss = MngmntSubarea(ora_subareas.crop_mngmnt_ss[subarea], ora_parms)

        carbon_change, nitrogen_change, soil_water = \
                                        _cn_steady_state(form, ora_parms, ora_weather, mngmnt_ss, soil_vars, subarea)
        if carbon_change is None:
            print('Skipping forward run for ' + subarea)
            continue

        pi_tonnes = carbon_change.data['c_pi_mnth']

        mngmnt_fwd = MngmntSubarea(ora_subareas.crop_mngmnt_fwd[subarea], ora_parms, pi_tonnes)
        complete_run = \
            _cn_forward_run(ora_parms, ora_weather, mngmnt_fwd, soil_vars, carbon_change, nitrogen_change, soil_water)

        # outputs only
        # ============
        form.all_runs_output[subarea] = complete_run
        if excel_out_flag:
            generate_excel_outfiles(study, subarea, lookup_df, form.settings['out_dir'], ora_weather, complete_run,
                                                                                                mngmnt_ss, mngmnt_fwd)

        print()
        all_runs[subarea] = complete_run

    if len(all_runs) > 0:
        if excel_out_flag:
            write_excel_all_subareas(study, form.settings['out_dir'], ora_weather, all_runs)

        # update GUI with new Excel output files
        # ======================================
        if study.output_excel:
            retrieve_output_xls_files(form, study.study_name)

        form.w_disp_c.setEnabled(True)
        form.w_disp_n.setEnabled(True)
        form.w_disp_w.setEnabled(True)
    else:
        form.w_disp_c.setEnabled(False)
        form.w_disp_n.setEnabled(False)
        form.w_disp_w.setEnabled(False)

    print('\nCarbon, Nitrogen and Soil Water model run complete\n')
    return
