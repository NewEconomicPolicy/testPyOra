#-------------------------------------------------------------------------------
# Name:        weather_datasets.py
# Purpose:     script to create weather object and other functions
# Author:      Mike Martin
# Created:     23/02/2021
# Licence:     <your licence>
# Description:
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'weather_datasets.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
from os.path import join, normpath, isdir
import cftime
from netCDF4 import Dataset, num2date
from glob import glob

GRANULARITY = 120
MONTH_NAMES_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

sleepTime = 5

def _fetch_weather_nc_parms(nc_fname, weather_resource, resol_time, scenario):
    '''
    create object describing weather dataset characteristics
    '''

    # standard names
    # ==============
    time_var_name = 'time'
    if weather_resource == 'NASA' or weather_resource[0:5] == 'EObs_' or weather_resource[0:8] == 'ClimGen_':
        lat = 'latitude'
        lon = 'longitude'
    else:
        lat = 'lat'
        lon = 'lon'

    nc_fname = normpath(nc_fname)
    nc_dset = Dataset(nc_fname, 'r')
    time_var = nc_dset.variables[time_var_name]
    if 'calendar' in time_var.ncattrs():
        calendar_attr = time_var.calendar
    else:
        calendar_attr = 'standard'

    lat_var = nc_dset.variables[lat]
    lon_var = nc_dset.variables[lon]
    lat_frst = float(lat_var[0])
    lon_frst = float(lon_var[0])
    lat_last = float(lat_var[-1])
    lon_last = float(lon_var[-1])

    if lat_last > lat_frst:
        lat_ll = lat_frst; lat_ur = lat_last
    else:
        lat_ll = lat_last; lat_ur = lat_frst

    if lon_last > lon_frst:
        lon_ll = lon_frst; lon_ur = lon_last
    else:
        lon_ll = lon_last; lon_ur = lon_frst

    # resolutions
    # ===========
    resol_lon = (lon_var[-1] - lon_var[0])/(len(lon_var) - 1)
    resol_lat = (lat_var[-1] - lat_var[0])/(len(lat_var) - 1)
    if abs(resol_lat) != abs(resol_lon):
        print('Warning - weather resource {} has different lat/lon resolutions: {} {}'
                                                        .format(weather_resource, resol_lat, resol_lon))

    # Get the start and end date of the time series (as datetime objects):
    # ====================================================================
    if weather_resource[0:8] == 'ClimGen_':
        # print(weather_resource + ' future time units attribute: ' + time_var.units)
        start_year = int(time_var.units.split(' ')[-1])
        end_year = start_year + int(len(time_var)/12) - 1
    else:
        time_var_units = time_var.units
        start_day = time_var[0]
        try:
            start_date = num2date(start_day, units = time_var_units, calendar = calendar_attr)
        except (TypeError) as e:
            print('Error deriving start and end year for dataset: ' + nc_fname)
            return None

        end_day = int(time_var[-1])
        end_date = num2date(end_day, units = time_var_units, calendar = calendar_attr)
        start_year = start_date.year
        end_year = end_date.year

    # use list comprehension to convert to floats
    # ===========================================
    longitudes = [round(float(longi),8) for longi in lon_var]
    latitudes =  [round(float(lati),8) for lati in lat_var]
    nc_dset.close()

    # construct weather_resource
    # ==========================
    wthr_rsrc = {'year_start': start_year,  'year_end': end_year,
            'resol_lat': resol_lat, 'lat_frst': lat_frst, 'lat_last': lat_last, 'lat_ll': lat_ll, 'lat_ur': lat_ur,
            'resol_lon': resol_lon, 'lon_frst': lon_frst, 'lon_last': lon_last, 'lon_ll': lon_ll, 'lon_ur': lon_ur,
            'longitudes': longitudes, 'latitudes': latitudes,
            'resol_time': resol_time,  'scenario': scenario}

    print('{} start and end year: {} {}\tresolution: {} degrees'
            .format(weather_resource, wthr_rsrc['year_start'],  wthr_rsrc['year_end'], abs(wthr_rsrc['resol_lat'])))

    return wthr_rsrc

