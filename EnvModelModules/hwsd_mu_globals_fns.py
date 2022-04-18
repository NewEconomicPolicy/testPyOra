"""
#-------------------------------------------------------------------------------
# Name:
# Purpose:     consist of high level functions invoked by main GUI
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#
"""

__prog__ = 'hwsd_mu_globals_fns.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

import locale
from os.path import split
from pandas import read_csv
from numpy import int32, float64

null_value = -9999
big_number = 999.0
nonzero_proportion = 0.75  # threshold proportion of non-zero mu globals for a meta-cell below which centroid is calculated

def meta_cell_centroid(aggre_cell, irow, icol, num_non_zeros, resol_upscale, granularity):

    # work out centroid if there is a significant proportion of sea ie zero values
    irow_sum = 0
    icol_sum = 0
    for ir in range(resol_upscale):
        for ic in range(resol_upscale):
            if aggre_cell[ir,ic] > 0:
                irow_sum += ir
                icol_sum += ic

    irow_ave = irow_sum/num_non_zeros
    icol_ave = icol_sum/num_non_zeros
    # print('irow/icol ave: {} {}'.format(irow_ave, icol_ave))

    gran_lat = irow + irow_ave
    cell_lat = 90.0 - gran_lat/granularity
    gran_lon = icol + icol_ave
    cell_lon = gran_lon/granularity - 180.0

    return gran_lat, gran_lon, cell_lat, cell_lon

class HWSD_mu_globals_csv(object,):

    def __init__(self, form, csv_fname):

        '''
        this object uses pandas to read a file comprising granular lat, granular lon, mu_global, latitude, longitude
        and ascertains its bounding box
        '''
        class_name =  'HWSD_aoi_mu_globals_csv'
        mess = 'Creating class ' + class_name + ' from CSV file ' + csv_fname
        form.lggr.info(mess); print(mess + '\n\t- this may take some time...')

        # read the CSV file
        # =================
        headers = ['gran_lat', 'gran_lon', 'mu_global', 'latitude', 'longitude', 'land_use']
        data_frame = read_csv(csv_fname, sep = ',', names = headers, dtype={'gran_lat': int32, 'gran_lon': int32,
                                                        'mu_global': int32, 'latitude': float64, 'longitude': float64})
        nlines = len(data_frame)
        locale.setlocale(locale.LC_ALL, '')
        nlines_str = locale.format_string("%d", nlines, grouping=True )

        # sort values North to South and West to East
        # ===========================================
        data_frame = data_frame.sort_values(by=["gran_lat", "gran_lon"])

        # determine the largest bbox enclosing the AOI
        lon_ll_aoi = data_frame['longitude'].min()
        lat_ll_aoi = data_frame['latitude'].min()
        lon_ur_aoi = data_frame['longitude'].max()
        lat_ur_aoi = data_frame['latitude'].max()

        mess = 'read and sorted {} lines using pandas'.format(nlines_str)
        form.lggr.info(mess); print(mess)

        mu_global_dict = dict(data_frame['mu_global'].value_counts())

        aoi_label = 'LL: {:.2f} {:.2f}\tUR: {:.2f} {:.2f}\t# cells: {}' \
                                .format(lon_ll_aoi, lat_ll_aoi, lon_ur_aoi, lat_ur_aoi, nlines_str)
        mess = 'Exiting function {} AOI: {}\tCSV file {}\n'.format(class_name, aoi_label, csv_fname)
        form.lggr.info(mess)

        # list file contents
        # ==================
        mu_global_list = list(mu_global_dict.keys())
        dummy, fname_short = split(csv_fname)
        mess = 'HWSD csv file {} has {} unique mu globals'.format(fname_short, len(mu_global_list))
        print(mess);         form.lggr.info(mess)
        # self.soil_recs = hwsd.get_soil_recs(sorted(mu_global_dict.keys())) # sorted key list (of mu_globals)

        # complete object
        # ===============
        self.lon_ll_aoi = lon_ll_aoi
        self.lat_ll_aoi = lat_ll_aoi
        self.lon_ur_aoi = lon_ur_aoi
        self.lat_ur_aoi = lat_ur_aoi
        self.nlines = nlines
        self.mu_global_list = sorted(mu_global_list)
        self.aoi_label = aoi_label
        self.csv_fname = csv_fname
        self.data_frame = data_frame
