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
from os.path import isfile, normpath, join
from shutil import copyfile
import numpy
from scipy.stats import norm

from ora_excel_read import read_econ_purch_sales_sheet, read_econ_labour_sheet

FNAME_ECONOMICS = 'PurchasesSalesLabour.xlsx'
WARN_STR = '*** Warning *** '

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
    mgmt_dir = form.w_run_dir3.text()
    econ_xls_fname = normpath(join(mgmt_dir, FNAME_ECONOMICS))
    if not isfile(econ_xls_fname):
        try:
            copyfile(form.settings['econ_xls_fn'], econ_xls_fname)
        except FileNotFoundError as err:
            print(err)
            return -1
        else:
            print('Copied economics Excel file ' + FNAME_ECONOMICS + ' from templates')

    purch_sales_df = read_econ_purch_sales_sheet(econ_xls_fname, 'Purchases & Sales', 3)
    purch_sales_df = purch_sales_df.drop(columns=['Units.2','Units.3', 'Units.4', 'Units.5', 'Units.6', 'Units.7',
                                                  'Unnamed: 18'])
    purch_sales_df.columns= ['category', 'name', 'dryseas_pur_pr', 'units', 'dryseas_pur_quant', 'measure',
                             'wetseas_pur_pr', 'wetseas_pur_quant', 'dryseas_sale_pr', 'dryseas_sale_quant',
                             'wetseas_sale_pr', 'wetseas_sale_quant']
    # Calculate value of all sales
    purch_sales_df['dryseas_sales_value'] = purch_sales_df['dryseas_sale_pr'] * purch_sales_df['dryseas_sale_quant']
    purch_sales_df['wetseas_sales_value'] = purch_sales_df['wetseas_sale_pr'] * purch_sales_df['wetseas_sale_quant']

    labour_df = read_econ_labour_sheet(econ_xls_fname, 'Labour', 0)

    # ----------------------------------------
    # Create instances of HouseholdPurchasesSales Class using Dataframe created from excel sheet. Store in list.
    hh_purchases_sales = []
    for index, calcs in purch_sales_df.iterrows():
        hh_ps_instance = HouseholdPurchasesSales(calcs)
        hh_purchases_sales.append(hh_ps_instance)

    # ----------------------------------------
    # Create instances of HouseholdMembers Class using Dataframe created from excel sheet. Store in list.
    hh_members = []
    labour_df = labour_df.iloc[: , 1:]
    for column_name, column_data in labour_df.iteritems():
        hh_lab_instance =  HouseholdMembers(column_name, column_data)
        if hh_lab_instance.number == 0:
            pass
        else:
            hh_members.append(hh_lab_instance)

    # ----------------------------------------
    # Check if crop model has been run
    # If yes > import crop production data for forward run
    # If no > prompt user
    if form.crop_run:
        crop_data = form.crop_production

    else:
        crop_data = {}
        print('No crop data! Please run C and N model first')

    #----------------------------------------
    # Check if livestock model has been run
    # If yes > Import livestock data and get total yearly manure production data for forward run
    # If no > Prompt user
    if form.livestock_run:
        manure_data = form.total_an_prod_all_subareas
        management_type_manure_dic = {}
        for management_type, calcs in manure_data.items():
            calc_method_manure_dic = {}
            for calc_method, livestock in calcs.items():
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
                            # USING DRY SEASON PRICE TO CALCULATE - SHOULD IT BE WET SEASON? OR AVERAGE?
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

    # Collapse all subareas into one to show total crop sales for household
    keys = []
    values = []
    items = all_management_crops_value_dic.items()
    for item in items:
        keys.append(item[0]), values.append(item[1])

    total_crop_sales = {}
    for value in values:
        for man_type, crop_value in value.items():
            if man_type not in total_crop_sales.keys():
                fr_crop_values = []
                for year in crop_value:
                    value = year['Total Crop Sales']
                    fr_crop_values.append(value)
                total_crop_sales.update({man_type : fr_crop_values})
            else:
                fr_crop_values = []
                for year in crop_value:
                    value = year['Total Crop Sales']
                    fr_crop_values.append(value)
                dic_value = total_crop_sales[man_type]
                new_value = [x + y for x, y in zip(fr_crop_values, dic_value)]
                total_crop_sales.update({man_type : new_value})

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
    # Equation to calculate full household income for each year in the forward run, and based on the three crop calc
    # methods
    # DAP and Urea not included yet
    # CHECK THIS EQUATION IS CORRECT
    all_subareas_full_hh_dic = {}
    for calc_method, fr_years in total_crop_sales.items():
        fr_total_hh_income = []
        for year in fr_years:
            # values divided by 1000 to normalise data
            total_hh_income = (year/1000) - (total_hh_ag_value/1000) - (total_dom_labour_value/1000) + \
                              (total_hh_working_hours/1000)
            fr_total_hh_income.append(total_hh_income)
        all_subareas_full_hh_dic.update({calc_method : fr_total_hh_income})

    # ----------------------------------------
    # Calculate values to be used in equations for PCC, food insecurity, and dietary diversity
    # Livestock: Are all livestock worth the same? I.e do cow, pig, chicken all = 1. For now they do
    tlu = 0
    livestock_list = form.livestock_list
    for animal_type in livestock_list:
        animal_type_total = animal_type.number
        tlu = tlu + animal_type_total
    tlu_squared = tlu * tlu

    # Land utilised in Ha (calculated by adding up all subareas)
    land = 0
    for subarea, data in form.all_runs_crop_model.items():
        subarea_area = data.area_ha
        land = land + subarea_area
    land_squared = land * land

    # Size of household in adult equivalents - how to deal with children ( assume 1/2 of adult just now)
    # Using simple equivalence scales
    household_size = 0
    for people in hh_members:
        if people.name == 'Male adults':
            household_size = household_size + people.number
        elif people.name == 'Female adults':
            household_size = household_size + people.number
        elif people.name == 'Male children':
            household_size = household_size + (people.number * 0.5)
        elif people.name == 'Female children':
            household_size = household_size + (people.number * 0.5)
        else:
            print ('Please enter family members in economics sheet as either '
                   'Male adults, Female adults, Male children, or Female children')
            continue
    household_size_log = numpy.log(household_size)

    # ----------------------------------------
    # Equation to calculate PER CAPITA CONSUMPTION
    # Only using variables of household income, total livestock units, and land owned

    # Alpha values for PCC
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

    # Use Full Household income for each year for each calc method to calculate yearly PCC
    farm_pcc = {}
    for calc_method, calcs in all_subareas_full_hh_dic.items():
        fr_pcc = []
        for year in calcs:
                # year is FHI for each year
            year_pcc = alpha_0 + (alpha_1 * year) + (alpha_2 * land) + (alpha_3 * land_squared) + \
                        (alpha_4 * tlu) + (alpha_5 * tlu_squared) + (alpha_6 * household_size_log) + alpha_7
            fr_pcc.append(year_pcc)
        farm_pcc.update({calc_method : fr_pcc})
