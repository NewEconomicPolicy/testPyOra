# -------------------------------------------------------------------------------
# Name:        livestock_output_data.py
# Purpose:     Functions to create TODO
# Author:      Dave Mcbey
# Created:     22/03/2020
# Description:
# -------------------------------------------------------------------------------
__prog__ = 'livestock_output_data.py'
__version__ = '1.0.1'
__author__ = 's02dm4'

from os.path import isfile, normpath
import numpy as np
from PyQt5.QtWidgets import QApplication
from pathlib import Path
from ora_excel_read import ReadLivestockSheet
from ora_excel_read import ReadAnmlProdn
from ora_excel_read import ReadCropOwNitrogenParms, ReadStudy
from merge_data import merge_harvest_land_use
from livestock_class import Livestock
from ora_cn_classes import LivestockModel
from ora_gui_misc_fns import simulation_yrs_validate

def check_livestock_run_data(form, ntab=3):
    """
    Test livestock data
    """

    # read inputs and create folder to store graphs in
    # =================================================
    xls_inp_fname = normpath(form.settings['params_xls'])
    if not isfile(xls_inp_fname):
        print('Excel input file ' + xls_inp_fname + 'must exist')
        QApplication.processEvents()
        return

    # read sheets from input Excel workbook
    # =====================================
    print('Loading: ' + xls_inp_fname)
    ora_parms = ReadCropOwNitrogenParms(xls_inp_fname)

    # create animal production object which includes crop names for validation purposes
    # =================================================================================
    anml_prodn_obj = ReadAnmlProdn(xls_inp_fname, ora_parms.crop_vars)
    if anml_prodn_obj.retcode is None:
        return

    # read and validate livestock JSON files
    # ======================================
    if ntab == 3:
        all_lvstck = ReadLivestockSheet(form.w_run_dir3, anml_prodn_obj)
    else:
        all_lvstck = ReadLivestockSheet(form.w_run_dir0, anml_prodn_obj)

    try:
        getattr(all_lvstck, 'subareas')
    except AttributeError as err:
        print(str(err))
        QApplication.processEvents()
        return None

    _get_production_and_n_excreted(anml_prodn_obj, all_lvstck)    # updates

    return len(all_lvstck.subareas['all']['lvstck_grp'])

def _get_pigs_or_poultry_production(anml_type):
    """
    pigs are based on goats
    poultry are guessed
    NOT USED NOW
    """
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
    """

    """
    anml_prodn_df = anml_prodn_obj.anml_prodn

    for subarea in all_lvstck.subareas:
        lvstck_defn = all_lvstck.subareas[subarea]
        region = lvstck_defn['region']
        system = lvstck_defn['system']

        new_lvstck_grp = []
        for lvstck in lvstck_defn['lvstck_grp']:
            num = lvstck.number
            anml_type = lvstck.type
            res = anml_prodn_df[(anml_prodn_df.Region == region) &
                                    (anml_prodn_df.System == system) & (anml_prodn_df.Type == anml_type)]
            manure = res.Manure.values[0]
            n_excrete = res.ExcreteN.values[0]
            meat = res.Meat.values[0]
            milk = res.Milk.values[0]

            # capture instances where production system data isn't available, and default to 'ANY' in Herrero table

            if np.isnan(manure):
                print(f'No {anml_type} data available for {system} production system for {region}. '
                      f'"ANY" data used instead.')
                res = anml_prodn_df[(anml_prodn_df.Region == region) &
                                    (anml_prodn_df.System == 'ANY') & (anml_prodn_df.Type == anml_type)]
                manure = res.Manure.values[0]
                n_excrete = res.ExcreteN.values[0]
                meat = res.Meat.values[0]
                milk = res.Milk.values[0]
                lvstck.manure = manure
                lvstck.n_excrete = n_excrete
                lvstck.meat = meat
                lvstck.milk = milk
                new_lvstck_grp.append(lvstck)

            else:
                lvstck.manure = manure
                lvstck.n_excrete = n_excrete
                lvstck.meat = meat
                lvstck.milk = milk
                new_lvstck_grp.append(lvstck)

        lvstck_defn['lvstck_grp'] = new_lvstck_grp
        all_lvstck.subareas[subarea] = lvstck_defn

    return

