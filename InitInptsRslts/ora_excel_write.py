#-------------------------------------------------------------------------------
# Name:        ora_excel_write.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     26/12/2019
# Licence:     <your licence>
# Definitions:
#   spin_up
#
# Description:
#
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_excel_write.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os
from glob import glob
from pandas import DataFrame, ExcelWriter, Series
from PyQt5.QtWidgets import QApplication

from openpyxl import load_workbook
from openpyxl.chart import (LineChart, Reference)

from ora_classes_excel_write import A1SomChange, A2MineralN, A3SoilWater, A2aSoilNsupply, A2bCropNuptake, \
                A2cLeachedNloss, A2dDenitrifiedNloss, A2eVolatilisedNloss, A2fNitrification, \
                B1CropProduction, B1cNlimitation

from ora_lookup_df_fns import fetch_variable_definition

PREFERRED_LINE_WIDTH = 25000       # 100020 taken from chart_example.py     width in EMUs

from string import ascii_uppercase
ALPHABET = list(ascii_uppercase)
FIXED_WDTHS = {'A':13, 'B':6, 'C':7, 'D':11}      # period, year, month and crop name

def generate_excel_outfiles(study, subarea, lookup_df, out_dir,  weather, complete_run, mngmnt_ss, mngmnt_fwd):
    '''

    '''
    study_full_name = study.study_name + ' ' + subarea      # typical study: Zerai Farm; subarea: Base line

    # concatenate weather into single entity
    # ======================================
    len_ss = len(weather.pettmp_ss['precip'])
    period_lst = len_ss*['steady state']

    len_fwd = len(weather.pettmp_fwd['precip'])
    period_lst += len_fwd*['forward run']

    precip_lst = weather.pettmp_ss['precip'] + weather.pettmp_fwd['precip']
    tair_lst = weather.pettmp_ss['tair'] + weather.pettmp_fwd['tair']
    pet_lst = weather.pettmp_ss['pet'] + weather.pettmp_fwd['pet']
    gdds_lst = weather.pettmp_ss['grow_dds'] + weather.pettmp_fwd['grow_dds']

    pettmp = {'period':period_lst, 'precip':precip_lst, 'tair':tair_lst, 'pet':pet_lst, 'grow_dds':gdds_lst}

    carbon_change, nitrogen_change, soil_water = complete_run
    nitrogen_change.additional_n_variables() # use existing data to populate additional fields
    print()

    crop_prodn_b1 = B1CropProduction(pettmp, soil_water, mngmnt_ss, mngmnt_fwd)
    _write_excel_out(study_full_name, lookup_df, 'B1 Crop Production', out_dir, crop_prodn_b1, create_flag = True)

    n_limitation_b1c = B1cNlimitation(pettmp, carbon_change, nitrogen_change, soil_water, mngmnt_ss, mngmnt_fwd)
    _write_excel_out(study_full_name, lookup_df, 'B1c Nitrogen Limitation', out_dir, n_limitation_b1c)

    som_change_a1 = A1SomChange(pettmp, carbon_change, soil_water)
    _write_excel_out(study_full_name, lookup_df, 'A1 SOM change', out_dir, som_change_a1)

    mineralN_a2 = A2MineralN(pettmp, nitrogen_change)
    _write_excel_out(study_full_name, lookup_df, 'A2 Mineral N', out_dir, mineralN_a2)

    soilN_supply_a2a = A2aSoilNsupply(pettmp, nitrogen_change)
    _write_excel_out(study_full_name, lookup_df, 'A2a Soil N supply', out_dir, soilN_supply_a2a)

    cropN_uptake_a2b = A2bCropNuptake(pettmp, nitrogen_change)
    _write_excel_out(study_full_name, lookup_df, 'A2b Crop N uptake', out_dir, cropN_uptake_a2b)
     
    leachedN_loss_a2c = A2cLeachedNloss(pettmp, soil_water, nitrogen_change)
    _write_excel_out(study_full_name, lookup_df, 'A2c LeachedNloss', out_dir, leachedN_loss_a2c)

    denitrified_Nloss_a2d = A2dDenitrifiedNloss(pettmp, carbon_change, nitrogen_change, soil_water)
    _write_excel_out(study_full_name, lookup_df, 'A2d Denitrified N loss', out_dir, denitrified_Nloss_a2d)

    volatilised_Nloss_a2e = A2eVolatilisedNloss(pettmp, nitrogen_change)
    _write_excel_out(study_full_name, lookup_df, 'A2e Volatilised N loss', out_dir, volatilised_Nloss_a2e)

    nitrification_a2f = A2fNitrification(pettmp, nitrogen_change)
    _write_excel_out(study_full_name, lookup_df, 'A2f Nitrification', out_dir, nitrification_a2f)

    soil_water_a3 = A3SoilWater(pettmp, nitrogen_change, soil_water)
    _write_excel_out(study_full_name, lookup_df, 'A3 Soil Water', out_dir, soil_water_a3)

    return

