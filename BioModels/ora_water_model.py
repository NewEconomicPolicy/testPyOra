# -------------------------------------------------------------------------------
# Name:        ora_water_model.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     13/04/2017
# Licence:     <your licence>
#
# Description:
#   to enable the available water in a given depth of soil to be determined
#
# -------------------------------------------------------------------------------

__prog__ = 'ora_water_model.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from calendar import monthrange
from copy import copy

from thornthwaite import thornthwaite

WAT_STRSS_INDX_DFLT = 1.0

def _theta_values(pcnt_c, pcnt_clay, pcnt_silt, pcnt_sand, halaba_flag=False):
    """
    Volumetric water content at field capacity and permanent wilting point
    """
    if halaba_flag:
        theta_fc = (4.442 * pcnt_c) - (0.061 * pcnt_sand) + (0.34 * pcnt_clay) + 22.821  # (eq.2.2.5)

        theta_pwp = (1.963 * pcnt_c) - (0.029 * pcnt_sand) + (0.166 * pcnt_clay) + 11.746  # (eq.2.2.6)
    else:
        invrs_c = 1 / (1 + pcnt_c)

        # (eq.2.2.3)
        # ==========
        theta_fc = (24.49 - (18.87 * invrs_c) + (0.4527 * pcnt_clay) + (0.1535 * pcnt_silt) +
                        (0.1442 * pcnt_silt * invrs_c) - (0.00511 * pcnt_silt * pcnt_clay) +
                                                                    (0.08676 * pcnt_clay * invrs_c))

        # (eq.2.2.4)
        # ==========
        theta_pwp = (9.878 + (0.2127 * pcnt_clay) - (0.08366 * pcnt_silt) - (7.67 * invrs_c) +
                     (0.003853 * pcnt_silt * pcnt_clay) + (0.233 * pcnt_clay * invrs_c) +
                                                                    (0.09498 * pcnt_silt * invrs_c))

    return theta_fc, theta_pwp

def get_soil_water_constants(soil_vars, n_parms, tot_soc):
    """
    get water content at field capacity and at permanent wilting point (mm)
    For a given depth of soil, d (cm), the available water is calculated as the difference between the water content at
                                                            field capacity, Vfc(mm), and a lower limit of water content
    """
    pcnt_clay = soil_vars.t_clay
    pcnt_silt = soil_vars.t_silt
    pcnt_sand = soil_vars.t_clay
    t_depth = soil_vars.t_depth  # soil_depth (cm)
    r_dry = n_parms['r_dry']

    pcnt_c = tot_soc / (t_depth * soil_vars.t_bulk)

    # The volumetric water content at field capacity, Theta_fc (%) and the volumetric water content at permanent
    # wilting point, Theta_pwp (%), are defined
    # =========================================
    theta_fc, theta_pwp = _theta_values(pcnt_c, pcnt_clay, pcnt_silt, pcnt_sand)

    # (eq.2.2.1) Vfc Water content at field capacity of soil to given depth (mm)
    # ==========================================================================
    wc_fld_cap = theta_fc * t_depth / 10

    # The lower limit for the water content is calculated from the water content at permanent wilting point
    # divided by a "drying potential", rdry (currently set to 2).  (eq.2.2.2)
    # =======================================================================
    wc_pwp = theta_pwp * t_depth / (10 * r_dry)

    return wc_fld_cap, wc_pwp, pcnt_c

def add_pet_to_weather(latitude, pettmp_grid_cell):
    """
    feed monthly annual temperatures to Thornthwaite equations to estimate Potential Evapotranspiration [mm/month]
    """
    # initialise output var
    # =====================
    nyears = int(len(pettmp_grid_cell['precip']) / 12)
    pettmp_reform = {}
    for var in list(['precip', 'tair', 'pet']):
        pettmp_reform[var] = []

    precip = pettmp_grid_cell['precip']  #
    temper = pettmp_grid_cell['tair']

    indx1 = 0
    for year in range(nyears):

        indx2 = indx1 + 12

        # precipitation and temperature
        precipitation = precip[indx1:indx2]  #
        tmean = temper[indx1:indx2]

        # pet
        if max(tmean) > 0.0:
            pet = thornthwaite(tmean, latitude, year)
        else:
            pet = [0.0] * 12
            mess = '*** Warning *** monthly temperatures are all below zero for latitude: {}'.format(latitude)
            print(mess)

        pettmp_reform['precip'] += precipitation
        pettmp_reform['tair'] += tmean
        pettmp_reform['pet'] += pet

        indx1 += 12

    return pettmp_reform

