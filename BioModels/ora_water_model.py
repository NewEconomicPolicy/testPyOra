#-------------------------------------------------------------------------------
# Name:        ora_water_model.py
# Purpose:     a collection of reusable functions
# Author:      Mike Martin
# Created:     13/04/2017
# Licence:     <your licence>
#
# Description:
#   to enable the available water in a given depth of soil to be determined
#
#-------------------------------------------------------------------------------

__prog__ = 'ora_water_model.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from calendar import monthrange
from thornthwaite import thornthwaite

def _theta_values(pcnt_c, pcnt_clay, pcnt_silt, pcnt_sand, halaba_flag = False):
    """
    Volumetric water content at field capacity and permanent wilting point
    """
    if halaba_flag:
        theta_fc = 4.442*pcnt_c - 0.061*pcnt_sand + 0.34*pcnt_clay + 22.821    # (eq.2.2.5)

        theta_pwp = 1.963*pcnt_c - 0.029*pcnt_sand + 0.166*pcnt_clay + 11.746  # (eq.2.2.6)
    else:
        invrs_c = 1/(1 + pcnt_c)

        theta_fc = 24.49 - 18.87*invrs_c + 0.4527*pcnt_clay + 0.1535*pcnt_silt + 0.1442*pcnt_silt*invrs_c \
                   - 0.00511*pcnt_silt*pcnt_clay + 0.08676*pcnt_clay*invrs_c    # (eq.2.2.3)

        theta_pwp = 9.878 + 0.2127*pcnt_clay - 0.08366*pcnt_silt - 7.67*invrs_c + 0.003853*pcnt_silt*pcnt_clay \
                    + 0.233*pcnt_clay*invrs_c + 0.09498*pcnt_silt*invrs_c       # (eq.2.2.4)

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
    wc_fld_cap = theta_fc*t_depth/10

    # The lower limit for the water content is calculated from the water content at permanent wilting point
    # divided by a "drying potential", rdry (currently set to 2).  (eq.2.2.2)
    # =======================================================================
    wc_pwp = theta_pwp*t_depth/(10*r_dry)

    return wc_fld_cap, wc_pwp, pcnt_c

def add_pet_to_weather(latitude, pettmp_grid_cell):
    """
    feed monthly annual temperatures to Thornthwaite equations to estimate Potential Evapotranspiration [mm/month]
    """
    # initialise output var
    # =====================
    nyears = int(len(pettmp_grid_cell['precip'])/12)
    pettmp_reform = {}
    for var in list(['precip','tair','pet']):
        pettmp_reform[var] = []

    precip = pettmp_grid_cell['precip']         #
    temper = pettmp_grid_cell['tair']

    indx1 = 0
    for year in range(nyears):

        indx2 = indx1 + 12

        # precipitation and temperature
        precipitation = precip[indx1:indx2]            #
        tmean =         temper[indx1:indx2]

        # pet
        if max(tmean) > 0.0:
            pet = thornthwaite(tmean, latitude, year)
        else:
            pet = [0.0]*12
            mess = '*** Warning *** monthly temperatures are all below zero for latitude: {}'.format(latitude)
            print(mess)

        pettmp_reform['precip'] += precipitation
        pettmp_reform['tair']   += tmean
        pettmp_reform['pet'] += pet

        indx1 += 12

    return pettmp_reform

def get_soil_water(precip, pet, irrigation, wc_fld_cap, wc_pwp, wc_t0):
    """
    Initialisation and subsequent calculation of soil water
    """
    if wc_t0 is None:
        wat_soil = (wc_fld_cap + wc_pwp)/2     # see Initialisation of soil water in 2.2. Soil water
    else:
        wat_soil = max(wc_pwp, min((wc_t0 + precip - pet + irrigation), wc_fld_cap)) # (eq.2.2.14)

    return wat_soil

