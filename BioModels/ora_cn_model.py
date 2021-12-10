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
from PyQt5.QtWidgets import QApplication

from ora_low_level_fns import gui_summary_table_add, gui_optimisation_cycle, extend_out_dir
from ora_cn_fns import get_soil_vars, init_ss_carbon_pools, generate_miami_dyce_npp, npp_zaks_grow_season
from ora_cn_classes import MngmntSubarea, CarbonChange, NitrogenChange, EnsureContinuity, CropModel
from ora_water_model import SoilWaterChange
from ora_nitrogen_model import soil_nitrogen
from ora_excel_write import retrieve_output_xls_files, generate_excel_outfiles
from ora_excel_write_cn_water import write_excel_all_subareas
from ora_excel_read import ReadCropOwNitrogenParms, ReadStudy, read_run_xlxs_file
from ora_rothc_fns import run_rothc

# takes 83 (1e-09), 77 (1e-08) and 66 (1e-07) iterations for Gondar Single "Base line mgmt.json"
# =============================================================================================
MAX_ITERS = 200
SOC_MIN_DIFF = 0.0000001   # convergence criteria tonne/hectare

ERROR_STR = '*** Error *** '
FNAME_RUN = 'FarmWthrMgmt.xlsx'

def _cn_steady_state(form, parameters, weather, management, soil_vars, subarea):
    '''

    '''
    pettmp = weather.pettmp_ss
    generate_miami_dyce_npp(pettmp, management)

    dum, dum, dum, dum, tot_soc_meas, dum, dum, dum = get_soil_vars(soil_vars, subarea, write_flag = True)
    continuity = EnsureContinuity(tot_soc_meas)

    summary_table = gui_summary_table_add(continuity, management.pi_tonnes)
    converge_flag = False
    for iteration in range(MAX_ITERS):
        carbon_change = CarbonChange()
        soil_water = SoilWaterChange()
        nitrogen_change = NitrogenChange()

        # run RothC
        # =========
        gui_optimisation_cycle(form, subarea, iteration)

        run_rothc(parameters, pettmp, management, carbon_change, soil_vars, soil_water, continuity)
        continuity.adjust_soil_water(soil_water)

        soil_nitrogen(carbon_change, soil_water, parameters, pettmp, management, soil_vars, nitrogen_change, continuity)
        continuity.adjust_soil_n_change(nitrogen_change)

        # after steady state period has completed adjust plant inputs
        # ===========================================================
        tot_soc_simul = continuity.sum_c_pools()
        rat_meas_simul_soc = tot_soc_meas/tot_soc_simul                                     # ratio of measured vs simulated SOC
        management.pi_tonnes = [val*rat_meas_simul_soc for val in management.pi_tonnes]     # (eq.2.1.1) adjust PIs

        # check for convergence
        # =====================
        diff_abs = abs(tot_soc_meas - tot_soc_simul)
        if  diff_abs < SOC_MIN_DIFF:
            print('\nSimulated and measured SOC: {}\t*** converged *** after {} iterations'
                                                            .format(round(tot_soc_simul, 3), iteration + 1))
            gui_summary_table_add(continuity, management.pi_tonnes, summary_table)
            converge_flag = True
            break

    npp_zaks_grow_season(management)

    if not converge_flag:
        print('Simulated SOC: {}\tMeasured SOC: {}\t *** failed to converge *** after iterations: {}'
              .format(round(tot_soc_simul, 3), round(tot_soc_meas, 3), iteration + 1))

    QApplication.processEvents()    # allow event loop to update unprocessed events
    return carbon_change, nitrogen_change, soil_water, converge_flag

def _cn_forward_run(parameters, weather, management, soil_vars, carbon_change, nitrogen_change, soil_water):
    '''

    '''
    pettmp = weather.pettmp_fwd
    if management.ntsteps > len(pettmp['precip']):
        print('Cannot proceed with forward run due to insuffient weather timesteps ')
        return None

    management.pet_prev = weather.pettmp_ss['pet'][-1]    # TODO: ugly patch to ensure smooth tranistion in RothC
    generate_miami_dyce_npp(pettmp, management)

    # run RothC
    # =========
    continuity = EnsureContinuity()
    continuity.adjust_soil_water(soil_water)

    run_rothc(parameters, pettmp, management, carbon_change, soil_vars, soil_water, continuity)
    continuity.adjust_soil_water(soil_water)

    continuity.adjust_soil_n_change(nitrogen_change)
    soil_nitrogen(carbon_change, soil_water, parameters, pettmp, management, soil_vars, nitrogen_change, continuity)

    npp_zaks_grow_season(management)

    return (carbon_change, nitrogen_change, soil_water)

