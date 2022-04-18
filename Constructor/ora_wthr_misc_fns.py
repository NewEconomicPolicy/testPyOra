#-------------------------------------------------------------------------------
# Name:        ora_wthr_misc_fns.py
# Purpose:     additional functions for getClimGenNC.py
# Author:      s03mm5
# Created:     08/02/2019
# Licence:     <your licence>
# Description:
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'ora_wthr_misc_fns.py'
__author__ = 's03mm5'

from os.path import isfile
from csv import reader, Sniffer
from math import ceil

ERROR_STR = '*** Error *** '
WARNING_STR = '*** Warning *** '
GRANULARITY = 120
FARMING_TYPES = {'LG': 'Livestock grazing', 'MR': 'Mixed rotation'}
CLIMATE_TYPES = {'A': 'Arid/semi-arid', 'H': 'humid/sub-humid', 'T': 'Tropical highlands or temperate'}

def prod_system_to_descr(prod_system):
    '''

    '''
    psys2 = prod_system[:2]
    if psys2 in FARMING_TYPES:
        sys_descr = FARMING_TYPES[psys2]
        clim_type = prod_system[2]
        if clim_type in CLIMATE_TYPES:
            sys_descr += ' - ' + CLIMATE_TYPES[clim_type]
    else:
        sys_descr = prod_system.title()

    return sys_descr

def read_csv_wthr_file(csv_fn, w_view_csv = None, w_csv_dscr = None):
    '''
    read and validate CSV file of weather
    could use Multiple Char Separator in read_csv in Pandas
        see: https://datascientyst.com/use-multiple-char-separator-read_csv-pandas/
    '''
    csv_valid_flag = False
    pettmp = {'precip': [], 'tair': []}

    if not isfile(csv_fn):
        mess = 'does not exist'
        if w_view_csv is not None:
            w_view_csv.setEnabled(False)
    else:
        if w_view_csv is not None:
            w_view_csv.setEnabled(True)

        with open(csv_fn, 'r') as fobj:
            dialect = Sniffer().sniff(fobj.read(1024))
        delim = dialect.delimiter       # "delimiter" is a 1-character string

        with open(csv_fn, 'r') as fobj:
            wthr_reader = reader(fobj, delimiter = delim)
            hdr = next(wthr_reader)   # skip header
            for row in wthr_reader:
                year = int(row[2])
                pettmp['precip'].append(float(row[0]))
                pettmp['tair'].append(float(row[1]))

        # validate inputs
        # ===============
        print('Read ' + csv_fn)
        nmnths_read = len(pettmp['precip'])
        nyears = round(nmnths_read / 12)
        mess = '{} years'.format(nyears)
        csv_detail = 'Read {} years of data'.format(nyears)
        if nmnths_read < 12:
            print(ERROR_STR + csv_detail + ' - should be at least 12')
        else:
            nmnths_srpls = nmnths_read % 12
            if nmnths_srpls > 0:
                print(ERROR_STR + '12 should be a factor of number of months - read {} surplus months'.format(nmnths_srpls))
            else:
                csv_valid_flag = True

    if w_csv_dscr is not None:
        w_csv_dscr.setText(mess)    # post detail

    return csv_valid_flag, pettmp

