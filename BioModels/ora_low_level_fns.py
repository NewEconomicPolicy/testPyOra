# -------------------------------------------------------------------------------
# Name:        ora_low_level_fns.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     26/12/2019
# Licence:     <your licence>
# Description:
#
# -------------------------------------------------------------------------------

__prog__ = 'ora_low_level_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from os.path import isfile, join, isdir, normpath, split
from os import mkdir
from PyQt5.QtWidgets import QApplication
from calendar import month_abbr

from thornthwaite import thornthwaite

MNTH_NAMES_SHORT = [mnth for mnth in month_abbr[1:]]
KEYS = ['Initiation', 'Plant inputs', 'DPM carbon', 'RPM carbon', 'BIO carbon', 'HUM carbon', 'IOM carbon', 'TOTAL SOC']

ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '

def chck_weather_mngmnt(ora_weather, ora_subareas, sba):
    """
    called from fn run_soil_cn_algorithms
    """
    integrity_flag = True

    warn_str = WARN_STR + 'Subarea ' + sba + '\t'
    pettmp_fwd_nvals = len(ora_weather.pettmp_fwd['precip'])
    ntsteps_fwd = ora_subareas[sba].ntsteps_fwd
    if ntsteps_fwd > pettmp_fwd_nvals:
        integrity_flag = False
        mess = warn_str
        mess += 'Foward run weather months: {}\tmanagement months: {}'.format(pettmp_fwd_nvals, ntsteps_fwd)
        print(mess)
        QApplication.processEvents()

    pettmp_ss_nvals = len(ora_weather.pettmp_ss['precip'])
    ntsteps_ss = ora_subareas[sba].ntsteps_ss
    if ntsteps_ss > pettmp_ss_nvals:
        integrity_flag = False
        mess = warn_str
        mess += 'Steady state weather months: {}\tmanagement months: {}'.format(pettmp_ss_nvals, ntsteps_ss)
        print(mess)
        QApplication.processEvents()

    return integrity_flag

def get_crops_growing(crop_names):
    """
    C
    """
    n_crops = 0
    prev_crop = None
    grow_crops = []
    for crp_nm in crop_names:
        if crp_nm == prev_crop:
            continue
        else:
            prev_crop = crp_nm
            if crp_nm is None:
                continue
            n_crops += 1
            grow_crops.append(crp_nm)

    return grow_crops

def _dump_summary(sum_tbl):
    """
    C
    """
    wdth25 = 25
    wdth13 = 13
    line = KEYS[0].center(wdth25)
    for key in KEYS[1:]:
        line += key.rjust(wdth13)
    print(line)

    for iline in range(2):
        line = sum_tbl[KEYS[0]][iline].rjust(wdth25)
        for key in KEYS[1:]:
            line += '{:13.3f}'.format(sum_tbl[key][iline])
        print(line)

    return

def gui_summary_table_add(continuity, pi_tonnes, summary_table=None):
    """
    create or add to summary table
    """
    dum, dum, pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom = continuity.get_rothc_vars()
    totsoc = continuity.sum_c_pools()
    pi_tonnes_sum = sum(pi_tonnes)
    data_list = list([pi_tonnes_sum, pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, totsoc])

    if summary_table is None:
        val_list = ['Starting conditions'] + data_list
        summary_table = {}
        for key, val in zip(KEYS, val_list):
            summary_table[key] = [val]

        return summary_table
    else:
        val_list = ['Ending conditions'] + data_list
        for key, val in zip(KEYS, val_list):
            summary_table[key].append(val)

        _dump_summary(summary_table)

        return

def populate_org_fert(org_fert):
    """
    TODO: clumsy attempt to ensure org_fert is populated as required for calculation of C and N pools
    """
    indx_frst = 0
    frst_applic_filler = None
    applic_filler = None
    for indx, val in enumerate(org_fert):
        if val is not None:
            ow_type = val['ow_type']
            amount = 0
            applic_filler = {'ow_type': ow_type, 'amount': 0}

            # save first ow type
            # ==================
            if frst_applic_filler is None:
                indx_frst = indx
                frst_applic_filler = applic_filler
        else:
            org_fert[indx] = applic_filler

    org_fert[:indx_frst] = indx_frst * [frst_applic_filler]

    return org_fert

def average_weather(latitude, precip, tair):
    """
    return average weather
    """
    func_name = __prog__ + '\taverage_weather'

    indx_start = 0
    indx_end = len(precip)

    # use dict-comprehension to initialise precip. and tair dictionaries
    # =========================================================================
    hist_precip = {mnth: 0.0 for mnth in MNTH_NAMES_SHORT}
    hist_tmean = {mnth: 0.0 for mnth in MNTH_NAMES_SHORT}

    for indx in range(indx_start, indx_end, 12):

        for imnth, month in enumerate(MNTH_NAMES_SHORT):
            hist_precip[month] += precip[indx + imnth]
            hist_tmean[month] += tair[indx + imnth]

    # write stanza for input.txt file consisting of long term average climate
    # =======================================================================
    ave_precip = []
    ave_tmean = []
    num_years = len(precip) / 12
    for month in MNTH_NAMES_SHORT:
        ave_precip.append(hist_precip[month] / num_years)
        ave_tmean.append(hist_tmean[month] / num_years)

    year = 2001  # not a leap year
    pet = thornthwaite(ave_tmean, latitude, year)

    return ave_precip, ave_tmean, pet

def gui_optimisation_cycle(form, subarea=None, iteration=None):
    """
    Update progress bar
    """
    if subarea is None:
        mess = 'Optimisation Cycle'
    else:
        mess = 'Sub area: ' + subarea + '\t\tOptimisation Cycle:'

    if iteration is None:
        return mess
    else:
        mess += ' {:6d}'.format(iteration + 1)
        if int(iteration / 10) * 10 == iteration:
            # sys.stdout.flush()
            # sys.stdout.write('\r' + mess)
            QApplication.processEvents()

        form.w_opt_cycle.setText(mess)
    return
