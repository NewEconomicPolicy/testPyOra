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
# The simulation is continued for 100 years, after which time, the C in the DPM, RPM, BIO, HUM and IOM pools are
# summed and compared to the measured soil C. The soil C pools are then re-initialised with the values calculated
# after 100 years and the plant inputs, CPI, are adjusted according to the ratio of measured and simulated total soil C
#
# -------------------------------------------------------------------------------

__prog__ = 'ora_cn_model.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from os.path import isfile, join
from copy import copy, deepcopy
from numpy import arange
from PyQt5.QtWidgets import QApplication
from calendar import month_abbr

from livestock_output_data import check_livestock_run_data
from ora_low_level_fns import gui_summary_table_add, gui_optimisation_cycle
from ora_cn_fns import get_soil_vars, npp_zaks_grow_season
from ora_cn_classes import MngmntSubarea, CarbonChange, NitrogenChange, EnsureContinuity, CropProdModel
from ora_water_model import SoilWaterChange
from ora_nitrogen_model import soil_nitrogen
from ora_excel_write import retrieve_output_xls_files, generate_excel_outfiles
from ora_excel_write_cn_water import write_excel_all_subareas
from ora_excel_read import ReadCropOwNitrogenParms, ReadStudy, read_xls_run_file
from ora_rothc_fns import run_rothc
from ora_gui_misc_fns import edit_rate_inhibit

MNTH_NAMES_SHORT = [mnth for mnth in month_abbr[1:]]

NPP_MODELS = ('MIAMI', 'Zaks', 'N_lim')
# NPP_MODELS = ('Zaks')

# takes 83 (1e-09), 77 (1e-08) and 66 (1e-07) iterations for Gondar Single 'Base line mgmt.json'
# =============================================================================================
MAX_ITERS = 200
SOC_MIN_DIFF = 0.0000001  # convergence criteria tonne/hectare

WARN_STR = '*** Warning *** '
ERROR_STR = '*** Error *** '
FNAME_RUN = 'FarmWthrMgmt.xlsx'

def _cn_steady_state(form, parameters, weather, management, soil_vars, subarea):
    """

    """
    pettmp = weather.pettmp_ss
    dum, dum, dum, dum, tot_soc_meas, dum, dum, dum = get_soil_vars(soil_vars, subarea, write_flag=True)
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
        rat_meas_simul_soc = tot_soc_meas / tot_soc_simul  # ratio of measured vs simulated SOC
        management.pi_tonnes = [val * rat_meas_simul_soc for val in management.pi_tonnes]  # (eq.2.1.1) adjust PIs

        # check for convergence
        # =====================
        diff_abs = abs(tot_soc_meas - tot_soc_simul)
        if diff_abs < SOC_MIN_DIFF:
            print('\nSimulated and measured SOC: {}\t*** converged *** after {} iterations'
                  .format(round(tot_soc_simul, 3), iteration + 1))
            gui_summary_table_add(continuity, management.pi_tonnes, summary_table)
            converge_flag = True
            break

    if not converge_flag:
        print('Simulated SOC: {}\tMeasured SOC: {}\t *** failed to converge *** after iterations: {}'
              .format(round(tot_soc_simul, 3), round(tot_soc_meas, 3), iteration + 1))

    QApplication.processEvents()  # allow event loop to update unprocessed events
    return carbon_change, nitrogen_change, soil_water, converge_flag

def _cn_forward_run(parameters, weather, mngmnt_fwd, soil_vars, c_change_ss, n_change_ss, soil_water_ss, crop_model):
    """

    """
    pettmp = weather.pettmp_fwd
    if mngmnt_fwd.ntsteps > len(pettmp['precip']):
        print('Cannot proceed with forward run due to insuffient weather timesteps ')
        return None

    complete_runs = {}

    continuity = EnsureContinuity()
    continuity.adjust_soil_water(soil_water_ss)

    for npp_model in NPP_MODELS:
        c_change = deepcopy(c_change_ss)
        soil_water = deepcopy(soil_water_ss)
        n_change = deepcopy(n_change_ss)

        # run RothC
        # =========
        run_rothc(parameters, pettmp, mngmnt_fwd, c_change, soil_vars, soil_water, continuity, npp_model)
        continuity.adjust_soil_water(soil_water)

        continuity.adjust_soil_n_change(n_change)
        soil_nitrogen(c_change, soil_water, parameters, pettmp, mngmnt_fwd, soil_vars, n_change, continuity)

        complete_run = (c_change, n_change, soil_water)
        crop_model.add_management_fwd(complete_run, mngmnt_fwd, npp_model)

        complete_runs[npp_model] = complete_run

    return complete_runs