def fetch_csv_wthr(csv_fn, nyrs_ss, nyrs_fwd):
    """
    read and check weather data from a CSV file
    stretch weather to fulfill total number of years
    """
    func_name =  __prog__ + ' read_csv_wthr'

    csv_valid_flag, pettmp = read_csv_wthr_file(csv_fn)
    if not csv_valid_flag:
        return None

    nmnths_read = len(pettmp['precip'])

    pettmp_strtch = {'precip': [], 'tair': []}
    pettmp_ss = {'precip': [], 'tair': []}
    pettmp_fwd = {'precip': [], 'tair': []}

    nmnths_rqrd = 12 * (nyrs_ss + nyrs_fwd)
    print('Total number of months required {} for run, read {} months'.format(nmnths_rqrd, nmnths_read))

    # stretch data if necessary to cover steady state and forward run
    # =======================================================#=======
    nstrtch = ceil(nmnths_rqrd / nmnths_read)
    if nstrtch > 1:
        for ic in range(nstrtch):
            for metric in pettmp:
                pettmp_strtch[metric] += pettmp[metric]

        # overwrite with stretched
        # ========================
        for metric in pettmp:
            pettmp[metric] = pettmp_strtch[metric]

    # stanza to discard surplus
    # =========================
    nmnths_read = len(pettmp['tair'])
    nmnths_diff = nmnths_read - nmnths_rqrd
    if nmnths_diff > 0:
        for metric in pettmp:
            pettmp[metric] = pettmp[metric][:-nmnths_diff]
    elif nmnths_diff < 0:
        mess = ERROR_STR + 'problem in ' + func_name
        print(mess + ' stretch failed - months read: {}\trequired'.format(nmnths_read, nmnths_rqrd))
        return None

    # split into steady state and forward run
    # =======================================
    nmnths_ss = 12 * nyrs_ss
    nmnths_fwd = 12 * nyrs_fwd
    for metric in pettmp:
        pettmp_ss[metric] = pettmp[metric][:nmnths_ss]
        pettmp_fwd[metric] = pettmp[metric][nmnths_ss:nmnths_fwd]

    return len(pettmp_ss[metric]), pettmp_ss, len(pettmp_fwd[metric]), pettmp_fwd

def _write_coords_for_key(mess, climgen, proximate_keys, lookup_key, func_name):

    # should go in log file - TODO
    gran_lat, gran_lon = proximate_keys[lookup_key]
    latitude  = 90 - gran_lat/GRANULARITY
    longitude = gran_lon/GRANULARITY - 180
    mess += ' Lat: {}\tGran lat: {}\tLon: {}\tGran lon: {}\tin {}'.format(latitude, gran_lat, longitude, gran_lon,
                                                                                                        func_name)
    climgen.lggr.info(mess)

    return