def _write_excel_out(study, lookup_df, sheet_name, out_dir, output_obj, create_flag = False):
    '''
    condition data before outputting
    '''
    func_name =  __prog__ +  ' write_excel_out'

    # make a safe name
    # ===============
    fname = os.path.join(out_dir, study + '.xlsx')
    if create_flag:
        if os.path.isfile(fname):
            try:
                os.remove(fname)
            except PermissionError as err:
                print(err)
                return -1
    else:
        if not os.path.isfile(fname):
            print('File ' + fname + ' must exist')
            return -1

    # create data frame from dictionary
    # =================================
    data_frame = DataFrame()
    for var_name in output_obj.var_name_list:

        tmp_list = output_obj.sheet_data[var_name]

        var_fmt = output_obj.var_formats[var_name]
        if var_fmt[-1] == 'f':
            ndecis = int(var_fmt[:-1])
            try:
                if var_name == 'crop_name':
                    data_frame[var_name] = Series(tmp_list)
                else:
                    data_frame[var_name] = Series([round(val, ndecis) for val in tmp_list])
            except TypeError as err:
                print(err)
                return -1
        else:
            data_frame[var_name] = Series(tmp_list)

    # use pandas to write to Excel
    # ============================
    writer = ExcelWriter(fname, engine = 'openpyxl')
    if not create_flag:
        writer.book = load_workbook(fname)  # open existing workbook
        writer.sheets = dict((ws.title, ws) for ws in writer.book.worksheets)   # copy existing sheets

    data_frame.to_excel(writer, sheet_name, index=False, freeze_panes=(1, 1))
    writer.save()

    # reopen Excel file and write a chart
    # ===================================
    _generate_metric_charts(fname, lookup_df, sheet_name, create_flag)

    return 0

def _generate_metric_charts(fname, lookup_df, sheet_name, create_flag):
    '''
    add charts to an existing Excel file
    '''
    func_name =  __prog__ + ' generate_charts'

    wb_obj = load_workbook(fname, data_only=True)
    sheet = wb_obj[sheet_name]

    # reset column width
    # ==================
    max_wdth = 8       # we want first column to be as wide as "steady state" i.e. 12 chars
    for icol in range(sheet.max_column):
        val = sheet.cell(row = 1, column = icol + 1).value
        nchars = len(val)
        if nchars > max_wdth:
            max_wdth = nchars

    for ch in ALPHABET[4:]:
        sheet.column_dimensions[ch].width = max_wdth + 2  # set the width of the column

    for ch in FIXED_WDTHS:
        sheet.column_dimensions[ch].width = FIXED_WDTHS[ch]

    # adjust row height
    # =================
    for irow in range(sheet.max_row):
        sheet.row_dimensions[irow].height = 18

    # chart creation
    # ==============
    sheet_ref = sheet_name.split()[0]
    chart_sheet = wb_obj.create_sheet(sheet_ref + ' charts')
    nrow_chart = 10

    # generate charts for all metrics except for period, month and tstep
    # ==================================================================
    max_column = min(len(ALPHABET), sheet.max_column)
    for col_indx in range(max_column, 4, -1):               # ignore period, month and tstep fields
        metric_chart = LineChart()
        metric_chart.style = 13

        metric = sheet[ALPHABET[col_indx - 1] + '1'].value      # read field name
        defn, units = fetch_variable_definition(lookup_df, metric)
        metric_chart.title = defn
        metric_chart.y_axis.title = units
        metric_chart.x_axis.title = 'Time step'
        metric_chart.height = 10
        metric_chart.width = 20

        data = Reference(sheet, min_col = col_indx, min_row = 1, max_col = col_indx, max_row = sheet.max_row)
        metric_chart.add_data(data, titles_from_data = True)

        # Style the lines
        # ===============
        sref = metric_chart.series[0]
        sref.graphicalProperties.line.width = PREFERRED_LINE_WIDTH
        sref.graphicalProperties.line.solidFill = "FF0000"
        sref.smooth = True

        # now write to previously created sheet
        # =====================================
        chart_sheet.add_chart(metric_chart, "D" + str(nrow_chart))
        nrow_chart += 20

    try:
        wb_obj.active = 1   # make the charts sheet active - assumes there are only two sheets
        wb_obj.save(fname)
        if create_flag:
            print('Created: ' + fname)
        print('\tadded charts for sheet: ' + sheet_name)

    except PermissionError as err:
        print(str(err) + ' - could not save: ' + fname)

    QApplication.processEvents()

    return

def extend_out_dir(form):

    # check and if necessary create extended output directory
    # =======================================================
    mgmt_dir = form.w_lbl06.text()
    dummy, short_dir = os.path.split(mgmt_dir)
    curr_out_dir = form.w_lbl15.text()

    out_dir = os.path.normpath(os.path.join(curr_out_dir, short_dir))
    if os.path.isdir(out_dir):
        form.settings['out_dir'] = out_dir
    else:
        try:
            os.mkdir(out_dir)
            print('Created output directory: ' + out_dir)
            form.settings['out_dir'] = out_dir
        except PermissionError as err:
            print('*** Error *** Could not create output directory: ' + out_dir + ' will use ' + curr_out_dir)

    return

def retrieve_output_xls_files(form, study_name = None):
    '''
    retrieve list of Excel files in the output directory

    '''
    if study_name is None:
        study_name = form.settings['study']

    out_dir = form.settings['out_dir']      # existence has been pre-checked in check_excel_input_fname
    xlsx_list = glob(out_dir + '/' + study_name + '*.xlsx')
    form.w_combo17.clear()
    if len(xlsx_list) > 0:
        form.w_disp_out.setEnabled(True)
        for out_xlsx in xlsx_list:
            dummy, short_fn = os.path.split(out_xlsx)
            form.w_combo17.addItem(short_fn)
    return