def calc_livestock_data(form):
    """
    Calculate livestock data
    """
    # Change flag to show livestock module has been run
    # =================================================
    form.livestock_run = True

    # read inputs and create folder to store graphs in
    # =================================================
    xls_inp_fname = normpath(form.settings['params_xls'])
    if not isfile(xls_inp_fname):
        print('Excel input file ' + xls_inp_fname + 'must exist')
        return

    # read sheets from input Excel workbook
    # =====================================
    print('Loading: ' + xls_inp_fname)
    ora_parms = ReadCropOwNitrogenParms(xls_inp_fname)
    out_dir = form.settings['out_dir']
    Path(out_dir + "/Livestock/Graphs").mkdir(parents = True, exist_ok = True)

    # create animal production object which includes crop names for validation purposes
    # =================================================================================
    anml_prodn_obj = ReadAnmlProdn(xls_inp_fname, ora_parms.crop_vars)
    if anml_prodn_obj.retcode is None:
        return

    # read and validate livestock JSON files
    # ======================================
    all_lvstck = ReadLivestockSheet(form.w_run_dir3, anml_prodn_obj)
    _get_production_and_n_excreted(anml_prodn_obj, all_lvstck)    # updates

    # Access crop production data
    # ===========================
    harvest_land_use_merged = merge_harvest_land_use(form.all_runs_crop_model)

    # Calculate total production and add to form object, so it can be accessed by econ module. First make dic with
    # area in ha for each subarea
    total_area_dic = {}
    for sub_area, data in form.all_runs_crop_model.items():
        area_ha = data.area_ha
        total_area_dic.update({sub_area:area_ha})

    # Iterate through all production data and multiply yield per ha by field area in hectares
    for management_type, calc_methods in harvest_land_use_merged.items():
        area_ha = total_area_dic.get(management_type)
        for calc_method, years in calc_methods.items():
            for year in years:
                for crop, prod in year.items():
                    total_yield = prod * area_ha
                    year.update({crop: total_yield})

    # Add to form object to it can be accessed by econ module
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

    # Add livestock list to form object so it can be used in econ module
    form.livestock_list = livestock_list

    # Calculate change in production for each crop sub-area and management type, using each calculation method
    print('Calculating livestock production')
    total_an_prod_all_subareas = {}
    for subarea in harvest_land_use_merged.items():
        calc_method_dic = {}
        for calc_method in subarea[1].items():
            subarea_prod = {}
            for livestock_subarea in livestock_all_subareas:
                for livestock in livestock_subarea:
                    # Delineate whether feeding strategy is bought in or using on farm production
                    if livestock.strat == 'On farm production':
                        prod = livestock.calc_prod_chng(calc_method)
                        prod_dic = {livestock.livestock_name : prod}
                        subarea_prod.update(prod_dic)
                    else:
                        # Right now keep production steady, but don't 'use' crops
                        # Need data on how much crop to 'use' per animal if we want to reduce crop available for sale
                        prod = livestock.calc_steady_prod(calc_method)
                        prod_dic = {livestock.livestock_name : prod}
                        subarea_prod.update(prod_dic)

            calc_dic = {calc_method[0] : subarea_prod}
            calc_method_dic.update(calc_dic)
        tot_prod_data = {subarea[0] : calc_method_dic}
        total_an_prod_all_subareas.update(tot_prod_data)
    print('Livestock calcs completed')

    form.total_an_prod_all_subareas = total_an_prod_all_subareas

    # Collapse all subareas into one to show total animal production for farm
    keys = []
    values = []
    items = total_an_prod_all_subareas.items()
    for item in items:
        keys.append(item[0]), values.append(item[1])

    full_farm_livestock_production = {}
    for value in values:
        for man_type, all_livestock in value.items():
            if man_type not in full_farm_livestock_production.keys():
                temp_dic = {}
                for livestock, productions in all_livestock.items():
                    temp_dic.update({livestock : productions})
                full_farm_livestock_production.update({man_type : temp_dic})
            elif man_type in full_farm_livestock_production.keys():
                temp_dic = {}
                for livestock, productions in all_livestock.items():
                    temp_dic_2 = {}
                    for output, volume in productions.items():
                        new_values = [x + y for x, y in zip(productions[output], full_farm_livestock_production[man_type][livestock][output])]
                        temp_dic_2.update({output : new_values})
                    temp_dic.update({livestock:temp_dic_2})
                full_farm_livestock_production.update({man_type:temp_dic})

    # Format data to class object so it can be used in GUI charts. Only do for N Lim, although output data for all
    livestock_GUI_class = LivestockModel()
    form.all_farm_livestock_production = {'full_farm' : livestock_GUI_class}

    for calc_method, livestock in full_farm_livestock_production.items():
        if calc_method == 'n_lim':
            for animal, outputs in livestock.items():
                if animal == 'Dairy cattle':
                    for output, calcs in outputs.items():
                        if output == 'n_excrete_fr':
                            livestock_GUI_class.data['dairy_cat_n_excrete_nlim'] = calcs
                        elif output == 'milk_prod_fr':
                            livestock_GUI_class.data['dairy_cat_milk_prod_nlim'] = calcs
                        elif output == 'meat_prod_fr':
                            livestock_GUI_class.data['dairy_cat_meat_prod_nlim'] = calcs
                        elif output == 'manure_prod_fr':
                            livestock_GUI_class.data['dairy_cat_manure_prod_nlim'] = calcs
                elif animal == 'Beef cattle':
                    for output, calcs in outputs.items():
                        if output == 'n_excrete_fr':
                            livestock_GUI_class.data['beef_cat_n_excrete_nlim'] = calcs
                        elif output == 'milk_prod_fr':
                            pass
                        elif output == 'meat_prod_fr':
                            livestock_GUI_class.data['beef_cat_meat_prod_nlim'] = calcs
                        elif output == 'manure_prod_fr':
                            livestock_GUI_class.data['beef_cat_manure_prod_nlim'] = calcs
                elif animal == 'Goats/sheep for milk':
                    for output, calcs in outputs.items():
                        if output == 'n_excrete_fr':
                            livestock_GUI_class.data['goats_sheep_n_excrete_nlim'] = calcs
                        elif output == 'milk_prod_fr':
                            livestock_GUI_class.data['goats_sheep_milk_prod_nlim'] = calcs
                        elif output == 'meat_prod_fr':
                            livestock_GUI_class.data['goats_sheep_meat_prod_nlim'] = calcs
                        elif output == 'manure_prod_fr':
                            livestock_GUI_class.data['goats_sheep_manure_prod_nlim'] = calcs
                elif animal == 'Poultry':
                    for output, calcs in outputs.items():
                        if output == 'n_excrete_fr':
                            livestock_GUI_class.data['poultry_n_excrete_nlim'] = calcs
                        elif output == 'milk_prod_fr':
                            livestock_GUI_class.data['poultry_eggs_prod_nlim'] = calcs
                        elif output == 'meat_prod_fr':
                            livestock_GUI_class.data['poultry_meat_prod_nlim'] = calcs
                        elif output == 'manure_prod_fr':
                            livestock_GUI_class.data['poultry_manure_prod_nlim'] = calcs
                elif animal == 'Pigs':
                    for output, calcs in outputs.items():
                        if output == 'n_excrete_fr':
                            livestock_GUI_class.data['pigs_n_excrete_nlim'] = calcs
                        elif output == 'milk_prod_fr':
                            pass
                        elif output == 'meat_prod_fr':
                            livestock_GUI_class.data['pigs_meat_prod_nlim'] = calcs
                        elif output == 'manure_prod_fr':
                            livestock_GUI_class.data['pigs_manure_prod_nlim'] = calcs
                else:
                    pass
        else:
            pass