def get_soil_water(precip, pet, irrig, wc_fld_cap, wc_pwp, wc_t0):
    """
    Initialisation and subsequent calculation of soil water
    """
    if wc_t0 is None:
        wat_soil = (wc_fld_cap + wc_pwp) / 2  # see Initialisation of soil water in 2.2. Soil water
        wat_soil_no_irri = copy(wat_soil)
    else:
        # (eq.2.2.14)
        # ===========
        wat_add_soil = wc_t0 + precip - pet
        wat_soil_no_irri = max(wc_pwp, min(wat_add_soil, wc_fld_cap))  # column K, sheet A3
        wat_soil = max(wc_pwp, min((wat_add_soil + irrig), wc_fld_cap))  # column O

    return wat_soil, wat_soil_no_irri

class SoilWaterChange(object, ):
    """
    C
    """
    def __init__(self):
        """
        A3 - Soil water
        Conventions:
            a) irrigation is included unless variable is appended with _no_irrig
            b) water content is measured at root zone
        """
        self.title = 'SoilWaterChange'

        self.irrig = 0  # D1. Water use

        self.data = {}
        var_name_list = list(['wat_soil', 'wat_soil_no_irri', 'wc_pwp', 'wc_fld_cap', 'wat_strss_indx', 'wat_drain',
                                    'wat_hydro_eff', 'pet', 'aet', 'aet_no_irri', 'irrig', 'pcnt_c', 'max_root_dpth'])
        for var_name in var_name_list:
            self.data[var_name] = []

        self.var_name_list = var_name_list

    def get_wvals_for_tstep(self, tstep):
        """
        C
        """
        wc_pwp = self.data['wc_pwp'][tstep]
        wat_soil = self.data['wat_soil'][tstep]
        wc_fld_cap = self.data['wc_fld_cap'][tstep]
        aet = self.data['aet'][tstep]

        irrig = self.data['irrig'][tstep]
        aet_no_irri = self.data['aet_no_irri'][tstep]
        wat_drain = self.data['wat_drain'][tstep]

        return wat_soil, wc_pwp, wc_fld_cap

    def append_wvars(self, imnth, max_root_dpth, pcnt_c, precip, pet_prev, pet, irrig, wc_pwp,
                                                                            wat_soil, wat_soil_no_irri, wc_fld_cap):
        """
        all values are in mm unless otherwise specified
        columns refer to sheet A3

        # NB required: num months growing, col I in sheet D2. Water use for crops
        """
        dummy, days_in_mnth = monthrange(2011, imnth)  # use 2011 as this is not a leap year

        if len(self.data['wat_drain']) > 0:

            # AET to rooting depth without and with irrigation using (eq.3.2.4) cols L and O sheet A3
            # =======================================================================================
            aet_no_irri = min(pet_prev, 5 * days_in_mnth, (wat_soil_no_irri - wc_pwp))
            aet = min(pet_prev, 5 * days_in_mnth, (wat_soil - wc_pwp))
            if pet_prev > 0.0:
                self.data['wat_strss_indx'].append(self.data['aet'][-1] / pet_prev)     # (eq.3.2.3)
            else:
                self.data['wat_strss_indx'].append(WAT_STRSS_INDX_DFLT)
            wat_soil_prev = self.data['wat_soil'][-1]
        else:
            self.data['wat_strss_indx'].append(WAT_STRSS_INDX_DFLT)
            aet_no_irri = min(pet, 5 * days_in_mnth, (wat_soil_no_irri - wc_pwp))
            aet = min(pet, 5 * days_in_mnth, (wat_soil - wc_pwp))
            wat_soil_prev = wat_soil

        self.data['pet'].append(pet)
        self.data['aet'].append(aet)    # col O - AET to rooting depth after irrigation (mm)
        self.data['aet_no_irri'].append(aet_no_irri)

        self.data['pcnt_c'].append(pcnt_c)
        self.data['max_root_dpth'].append(max_root_dpth)  # col H
        self.data['wc_pwp'].append(wc_pwp)  # col I - Lower limit for water extraction
        self.data['wc_fld_cap'].append(wc_fld_cap)  # col J - Water content of root zone at field capacity

        self.data['wat_soil'].append(wat_soil)  # col P - Soil water content of root zone after irrigation
        self.data['wat_soil_no_irri'].append(wat_soil_no_irri)  # col K - Soil water content before irrigation

        self.data['irrig'].append(irrig)  # col M - irrigation

        wat_hydro_eff = irrig + precip - pet   # effective rainfall
        wat_drain = max(wat_hydro_eff - (wc_fld_cap - wat_soil_prev), 0)  # (eq.2.4.7)
        self.data['wat_drain'].append(wat_drain)  # col Q - Drainage from soil depth (mm)
        self.data['wat_hydro_eff'].append(wat_hydro_eff)

        return