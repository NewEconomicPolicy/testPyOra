#-------------------------------------------------------------------------------
# Name:        getClimGenNC.py
# Purpose:     read netCDF files comprising ClimGen data
# Author:      s03mm5
# Created:     01/03/2021
# Licence:     <your licence>
# Description:
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'getClimGenNC.py'
__author__ = 's03mm5'

import netCDF4 as cdf
from math import ceil
from numpy import arange, seterr, ma
import warnings

null_value = -9999
set_spacer_len = 12

numSecsDay = 3600*24
ngranularity = 120
WTHR_RSRC_PERMITTED = list(['CRU'])

class ClimGenNC(object,):

    def __init__(self, lggr, wthr_sets, wthr_rsrc, fut_clim_scen,
                                                        hist_start_year, hist_end_year, sim_start_year, sim_end_year):
        """
        this class has been adapted from Global Ecosse, arguments map as below:
         hist_start_year == strt_yr_ss
         hist_end_year == end_yr_ss
         sim_start_year == strt_yr_fwd
         sim_end_year == end_yr_fwd
        """
        func_name =  __prog__ +  ' ClimGenNC __init__'

        # user choices
        # ============
        if wthr_rsrc not in WTHR_RSRC_PERMITTED:
            raise Exception('Only CRU allowed when creating ClimGenNC object')

        self.wthr_rsrce = wthr_rsrc

        # African Monsoon Multidisciplinary Analysis (AMMA) 2050 datasets
        # ===============================================================
        if wthr_rsrc == 'CRU':
            wthr_set_key = 'ClimGen_' + fut_clim_scen
            if wthr_set_key not in wthr_sets:
                print('key {} not in weather sets in function {} - cannot continue'.format(wthr_set_key, func_name))
                return
            hist_weather_set = wthr_sets['CRU_hist']
            fut_weather_set  = wthr_sets['ClimGen_' + fut_clim_scen]
            lat = 'latitude'
            lon = 'longitude'
        else:
            raise Exception('weather resource ' + wthr_rsrc + ' not recognised in ' + func_name + ' - cannot continue')

        # make sure start and end years are within dataset limits
        # =======================================================
        hist_start_year = max(hist_weather_set['year_start'], hist_start_year)
        hist_end_year   = min(hist_weather_set['year_end'], hist_end_year)

        self.ave_weather_flag = False
        num_hist_years = hist_end_year - hist_start_year + 1
        self.num_hist_years = num_hist_years
        self.hist_start_year = hist_start_year
        self.hist_end_year   = hist_end_year
        self.months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        self.fut_clim_scen = fut_clim_scen

        # future data
        # ===========
        self.fut_precip_fname = fut_weather_set['ds_precip']
        self.fut_tas_fname = fut_weather_set['ds_tas']
        self.resolution_lon = fut_weather_set['resol_lon']
        self.resolution_lat = fut_weather_set['resol_lat']

        # granularity
        # ===========
        self.lon = lon
        self.lat = lat
        self.lon_min = fut_weather_set['lon_ll']
        self.lat_min = fut_weather_set['lat_ll']
        self.longitudes = fut_weather_set['longitudes']
        self.latitudes =  fut_weather_set['latitudes']
        self.pettmp = {}        # dictionary whose keys will reference the climate grid, pt_grid
        self.lggr = lggr

        # past (monthly) data
        # ===================
        self.hist_precip_fname = hist_weather_set['ds_precip']
        self.hist_tas_fname    = hist_weather_set['ds_tas']
        self.latitudes_hist    = hist_weather_set['latitudes']

        # New stanza to facilitate option when user selects "use average weather"
        # =======================================================================
        num_years_str = '{:0=3d}'.format(num_hist_years)
        self.met_ave_file = 'met' + num_years_str + 'a.txt'

        # only the years for which we we have historic data will be taken into account
        self.num_ave_wthr_years = hist_end_year - hist_start_year + 1

        # might need these later
        # =====================
        self.sim_start_year = sim_start_year
        self.sim_end_year   = sim_end_year
        self.num_fut_years = sim_end_year - sim_start_year + 1
        self.fut_ave_file = 'met{}_to_{}_ave.txt'.format(sim_start_year, sim_end_year)

        # New stanza to facilitate PyOrator weather extraction
        # ====================================================
        self.indx_strt_fut = (wthr_sets['CRU_hist']['year_end'] - wthr_sets['ClimGen_A1B']['year_start']) * 12

        self.indx_strt_ss = (hist_start_year - wthr_sets['CRU_hist']['year_start']) * 12
        self.indx_end_ss = (hist_end_year - wthr_sets['CRU_hist']['year_start']) * 12

        self.indx_strt_fwd = (sim_start_year - wthr_sets['CRU_hist']['year_start']) * 12
        self.indx_end_fwd = (sim_end_year - wthr_sets['CRU_hist']['year_start']) * 12


    def genLocalGrid(self, bbox, hwsd, snglPntFlag, num_band = None):
        """
        # return the weather indices for the area which encloses the supplied bounding box
        # this function does not alter the ClimGenNC (self) object
        """
        func_name =  __prog__ +  ' genLocalggrid'
        junk = seterr(all='ignore') # switch off warning messages

        bbLonMin, bbLatMin, bbLonMax, bbLatMax =  bbox
        if snglPntFlag:
            bbLonMax = bbLonMin
            bbLatMax = bbLatMin

        # determine bounds for climate grid which will enclose the supplied bounding box
        # ==============================================================================
        resol_lat = self.resolution_lat   # negative for future CRU data
        lat_indices = []
        lat_indices_hist = []
        clim_lat_min = self.lat_min
        num_lats = ceil( abs((bbLatMax - clim_lat_min)/resol_lat) )
        latMax = round(abs(num_lats*resol_lat) + clim_lat_min, 8)   # rounding introduced for NCAR_CCSM4
        lat_indices.append(self.latitudes.index(latMax))
        lat_indices_hist.append(self.latitudes_hist.index(latMax))

        num_lats = int( abs((bbLatMin - clim_lat_min)/resol_lat) )
        latMin = round(abs(num_lats*resol_lat) + clim_lat_min, 8)   # rounding introduced for NCAR_CCSM4
        lat_indices.append(self.latitudes.index(latMin))
        lat_indices_hist.append(self.latitudes_hist.index(latMin))

        # longitudes
        # ==========
        lon_indices = []
        resol_lon = self.resolution_lon
        clim_lon_min = self.lon_min
        num_lons = ceil((bbLonMax - clim_lon_min)/resol_lon)
        lonMax = num_lons*resol_lon + clim_lon_min
        lon_indices.append(self.longitudes.index(lonMax))

        num_lons = int((bbLonMin - clim_lon_min)/resol_lon)
        lonMin = num_lons*resol_lon + clim_lon_min
        lon_indices.append(self.longitudes.index(lonMin))

        # generate ClimGen grid    NB need to add one when slicing!!!
        # =====================    ==================================
        alons = arange(lonMin, lonMax, resol_lon)
        alats = arange(latMin, latMax, resol_lat)
        nlats = len(alats)
        nlons = len(alons)

        granlons = arange(nlons)
        for ic, lon in enumerate(alons):
            granlons[ic] = (180.0 + lon)*hwsd.granularity
        granlons.sort()

        granlats = arange(nlats)
        for ic, lat in enumerate(alats):
            granlats[ic] = (90.0 - lat)*hwsd.granularity
        granlats.sort()

        # must be in correct order
        # ========================
        lat_indices.sort()
        lat_indices_hist.sort()
        lon_indices.sort()

        aoi_indices_fut = lat_indices + lon_indices
        aoi_indices_hist = lat_indices_hist + lon_indices
        return aoi_indices_fut, aoi_indices_hist

    def fetch_cru_future_NC_data(self, aoi_indices, num_band, fut_start_indx = 0):
        '''
        get precipitation or temperature data for a given variable and lat/long index for all times
        CRU uses NETCDF4 format
        '''
        func_name = __prog__ +  ' fetch_fut_future_NC_data'
        warnings.simplefilter('default')

        num_key_masked = 0
        lat_indx_min, lat_indx_max, lon_indx_min, lon_indx_max = aoi_indices
        pettmp = {}

        # process future climate
        # ======================
        varnams_mapped = {'precipitation':'precip','temperature':'tair'}

        varnams = sorted(varnams_mapped.keys())

        for varname, fname in zip(varnams, list([self.fut_precip_fname, self.fut_tas_fname])):
            varnam_map = varnams_mapped[varname]
            pettmp[varnam_map] = {}
            ncfile = cdf.Dataset(fname, mode='r')

            # collect readings for all time values
            # ====================================
            slice = ncfile.variables[varname][lat_indx_min:lat_indx_max + 1, lon_indx_min:lon_indx_max + 1, :]

            if ma.is_masked(slice):
                slice_is_masked_flag = True
                self.lggr.info('Future slice is masked in band {}'.format(num_band))
            else:
                slice_is_masked_flag = False

            # reform slice
            # ============
            for ilat, lat_indx in enumerate(range(lat_indx_min, lat_indx_max + 1)):
                gran_lat = round((90.0 - self.latitudes[lat_indx])*ngranularity)

                for ilon, lon_indx in enumerate(range(lon_indx_min, lon_indx_max + 1)):
                    gran_lon = round((180.0 + self.longitudes[lon_indx])*ngranularity)
                    key = '{:0=5d}_{:0=5d}'.format(int(gran_lat), int(gran_lon))

                    # validate values
                    # ===============
                    pettmp[varnam_map][key] = null_value
                    if slice_is_masked_flag :
                        val = slice[ilat,ilon,0]
                        if val is ma.masked:
                            self.lggr.info('val is ma.masked for key ' + key)
                            pettmp[varnam_map][key] = None
                            num_key_masked += 1

                    # add data for this coordinate
                    # ============================
                    if pettmp[varnam_map][key] == null_value:
                        # remove overlap with historic data - for CRU data only
                        record = [round(val, 1) for val in slice[ilat,ilon,:]]
                        pettmp[varnam_map][key] = record[fut_start_indx:]

            # close netCDF file
            ncfile.close()
            if num_key_masked > 0:
                print('# masked weather keys: {}'.format(num_key_masked))

        return pettmp

    def fetch_cru_historic_NC_data(self, aoi_indices, num_band):
        '''
        get precipitation or temperature data for a given variable and lat/long index for all times
        CRU uses NETCDF4 format
        '''
        func_name = __prog__ +  ' fetch_historic_NC_data'
        warnings.simplefilter('default')

        num_key_masked = 0
        lat_indx_min, lat_indx_max, lon_indx_min, lon_indx_max = aoi_indices
        pettmp = {}

        # process historic climate
        # ========================
        varnams_mapped = {'pre':'precip','tmp':'tair'}

        varnams = sorted(varnams_mapped.keys())

        for varname, fname in zip(varnams, list([self.hist_precip_fname, self.hist_tas_fname])):
            varnam_map = varnams_mapped[varname]
            pettmp[varnam_map] = {}
            ncfile = cdf.Dataset(fname, mode='r')

            # collect readings for all time values
            # ====================================

            slice = ncfile.variables[varname][:, lat_indx_min:lat_indx_max + 1, lon_indx_min:lon_indx_max + 1]

            if ma.is_masked(slice):
                slice_is_masked_flag = True
                self.lggr.info('Historic weather slice is masked in band {}'.format(num_band))
            else:
                slice_is_masked_flag = False

            # reform slice
            # ============
            for ilat, lat_indx in enumerate(range(lat_indx_min, lat_indx_max + 1)):
                gran_lat = round((90.0 - self.latitudes_hist[lat_indx])*ngranularity)

                for ilon, lon_indx in enumerate(range(lon_indx_min, lon_indx_max + 1)):
                    gran_lon = round((180.0 + self.longitudes[lon_indx])*ngranularity)
                    key = '{:0=5d}_{:0=5d}'.format(int(gran_lat), int(gran_lon))

                    # validate values
                    # ===============
                    pettmp[varnam_map][key] = null_value
                    if slice_is_masked_flag :
                        val = slice[0,ilat,ilon]
                        if val is ma.masked:
                            self.lggr.info('val is ma.masked for key ' + key)
                            pettmp[varnam_map][key] = None
                            num_key_masked += 1

                    # add data for this coordinate
                    if pettmp[varnam_map][key] == null_value:
                        pettmp[varnam_map][key] = [round(val, 1) for val in slice[:, ilat,ilon]]

            # close netCDF file
            ncfile.close()
            if num_key_masked > 0:
                print('# masked weather keys: {}'.format(num_key_masked))

        return pettmp