#    farm_pcc = farm_pcc

    # ----------------------------------------
    # Equation to calculate RELATIVE FOOD INSECURITY. Each year will return value between 0 and 1
    # Only using variables of household income, total livestock units, and land owned

    # Alpha values for RFI
    # Intercept
    alpha_0 = -1.782
    # Full Household income
    alpha_1 = -0.0333
    # Land
    alpha_2 = -0.102
    # Land squared
    alpha_3 = 0.000222
    # Total land utilised
    alpha_4 = -0.008400
    # Total land utilised squared
    # NO DATA SO REMOVED FROM EQUATION
    # alpha_5 = 000000000000000000000000
    # Log - Household size adult equivalents
    alpha_6 = 0.802
    # Regional price index
    # CHECK!!!!
    alpha_7 = 1

    # Use Full Household income for each year for each calc method to calculate yearly relative food insecurity
    farm_rfi = {}
    for calc_method, calcs in all_subareas_full_hh_dic.items():
        fr_rfi = []
        for year in calcs:
                # year is FHI for each year
            year_rfi = alpha_0 + (alpha_1 * year) + (alpha_2 * land) + (alpha_3 * land_squared) + \
                        (alpha_4 * tlu) + (alpha_6 * household_size_log) + alpha_7
            # Calculate probit to return value between 0 and 1
            year_rfi = norm.cdf(year_rfi)
            fr_rfi.append(year_rfi)
        farm_rfi.update({calc_method : fr_rfi})