def run_soil_cn_algorithms(form):
    """
    retrieve weather and soil
    """
    func_name = __prog__ + '\ttest_soil_cn_algorithms'

    excel_out_flag = form.w_make_xls.isChecked()

    parms_xls_fname = form.settings['params_xls']
    print('Reading: ' + parms_xls_fname)
    ora_parms = ReadCropOwNitrogenParms(parms_xls_fname)
    if ora_parms.ow_parms is None:
        return

    mgmt_dir = form.w_lbl06.text()
    run_xls_fname = os.path.join(mgmt_dir, FNAME_RUN)
    if not os.path.isfile(run_xls_fname):
        print(ERROR_STR + 'Excel run file ' + run_xls_fname + 'must exist')
        return

    lookup_df = form.settings['lookup_df']

    # read input Excel workbook
    # =========================
    print('Reading: Run file: ' + run_xls_fname)
    study = ReadStudy(form, form.w_lbl06.text(), run_xls_fname, form.settings['out_dir'])
    retcode = read_run_xlxs_file(run_xls_fname, ora_parms.crop_vars, study.latitude)
    if retcode is None:
        return
    else:
        ora_weather, ora_subareas = retcode

    # process each subarea
    # ====================
    form.all_runs_output = {}   # clear previously recorded outputs
    all_runs = {}
    for sba in ora_subareas:

        soil_vars = ora_subareas[sba].soil_for_area

        mngmnt_ss = MngmntSubarea(ora_subareas[sba].crop_mngmnt_ss, ora_parms)

        carbon_change, nitrogen_change, soil_water, converge_flag = \
                                        _cn_steady_state(form, ora_parms, ora_weather, mngmnt_ss, soil_vars, sba)
        if converge_flag is None:
            print('Skipping forward run for ' + sba)
            continue

        pi_tonnes = carbon_change.data['c_pi_mnth']

        mngmnt_fwd = MngmntSubarea(ora_subareas[sba].crop_mngmnt_fwd, ora_parms, pi_tonnes)
        complete_run = \
            _cn_forward_run(ora_parms, ora_weather, mngmnt_fwd, soil_vars, carbon_change, nitrogen_change, soil_water)
        if complete_run is None:
            continue

        form.all_runs_crop_model[sba] = CropModel(complete_run, mngmnt_ss, mngmnt_fwd, ora_parms.crop_vars,
                                                                                        ora_subareas[sba].area_ha)
        form.crop_run = True
        # outputs only
        # ============
        form.all_runs_output[sba] = complete_run
        if excel_out_flag:
            generate_excel_outfiles(study, sba, lookup_df, form.settings['out_dir'], ora_weather, complete_run,
                                                                                                mngmnt_ss, mngmnt_fwd)
        print()
        all_runs[sba] = complete_run

    if len(all_runs) > 0:
        if excel_out_flag:
            write_excel_all_subareas(study, form.settings['out_dir'], lookup_df, all_runs)

        # update GUI by activating the livestock and new Excel output files push buttons
        # ==============================================================================
        if len(form.settings['lvstck_files']) > 0:
            form.w_livestock.setEnabled(True)

        if study.output_excel:
            retrieve_output_xls_files(form, study.study_name)

        form.w_disp_c.setEnabled(True)
        form.w_disp_n.setEnabled(True)
        form.w_disp_w.setEnabled(True)
    else:
        form.w_disp_c.setEnabled(False)
        form.w_disp_n.setEnabled(False)
        form.w_disp_w.setEnabled(False)

    if len(form.all_runs_crop_model) > 0:
        form.w_disp_cm.setEnabled(True)
        form.w_disp_econ.setEnabled(True)
    else:
        form.w_disp_cm.setEnabled(False)
        form.w_disp_econ.setEnabled(False)

    print('\nCarbon, Nitrogen and Soil Water model run complete after {} subareas processed\n'.format(len(all_runs)))
    return
