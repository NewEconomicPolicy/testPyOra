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
import os, numpy

from ora_excel_read import read_econ_purch_sales_sheet, read_econ_labour_sheet

#----------------------------------------------------------
# Create class to store instances of family members, in order to work out labour

class HouseholdMembers:

    '''
    Class to store information on household members and their labour contribution
    '''

    def __init__(self, name, labour_data):

        labour_data = labour_data
        self.name = name
        self.number = labour_data[0]
        self.awake = labour_data[1]
        self.awake_year = self.awake * 365

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

        # Information on wage rates
        self.wage_month = labour_data[43]
        self.wage_year = self.wage_month * 12
        # Assume work 365 days per year
        self.wage_day = self.wage_year / 365
        # Assume work 12 hrs day
        self.wage_hour = self.wage_day / 14

        # Calculation for total labour value
        self.value_of_labour_year = self.awake_year * self.wage_hour



    def agricultural_labour_calc(self):
        '''
        Function to calculate time spent on agricultural labour, including dung collection
        '''

        # In excel sheet this says 'typical weather' - what does this mean? drought years need to be considered?
        livestock_time = self.daily_time_spent_tending_animals + self.daily_time_dung_management
        self.livestock_time_annual = livestock_time * 365

        # How to differentriate sowing time from growing season from harvest time? Attatch to form object for calcs
        # Need also hourly rate for wages?
        self.sowing_time_year = self.total_days_sowing_crops * self.daily_average_time_sowing_crops

        # Create 'growing_season variable - how? IMPORT FROM CROP MODULE
        grow_season_days_total = 200
        self.tending_crops_time = self.grow_seas_total_time_tending_crops * grow_season_days_total

        self.harvest_crops_year = self.harvest_total_days_harvesting * self.harvest_average_day_hrs_spent_harvesting
        # Total hours spent annually
        self.total_agriculture_labour_yearly = self.livestock_time_annual + self.sowing_time_year + \
                                               self.tending_crops_time
        self.total_ag_labour_year_value = self.total_agriculture_labour_yearly * self.wage_hour

        return self.total_ag_labour_year_value
        
    def domestic_labour_calc(self):
        '''
        Function to calculate time spent on household labour (collecting water, firewood, cooking)
        '''
        wood_collection_weekly = self.number_weekly_wood_trips * \
                                 (self.per_wood_trip_time_spent_travelling + self.per_wood_trip_time_spent_collecting)
        self.year_wood_collect = wood_collection_weekly * 52
        water_collection_weekly_normal = self.weekly_trips_water_collect_non_irrigation * \
                                         (self.normal_year_time_travel_water_per_trip +
                                          self.normal_year_time_queue_water_per_trip)
        self.water_collection_yearly_normal = water_collection_weekly_normal * 52
        water_collection_weekly_drought = self.weekly_trips_water_collect_non_irrigation * \
                                          (self.drought_year_time_travel_water_per_trip +
                                           self.drought_year_time_queue_water_per_trip)
        self.water_collection_yearly_drought = water_collection_weekly_drought * 52

        # Currently doing this calc for 365 days, but how to do for only grow season?
        self.essential_activities_year = self.grow_seas_essential_activities_hrs_day * 365
        self.non_essential_activites_year = self.grow_seas_non_essential_activities_hrs_day * 365

        # Currently only for normal years. Need to define drought years and attacth to form object then add if statement
        # This is total hours per year spent doing activities
        self.total_domestic_labour = self.year_wood_collect + self.water_collection_yearly_normal + \
                                     self.essential_activities_year + self.non_essential_activites_year
        self.total_dom_labour_year_value = self.total_domestic_labour * self.wage_hour

        return self.total_dom_labour_year_value


