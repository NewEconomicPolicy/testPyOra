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

from ora_excel_read import read_econ_purch_sales_sheet, read_econ_labour_sheet

#----------------------------------------------------------
# Create class to store instances of family members, in order to work out labour


class HouseholdMembers:

    '''
    Information on household members and their labour contribution
    '''

    def __init__(self, name, labour_data):

        labour_data = labour_data
        self.name = name
        self.number = labour_data[0]
        self.awake = labour_data[1]

        # Information on wood
        self.wood_bundle_weight = labour_data[3]
        self. time_collect_1_wood_bundle = labour_data[4]
        self.number_weekly_wood_trips = labour_data[6]
        self.per_wood_trip_time_spent_travelling = labour_data[8]
        self.per_wood_trip_time_spent_collecting = labour_data[9]

        # Information on water
        self.weekly_trips_water_collect_non_irrigation = labour_data[12]
        self.volume_water_carried_per_trip = labour_data[14]
        self.normal_year_time_travel_water_per_trip = labour_data[16]
        self.normal_year_time_queue_water_per_trip = labour_data[17]
        self.drought_year_time_travel_water_per_trip = labour_data[19]
        self.drought_year_time_queue_water_per_trip = labour_data[20]

        # Information on livestock
        self.daily_time_spent_tending_animals = labour_data[23]
        self.daily_time_dung_management = labour_data[24]

        # Information on crop production
        self.total_days_sowing_crops = labour_data[27]
        self.daily_average_time_sowing_crops = labour_data[29]
        self.grow_seas_total_time_tending_crops = labour_data[32]
        self.harvest_total_days_harvesting = labour_data[34]
        self.harvest_average_day_hrs_spent_harvesting = labour_data[36]

        # Information on other activities
        self.grow_seas_essential_activities_hrs_day = labour_data[40]
        self.grow_seas_non_essential_activities_hrs_day = labour_data[41]


def test_economics_algorithms(form):

    '''
    Algorithm to model household economics
    '''

    #----------------------------------------------------------
    # Import data on purchases and sales, and labour, from excel spreadsheet
    # Save as a DataFrame

    xls_inp_fname = os.path.normpath(form.w_lbl13.text())
    purch_sales_df = read_econ_purch_sales_sheet(xls_inp_fname, 'Purchases & Sales', 3)
    purch_sales_df = purch_sales_df.drop(columns=['Units.2','Units.3', 'Units.4', 'Units.5', 'Units.6', 'Units.7',
                                                  'Unnamed: 18'])
    purch_sales_df.columns= ['category', 'name', 'dryseas_pur_pr', 'units', 'dryseas_pur_quant', 'measure',
                             'wetseas_pur_pr', 'wetseas_pur_quant', 'dryseas_sale_pr', 'dryseas_sale_quant',
                             'wetseas_sale_pr', 'wetseas_sale_quant']
    labour_df = read_econ_labour_sheet(xls_inp_fname, 'Labour', 0)

    # ----------------------------------------
    # Create instances of HouseholdMembers Class using dataframe created from excel sheet
    hh_members = []
    labour_df = labour_df.iloc[: , 1:]
    for column_name, column_data in labour_df.iteritems():
        hh_instance =  HouseholdMembers(column_name, column_data)
        hh_members.append(hh_instance)




    # ----------------------------------------
    # Check if crop model has been run
    # If yes > import crop production data for forward run
    # If no > prompt user
    if form.crop_run:
        crop_data = form.crop_production

    else:
        print('No crop data! Please run C and N model first')



    #----------------------------------------
    # Check if livestock model has been run
    # If yes > Import livestock data and get total yearly manure production data for forward run
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

    # Calculate how much manure is needed/produced/sold during year

    # Calculate wet and dry season income
    dryseas_income = ((purch_sales_df['dryseas_sale_pr'] * purch_sales_df['dryseas_sale_quant']) -
                            (purch_sales_df['dryseas_pur_pr'] *  purch_sales_df['dryseas_pur_quant']))
    total_dryseas_income = dryseas_income.sum()
    wetseas_income = ((purch_sales_df['wetseas_sale_pr'] * purch_sales_df['wetseas_sale_quant']) -
                            (purch_sales_df['wetseas_pur_pr'] *  purch_sales_df['wetseas_pur_quant']))
    total_wetseas_income = wetseas_income.sum()
    total_income = total_dryseas_income + total_wetseas_income





    print('Economics Calcs completed')
    return