def run_soil_cn_algorithms(form):
    """
    retrieve weather and soil
    NB return code convention is 0 for success, -1 for failure
    """
    func_name = __prog__ + '\trun_soil_cn_algorithms'

    excel_out_flag = form.w_make_xls.isChecked()
    out_dir = form.settings['out_dir']

    parms_xls_fname = form.settings['params_xls']
    print('Reading: ' + parms_xls_fname)
    ora_parms = ReadCropOwNitrogenParms(parms_xls_fname)
    if ora_parms.ow_parms is None:
        return -1

    ora_parms.syn_fert_parms = edit_rate_inhibit(form.w_inhibit, ora_parms.syn_fert_parms)

    mgmt_dir = form.w_run_dir3.text()
    run_xls_fname = join(mgmt_dir, FNAME_RUN)
    if not isfile(run_xls_fname):
        print(ERROR_STR + 'Excel run file ' + run_xls_fname + 'must exist')
        return -1

    lookup_df = form.settings['lookup_df']

    # read input Excel workbook
    # =========================
    print('Reading: Run file: ' + run_xls_fname)
    study = ReadStudy(form, mgmt_dir, run_xls_fname, out_dir)
    retcode = read_xls_run_file(run_xls_fname, ora_parms.crop_vars, study.latitude)
    if retcode is None:
        return -1
    else:
        ora_weather, ora_subareas = retcode

    # process each subarea
    # ====================
    form.all_runs_output = {}  # clear previously recorded outputs
    all_runs = {}
    for sba in ora_subareas:
        crop_model = CropProdModel(ora_subareas[sba].area_ha)
        soil_vars = ora_subareas[sba].soil_for_area
        mngmnt_ss = MngmntSubarea(ora_subareas[sba].crop_mngmnt_ss, ora_weather)

        c_change, n_change, soil_water, cnvrg_flag = _cn_steady_state(form, ora_parms, ora_weather,
                                                                                            mngmnt_ss, soil_vars, sba)
        if not cnvrg_flag:
            print('Skipping forward run for ' + sba)
            continue

        crop_model.add_management_ss(n_change, mngmnt_ss)

        mngmnt_fwd = MngmntSubarea(ora_subareas[sba].crop_mngmnt_fwd, ora_weather, mngmnt_ss)  # also calculates MIAMI

        complete_runs = _cn_forward_run(ora_parms, ora_weather, mngmnt_fwd, soil_vars,
                                                c_change, n_change, soil_water, crop_model)
        complete_run = complete_runs['MIAMI']
        if complete_run is None:
            continue

        form.all_runs_crop_model[sba] = crop_model
        form.crop_run = True

        # outputs only
        # ============
        form.all_runs_output[sba] = complete_run
        if excel_out_flag:
            generate_excel_outfiles(form.lggr, study, sba, lookup_df, out_dir, ora_weather, complete_run,
                                                                                    mngmnt_ss, mngmnt_fwd)
        print()
        all_runs[sba] = complete_run

    if len(all_runs) > 0:
        if excel_out_flag:
            write_excel_all_subareas(study, out_dir, lookup_df, all_runs)

        # update GUI by activating the livestock and new Excel output files push buttons
        # ==============================================================================
        ngrps = check_livestock_run_data(form)
        if ngrps > 0:
            form.w_livestock.setEnabled(False)
        else:
            print('\nNo livestock to process')
            form.w_livestock.setEnabled(False)

        if study.output_excel:
            retrieve_output_xls_files(form, study.study_name)

        form.w_disp1_c.setEnabled(True)
        form.w_disp1_n.setEnabled(True)
        form.w_disp1_w.setEnabled(True)
        form.w_recalc.setEnabled(True)
    else:
        form.w_disp1_c.setEnabled(False)
        form.w_disp1_n.setEnabled(False)
        form.w_disp1_w.setEnabled(False)
        form.w_recalc.setEnabled(False)

    if len(form.all_runs_crop_model) > 0:
        form.w_disp_cm.setEnabled(True)
    else:
        form.w_disp_cm.setEnabled(False)

    # need these for subsequent functionality
    # =======================================
    form.ora_weather = ora_weather
    form.ora_subareas = ora_subareas

    print('\nCarbon, Nitrogen and Soil Water model run complete after {} subareas processed\n'.format(len(all_runs)))
    return 0


