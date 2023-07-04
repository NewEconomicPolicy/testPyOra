"""
#-------------------------------------------------------------------------------
# Name:        hwsd_bil.py
# Purpose:     Class to read HWSD .hdr and .bil files and return a 2D array comprising MU_GLOBAL values for a given
#              bounding box
#               input files are: hwsd.hdr and hwsd.bil
#               notes:
#                   a) lat longs are stored in unites of 30 arc seconds for sake of accuracy and simplicity - so we
#                       convert lat/longs read from shapefiles to nearest seconds using round()
#
#                   b) output file names take the form: mu_global_NNNNN.nc where NNNNN is the region name??
#
#                   c) modified on 03-09-2016 to include soils which have only a top layer
#
# Author:      Mike Martin
# Created:     16/09/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
"""

__prog__ = 'hwsd_bil.py'
__version__ = '0.0.0'

#
import csv
from os.path import isfile, join, isdir
import struct
import locale
from numpy import arange, zeros, int32, isnan
from pandas import read_csv
from time import sleep
import math

sleepTime = 5
GRANULARITY = 120

def check_hwsd_integrity(hwsd_dir):
    '''
    invoked at startup - check essential directory and files
    '''
    integrity_flag = True     # presumption that all good

    if not isdir(hwsd_dir):
        print('Error - HWSD directory ' + hwsd_dir + ' must exist')
        integrity_flag = False

    # check main table and header file
    # =================================
    inp_fname = 'HWSD_DATA.csv'
    csv_file = join(hwsd_dir, inp_fname)
    if not isfile(csv_file):
        print('Error - CSV file of main HWSD table ' + csv_file + ' must exist')
        integrity_flag = False

    inp_fname = 'hwsd.hdr'
    hdr_file = join(hwsd_dir, inp_fname)
    if not isfile(hdr_file):
        print('Error - HWSD HDR file ' + hdr_file + ' must exist')
        integrity_flag = False

    if integrity_flag:
        return
    else:
        sleep(sleepTime)
        exit(0)

def validate_hwsd_rec (lggr, mu_global, data_rec):
    """
    function to make sure we are supplying a valid HWSD data record for a given mu_global

    TODO: improve this function by using a named tuple:
                 data_rec = list([
                 0 row['SHARE'],
                 1 row['T_SAND'],
                 2 row['T_SILT'],
                 3 row['T_CLAY'],
                 4 row['T_BULK_DENSITY'],
                 5 row['T_OC'],
                 6 row['T_PH_H2O'],
                 7 row['S_SAND'],
                 8 row['S_SILT'],
                 9 row['S_CLAY'],
                10 row['S_BULK_DENSITY'],
                11 row['S_OC'],
                12 row['S_PH_H2O']
    """
    if len(data_rec) != 13:
        mess = 'Incomplete topsoil data - mu_global: ' + str(mu_global) + '\trecord: ' + ', '.join(data_rec)
        lggr.info(mess)
        return None

    share, t_sand, t_silt, t_clay, t_bulk_density, t_oc, t_ph_h2o, \
        s_sand, s_silt, s_clay, s_bulk_density, s_oc, s_ph_h2o = data_rec

    # topsoil is mandatory
    # ====================
    ts_rec = data_rec[1:7]
    for val in ts_rec:
        if isnan(val):
            # TODO: mess = 'Incomplete topsoil data - mu_global: ' + str(mu_global) + '\trecord: ' + ', '.join(data_rec)
            mess =  'Incomplete topsoil data - mu_global: ' + str(mu_global)
            lggr.info(mess)
            return None
    '''
    MJM: borrowed from mksims.py:
    Convert top and sub soil Organic Carbon percentage weight to kgC/ha as follows:
                      / 100: % to proportion,
                     * 100000000: cm3 to hectares,
                      /1000: g to kg,
                     *30: cm to lyr depth
    '''
    # lggr.info('Soil data check for mu_global {}\tshare: {}%'.format(mu_global,share))
    t_bulk = float(t_bulk_density)  # T_BULK_DENSITY
    t_oc = float(t_oc)    # T_OC
    t_c = round(t_bulk * t_oc / 100.0 * 30 * 100000000 / 1000.0, 1)

    # sub soil
    # ========
    ss_rec = data_rec[7:]
    for val in ss_rec:
        if isnan(val):
            # log a message
            lggr.info('Incomplete subsoil data - mu_global: ' + str(mu_global))
            # modified share to from int to float
            return list([t_c, t_bulk, float(t_ph_h2o), int(t_clay), int(t_silt), int(t_sand), float(share)])

    s_bulk = float(s_bulk_density) # S_BULK_DENSITY
    s_oc = float(s_oc)   # S_OC
    s_c = round(s_bulk * s_oc / 100.0 * 70 * 100000000 / 1000.0, 1)

    # Two layers: C content, bulk, PH, clay, silt, sand
    # =================================================
    try:
        # modified share to from int to float
        ret_list = list([t_c, t_bulk, float(t_ph_h2o), int(t_clay), int(t_silt), int(t_sand),
                 s_c, s_bulk, float(s_ph_h2o), int(s_clay), int(s_silt), int(s_sand), float(share)])
    except ValueError as err:
        mess = 'problem {} with mu_global {}\tdata_rec: {}'.format(err, mu_global, data_rec)
        lggr.info(mess)
        return None

    return ret_list