def read_weather_dsets_detail(form):
    '''
    ascertain the year span for historic datasets
    TODO: replace with approach adopted for Site Specific version of Global Ecosse
    '''

    # weather set linkages
    # ====================
    form.amma_2050_allowed_gcms = {}
    weather_resources_generic = list([])
    weather_set_linkages = {}
    wthr_sets = {}

    form.weather_resources_generic = weather_resources_generic
    form.weather_set_linkages = weather_set_linkages
    form.wthr_sets = wthr_sets
    form.wthr_settings_prev = {}

    if hasattr(form, 'settings'):
        wthr_dir = form.settings['wthr_dir']
    else:
        wthr_dir = form.setup['wthr_dir']

    if wthr_dir is None:
        return None

    # check NASA monthly
    # ==================
    generic_resource = 'NCAR_CCSM4'
    ncar_mnthly_dir  = wthr_dir + '\\NCAR_CCSM4\\Monthly'
    if isdir(ncar_mnthly_dir):
        wthr_rsrc = 'NCAR_CCSM4'
        ncar_fnames = glob(ncar_mnthly_dir + '\\rcp26\\*_Amon*.nc')
        if len(ncar_fnames) > 0:
            wthr_sets[wthr_rsrc] = _fetch_weather_nc_parms(ncar_fnames[0], wthr_rsrc, 'Monthly', 'historic')
            wthr_sets[wthr_rsrc]['base_dir']   = ncar_mnthly_dir
            wthr_sets[wthr_rsrc]['ds_precip']  = ncar_fnames[0]
            wthr_sets[wthr_rsrc]['ds_tas']     = ncar_fnames[1]
            weather_resources_generic.append(generic_resource)
            weather_set_linkages[generic_resource] = list([wthr_rsrc, wthr_rsrc])
        else:
            print('No ' + wthr_rsrc + ' monthly datasets present in ' + ncar_mnthly_dir)

    # check CRU historic
    # ==================
    generic_resource = 'CRU'
    cru_flag = False
    valid_wthr_dset_rsrces = []
    cru_dir  = wthr_dir + '\\CRU_Data'
    if isdir(cru_dir):
        wthr_rsrc = 'CRU_hist'
        cru_fnames = glob(cru_dir + '/cru*dat.nc')
        if len(cru_fnames) > 0:
            wthr_sets[wthr_rsrc] = _fetch_weather_nc_parms(cru_fnames[0], wthr_rsrc, 'Monthly', 'historic')
            wthr_sets[wthr_rsrc]['base_dir']   = cru_dir
            wthr_sets[wthr_rsrc]['ds_precip']  = cru_fnames[0]
            wthr_sets[wthr_rsrc]['ds_tas']     = cru_fnames[1]
            wthr_sets[wthr_rsrc]['precip'] = 'pre'
            wthr_sets[wthr_rsrc]['tas']    = 'tmp'
            valid_wthr_dset_rsrces.append(wthr_rsrc)
            cru_flag = True
        else:
            print('No CRU historic datasets present in ' + cru_dir)

    # check ClimGen
    # =============
    climgen_flag = False
    for dset_scenario in list(['A1B','A2','B1','B2']):
        climgen_dir = join(wthr_dir, 'ClimGen', dset_scenario)
        wthr_rsrc = 'ClimGen_' + dset_scenario
        if isdir(climgen_dir):
            climgen_fnames = glob(climgen_dir + '\\*.nc')
            if len(climgen_fnames) > 0:
                wthr_sets[wthr_rsrc] = _fetch_weather_nc_parms(climgen_fnames[0], wthr_rsrc, 'Monthly', dset_scenario)
                wthr_sets[wthr_rsrc]['base_dir']   = climgen_dir
                wthr_sets[wthr_rsrc]['ds_precip']  = climgen_fnames[0]
                wthr_sets[wthr_rsrc]['ds_tas']     = climgen_fnames[1]
                wthr_sets[wthr_rsrc]['precip'] = 'precipitation'
                wthr_sets[wthr_rsrc]['tas'] = 'temperature'
                valid_wthr_dset_rsrces.append(wthr_rsrc)
                climgen_flag = True
        else:
            print('ClimGen datasets not present in ' + climgen_dir)

    if cru_flag and climgen_flag:
        weather_resources_generic.append(generic_resource)
        weather_set_linkages[generic_resource] = valid_wthr_dset_rsrces
    else:
        print('CRU historic or future datasets incomplete in ' + climgen_dir + 'or' + cru_dir)

    form.weather_resources_generic = weather_resources_generic
    form.weather_set_linkages = weather_set_linkages

    print('')
    return wthr_sets