def _amend_crop_mngmnt(crop_mngmnt, mnth_appl, ow_type, owex_amnt):
    """
    amend crop management organic waste application
    """
    crop_mngmnt_mod = copy(crop_mngmnt)

    warn_flag = True
    org_fert_mod = []
    for imnth, ow_apl in enumerate(crop_mngmnt['org_fert']):
        mnth = MNTH_NAMES_SHORT[imnth % 12]
        if mnth == mnth_appl:
            if ow_apl is None:
                new_amt = owex_amnt
            else:
                new_amt = ow_apl['amount'] + owex_amnt
                if ow_type != ow_apl['ow_type']:
                    if warn_flag:
                        print(WARN_STR + 'changing organic waste from ' + ow_apl['ow_type'] + ' to ' + ow_type)
                        warn_flag = False

            ow_apl_new = {'ow_type': ow_type, 'amount': new_amt}
        else:
            ow_apl_new = ow_apl

        org_fert_mod.append(ow_apl_new)

    crop_mngmnt_mod['org_fert'] = org_fert_mod
    return crop_mngmnt_mod


def _abbrev_to_steady_state(carbon_change, nitrogen_change, soil_water, nmnths_ss):
    """
    abbreviate carbon, nitrogen and soil water objects to steady state only
    """
    carbon_chng = CarbonChange()
    for var_name in carbon_chng.var_name_list:
        carbon_chng.data[var_name] = carbon_change.data[var_name][:nmnths_ss]

    nitrogen_chng = NitrogenChange()
    for var_name in nitrogen_chng.var_name_list:
        nitrogen_chng.data[var_name] = nitrogen_change.data[var_name][:nmnths_ss]

    soil_h2o_chng = SoilWaterChange()
    for var_name in soil_h2o_chng.var_name_list:
        soil_h2o_chng.data[var_name] = soil_water.data[var_name][:nmnths_ss]

    return carbon_chng, nitrogen_chng, soil_h2o_chng


def recalc_fwd_soil_cn(form):
    """
    apply modified management to the forward run
    typically additional organic waste or irrigation
    """
    func_name = __prog__ + '\trecalc_fwd_soil_cn'

    ora_weather = form.ora_weather
    ora_subareas = form.ora_subareas
    all_runs_output = form.all_runs_output
    ora_parms = form.ora_parms

    ow_type = form.w_combo13.currentText()
    try:
        owex_min = float(form.w_owex_min.text())
        owex_max = float(form.w_owex_max.text())
    except ValueError as err:
        print(ERROR_STR + str(err) + ' organic waste applied must be a number')
        return None

    if (owex_max - owex_min) <= 0:
        print(ERROR_STR + ' maximum organic waste applied must exceed minimum')
        return None

    nsteps = 6
    owext_incr = (owex_max - owex_min) / nsteps

    mnth_appl = form.w_mnth_appl.currentText()

    # process each subarea
    # ====================
    all_runs_out = {}  # clear previously recorded outputs
    for sba in ora_subareas:

        nmnths_ss = len(ora_subareas[sba].crop_mngmnt_ss['fert_n'])

        all_runs_out[sba] = {}

        carbon_change, nitrogen_change, soil_water = all_runs_output[sba]
        soil_vars = ora_subareas[sba].soil_for_area
        pi_tonnes = carbon_change.data['c_pi_mnth']
        carbon_chng, nitrogen_chng, soil_h2o = _abbrev_to_steady_state(carbon_change,
                                                                       nitrogen_change, soil_water, nmnths_ss)
        for owex_amnt in arange(owex_min, owex_max, owext_incr):

            owext_str = str(round(owex_amnt, 3))
            crop_mngmnt_fwd = _amend_crop_mngmnt(ora_subareas[sba].crop_mngmnt_fwd, mnth_appl, ow_type, owex_amnt)

            mngmnt_fwd = MngmntSubarea(crop_mngmnt_fwd, ora_parms, pi_tonnes)
            complete_run = _cn_forward_run(ora_parms, ora_weather, mngmnt_fwd, soil_vars, carbon_chng,
                                           nitrogen_chng, soil_h2o)
            carbon_chng, nitrogen_chng, soil_h2o = _abbrev_to_steady_state(carbon_chng,
                                                                           nitrogen_chng, soil_h2o, nmnths_ss)
            if complete_run is None:
                continue

            # outputs only
            # ============
            all_runs_out[sba][owext_str] = complete_run

    print('\nForward run recalculation complete after {} increments processed\n'.format(nsteps))
    return all_runs_out