class HouseholdPurchasesSales:

    '''
    Class to store information on household/farm purchases and sales
    '''

    def __init__(self, purchase_sales_data):

        purchase_sales_data= purchase_sales_data
        self.category = purchase_sales_data[0]
        self.name = purchase_sales_data[1]
        self.dryseas_pur_price = purchase_sales_data[2]
        self.cost_units = purchase_sales_data[3]
        self.dryseas_pur_quant = purchase_sales_data[4]
        self.quant_units = purchase_sales_data[5]
        self.wetseas_pur_price = purchase_sales_data[6]
        self.wetseas_pur_quant = purchase_sales_data[7]
        self.dryseas_sale_price = purchase_sales_data[8]
        self.dryseas_sale_quant = purchase_sales_data[9]
        self.wetseas_sale_price = purchase_sales_data[10]
        self.wetseas_sale_quant = purchase_sales_data[11]



def test_economics_algorithms(form):

    '''
    Algorithm to model household economics
    '''

    #----------------------------------------------------------
    # Import data on purchases and sales, and labour, from excel spreadsheet
    # Save as a DataFrame

    xls_inp_fname = os.path.normpath(form.settings['params_xls'])
    purch_sales_df = read_econ_purch_sales_sheet(xls_inp_fname, 'Purchases & Sales', 3)
    purch_sales_df = purch_sales_df.drop(columns=['Units.2','Units.3', 'Units.4', 'Units.5', 'Units.6', 'Units.7',
                                                  'Unnamed: 18'])
    purch_sales_df.columns= ['category', 'name', 'dryseas_pur_pr', 'units', 'dryseas_pur_quant', 'measure',
                             'wetseas_pur_pr', 'wetseas_pur_quant', 'dryseas_sale_pr', 'dryseas_sale_quant',
                             'wetseas_sale_pr', 'wetseas_sale_quant']
    # Calculate value of all sales
    purch_sales_df['dryseas_sales_value'] = purch_sales_df['dryseas_sale_pr'] * purch_sales_df['dryseas_sale_quant']
    purch_sales_df['wetseas_sales_value'] = purch_sales_df['wetseas_sale_pr'] * purch_sales_df['wetseas_sale_quant']

    labour_df = read_econ_labour_sheet(xls_inp_fname, 'Labour', 0)

    # ----------------------------------------
    # Create instances of HouseholdPurchasesSales Class using Dataframe created from excel sheet. Store in list.
    hh_purchases_sales = []
    for index, data in purch_sales_df.iterrows():
        hh_ps_instance = HouseholdPurchasesSales(data)
        hh_purchases_sales.append(hh_ps_instance)

    # ----------------------------------------
    # Create instances of HouseholdMembers Class using Dataframe created from excel sheet. Store in list.
    hh_members = []
    labour_df = labour_df.iloc[: , 1:]
    for column_name, column_data in labour_df.iteritems():
        hh_lab_instance =  HouseholdMembers(column_name, column_data)
        hh_members.append(hh_lab_instance)

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

    #----------------------------------------
    # Calculate value of crops produced
    # First create list containing only instances of crops
    crop_purch_sales = []
    for good in hh_purchases_sales:
        if good.category == 'crop':
            crop_purch_sales.append(good)
        else:
            continue

    # Calculate value of crops produced on a yearly basis
    all_management_crops_value_dic = {}
    for management_type, calc_methods in crop_data.items():
        fr_crop_sales_value = {}
        for method, crops in calc_methods.items():
            all_yrs_crop_sale_value = []
            for year in crops:
                yearly_crop_sales_value = {}
                for single_crop_name, single_crop_yield in year.items():
                    for good in crop_purch_sales:
                        if good.name == single_crop_name:
                            # Only calculating for dry season just now
                            # Assume input is in ETB/$ per kg, so multiply by 1000 to get ETB/$ per tonne
                            value_of_good = (good.dryseas_sale_price * 1000) * single_crop_yield
                            value_of_good_dic = {single_crop_name : value_of_good}
                            yearly_crop_sales_value.update(value_of_good_dic)
                        else:
                            continue
                total_sales = sum(yearly_crop_sales_value.values())
                yearly_crop_sales_value.update({'Total Crop Sales': total_sales})
                all_yrs_crop_sale_value.append(yearly_crop_sales_value)
            fr_crop_sales_value.update({method : all_yrs_crop_sale_value})
        all_management_crops_value_dic.update({management_type: fr_crop_sales_value})

    # ----------------------------------------
    # Calculate dry and wet season fixed sales (i.e. those taken from excel input)
    dry_seas_fixed_sales_total = purch_sales_df['dryseas_sales_value'].sum()
    wet_seas_fixed_sales_total = purch_sales_df['wetseas_sales_value'].sum()

    # ----------------------------------------
    # Calculate value of time for each household member undertaking agricultural activities (including dung collection)
    # and other activities (collecting water, firewood, cooking)
    # Total working hours is currently total hours awake NEED TO CHANGE?
    household_working_hours = []
    household_ag_labour_value = []
    household_dom_labour_value = []
    for person_type in hh_members:
        household_working_hours.append(person_type.value_of_labour_year)
        household_ag_labour_value.append(person_type.agricultural_labour_calc())
        household_dom_labour_value.append(person_type.domestic_labour_calc())

    total_hh_working_hours = sum(household_working_hours)
    total_hh_ag_value = sum(household_ag_labour_value)
    total_dom_labour_value = sum(household_dom_labour_value)

    #----------------------------------------
    # Equation to calculate net household income for each year in the forward run, and based on the three crop calc
    # methods
    # DAP and Urea not included yet
    all_subareas_full_hh_dic = {}
    for subarea, data in all_management_crops_value_dic.items():
        calc_method_dic = {}
        for calc_method, fr_years in data.items():
            fr_total_hh_income = []
            for year in fr_years:
                total_hh_income = year['Total Crop Sales'] - total_hh_ag_value - total_dom_labour_value + \
                                  total_hh_working_hours
                fr_total_hh_income.append(total_hh_income)
            calc_method_dic.update({calc_method : fr_total_hh_income})
        all_subareas_full_hh_dic.update({subarea : calc_method_dic})

    # ----------------------------------------
    # Equation to calculate per capita consumption. Dummy variables created for now
    # Only using variables of household income, total livestock units, and land owned

    # Alpha values (allow these to be input by user: update GUI)
    # Intercept
    alpha_0 = 9.194
    # Full Household income
    alpha_1 = 0.0154
    # Land
    alpha_2 = 0.0351
    # Land squared
    alpha_3 = -0.0000816
    # Total land utilised
    alpha_4 = 0.0211
    # Total land utilised squared
    alpha_5 = -0.000396
    # Log - Household size adult equivalents
    alpha_6 = -0.399
    # Regional price index
    alpha_7 = 1

    # Pull these values from elsewhere in model
    # Livestock
    tlu = 10
    tlu_squared = tlu * tlu
    # Land utilised
    land = 1000
    land_squared = land * land
    # Size of household in adult equivalents - how to deal with children (1/2 of adult?)
    household_size = 4.2
    household_size_log = numpy.log(household_size)

    # Use Full Household income for each year for each calc method and subarea
    all_subareas_pcc = {}
    for subarea, calc_methods in all_subareas_full_hh_dic.items():
        calc_method_dic = {}
        for calc_method, data in calc_methods.items():
            fr_pcc = []
            for year in data:
                # year is FHH for each year
                year_pcc = alpha_0 + (alpha_1 * year) + (alpha_2 * land) + (alpha_3 * land_squared) + \
                           (alpha_4 * tlu) + (alpha_5 * tlu_squared) + (alpha_6 * household_size_log) + alpha_7
                fr_pcc.append(year_pcc)
            calc_method_dic.update({calc_method : fr_pcc})
        all_subareas_pcc.update({subarea : calc_method_dic})




    print('Economics Calcs completed')
    return
