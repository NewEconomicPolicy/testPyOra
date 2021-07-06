#-------------------------------------------------------------------------------
# Name:        ora_economics_model.py
# Purpose:     functions for economics model
# Author:      David McBey
# Created:     23/07/2020
# Licence:     <your licence>
# defs:
#   test_economics_algorithms
#
# Description:
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_economics_model.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
import os

from ora_excel_read import read_econ_purch_sales_sheet


def test_economics_algorithms(form):

    '''
    Algorithm to model household economics
    '''

    #----------------------------------------------------------
    # Import data on purchases and sales from excel spreadsheet
    # Save as a DataFrame

    xls_inp_fname = os.path.normpath(form.w_lbl13.text())
    purch_sales_df = read_econ_purch_sales_sheet(xls_inp_fname, 'Purchases & Sales', 3)
    purch_sales_df = purch_sales_df.drop(columns=['Units.2','Units.3', 'Units.4', 'Units.5', 'Units.6', 'Units.7',
                                                  'Unnamed: 18'])
    purch_sales_df.columns= ['category', 'name', 'dryseas_pur_pr', 'units', 'dryseas_pur_quant', 'measure',
                             'wetseas_pur_pr', 'wetseas_pur_quant', 'dryseas_sale_pr', 'dryseas_sale_quant',
                             'wetseas_sale_pr', 'wetseas_sale_quant']

    #----------------------------------------
    # Check if livestock model has been run.
    # If yes > Import livestock data and get total yearly manure production data
    # If no > Prompt user
    if form.livestock_run:
        manure_data = form.total_an_prod_all_subareas
        management_type_manure_dic = {}
        for management_type, data in manure_data.items():
            calc_method_manure_dic = {}
            for calc_method, livestock in data.items():
                # Create variable which stores list of lists, each list is an animals manure production per year
                manure_fr = []
                for animal, prod_data in livestock.items():
                    manure_fr.append(prod_data['manure_prod_fr'])
                # Sum all manure production to get total produced each year for all animals
                total_manure_fr = [sum(i) for i in zip(*manure_fr)]
                # Update dictionary with calculation method total production
                calc_method_manure_dic.update({calc_method: total_manure_fr})
            management_type_manure_dic.update({management_type:calc_method_manure_dic})

    else:
        print('No manure production data! Please run livestock module')




    print('ORATOR economics model')
    return