class SoilWaterChange(object, ):
    """

    """
    def __init__(self):
        """
        A3 - Soil water
        Assumptions:
        """
        self.title = 'SoilWaterChange'

        self.irrig = 0  # D1. Water use

        self.data = {}
        var_name_list = list(['wc_pwp', 'wat_soil', 'wc_fld_cap', 'wat_strss_indx', 'aet', 'irrig',
                'wc_soil_irri_root_zone', 'aet_irri', 'wc_soil_irri', 'wat_drain', 'wat_hydro_eff', 'pcnt_c',
                                                                                                    'max_root_dpth'])
        for var_name in var_name_list:
            self.data[var_name] = []

        self.var_name_list = var_name_list

    def get_wvals_for_tstep(self, tstep):
        """

        """
        wc_pwp = self.data['wc_pwp'][tstep]
        wat_soil = self.data['wat_soil'][tstep]
        wc_fld_cap = self.data['wc_fld_cap'][tstep]
        aet = self.data['aet'][tstep]

        irrig = self.data['irrig'][tstep]
        wc_soil_irri_root_zone = self.data['wc_soil_irri_root_zone'][tstep]
        aet_irri = self.data['aet_irri'][tstep]
        wc_soil_irri = self.data['wc_soil_irri'][tstep]
        wat_drain = self.data['wat_drain'][tstep]

        return wat_soil, wc_pwp, wc_fld_cap

    def append_vars(self, imnth, t_depth, max_root_dpth, precip, pet_prev, pet, irrig, wc_pwp, wat_soil, wc_fld_cap,
                                                                                                pcnt_c, wat_strss_indx):
        """
        all values are in mm unless otherwise specified
        """
        dummy, days_in_mnth = monthrange(2011, imnth)   # use 2011 as this is not a leap year

        # TODO: check
        # ===========
        if len(self.data['wat_drain']) > 0:
            aet = min(pet_prev, 5*days_in_mnth, (wat_soil - wc_pwp))    # (eq.3.2.4) col L - AET to rooting depth before irrigation
            if pet_prev > 0.0:
                self.data['wat_strss_indx'].append(self.data['aet'][-1]/pet_prev)
            else:
                self.data['wat_strss_indx'].append(1.0)
            wat_soil_prev = self.data['wat_soil'][-1]
        else:
            self.data['wat_strss_indx'].append(wat_strss_indx)
            aet = pet
            wat_soil_prev = wat_soil

        self.data['aet'].append(aet)    # TODO: revisit
        self.data['pcnt_c'].append(pcnt_c)  # col Q - Drainage from soil  depth
        self.data['wc_pwp'].append(wc_pwp)  # col I - Lower limit for water extraction
        self.data['wc_fld_cap'].append(wc_fld_cap)  # col J - Water content of root zone at field capacity
        self.data['wat_soil'].append(wat_soil)  # col K - Soil water content of root zone before irrigation

        # required: num months growing, col I in D2. Water use for crops
        self.data['irrig'].append(irrig)  # col M - irrigation

        wc_soil_irri = wat_soil
        self.data['wc_soil_irri_root_zone'].append(wc_soil_irri)  # col N - Soil water content of root zone after irrigation (mm)

        aet_irri = aet
        self.data['aet_irri'].append(aet_irri)  # col O - AET to rooting depth after irrigation (mm)
        self.data['wc_soil_irri'].append(wc_soil_irri)  # col P - Soil water content to soil depth after irrigation (mm)

        self.data['max_root_dpth'].append(max_root_dpth)    # col H
        dpth_soil_root_rat = t_depth / max_root_dpth  # used in PET (eq.2.2.13)
        pet_dpth = min(pet, pet*dpth_soil_root_rat)
        wat_hydro_eff = precip - pet_dpth
        wat_drain = max(wat_hydro_eff - (wc_fld_cap - wat_soil_prev), 0)  # (eq.2.4.7)
        self.data['wat_drain'].append(wat_drain)  # col Q - Drainage from soil depth (mm)
        self.data['wat_hydro_eff'].append(wat_hydro_eff)