class HWSD_bil(object,):

    def __init__(self, lggr, hwsd_dir):

        self.hwsd_dir = hwsd_dir
        self.lggr = lggr

        # the HWSD grid covers the globe's land area with 30 arc-sec grid-cells
        # =====================================================================
        self.granularity = GRANULARITY

        # required HWSD metrics
        # =====================
        dtypes = {'SHARE': float, 'T_SAND': float, 'T_SILT': float, 'T_CLAY': float,
                 'T_BULK_DENSITY': float, 'T_OC': float, 'T_PH_H2O': float,
                 'S_SAND': float, 'S_SILT': float, 'S_CLAY': float, 'S_BULK_DENSITY': float, 'S_OC': float,
                 'S_PH_H2O': float}
        self.field_list = list(dtypes.keys())

        # create data frame from main data set
        # ====================================
        inp_fname = 'HWSD_DATA.csv'
        csv_file = join(hwsd_dir, inp_fname)
        self.data_frame = read_csv(csv_file, sep=',', index_col=False, low_memory=False, dtype=dtypes)

        # open header file and read first 9 lines
        # ========================
        inp_fname = 'hwsd.hdr'
        inp_file = join(hwsd_dir, inp_fname)
        finp = open(inp_file, 'r')
        finp_reader = csv.reader(finp)

        row = next(finp_reader); dummy, byteorder = row[0].split()
        row = next(finp_reader)   # skip: LAYOUT       BIL

        row = next(finp_reader); dummy, f1 = row[0].split(); nrows = int(f1)
        row = next(finp_reader); dummy, f1 = row[0].split(); ncols = int(f1)
        row = next(finp_reader); dummy, f1 = row[0].split(); nbands = int(f1)
        row = next(finp_reader); dummy, f1 = row[0].split(); nbits = int(f1)

        row = next(finp_reader); dummy, f1 = row[0].split(); bandrowbytes = int(f1)
        row = next(finp_reader); dummy, f1 = row[0].split(); totalrowbytes = int(f1)
        row = next(finp_reader); dummy, f1 = row[0].split(); bandgapbytes = int(f1)

        finp.close()

        self.nrows = nrows
        self.ncols = ncols

        # wordsize is in bytes
        # ====================
        self.wordsize = round(nbits/8)

        # these attrubutes change according to the bounding box
        # =====================================================
        self.rows = arange(1)   # create ndarray
        self.mu_globals = []
        self.bad_muglobals = []
        self.badCntr = 0
        self.zeroCntr = 0

        # these define the extent of the grid of interest
        # ===============================================
        self.nlats = 0; self.nlons = 0
        self.nrow1 = 0; self.nrow2 = 0
        self.ncol1 = 0; self.ncol2 = 0

        self.coord_upper_left  = None
        self.coord_lower_right = None

        # this section is adapted from MR's hwsd_uk.py
        # ===========================================
        '''
        # self.nan = nan

        # self.Rec = namedtuple('Rec', ('id', 'lon', 'lat', 'soils'))
        self.Rec = namedtuple('Rec', ('mu_global', 'soils'))
        # define a tuple
        soil_fields = ('share', 't_sand', 't_silt', 't_clay', 't_bulk', 't_oc',
                       't_ph', 's_sand', 's_silt', 's_clay', 's_bulk', 's_oc',
                       's_ph')
        self.soil_fields = soil_fields
        self.nsoil_fields = len(soil_fields)
        self.Soil = namedtuple('Soil', soil_fields)
        '''

    def read_bbox_hwsd_mu_globals(self, bbox, hwsd_mu_globals, upscale_resol):

        # this function creates a grid of MU_GLOBAL values corresponding to a given
        # bounding box defined by two lat/lon pairs

        func_name =  __prog__ + '.read_bbox_hwsd_mu_globals'
        self.lggr.info('Running programme ' + func_name)
        locale.setlocale(locale.LC_ALL, '')

        # the HWSD grid covers the globe's land area with 30 arc-sec grid-cells
        # AOI is typically county sized e.g. Isle of Man

        # these are lat/lon
        coord_upper_left = [bbox[3],bbox[0]]
        coord_lower_right = [bbox[1],bbox[2]]
        self.coord_upper_left = coord_upper_left
        self.coord_lower_right = coord_lower_right

        # round these so that they are divisable by the requested resolution
        nlats = round((coord_upper_left[0] - coord_lower_right[0])*GRANULARITY)
        nlats = upscale_resol*math.ceil(nlats/upscale_resol)
        nlons = round((coord_lower_right[1] - coord_upper_left[1])*GRANULARITY)
        nlons = upscale_resol*math.ceil(nlons/upscale_resol)

        # construct 2D array
        rows = zeros(nlats*nlons, dtype = int32)
        rows.shape = (nlats,nlons)
        #
        # work out first and last rows
        nrow1 = round((90.0 - coord_upper_left[0])*GRANULARITY)
        nrow2 = nrow1 + nlats
        ncol1 = round((180.0 + coord_upper_left[1])*GRANULARITY)
        ncol2 = ncol1 + nlons

        # read a chunk the CSV file
        # =========================
        aoi_chunk = hwsd_mu_globals.data_frame.loc[hwsd_mu_globals.data_frame['gran_lat'].isin(range(nrow1, nrow2))]
        nvals_read = len(aoi_chunk)
        nrejects = 0
        for index, rec in aoi_chunk.iterrows():
            icol = int(rec[1])
            irow = int(rec[0])
            mu_global = int(rec[2])

            # make sure indices are kept within limits
            # ========================================
            col_indx = icol - ncol1
            if col_indx < 0 or col_indx >= nlons:
                nrejects += 1
            else:
                rows[irow-nrow1][icol-ncol1] = mu_global

        print('Read {} cells from hwsd mu globals data frame, rejected {}'.format(nvals_read, nrejects))

        self.nrow1 = nrow1
        self.nrow2 = nrow2
        self.ncol1 = ncol1
        self.ncol2 = ncol2

        self.rows = rows
        self.nlats = nlats
        self.nlons = nlons

        mess =  'Retrieved {} mu globals for AOI of {} lats and {} lons'.format(nvals_read, nlats, nlons)
        self.lggr.info(mess)
        print('Found mu_globals for {} cells'.format(nvals_read) + ' in function ' + func_name)

        return nvals_read

    def get_soil_recs(self, mu_global_pairs):
        """
        get soil records associated with each MU_GLOBAL list entry        
        remove bad mu globals
        """
        func_name =  __prog__ + ' get_soil_recs'

        # build a dictionary with mu_globals as keys
        # ==========================================
        soil_recs = {}

        for mu_global in mu_global_pairs:

            # do not create soil records for a previously identified bad mu_global
            # ====================================================================
            if mu_global in self.bad_muglobals:
                continue

            sub_frame = self.data_frame.loc[self.data_frame['MU_GLOBAL'] == mu_global]
            soil_recs[mu_global] = []

            for irec in range(len(sub_frame)):
                data_rec = []
                for field in self.field_list:
                    data_rec.append(sub_frame[field].values[irec])

                adjusted_datarec = validate_hwsd_rec(self.lggr, mu_global, data_rec)
                if adjusted_datarec is not None:
                    soil_recs[mu_global].append(adjusted_datarec)

            # check mu_global has soil records
            # ================================
            if len(soil_recs[mu_global]) == 0:
                self.bad_muglobals.append(mu_global)  # add to list of mu_globals which are missing data
            else:
                # adjust shares
                # =============
                pass

        self.lggr.info('Created {} soil records from dataframe in function {}'.format(len(soil_recs), func_name))
        if len(soil_recs) == 0:
            return None
        else:
            # clean mu_globals
            # ================
            for bad_mu in self.bad_muglobals:
                if bad_mu in mu_global_pairs:
                    del(mu_global_pairs[bad_mu])

            return soil_recs

    def read_bbox_mu_globals(self, bbox, snglPntFlag = False):
        '''
        create a grid of MU_GLOBAL values corresponding to given bounding box defined by two lat/lon pairs
        '''
        func_name =  __prog__ + ' read_bbox_mu_globals'
        self.lggr.info('Running programme ' + func_name)

        # the HWSD grid covers the globe's land area with 30 arc-sec grid-cells
        # AOI is typically county sized e.g. Isle of Man

        ncols = self.ncols
        wordsize = self.wordsize

        if snglPntFlag:
            nlats = 1
            nlons = 1
            lower_left_coord = [bbox[1],bbox[0]]
            nrow1 = round((90.0 - lower_left_coord[0])*GRANULARITY)
            nrow2 = nrow1
            ncol1 = round((180.0 + lower_left_coord[1])*GRANULARITY)
            ncol2 = ncol1
            nlats = 1
            nlons = 1
        else:
            # these are lat/lon
            coord_upper_left = [bbox[3],bbox[0]]
            coord_lower_right = [bbox[1],bbox[2]]
            self.coord_upper_left = coord_upper_left
            self.coord_lower_right = coord_lower_right

            nlats = int(round((coord_upper_left[0] - coord_lower_right[0])*GRANULARITY))
            nlons = int(round((coord_lower_right[1] - coord_upper_left[1])*GRANULARITY))
            #
            # work out first and last rows
            nrow1 = int(round((90.0 - coord_upper_left[0])*GRANULARITY) + 1)
            nrow2 = int(round((90.0 - coord_lower_right[0])*GRANULARITY))
            ncol1 = int(round((180.0 + coord_upper_left[1])*GRANULARITY) + 1)
            ncol2 = int(round((180.0 + coord_lower_right[1])*GRANULARITY))

        chunksize = wordsize*nlons
        form = str(int(chunksize/2)) + 'H'  # format for unpack

        # TODO - construct a 2D array from extraction
        inpfname = 'hwsd.bil'
        inp_file = join(self.hwsd_dir, inpfname)
        finp = open(inp_file, 'rb')

        nrows_read = 0
        rows = arange(nlats*nlons)
        rows.shape = (nlats,nlons)

        # read subset of HWSD .bil file
        # =============================
        for nrow in range(nrow1, nrow2 + 1):
            offst = (ncols*nrow + ncol1)*wordsize

            finp.seek(offst)
            chunk = finp.read(chunksize)
            if chunk:
                rows[nrows_read:] = struct.unpack(form,chunk)
                # build array of mu_globals
                nrows_read += 1
                # print(' row {0:d}\tform {1:s}'.format(nrow,form))
            else:
                break

        finp.close()

        self.nrow1 = nrow1
        self.nrow2 = nrow2
        self.ncol1 = ncol1
        self.ncol2 = ncol2

        self.rows = rows
        self.nlats = nlats
        self.nlons = nlons

        self.lggr.info('Exiting function {0} after reading {1} records from .bil file\n'.format(func_name,nrows_read))
        return nrows_read

    def mu_global_list(self):

        # build a list of mu_globals from grid

        # reshape
        mu_globals = []
        nlats = self.nlats
        nlons = self.nlons

        # reshape tuple
        self.rows.shape = (nlats*nlons)
        for mu_global in self.rows:
            if mu_global not in mu_globals:
                mu_globals.append(mu_global)

        # revert shape of tuple
        self.rows.shape = (nlats,nlons)

        self.mu_globals = mu_globals

        return len(mu_globals)

    def get_mu_globals_dict(self):
        '''
        return list of MU_GLOBALs in grid with number of occurrences of each MU_GLOBAL value
        '''
        func_name =  __prog__ + ' get_mu_globals_dict'

        mu_globals = {}     # initialise dictionary

        nlats = self.nlats
        nlons = self.nlons

        for irow in range(0,nlats):

            for icol in range(0,nlons):

                mu_global = self.rows[irow,icol]

                if mu_global not in mu_globals.keys():
                    # add detail
                    mu_globals[mu_global] = 1
                else:
                    mu_globals[mu_global] += 1

        self.lggr.info('Func: {}\tUnique number of mu_globals: {}'.format(func_name, len(mu_globals)))
        for key in sorted(mu_globals.keys()):
            self.lggr.info('\t' + str(key) + ' :\t' + str(mu_globals[key]))

        # filter sea, i.e. mu_global == 0
        # ===============================
        if 0 in mu_globals.keys():
            nzeros = mu_globals.pop(0)
            if len(mu_globals) == 0:
                mu_globals = None
                self.lggr.info('Only one mu_global with value of zero - nothing to process')

        return mu_globals

    def get_data_mapit(self):

        # function to return lists which can be plotted using mapit
        xcoords = []  # e.g. longitude or easting
        ycoords = []  # e.g. latitude or northing
        vals = []
        nrow1 = self.nrow1
        nrow2 = self.nrow2
        nlats = self.nlats

        ncol1 = self.ncol1
        ncol2 = self.ncol2
        nlons = self.nlons

        yc = self.nrow1
        for irow in range(0,nlats):
            xc = self.ncol1
            for icol in range(0,nlons):
                xcoords.append(xc)
                ycoords.append(yc)
                vals.append(self.rows[irow,icol])
                xc += 1
            yc += 1

        return xcoords, ycoords, vals