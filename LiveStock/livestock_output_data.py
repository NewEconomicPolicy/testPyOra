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
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from pandas import DataFrame
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

def calc_livestock_data(form):
    '''
    Calculate livestock data
    '''
    # Change flag to show livestock module has been run
    # =================================================
    form.livestock_run = True

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
    # Add on;y crop production data to form object so it can be used by econ module
    form.crop_production = harvest_land_use_merged

    # Calculate animal production
    # ===========================
    # Create list of all livestock types, for each livestock subarea
    livestock_all_subareas = []
    for subarea in all_lvstck.subareas.items():
        livestock_group = subarea[1]['lvstck_grp']
        region = subarea[1]['region']
        system = subarea[1]['system']
        livestock_list = []
        for livestock in livestock_group:
            subarea_livestock_instance = Livestock(livestock, region, system)
            livestock_list.append(subarea_livestock_instance)
    livestock_all_subareas.append(livestock_list)

    # Calculate change in production for each crop sub-area and management type, using each calculation method
    print('Calculating livestock production')
    total_an_prod_all_subareas = {}
    for subarea in harvest_land_use_merged.items():
        calc_method_dic = {}
        for calc_method in subarea[1].items():
            subarea_prod = {}
            for livestock_subarea in livestock_all_subareas:
                for livestock in livestock_subarea:
                    prod = livestock.calc_prod_chng(calc_method)
                    prod_dic = {livestock.livestock_name : prod}
                    subarea_prod.update(prod_dic)
            calc_dic = {calc_method[0] : subarea_prod}
            calc_method_dic.update(calc_dic)
        tot_prod_data = {subarea[0] : calc_method_dic}
        total_an_prod_all_subareas.update(tot_prod_data)
    print('livestock calcs completed')
    form.total_an_prod_all_subareas = total_an_prod_all_subareas
    return


    # Create graphs and CSV for each data
    # THIS IS VERY VERY SLOW RIGHT NOW - NEEDS REDONE
'''
    print('Creating livestock charts')
    parent_dir = 'c:/livestockoutputtest'
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    run_time = datetime.now()
    directory = f'Livestock run at {run_time.day}_{run_time.month}_{run_time.year} ' \
                f'{run_time.hour}_{run_time.minute}_{run_time.second}'
    path = os.path.join(parent_dir, directory)
    os.makedirs(path)
    all_livestock_df = DataFrame.from_dict(total_an_prod_all_subareas)
    all_livestock_df.to_csv(path+'\\all_data.csv')
    for subarea in total_an_prod_all_subareas.items():
        subarea_path = f'{subarea[0]}'
        join_path = os.path.join(path, subarea_path)
        os.makedirs(join_path)
        for calc_method in subarea[1].items():
            calc_method_path = f'{calc_method[0]}'
            calc_method_full = os.path.join(join_path, calc_method_path)
            os.makedirs(calc_method_full)
            for animal_type in calc_method[1].items():
                for output, values in animal_type[1].items():
                    values_array = np.array(values)
                    plt.plot(values_array)
                    plt.xlabel('Years since steady state')
                    plt.xticks(range(len(values)))
                    if output == 'milk_prod_fr':
                        plt.ylabel('Milk Production (Litres)')
                        plt.title('Milk Production Forward Run')
                    if output == 'meat_prod_fr':
                        plt.ylabel('Meat Production (Kg)')
                        plt.title('Meat Forward Run')
                    elif output == 'manure_prod_fr':
                        plt.ylabel('Manure Production (Kg)')
                        plt.title('Manure Production Forward Run')
                    elif output == 'n_excrete_fr':
                        plt.ylabel('Nitrogen Excreted (Kg)')
                        plt.title('Nitrogen Excreted Forward Run')
                    elif output == 'egg_prod_fr':
                        plt.ylabel('Egg production (Kg)')
                        plt.title('Egg Production Forward Run')
                    else:
                        plt.ylabel('Production')
                        plt.title(output)
                    if animal_type[0] == 'Goats/sheep for milk':
                        filename = f'Goats or sheep for milk {output}'
                    else:
                        filename = f'{animal_type[0]} {output}'
                    filename_path = os.path.join(calc_method_full,filename)
                    plt.savefig(filename_path)
                    plt.close()
'''
