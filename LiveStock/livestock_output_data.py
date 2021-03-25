#-------------------------------------------------------------------------------
# Name:        livestock_output_data.py
# Purpose:     Functions to create TODO
# Author:      Dave Mcbey
# Created:     22/03/2020
# Description:
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'livestock_output_data.py'
__version__ = '1.0.1'
__author__ = 's02dm4'


import os
from pathlib import Path
from ora_json_read import ReadLvstckJsonSubareas
from ora_excel_read import ReadAfricaAnmlProdn
from ora_excel_read import ReadCropOwNitrogenParms, ReadStudy
from merge_data import merge_harvest_land_use
from livestock_class import Livestock

def _get_pigs_or_poultry_production(anml_type):
    '''
    pigs are based on goats
    poultry are guessed
    '''

    if anml_type == 'Pigs':
        manure = 180.0
        n_excrete = 15.0
        meat = 10
        milk = 0
    else:
        manure = 2
        n_excrete = 0.1
        meat = 0.01
        milk = 0

    return manure, n_excrete, meat, milk

def _get_production_and_n_excreted(anml_prodn_obj, all_lvstck):
    '''

    '''
    anml_prodn_df = anml_prodn_obj.africa_anml_prodn

    for subarea in all_lvstck.subareas:
        lvstck_defn = all_lvstck.subareas[subarea]
        region = lvstck_defn['region']
        system = lvstck_defn['system']

        new_lvstck_grp = []
        for lvstck in lvstck_defn['lvstck_grp']:
            num = lvstck.number
            anml_type = lvstck.type
            if anml_type == 'Pigs' or anml_type == 'Poultry':
                manure, n_excrete, meat, milk = _get_pigs_or_poultry_production(anml_type)
            else:
                res = anml_prodn_df[(anml_prodn_df.Region == region) &
                                    (anml_prodn_df.System == system) & (anml_prodn_df.Type == anml_type)]
                manure = res.Manure.values[0]
                n_excrete = res.ExcreteN.values[0]
                meat = res.Meat.values[0]
                milk = res.Milk.values[0]

            lvstck.manure = manure
            lvstck.n_excrete = n_excrete
            lvstck.meat = meat
            lvstck.milk = milk
            new_lvstck_grp.append(lvstck)

        lvstck_defn['lvstck_grp'] = new_lvstck_grp
        all_lvstck.subareas[subarea] = lvstck_defn

    return

def write_livestock_charts(form):
    '''

    '''

    # read inputs and create folder to store graphs in
    # =================================================
    xls_inp_fname = os.path.normpath(form.w_lbl13.text())
    if not os.path.isfile(xls_inp_fname):
        print('Excel input file ' + xls_inp_fname + 'must exist')
        return

    # read sheets from input Excel workbook
    # =====================================
    print('Loading: ' + xls_inp_fname)
    study = ReadStudy(form.w_lbl06.text(), xls_inp_fname, form.settings['out_dir'])
    ora_parms = ReadCropOwNitrogenParms(xls_inp_fname)
    out_dir = form.settings['out_dir']
    Path(out_dir + "/Livestock/Graphs").mkdir(parents = True, exist_ok = True)

    # create animal production object which includes crop names for validation purposes
    # =================================================================================
    anml_prodn_obj = ReadAfricaAnmlProdn(xls_inp_fname, ora_parms.crop_vars)
    if anml_prodn_obj.retcode is None:
        return

    # read and validate livestock JSON files
    # ======================================
    all_lvstck = ReadLvstckJsonSubareas(form.settings['lvstck_files'], anml_prodn_obj)
    _get_production_and_n_excreted(anml_prodn_obj, all_lvstck)    # updates

    # Access crop production data
    # ===========================
    harvest_land_use_merged = merge_harvest_land_use(form.all_runs_crop_model)
    print('Returned harvest land use merged')

    # Calculate animal production
    # ===========================
    for subarea in all_lvstck.subareas.items():
        livestock_group = subarea[1]['lvstck_grp']
        region = subarea[1]['region']
        system = subarea[1]['system']
        livestock_list = []
        for livestock in livestock_group:
            subarea_livestock_instance = Livestock(livestock, region, system)
            livestock_list.append(subarea_livestock_instance)
        print(f"livestock list contains {len(livestock_list)} animals")


    '''
    livestock = Livestock(all_lvstck)
    livestock.get_monthly_harvest_change(orator_obj, harvest_land_use_merged)
    '''
    print('Finished livestock processing')
    return