#    farm_rfi = farm_rfi

    # ----------------------------------------
    # Equation to calculate DIETARY DIVERSITY.
    # Each year will return value that estimates number of food items consumed
    # Only using variables of household income, total livestock units, and land owned

    # Alpha values for Dietary Diversity
    # Intercept
    alpha_0 = 1.782
    # Full Household income
    alpha_1 = 0.000182
    # Land
    alpha_2 = 0.00718
    # Land squared
    alpha_3 = -0.0000185
    # Total land utilised
    alpha_4 = 0.00544
    # Agriculutrual Diversity (Number of crops)
    alpha_5 = 0.0269
    # Log - Household size adult equivalents
    alpha_6 = 0.0784
    # Regional price index
    # CHECK!!!!
    alpha_7 = 1

    # Number of crops grown by household in year
    # Bug in crop model so this is hard coded for now
    number_of_crops = 5
    crop_data = form.all_runs_crop_model
    for subarea, crops in crop_data.items():
        crop_list = crops.data['crops_ann']
        fr_years = crops.nyears_fwd
        crops_fr = crop_list[-fr_years:]

        # Use Full Household income for each year for each calc method to calculate yearly dietary diversity
    farm_diet_div = {}
    for calc_method, calcs in all_subareas_full_hh_dic.items():
        diet_div = []
        for year in calcs:
            # year is FHI for each year
            year_dd = alpha_0 + (alpha_1 * year) + (alpha_2 * land) + (alpha_3 * land_squared) + \
                        (alpha_4 * tlu) + (alpha_5 * number_of_crops) + (alpha_6 * household_size_log) + alpha_7
            diet_div.append(year_dd)
        farm_diet_div.update({calc_method: diet_div})



#    data = {}
#    for calc_method, calcs in all_subareas_full_hh_dic.items():
#        if calc_method == 'n_lim':
#            data.update({'full_hh_income_n_lim' : calcs})
#        elif calc_method == 'zaks':
#            data.update({'full_hh_income_zaks' : calcs})
#        elif calc_method == 'miami':
#            data.update({'full_hh_income_miami': calcs})
    # ----------------------------------------
    # Put all calcs in format that can be read by GUI graph constructor THIS NEEDS TO BE A CLASS OBJECT
    # Start woth full household income

    economics_GUI_class = form.all_farm_livestock_production
    for calc_method, calcs in all_subareas_full_hh_dic.items():
        if calc_method == 'n_lim':
            economics_GUI_class['full_farm'].data['full_hh_income_n_lim'] = calcs
        elif calc_method == 'zaks':
            economics_GUI_class['full_farm'].data['full_hh_income_zaks'] = calcs
        elif calc_method == 'miami':
            economics_GUI_class['full_farm'].data['full_hh_income_miami'] = calcs

    # Add PCC to form object for GUI graph constructor
    for calc_method, calcs in farm_pcc.items():
        if calc_method == 'n_lim':
            economics_GUI_class['full_farm'].data['per_capita_consumption_n_lim'] = calcs
        elif calc_method == 'zaks':
            economics_GUI_class['full_farm'].data['per_capita_consumption_zaks'] = calcs
        elif calc_method == 'miami':
            economics_GUI_class['full_farm'].data['per_capita_consumption_miami'] = calcs

    # Add RFI to form object for GUI graph constructor
    for calc_method, calcs in farm_rfi.items():
        if calc_method == 'n_lim':
            economics_GUI_class['full_farm'].data['relative_food_insecurity_n_lim'] = calcs
        elif calc_method == 'zaks':
            economics_GUI_class['full_farm'].data['relative_food_insecurity_zaks'] = calcs
        elif calc_method == 'miami':
            economics_GUI_class['full_farm'].data['relative_food_insecurity_miami'] = calcs

    # Add dietary diversity to form object for GUI graph constructor
    for calc_method, calcs in farm_diet_div.items():
        if calc_method == 'n_lim':
            economics_GUI_class['full_farm'].data['dietary_diversity_n_lim'] = calcs
        elif calc_method == 'zaks':
            economics_GUI_class['full_farm'].data['dietary_diversity_zaks'] = calcs
        elif calc_method == 'miami':
            economics_GUI_class['full_farm'].data['dietary_diversity_miami'] = calcs

    form.all_farm_livestock_production = economics_GUI_class

    print('Economics calcs completed')
    return