#        elif calc_method == 'zaks':
#            livestock_GUI_class.data['full_hh_income_zaks'] = calcs
#        elif calc_method == 'miami':
#            livestock_GUI_class.data['full_hh_income_miami': calcs]

    form.all_farm_livestock_production = {'full_farm' : livestock_GUI_class}

    form.w_disp_econ.setEnabled(True)
    form.w_disp_lvstck.setEnabled(True)

    return

    # Create graphs and CSV for each data
    # THIS IS VERY VERY SLOW RIGHT NOW - NEEDS REDONE
'''
    print('Creating livestock charts')
    parent_dir = 'c:/livestockoutputtest'
    if not exists(parent_dir):
        os.makedirs(parent_dir)
    run_time = datetime.now()
    directory = f'Livestock run at {run_time.day}_{run_time.month}_{run_time.year} ' \
                f'{run_time.hour}_{run_time.minute}_{run_time.second}'
    path = join(parent_dir, directory)
    os.makedirs(path)
    all_livestock_df = DataFrame.from_dict(total_an_prod_all_subareas)
    all_livestock_df.to_csv(path+'\\all_data.csv')
    for subarea in total_an_prod_all_subareas.items():
        subarea_path = f'{subarea[0]}'
        join_path = join(path, subarea_path)
        os.makedirs(join_path)
        for calc_method in subarea[1].items():
            calc_method_path = f'{calc_method[0]}'
            calc_method_full = join(join_path, calc_method_path)
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
                    filename_path = join(calc_method_full,filename)
                    plt.savefig(filename_path)
                    plt.close()
'''