def associate_climate(site_rec, climgen, pettmp_hist, pettmp_fut):
    """
    this function associates each soil grid point with the most proximate climate data grid cell
    at the time of writing (Dec 2015) HWSD soil data is on a 30 arc second grid whereas climate data is on 30 or 15 or
     7.5 arc minute grid i.e. 0.5 or 0.25 or 0.125 of a degree
    """
    func_name =  __prog__ + ' associate_climate'

    proximate_keys = {}
    gran_lat_cell, gran_lon_cell, latitude, longitude, dummy, dummy = site_rec
    metric_list = pettmp_fut.keys()

    # TODO: find a more elegant methodology
    # =====================================
    for lookup_key in pettmp_hist['precip']:
        if pettmp_fut['precip'][lookup_key] == None or pettmp_fut['tair'][lookup_key] == None or \
                    pettmp_hist['precip'][lookup_key] == None or pettmp_fut['tair'][lookup_key] == None:
            continue
        else:
            slat, slon = lookup_key.split('_')
            gran_lat = int(slat)
            gran_lon = int(slon)

            # situation where grid cell is coincidental with weather cell
            # ===========================================================
            if gran_lat == gran_lat_cell and gran_lon == gran_lon_cell:
                climgen.lggr.info('Cell with lookup key ' + lookup_key + ' is coincidental with weather cell')
                pettmp_out = {}
                for metric in pettmp_fut.keys():
                    pettmp_out[metric] = list([pettmp_hist[metric][lookup_key], pettmp_fut[metric][lookup_key]])
                return pettmp_out
            else:
                proximate_keys[lookup_key] = list([gran_lat, gran_lon])

    # return empty dict if no proximate keys (unlikely)
    # =================================================
    if len(proximate_keys) == 0:
        print('\nNo weather keys assigned for site record with granular coordinates: {} {}\tand lat/lon: {} {}'
                                        .format(gran_lat_cell, gran_lon_cell, round(latitude,4), round(longitude,4)))
        return {}

    '''
    use the minimum distance to assign weather for specified grid cell
    '''

    # first stanza: calculate the squares of the distances in granular units between the grid cell and weathers cells
    # =============
    dist = {}
    total_dist = 0
    for lookup_key in proximate_keys:
        gran_lat, gran_lon = proximate_keys[lookup_key]
        # _write_coords_for_key('\t', proximate_keys, lookup_key, func_name)

        dist[lookup_key] = (gran_lat - gran_lat_cell)**2 + (gran_lon - gran_lon_cell)**2
        total_dist += dist[lookup_key]

    # find key corresponding to the minimum value using conversions to lists
    # ======================================================================
    minval = sorted(dist.values())[0]
    lookup_key = list(dist.keys())[list(dist.values()).index(minval)]
    _write_coords_for_key('Selected weather key', climgen, proximate_keys, lookup_key, func_name)

    #
    pettmp_final = {}
    for metric in metric_list:
        pettmp_final[metric] = list([pettmp_hist[metric][lookup_key], pettmp_fut[metric][lookup_key]])

    # New stanza to facilitate PyOrator weather extraction
    # ====================================================

    indx_strt_fut = climgen.indx_strt_fut

    indx_strt_ss = climgen.indx_strt_ss
    indx_end_ss = climgen.indx_end_ss

    indx_strt_fwd = climgen.indx_strt_fwd
    indx_end_fwd = climgen.indx_end_fwd

    pettmp_ss = {}
    pettmp_fwd = {}
    for metric in pettmp_final:
        pettmp_all_yrs = pettmp_final[metric][0] + pettmp_final[metric][1][indx_strt_fut:]
        pettmp_ss[metric] = pettmp_all_yrs[indx_strt_ss:indx_end_ss]
        pettmp_fwd[metric] = pettmp_all_yrs[indx_strt_fwd:indx_end_fwd]

    return len(pettmp_ss[metric]), pettmp_ss, len(pettmp_fwd[metric]), pettmp_fwd

def check_clim_nc_limits(form, weather_resource, bbox_aoi = None):

    """
    this function makes sure that the specified bounding box lies within extent of the requested weather dataset
    NB lats run from North to South
        lons run from West to East
    """
    func_name =  __prog__ + ' check_clim_nc_limits'

    limits_ok_flag = True

    # CRU covers the globe
    # ====================
    if weather_resource == 'CRU':
        return limits_ok_flag
    #
    wthr_set_name = form.weather_set_linkages[weather_resource][0]

    lon_ur_aoi = float(form.w_ur_lon.text())
    lat_ur_aoi = float(form.w_ur_lat.text())
    if form.version == 'HWSD_grid':
        lon_ll_aoi = float(form.w_ll_lon.text())
        lat_ll_aoi = float(form.w_ll_lat.text())
    else:
        lon_ll_aoi = lon_ur_aoi
        lat_ll_aoi = lat_ur_aoi

    lat_ur_dset = form.weather_sets[wthr_set_name]['lat_ur']
    lon_ur_dset = form.weather_sets[wthr_set_name]['lon_ur']
    lat_ll_dset = form.weather_sets[wthr_set_name]['lat_ll']
    lon_ll_dset = form.weather_sets[wthr_set_name]['lon_ll']

    # similar functionality in lu_extract_fns.py in LU_extract project
    # ================================================================
    if (lon_ll_dset < lon_ll_aoi and lon_ur_dset > lon_ur_aoi) and \
                    (lat_ll_dset < lat_ll_aoi and lat_ur_dset > lat_ur_aoi):
        print('AOI lies within ' + weather_resource + ' weather dataset')
    else:
        print('AOI lies outwith ' + weather_resource + ' weather dataset - LL long/lat: {} {}\tUR long/lat: {} {}'
              .format(lon_ll_dset, lat_ll_dset, lon_ur_dset, lat_ur_dset))
        limits_ok_flag = False

    return limits_ok_flag
