#-------------------------------------------------------------------------------
# Name:        ora_low_level_fns.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     26/12/2019
# Licence:     <your licence>
# Description:
#
#-------------------------------------------------------------------------------

__prog__ = 'ora_low_level_fns.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os
import sys
from time import time
from openpyxl import load_workbook
from pandas import read_excel
from zipfile import BadZipFile

from thornthwaite import thornthwaite

MNTH_NAMES_SHORT_DIC = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10,
                                                                                                'Nov':11, 'Dec':12}
MNTH_NAMES_SHORT = MNTH_NAMES_SHORT_DIC.keys()

KEYS = ['Initiation', 'Plant inputs', 'DPM carbon', 'RPM carbon', 'BIO carbon', 'HUM carbon', 'IOM carbon', 'TOTAL SOC']

ERROR_STR = '*** Error *** '

def get_imnth(month_short_name, func_name = None):

    imonth = -1
    if month_short_name not in MNTH_NAMES_SHORT:
        print(ERROR_STR + 'Short month name : ' + month_short_name + ' must be in list of short month names: ')
    else:
        imonth = MNTH_NAMES_SHORT_DIC[month_short_name]

    return imonth

def _dump_summary(sum_tbl):

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

def summary_table_add(pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom, pi_tonnes,
                      summary_table = None):
    '''
    create or add to summary table
    =============================
    '''
    totsoc = sum([pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom])
    pi_tonnes_sum = sum(pi_tonnes)
    data_list = list([pi_tonnes_sum, pool_c_dpm, pool_c_rpm,pool_c_bio,pool_c_hum,pool_c_iom, totsoc])

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

def populate_org_fert(org_fert):
    '''
    TODO: clumsy attempt to ensure org_fert is populated as required for calculation of C and N pools
    '''

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
    '''
    return average weather
    '''
    func_name =  __prog__ + '\taverage_weather'

    indx_start = 0
    indx_end   = len(precip)

    # use dict-comprehension to initialise precip. and tair dictionaries
    # =========================================================================
    hist_precip = {mnth: 0.0 for mnth in MNTH_NAMES_SHORT}
    hist_tmean  = {mnth: 0.0 for mnth in MNTH_NAMES_SHORT}

    for indx in range(indx_start, indx_end, 12):

        for imnth, month in enumerate(MNTH_NAMES_SHORT):
            hist_precip[month] += precip[indx + imnth]
            hist_tmean[month]  += tair[indx + imnth]

    # write stanza for input.txt file consisting of long term average climate
    # =======================================================================
    ave_precip = []
    ave_tmean = []
    num_years = len(precip)/12
    for month in MNTH_NAMES_SHORT:
        ave_precip.append(hist_precip[month]/num_years)
        ave_tmean.append(hist_tmean[month]/num_years)

    year = 2001 # not a leap year
    pet = thornthwaite(ave_tmean, latitude, year)

    return  ave_precip, ave_tmean, pet

def optimisation_cycle(form, iteration = None):

    """Update progress bar."""
    mess = 'Optimisation Cycle'

    if iteration is None:
        return mess
    else:
        mess += ' {:6d}'.format(iteration)
        if int(iteration/10)*10 == iteration:
            sys.stdout.flush()
            sys.stdout.write('\r' + mess)

        form.w_opt_cycle.setText(mess)

def update_progress(last_time, iteration, tot_soc_meas, tot_soc_simul,
                                    pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom):

    """Update progress bar."""
    new_time = time()
    if new_time - last_time > 5:
        # used to be: Estimated remaining
        mess = '\rIterations completed: {:=6d} SOC meas: {:=8.3f} simul: {:=8.3f}'\
                                                        .format(iteration, tot_soc_meas, tot_soc_simul)

        mess += ' pools dpm: {:=8.3f} rpm: {:=8.3f} bio: {:=8.3f} hum: {:=8.3f} iom: {:=8.3f}'\
                                    .format(pool_c_dpm, pool_c_rpm, pool_c_bio, pool_c_hum, pool_c_iom)
        sys.stdout.flush()
        sys.stdout.write(mess)
        last_time = new_time

    return last_time


