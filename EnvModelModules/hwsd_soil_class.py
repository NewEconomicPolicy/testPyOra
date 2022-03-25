"""
#-------------------------------------------------------------------------------
# Name:        hwsd_soil_class.py
# Purpose:     class definition for soils for a grid cell
# Author:      Mike Martin
# Created:     13/06/2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#
"""

__prog__ = 'hwsd_soil_class.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

from operator import itemgetter
from copy import copy
import copy

granularity = 120

def _gran_coords_from_lat_lon(lat, lon):
    '''

    '''
    granlat = round((90.0 - lat)*granularity)
    granlon = round((180.0 + lon)*granularity)

    return int(granlat), int(granlon)


class HWSD_soil_defn(object,):

    def __init__(self, lgr):

        '''
        Each meta-cell comprises one or more HWSD mu global keys with each key paired with the number
        of HWSD cells with that mu global
        Call max(iterable, key=dict.get) with the same dictionary as both iterable and dict to find the
        key paired with the max value. Somewhat similar to list comprehension.
        '''

        class_name =  'HWSD_soil_defn'

        # define current cell object
        # ==========================
        self.lgr  = lgr
        self.area = None
        self.lat  = None
        self.lon  = None
        self.gran_lat = None
        self.gran_lon = None
        self.cell_hwsd_df    = None
        self.soil_recs       = None
        self.mu_global_pairs = None     # dictionary of mu_globals and corresponding number of HWSD cells

    def populate(self, lat, lon, area, cell_hwsd_df, mu_global_pairs, soil_recs):

        self.gran_lat, self.gran_lon = _gran_coords_from_lat_lon(lat, lon)
        self.area = area
        self.lat  = lat
        self.lon  = lon
        self.cell_hwsd_df = cell_hwsd_df
        self.soil_recs  = soil_recs
        self.mu_global_pairs = mu_global_pairs

        mess = 'Cell with Lat: {}\tLon: {}'.format(lat, lon)
        mess += '\thas {} rows and {} columns of HWSD grid'.format(cell_hwsd_df.shape[0], cell_hwsd_df.shape[1])
        mess += '\tN soil recs: {}'.format(len(soil_recs))
        self.lgr.info(mess)

    def simplify_soil_defn(self, use_dom_soil_flag, use_high_cover_flag, bad_muglobals):

        self.soil_recs = _simplify_soil_recs(self.lgr, bad_muglobals, self.soil_recs, use_dom_soil_flag)

        # collapse the cell mu_global dictionary into a single entry with the same total number of HWSD cells
        # ===================================================================================================
        if use_high_cover_flag:
            mu_global_pairs = self.mu_global_pairs
            nsize = sum(mu_global_pairs.values())
            try:
                mu_global = max(mu_global_pairs, key = mu_global_pairs.get)
            except ValueError as err:
                print('\n*** Error *** ' + str(err))
                return None

            self.mu_global_pairs = {mu_global: nsize}
            return 0

def _simplify_soil_recs(lgr, bad_muglobals, soil_recs, use_dom_soil_flag):
    """
    compress soil records if duplicates are present
    simplify soil records if requested
    each mu_global points to a group of soils
    a soil group can have up to ten soils
    """
    func_name =  __prog__ + ' _simplify_soil_recs'

    # clean out 7000, 7003
    # ====================
    for mu_global in bad_muglobals:
        if mu_global in soil_recs:
            del soil_recs[mu_global]

    num_raw = 0 # total number of sub-soils
    num_compress = 0 # total number of sub-soils after compressions

    new_soil_recs = {}
    for mu_global in soil_recs:

        # no processing necessary
        # =======================
        num_sub_soils = len(soil_recs[mu_global])
        num_raw += num_sub_soils
        if num_sub_soils == 1:
            num_compress += 1
            new_soil_recs[mu_global] = soil_recs[mu_global]
            continue

        # check each soil for duplicates
        # ==============================
        new_soil_group = []
        soil_group = sorted(soil_recs[mu_global])
        if len(soil_group) == 0:
            lgr.info('*** Error *** mu global: {} has empty soil group from in soil_recs: {}'.format(mu_global,
                                                                                         str(soil_recs[mu_global])))
            continue

        first_soil = soil_group[0]
        metrics1 = first_soil[:-1]
        share1   = first_soil[-1]
        for soil in soil_group[1:]:
            metrics2 = soil[:-1]
            share2 =   soil[-1]
            if metrics1 == metrics2:
                share1 += share2
            else:
                new_soil_group.append(metrics1 + [share1])
                metrics1 = metrics2
                share1 = share2

        new_soil_group.append(metrics1 + [share1])
        num_sub_soils = len(new_soil_group)
        num_compress += num_sub_soils
        if num_sub_soils == 1:
            new_soil_recs[mu_global] = new_soil_group
            continue

        if use_dom_soil_flag:
            # assign 100% to the first entry of sorted list
            # =============================================
            dom_soil = sorted(new_soil_group, reverse = True, key = itemgetter(-1))[0]
            dom_soil[-1] = 100.0
            new_soil_recs[mu_global] = list([dom_soil])

    mess = 'Exiting {}\trecords in: {} out: {}'.format(func_name, len(soil_recs),len(new_soil_recs))
    lgr.info(mess + '\tnum raw sub-soils: {}\tafter compression: {}'.format(num_raw, num_compress))
    return new_soil_recs

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