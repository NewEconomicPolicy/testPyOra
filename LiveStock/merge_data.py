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
    Function to merge together previous harvest and land use info from ORATOR A1a
    TODO: Change this so that it uses crop data created in PyORATOR rather than EXCELORATOR
    '''
    harvest_data = orator_obj
    subarea_crop_prod_change = []
    for subarea in harvest_data:
        crop_model = harvest_data[subarea]
        crops = crop_model.data['crop_name']
        typ_yield = crop_model.data['yld_ann_typ']
        yld_n_lim = crop_model.data['yld_n_lim']
        zipped = (typ_yield + yld_n_lim)
        dic_list = (crops, zipped)
        df = DataFrame(dic_list)
        subarea_crop_prod_change.append(df)

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