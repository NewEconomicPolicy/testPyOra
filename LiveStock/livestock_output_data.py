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

import matplotlib.pyplot as plt
from pathlib import Path
from pull_input_data import ReadInputExcel
from merge_data import merge_harvest_land_use
from livestock_class import Livestock

# from livestock_class import Livestock, livestock_list
livestock_list = []

def write_livestock_charts(form):

    # read inputs and create folder to store graphs in
    # =================================================
    xls_fname = form.settings['livestock_fname']
    out_dir = form.settings['out_dir']
    Path(out_dir + "/Livestock/Graphs").mkdir(parents = True, exist_ok = True)

    orator_obj = ReadInputExcel(form, xls_fname)
    if orator_obj.retcode is None:
        return

    harvest_land_use_merged = merge_harvest_land_use(orator_obj)
    print('Returned harvest land use merged with shape: ' + str(harvest_land_use_merged.shape))

    livestock = Livestock(orator_obj)
    livestock.get_monthly_harvest_change(orator_obj, harvest_land_use_merged)

    return

class Charts(object):
    '''
    Create charts
    '''
    def __init__(self, orator_obj):

        self.title = 'Chart creation'
        '''
        Create graphs with all livestock shown on it
        '''

        # Milk and Eggs
        # =============
        plt.style.use('seaborn')
        fig, ax = plt.subplots()
        liv_manure_10_yr_monthly = {}
        for livestock in livestock_list:
            ax.plot(livestock.atyp_milk_prod, linewidth=3, label=livestock.neat_name)

        plt.title("All livestock atypical milks/egg production", fontsize=24)
        plt.xlabel('Months since typical', fontsize=16)
        plt.ylabel('Production (Kg per year', fontsize=16)
        plt.legend(loc="upper right")
        plt.tick_params(axis='both', which='major', labelsize=16)
        plt.savefig('Outputs/Livestock/Graphs/all_livestock_milk_eggs_atypical.png', bbox_inches='tight')

        # Meat
        # ====
        plt.style.use('seaborn')
        fig, ax = plt.subplots()
        liv_manure_10_yr_monthly = {}
        for livestock in livestock_list:
            ax.plot(livestock.atyp_meat_prod, linewidth=3, label=livestock.neat_name)

        plt.title("All livestock atypical meat production", fontsize=24)
        plt.xlabel('Months since typical', fontsize=16)
        plt.ylabel('Production (Kg per year', fontsize=16)
        plt.legend(loc="upper right")
        plt.tick_params(axis='both', which='major', labelsize=16)
        plt.savefig('Outputs/Livestock/Graphs/all_livestock_meat_atypical.png', bbox_inches='tight')

        # Manure
        # ======
        plt.style.use('seaborn')
        fig, ax = plt.subplots()
        liv_manure_10_yr_monthly = {}
        for livestock in livestock_list:
            ax.plot(livestock.atyp_man_prod, linewidth=3, label=livestock.neat_name)

        plt.title("All livestock atypical manure production", fontsize=24)
        plt.xlabel('Months since typical', fontsize=16)
        plt.ylabel('Production (Kg per year', fontsize=16)
        plt.legend(loc="upper right")
        plt.tick_params(axis='both', which='major', labelsize=16)
        plt.savefig('Outputs/Livestock/Graphs/all_livestock_manure_atypical.png', bbox_inches='tight')

        # Excreted N
        # ==========
        plt.style.use('seaborn')
        fig, ax = plt.subplots()
        liv_manure_10_yr_monthly = {}
        for livestock in livestock_list:
            ax.plot(livestock.atyp_N_excr, linewidth=3, label=livestock.neat_name)

        plt.title("All livestock atypical Nitrogen excretion", fontsize=24)
        plt.xlabel('Months since typical', fontsize=16)
        plt.ylabel('N Excretions (Kg per year', fontsize=16)
        plt.legend(loc="upper right")
        plt.tick_params(axis='both', which='major', labelsize=16)
        plt.savefig('Outputs/Livestock/Graphs/all_livestock_nitrogen_atypical.png', bbox_inches='tight')

        # Create graph with data for each animal and production type
        # ==========================================================
        for livestock in livestock_list:
            plt.style.use('seaborn')
            fig, ax = plt.subplots()
            ax.plot(livestock.atyp_milk_prod, linewidth=3)

            #Set chart title and label access
            ax.set_title(f"Milk/Egg Production: {livestock.name}", fontsize=24)
            ax.set_xlabel("Months since typical", fontsize=14)
            ax.set_ylabel("Production (Kg per year", fontsize=14)

            #Set size of tick labels
            ax.tick_params(axis='both', labelsize=14)

            # Save output
            plt.savefig(f'Outputs/Livestock/Graphs/{livestock.neat_name}_milk_egg_prod_atypical.png', bbox_inches='tight')

        for livestock in livestock_list:
            plt.style.use('seaborn')
            fig, ax = plt.subplots()
            ax.plot(livestock.atyp_meat_prod, linewidth=3)

            #Set chart title and label access
            ax.set_title(f"Meat Production: {livestock.name}", fontsize=24)
            ax.set_xlabel("Months since typical", fontsize=14)
            ax.set_ylabel("Production (Kg per year", fontsize=14)

            #Set size of tick labels
            ax.tick_params(axis='both', labelsize=14)

            # Save output
            plt.savefig(f'Outputs/Livestock/Graphs/{livestock.neat_name}_meat_atypical.png', bbox_inches='tight')

        for livestock in livestock_list:
            plt.style.use('seaborn')
            fig, ax = plt.subplots()
            ax.plot(livestock.atyp_man_prod, linewidth=3)

            #Set chart title and label access
            ax.set_title(f"Manure Production: {livestock.name}", fontsize=24)
            ax.set_xlabel("Months since typical", fontsize=14)
            ax.set_ylabel("Production (Kg per year", fontsize=14)

            #Set size of tick labels
            ax.tick_params(axis='both', labelsize=14)

            # Save output
            plt.savefig(f'Outputs/Livestock/Graphs/{livestock.neat_name}_man_prod_atypical.png', bbox_inches='tight')

        for livestock in livestock_list:
            plt.style.use('seaborn')
            fig, ax = plt.subplots()
            ax.plot(livestock.atyp_N_excr, linewidth=3)

            #Set chart title and label access
            ax.set_title(f"N Excretion: {livestock.name}", fontsize=24)
            ax.set_xlabel("Months since typical", fontsize=14)
            ax.set_ylabel("Excretion (Kg per year", fontsize=14)

            #Set size of tick labels
            ax.tick_params(axis='both', labelsize=14)

            # Save output
            plt.savefig(f'Outputs/Livestock/Graphs/{livestock.neat_name}_N_excretion_atypical.png', bbox_inches='tight')
