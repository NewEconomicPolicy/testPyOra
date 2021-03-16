#-------------------------------------------------------------------------------
# Name:        merge_data.py
# Purpose:     Functions to create TODO
# Author:      Dave Mcbey
# Created:     22/03/2020
# Description:
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'merge_data.py'
__version__ = '0.0.0'
__author__ = 's02dm4'

from pandas import concat, DataFrame


def merge_harvest_land_use(orator_obj):

    '''
    Function to create list of list of dictionaries; each list of dictionaries contains annual crop yields
    using N limitation, Zaks, and Miami model calculations.
    '''
    harvest_data = orator_obj
    subarea_crop_prod_change = []
    for subarea in harvest_data:
        crop_model = harvest_data[subarea]

        # Create dictionary with keys the names of crops and values their yield in typical years
        crops = crop_model.data['crop_name']
        typ_yield = crop_model.data['yld_ann_typ']
        zipped = (crops, typ_yield)
        typ_prod_dic = dict(zip(crops, typ_yield))

        # Use equation 4.0.1 to calculate proportion of yield in atypical vs typical years, using various methods
        # First, get a list with only forward run crops in it
        crops_per_year = crop_model.data['crops_ann']
        ss_years = crop_model.nyears_ss
        fr_crops_per_year = crops_per_year[ss_years:]

        # Get each years crop production data into a list of dictionaries
        yld_n_lim = crop_model.data['yld_ann_n_lim']
        yld_n_lim_dic = []
        for year in fr_crops_per_year:
            crop_yield_dic = {crop : 0 for crop in year}
            temp_dic = {}
            for crop in crop_yield_dic:
                crop_yield_dic_values = {crop : yld_n_lim[0]}
                del yld_n_lim[0]
                temp_dic.update(crop_yield_dic_values)
            yld_n_lim_dic.append(temp_dic)

        yld_zaks = crop_model.data['yld_ann_zaks']
        yld_zaks_dic = []
        for year in fr_crops_per_year:
            crop_yield_dic = {crop : 0 for crop in year}
            temp_dic = {}
            for crop in crop_yield_dic:
                crop_yield_dic_values = {crop : yld_zaks[0]}
                del yld_zaks[0]
                temp_dic.update(crop_yield_dic_values)
            yld_zaks_dic.append(temp_dic)

        yld_miami = crop_model.data['yld_ann_miami']
        yld_miami_dic = []
        for year in fr_crops_per_year:
            crop_yield_dic = {crop : 0 for crop in year}
            temp_dic = {}
            for crop in crop_yield_dic:
                crop_yield_dic_values = {crop : yld_miami[0]}
                del yld_miami[0]
                temp_dic.update(crop_yield_dic_values)
            yld_miami_dic.append(temp_dic)

        # Calculate the change in yield using each of the three methods
        n_lim_harv_change = []
        for year in yld_n_lim_dic:
            harv_yld_dic = {}
            for key, value in year.items():
                if key in typ_prod_dic:
                    harv_chan = typ_prod_dic[key] * value / 100
                    temp_dic = {key : harv_chan}
                    harv_yld_dic.update(temp_dic)
            n_lim_harv_change.append(harv_yld_dic)

        zaks_harv_change = []
        for year in yld_zaks_dic:
            harv_yld_dic = {}
            for key, value in year.items():
                if key in typ_prod_dic:
                    harv_chan = typ_prod_dic[key] * value / 100
                    temp_dic = {key : harv_chan}
                    harv_yld_dic.update(temp_dic)
            zaks_harv_change.append(harv_yld_dic)

        miami_harv_change = []
        for year in yld_miami_dic:
            harv_yld_dic = {}
            for key, value in year.items():
                if key in typ_prod_dic:
                    harv_chan = typ_prod_dic[key] * value / 100
                    temp_dic = {key : harv_chan}
                    harv_yld_dic.update(temp_dic)
            miami_harv_change.append(harv_yld_dic)

        list_of_dics = [n_lim_harv_change, zaks_harv_change, miami_harv_change]

        subarea_crop_prod_change.append(list_of_dics)

    return subarea_crop_prod_change

    '''
    land_use_tran = _transform_land_use_data(orator_obj)

    harvest_land_use_merged = concat([land_use_tran, harvest_data], axis=1)
    
    # Reorder columns to make dataframe more readable; shape is 120,10
    # ================================================================
    harvest_land_use_merged = harvest_land_use_merged[['Last land use', 'Percent prod. last harvest', 'Unnamed: 46',
                                                       'Unnamed: 41', 'Unnamed: 47', 'Unnamed: 42', 'Unnamed: 48',
                                                       'Unnamed: 43', 'Unnamed: 49', 'Unnamed: 44']]
    # Rename columns to make dataframe more readable
    # ==============================================
    harvest_land_use_merged.rename(columns={'Last land use' : 'area_1_crop',
                                                                 'Percent prod. last harvest' : 'area_1_yield_change',
                                                                 'Unnamed: 46' : 'area_2_crop',
                                                                 'Unnamed: 41' : 'area_2_yield_change',
                                                                 'Unnamed: 47' : 'area_3_crop',
                                                                 'Unnamed: 42' : 'area_3_yield_change',
                                                                 'Unnamed: 48' : 'area_4_crop',
                                                                 'Unnamed: 43' : 'area_4_yield_change',
                                                                 'Unnamed: 49' : 'area_5_crop',
                                                                 'Unnamed: 44' : 'area_5_yield_change'}, inplace=True)
    # remove missing data i.e. None and NaN to get rid of extra rows
    # ==============================================================
    harvest_land_use_merged.dropna(inplace=True)
    return harvest_land_use_merged

def _transform_land_use_data(orator_obj):
    Change land use data from key to name of crop

    last_land_use = orator_obj.last_land_use

    last_land_use_transform = last_land_use.replace({1: 'None',
                         2 : 'Grassland' ,
                         3: 'Shrubland',
                         4 : 'Maize',
                         5 : 'Haricot beans',
                         6 : 'Teff',
                         7 : 'Finger Millet',
                         8 : 'Pepper',
                         9 : 'Coffee',
                         10 : 'Chat',
                         11 : 'Tomatoes',
                         12 : 'Cabbage',
                         13 : 'Wheat',
                         14 : 'Sorghum'
                         })
    return last_land_use_transform

def get_atypical_years_crop_prod():

    Calculate the change in crop production for each crop for atypical years
    
    harv_land_use_merged = _transform_land_use_data()
    harv_land_use_merged["Crop A"] = ""
    harv_land_use_merged["Tot production crop A"] = ""
    harv_land_use_merged["Crop B"] = ""
    harv_land_use_merged["Tot production crop B"] = ""
    harv_land_use_merged["Crop C"] = ""
    harv_land_use_merged["Tot production crop C"] = ""
    harv_land_use_merged["Crop D"] = ""
    harv_land_use_merged["Tot production crop D"] = ""
    harv_land_use_merged["Crop E"] = ""
    harv_land_use_merged["Tot production crop E"] = ""

    harv_land_use_merged.to_csv('harv_land_use_data_merged.csv')
'''