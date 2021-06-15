#-------------------------------------------------------------------------------
# Name:        ora_economics_model.py
# Purpose:     functions for economics model
# Author:      Euan Phimster
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
    stub
    '''
    xls_inp_fname = os.path.normpath(form.w_lbl13.text())
    purch_sales_df = read_econ_purch_sales_sheet(xls_inp_fname, 'Purchases & Sales', 3)
    purch_sales_df = purch_sales_df.drop(columns=['Units.2','Units.3', 'Units.4', 'Units.5', 'Units.6', 'Units.7',
                                                  'Unnamed: 18'])
    purch_sales_df.columns= ['category', 'name', 'dryseas_pur_pr', 'units', 'dryseas_pur_quant', 'measure',
                             'wetseas_pur_pr', 'wetseas_sale_quant', 'dryseas_sale_pr', 'dryseas_sale_quant',
                             'wetseas_sale_pr', 'wetseas_sale_quant']

    print('ORATOR economics model')
    return
