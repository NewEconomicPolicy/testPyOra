"""
Name:        fao_eto.py
Purpose:     Library for calculating reference evapotransporation (ETo) for
             grass using the FAO Penman-Monteith equation
Author:      Mark Richards <m.richards@REMOVETHISabdn.ac.uk>
Copyright:   (c) Mark Richards 2011

Licence
=======
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Description
===========
A library of functions to allow calculation of reference evapotranspiration
(ETo) for a grass crop using minimum meteorological data. The methods are based
on guidelines published by the Food and Argiculture Organisation (FAO) of the
United Nations in:

Allen, R.G., Pereira, L.S., Raes, D. and Smith, M. (1998) Crop
    evapotranspiration. Guidelines for computing crop water requirements,
    FAO irrigation and drainage paper 56)

Almost all of the functions have been tested against examples given in the FAO
paper.

Instructions
============
These instructions are a brief summary of those given in Allen et al (1998).
The data required to calculate the daily, ten-day or monthly evapotranspiration
over grass using the FAO Penman-Monteith equation are specified below. If
measured data are not available, many of the variables can be estimated using
functions in this module.

If insufficient data are available, the alternative,
data light Hargreaves ETo equation can be used.  However, in general,
estimating solar radiation, vapor pressure and wind speed using the functions
describedbelow and then calculating evapotranspiration using the Penman-Monteith
method will provide somewhat more accurate estimates compared to the Hargreaves
equation. This is dueto the ability of the estimation equations to incorporate
general climatic characteristics such as high or low wind speed or high or low
relative humidity into the ETo estimate made using Penman-Monteith.

The Hargreaves equation has a tendency to underpredict under high wind
conditions(u2 > 3m/s) and to overpredict under conditions of high relative
humidity.

Monthly (or ten-day) time step
------------------------------
The value of reference evapotranspiration calculated with mean monthly weather
data is very similar to the average of the daily ETo values calculated with
average weather data for that month. The follwoing data are required (if using
a ten-day period substitude the words 'ten-day' in place of 'monthly'):

- monthly average daily maximum and minimum temperature
- monthly avereage of actual vapour pressure derived from psychrometric,
  dewpoint or relative humidty data.
- monthly average of daily wind speed data measured at 2 m height (can be
  estimated from measurements made at different heights)
- monthly avereage of daily net radiation computed from monthly measured short-
  wave radiation or from actual duration of daily sunshine hours. The
  extraterrestrial radiation and daylight hours for a specific day of the
  month can be computed using functions in this module.
- soil heat flux for monthly periods can be significant when soil is warming in
  spring or cooling in autumn so its value should be determined from the
  mean monthly air tmperatures of the previous and next month (see
  monthly_soil_heat_flux().

Daily time step
---------------
The required meteorological data are:

- minimum and maximum daily air temperature
- mean daily actual vapour pressure derived from psychrometric, dewpoint
  temperature or relative humidty data (or even just minimum temperature)
- daily average wind speed measured at 2 m height (can be estimated from
  measurements made at different heights)
- net radiation measured or computed from solar (shortwave) and longwave
  radiation or from the actual duration of sunshine. The extraterrestrial
  radiation for a specific day of the month should be computed using
  the et_rad() and daylight_hours() functions.
- as the magnitude of daily soil heat flux beneath a reference grass crop
  is relatively small it may ignored (soil heat flux = 0) for daily time
  steps though if you wish you can calculate it using the
  daily soil_heat_flux() function.

To calculate ETo using the penman_monteith_ETo() function gather the data
necessary for the function's arguments. It is best to provide measured
values for the inputs where possible but if some of the data is not
available then use one of the other functions to estimate the input.

For some input variables there is an order of preference for which function
to use to estimate the values due to variation
in the robustness/generality of the different methods.

e.g. If you wish to calculate daily net radiation
you can estimate it from measured sunshine hours (intermediate option) or
from the minimum temperature (worst option).

Below is a list of variables for which multiple functions exist along with the
order of preference for their use:

Actual vapour pressure
----------------------
If measured values are not available then use the following functions
to estimate AVP (in order of preference):
1. If dewpoint temperature data are available use ea_from_tdew()
2. If dry and wet bulb temperatures are available from a psychrometer
   use ea_from_twet_tdry()
3. If reliable min and max relatiuve humidity data available use
   aea_from_rhmin_rh_max()
4. If measurement errors of RH are large then use only RH max using
   ea_from_rhmax()
5. If RH min and RH max are not available but RH mean is then use
   ea_from_rhmean() (but this is less reliable than options 3 or 4)
6. If no data for the above are available then use ea_from_tmin().
   This function is less reliable in arid areas where it is recommended that
   2 deg C is subtracted from Tmin before it is passed to the function
   following Annex 6 of the FAO paper.

Soil heat flux
--------------
For a daily time step soil heat flux is small compared to net radiation
when the soil is covered by vegetation so it can be assumed to be zero.
However, it daily soil heat flux can be estimated using daily_soil_heat_flux().

For a monthy time step soil heat flux is significant and should be estimated
using:
1. monthly_soil_heat_flux if temperature data for the previous and next month
  is available or
2. monthly_soil_heat_flux2 if temeprature for the next month is not available.

Solar (shortwave) radiation
---------------------------
The amount of incoming solar radiation (AKA shortwave radiation) reaching a
horizontal plane after scattering by the atmosphere.
If measured values of gross solar radiation are not available the following 2
methods are available (in order of preference) to estimate it:
1. If sunshine duration data are available use sol_rad_from_sun_hours()
2. Otherwise use sol_rad_from_t() which requires T min and T max data.
   Suitable for coastal or inland areas but not islands.
3. For island locations (island <= 20 km wide) where no measured values
   are available from elsewhere on the island and the altitude is 0-100m use
   sol_rad_island(). Only suitable for monthly calculations.

Net solar (shortwave) radiation
-------------------------------
The amount of solar radiation (sometimes referred to as shortwave radiation)
that is not reflected by the surface. The methods listed below assume an
albedo of 0.23 for a grass reference crop.
Use function net_rad() to estimate net solar radiation for a grass crop.

Functions
---------
Atmospheric pressure (P):
    atmos_pres()
Actual vapour pressure (ea):
    ea_from_tmin()
    ea_from_rhmin_rhmax()
    ea_from_rhmax()
    ea_from_rhmean()
    ea_from_tdew()
    ea_from_twet_tdry()
Evapotranspiration over grass (ETo):
    hargreaves_ETo()
    penman_monteith_ETo()
Pyschrometric constant:
    psy_const()
    psy_const_of_psychrometer()
Radiation:
    clear_sky_rad()
    daylight_hours()
    net_in_sol_rad()
    net_out_lw_rad()
    net_rad()
    rad2equiv_evap()
    sol_rad_from_sun_hours()
    sol_rad_from_t()
    sol_rad_island()
Relative humidity (RH):
    rh_from_ea_es()
Saturated vapour pressure (es):
    delta_sat_vap_pres()
    es_from_t()
    mean_es()
Soil heat flux:
    daily_soil_heat_flux()
    monthly_soil_heat_flux()
    monthly_soil_heat_flux2()
Solar angles etc:
    inv_rel_dist_earth_sun()
    sol_dec()
    sunset_hour_angle()
Temperature:
    daily_mean_t()
Wind speed:
    wind_speed_2m()

References
----------
Allen, R.G., Pereira, L.S., Raes, D. and Smith, M. (1998) Crop
   evapotranspiration. Guidelines for computing crop water requirements.
   FAO irrigation and drainage paper 56,FAO, Rome.
Hargreaves, G.H. and Z.A. Samani (1982) Estimating potential
   evapotranspiration. J. Irrig. and Drain Engr., ASCE, 108(IR3):223-230.
Hargreaves, G.H. and Z.A. Samani (1985) Reference crop evapotranspiration from
   temperature. Transaction of ASAE 1(2):96-99.

Version history
---------------
1.0.01 (14/09/2010) - Fixed error in sunset_hour_angle().
1.1.00 (23/11/2010) - Added rh_from_ea_es().
1.2.00 (25/11/2010) - Tidied up code, added function list to header and
                      added function for Hargreaves ETo equation.
1.2.01 (29/11/2010) - Fixed minor error when converting deg C to Kelvin (was
                      adding 273.16 instead of 273.15.
1.3.00 (18/05/2011) - Using math.pi instead of locally defined constant. Added
                      es_from_t() to calculate saturated vapour pressure from
                      temperature.
1.3.03 (09/07/2013) - Fixed error calculating sunset hour angle for high
                      latitudes where values go outside of acos() domain

TODO:
- Remove defensive parameter value checking?
================================================================================
"""
__author__ = "Mark Richards <m.richards@REMOVETHISabdn.ac.uk>"
__version__ = "1.3.03"
__date__ = "09/07/2013"

import math

def atmos_pres(alt):
    """
    Calculates atmospheric pressure (kPa) using equation (7) in
    the FAO paper, page 62. Calculated using a simplification
    of the ideal gas law, assuming 20 deg C for a standard atmosphere.

    Arguments:
    alt - elevation/altitude above sea level (m)
    """
    # Raise exceptions
    if (alt < -20 or alt > 11000):
        raise ValueError ('alt=%d is not in range -20 to 11000 m' %alt)

    tmp1 = (293.0 - (0.0065 * alt)) / 293.0
    tmp2 = math.pow(tmp1, 5.26)
    atmos_pres = 101.3 * tmp2
    return atmos_pres

def clear_sky_rad(alt, et_rad):
    """
    Calculates clear sky radiation [MJ m-2 day-1] based on FAO equation 37
    which is recommended when calibrated Angstrom values are not available.

    Arguments:
    alt      - elevation above sea level [m]
    et_rad   - extraterrestrial radiation [MJ m-2 day-1]
    """
    # Raise exceptions
    if (alt < -20 or alt > 8850):
        raise ValueError  ('altitude=%d is not in range -20 to 8850 m' % alt)
    elif (et_rad < 0.0 or et_rad > 50.0):
        # TODO: put in a more realistic upper bound for et_rad than this
        raise ValueError ('et_rad=%g is not in range 0-50' % et_rad)

    clear_sky_rad = (0.00002 * alt + 0.75) * et_rad
    return clear_sky_rad

def daily_mean_t(tmin, tmax):
    """
    Calculates mean daily temperature [deg C] from the daily minimum and
    maximum temperatures.

    Arguments:
    tmin - minimum daily temperature [deg C]
    tmax - maximum daily temperature [deg C]
    """
    # Raise exceptions
    if (tmin < -95.0 or tmin > 60.0):
        raise ValueError ('tmin=%g is not in range -95 to +60' % tmin)
    elif (tmax < -95.0 or tmax > 60.0):
        raise ValueError ('tmax=%g is not in range -95 to +60' % tmax)

    tmean = (tmax + tmin) / 2.0
    return tmean

def daily_soil_heat_flux(t_cur, t_prev, delta_t, soil_heat_cap=2.1, delta_z=0.10):
    """
    Estimates the daily soil heat flux (Gday) [MJ m-2 day-1]
    assuming a grass crop from the curent air temperature
    and the previous air temperature. The length over time over which the
    current and previous air temperatures are measured are specified by t_len
    which should be greater than 1 day. The calculations are based on FAO
    equation 41. The soil heat capacity is related to its mineral composition
    and water content. The effective soil depth (z) is only 0.10-0.20 m for one
    day. The resluting heat flux can be converted to
    equivalent evaporation [mm day-1] using the equiv_evap() function.

    Arguments:
    t_cur         - air temperature at tim i (current) [deg C]
    t_prev        - air temperature at time i-1 [deg C]
    delta_t       - length of time interval between t_cur and t_prev [day]
    soil_heat_cap - soil heat capacity [MJ m-3 degC-1] (default value is 2.1)
    delta_z       - effective soil depth [m] (default - 0.1 m following FAO
                    recommendation for daily calculations
    """
    # Raise exceptions
    if (t_prev < -95.0 or t_prev > 60.0):
        raise ValueError ('t_prev=%g is not in range -95 to +60' % t_prev)
    elif (t_cur < -95.0 or t_cur > 60.0):
        raise ValueError ('t_cur=%g is not in range -95 to +60' % t_cur)
    # for dilay calc delta_t should be greater than 1 day
    elif (delta_t < 1.0):
        raise ValueError ('delta_t=%g is less than 1 day' % delta_t)
    elif (soil_heat_cap < 1.0 or soil_heat_cap > 4.5):
        raise ValueError ('soil_heat_cap=%g is not in range 1-4.5' % soil_heat_cap)
    elif (delta_z < 0.0 or delta_z > 200.0):
        raise ValueError ('delta_z=%g is not in range 0-200 m' % delta_z)

    # Assume an effective soil depth of 0.10 m for a daily calculation as per
    # FAO recommendation
    soil_heat_flux = soil_heat_cap * ((t_cur - t_prev) / delta_t) * delta_z
    return soil_heat_flux

def daylight_hours(sha):
    """
    Calculates the number of daylight hours from sunset hour angle
    based on FAO equation 34.

    Arguments:
    sha - sunset hour angle [rad]
    """
    # Raise exceptions
    # TODO: Put in check for sunset hour angle
    daylight_hours = (24.0 / math.pi) * sha
    return daylight_hours

def delta_sat_vap_pres(t):
    """
    Calculates the slope of the saturation vapour pressure curve at a given
    temperature (t) [kPa degC-1] based on equation 13 from the FAO paper. For
    use in the Penman-Monteith equation the slope should be calculated using
    mean air temperature.

    Arguments:
    t - air temperature (deg C) (use mean air temp for use in Penman-Monteith)
    """
    # Raise exceptions
    if (t < -95.0 or t > 60.0):
        raise ValueError ('t=%g is not in range -95 to +60' % t)

    tmp1 = (17.27 * t) / (t + 237.3)
    tmp2 = 4098 * (0.6108 * math.exp(tmp1))
    delta_es = tmp2 / math.pow((t + 237.3), 2)
    return delta_es

def ea_from_tmin(tmin):
    """
    Calculates actual vapour pressure, ea [kPa] using equation (48) in
    the FAO paper. This method is to be used where humidity data are
    lacking or are of questionable quality. The method assumes that the
    dewpoint temperature is approximately equal to the minimum temperature
    (T_min), i.e. the air is saturated with water vapour at T_min.
    NOTE: This assumption may not hold in arid/semi-arid areas.
    In these areas it may be better to substract 2 deg C from t_min (see
    Annex 6 in FAO paper).

    Arguments:
    tmin - daily minimum temperature [deg C]
    """
    # Raise exception:
    if (tmin < -95.0 or tmin > 60.0):
        raise ValueError('tmin=%g is not in range -95 to 60 deg C' % tmin)

    ea = 0.611 * math.exp((17.27 * tmin)/(tmin + 237.3))
    return ea

def ea_from_rhmin_rhmax(e_tmin, e_tmax, rh_min, rh_max):
    """
    Calculates actual vapour pressure [kPa] from relative humidity data
    using FAO equation (17).

    Arguments:
    e_tmin  - saturation vapour pressure at daily minimum temperature [kPa]
    e_tmax  - saturation vapour pressure at daily maximum temperature [kPa]
    rh_min  - minimum relative humidity [%]
    rh_max  - maximum relative humidity [%]
    """
    # Raise exceptions:
    if (rh_min < 0 or rh_min > 100):
        raise ValueError ('RH_min=%g is not in range 0-100' % rh_min)
    if (rh_max < 0 or rh_max > 100):
        raise ValueError ('RH_max=%g is not in range 0-100' % rh_max)

    tmp1 = e_tmin * (rh_max / 100.0)
    tmp2 = e_tmax * (rh_min / 100.0)
    ea = (tmp1 + tmp2) / 2.0
    return ea

def ea_from_rhmax(e_tmin, rh_max):
    """
    Calculates actual vapour pressure [kPa] from maximum relative humidity
    using FAO equation (18).

    Arguments:
    e_tmin  - saturation vapour pressure at daily minimum temperature [kPa]
    rh_max  - maximum relative humidity [%]
    """
    # Raise exceptions:
    if (rh_max < 0 or rh_max > 100):
        raise ValueError ('RH_max=%g is not in range 0-100' % rh_max)

    return e_tmin * (rh_max / 100.0)

def ea_from_rhmean(e_tmin, e_tmax, rh_mean):
    """
    Calculates actual vapour pressure, ea [kPa] from mean relative humidity
    (the average of RH min and RH max) using FAO equation (19).

    Arguments:
    e_tmin  - saturation vapour pressure at daily minimum temperature [kPa]
    e_tmax  - saturation vapour pressure at daily maximum temperature [kPa]
    rh_mean - mean relative humidity [%] (average between RH min and RH max)
    """
    # Raise exceptions:
    if (rh_mean < 0 or rh_mean > 100):
        raise ValueError ('RH_mean=%g is not in range 0-100' % rh_mean)

    ea = (rh_mean / 100.0) * ((e_tmax + e_tmin) / 2.0)
    return ea

def ea_from_tdew(tdew):
    """
    Calculates actual vapour pressure, ea [kPa] from the dewpoint temperature
    using equation (14) in the FAO paper. As the dewpoint temperature is the
    temperature to which air needs to be cooled to make it saturated, the
    actual vapour pressure is the saturation vapour pressure at the dewpoint
    temperature. This method is preferable to calculating vapour pressure from
    minimum temperature.

    Arguments:
    tdew - dewpoint temperature [deg C]
    """
    # Raise exception:
    if (tdew < -95.0 or tdew > 65.0):
        # Are these reasonable bounds?
        raise ValueError ('tdew=%g is not in range -95 to +60 deg C' % tdew)

    tmp = (17.27 * tdew) / (tdew + 237.3)
    ea = 0.6108 * math.exp(tmp)
    return ea

def ea_from_twet_tdry(twet, tdry, e_twet, psy_const):
    """
    Calculates actual vapour pressure, ea [kPa] from the wet and dry bulb
    temperatures using equation (15) in the FAO paper. As the dewpoint temp
    is the temp to which air needs to be cooled to make it saturated, the
    actual vapour pressure is the saturation vapour pressure at the dewpoint
    temperature. This method is preferable to calculating vapour pressure from
    minimum temperature. Values for the psychrometric constant of the
    psychrometer (psy_const) can be calculated using the function
    psyc_const_of_psychrometer().

    Arguments:
    twet       - wet bulb temperature [deg C]
    tdry       - dry bulb temperature [deg C]
    e_twet     - saturated vapour pressure at the wet bulb temperature [kPa]
    psy_const  - psychrometric constant of the pyschrometer [kPa deg C-1]
    """
    # Raise exceptions:
    if (twet < -95.0 or twet > 65.0):
        # Are these reasonable bounds?
        raise ValueError ('T_wet=%g is not in range -95 to +65 deg C' % twet)
    elif (tdry < -95.0 or tdry > 65.0):
        # Are these reasonable bounds?
        raise ValueError ('T_dry=%g is not in range -95 to +65 deg C' % tdry)

    ea = e_twet - (psy_const * (tdry - twet))
    return ea

def es_from_t(t):
    """
    Calculates the saturation vapour pressure es [kPa] using equations (11)
    and (12) in the FAO paper (see references).

    Arguments:
    t        - temperature (deg C)
    """
    tmp1 = (17.27 * t) / (t + 237.3)
    es = 0.6108 * math.exp(tmp1)
    return es

def et_rad(lat, sd, sha, irl):
    """
    Calculates daily extraterrestrial radiation ('top of the atmosphere
    radiation') [MJ m-2 day-1] using FAO equation 21. If you require a monthly
    mean radiation figure then make sure the solar declination, sunset
    hour angle and inverse relative distance between earth and sun
    provided as function arguments have been calculated using
    the day of the year (doy) that corresponds to the middle of the month.

    Arguments:
    lat    - latitude [decimal degrees]
    sd     - solar declination [rad]
    sha    - sunset hour angle [rad]
    irl    - inverse relative distance earth-sun [dimensionless]
    """
    # Raise exceptions
    # TODO: raise exceptions for sd and sha
    if (lat < -90.0 or lat > 90.0):
        raise ValueError ('latitude=%g is not in range -90 to +90' % lat)
    if (irl < 0.9669 or irl > 1.0331):
        raise ValueError ('irl=%g is not in range 0.9669-1.0331' % irl)

    solar_const = 0.0820    # Solar constant [MJ m-2 min-1]
    lat_rad = lat  * (math.pi / 180.0)  # Convert decimal degrees to radians

    # Calculate daily extraterrestrial radiation based on FAO equation 21
    tmp1 = (24.0 * 60.0) / math.pi
    tmp2 = sha * math.sin(lat_rad) * math.sin(sd)
    tmp3 = math.cos(lat_rad) * math.cos(sd) * math.sin(sha)
    et_rad = tmp1 * solar_const * irl * (tmp2 + tmp3)
    return et_rad

def hargreaves_ETo(tmin, tmax, tmean, Ra):
    """
    Calcultaes evapotranspiration over grass [mm day-1] using the Hargreaves
    ETo equation. Generally, when solar radiation data, relative humidity data
    and/or wind speed data are missing, they should be estimated using the
    procedures/functions outlined in the comments at the top of this file and
    then ETo calculated using the Penman-Monteith equation.
    As an alternative, ETo can be estimated using the Hargreaves ETo equation.

    tmin    - minimum daily temperaure [deg C]
    tmax    - maximum daily temperaure [deg C]
    tmean   - mean daily temperaure [deg C]
    Ra      - extraterrestrial radiation as equivalent evaporation [mm day-1]
    """
    ETo = 0.0023 * (tmean + 17.8) * (tmax - tmin)**0.5 * Ra
    return ETo

def inv_rel_dist_earth_sun(doy):
    """
    Calculates the inverse relative distance between earth and sun from
    day of the year using FAO equation 23.

    Arguments:
    doy - day of year [between 1 and 366]
    """
    # Raise exception
    if (doy < 1 or doy > 366):
        raise ValueError ('doy=%d is not in range 1-366' % doy)

    inv_rel_dist = 1 + (0.033 * math.cos((2.0 * math.pi / 365.0)* doy))
    return inv_rel_dist

def mean_es(tmin, tmax):
    """
    Calculates mean saturation vapour pressure, es [kPa] using equations (11)
    and (12) in the FAO paper (see references). Mean saturation vapour
    pressure is calculated as the mean of the saturation vapour pressure at
    tmax (maximum temperature) and tmin (minimum temperature).

    Arguments:
    tmin        - minimum temperature (deg C)
    tmax        - maximum temperature (deg C)
    """
    # Raise exceptions
    if (tmin < -95.0 or tmin > 60.0):
        raise ValueError ('tmin=%g is not in range -95 to +60' % tmin)
    elif (tmax < -95.0 or tmax > 60.0):
        raise ValueError ('tmax=%g is not in range -95 to +60' % tmax)

    es_tmin = es_from_t(tmin)
    es_tmax = es_from_t(tmax)
    mean_es = (es_tmin + es_tmax) / 2.0
    return mean_es

def monthly_soil_heat_flux(t_month_prev, t_month_next):
    """
    Estimates the monthly soil heat flux (Gmonth) [MJ m-2 day-1]
    assuming a grass crop from the mean
    air temperature of the previous month and the next month based on FAO
    equation (43). If the air temperature of the next month is not known use
    function monthly_soil_heat_flux2(). The resluting heat flux can be
    converted to equivalent evaporation [mm day-1] using the equiv_evap()
    function.

    Arguments:
    t_month_prev  - mean air temperature of previous month [deg C]
    t_month2_next - mean air temperature of next month [deg C]
    """
    # Raise exceptions
    if (t_month_prev < -95.0 or t_month_prev > 60.0):
        raise ValueError ('t_month_prev=%g is not in range -95 to +60' % t_month_prev)
    elif (t_month_next < -95.0 or t_month_next > 60.0):
        raise ValueError ('t_month_next=%g is not in range -95 to +60' % t_month_next)

    soil_heat_flux = 0.07 * (t_month_next - t_month_prev)
    return soil_heat_flux

def monthly_soil_heat_flux2(t_month_prev, t_month_cur):
    """
    Estimates the monthly soil heat flux (Gmonth) [MJ m-2 day-1]
    assuming a grass crop from the mean
    air temperature of the previous and current month based on FAO
    equation (44). If the air temperature of the next month is available use
    monthly_soil_heat_flux() function instead. The resluting heat flux can be
    converted to equivalent evaporation [mm day-1] using the equiv_evap()
    function.

    Arguments:
    t_month_prev - mean air temperature of previous month [deg C]
    t_month2_cur - mean air temperature of current month [deg C]
    """
    # Raise exceptions
    if (t_month_prev < -95.0 or t_month_prev > 60.0):
        raise ValueError ('t_month_prev=%g is not in range -95 to +60' % t_month_prev)
    elif (t_month_cur < -95.0 or t_month_cur > 60.0):
        raise ValueError ('t_month_cur=%g is not in range -95 to +60' % t_month_cur)

    soil_heat_flux = 0.14 * (t_month_cur - t_month_prev)
    return soil_heat_flux

def net_out_lw_rad(tmin, tmax, sol_rad, clear_sky_rad, ea):
    """
    Calculates net outgoing longwave radiation [MJ m-2 day-1] based on
    FAO equation 39. This is the net longwave energy (net energy flux) leaving
    the earth's surface. It is proportional to the absolute temperature of
    the surface raised to the fourth power according to the Stefan-Boltzmann
    law. However, water vapour, clouds, carbon dioxide and dust are absorbers
    and emitters of longwave radiation. This function corrects the Stefan-
    Boltzmann law for humidty (using actual vapor pressure) and cloudiness
    (using solar radiation and clear sky radiation). The concentrations of all
    other absorbers are assumed to be constant. The output can be converted
    to equivalent evapouration [mm day-1] using the equiv_evap() function.

    Arguments:
    tmin          - absolute daily minimum temperature [deg C]
    tmax          - absolute daily maximum temperature [deg C]
    sol_rad       - solar radiation [MJ m-2 day-1]
    clear_sky_rad - clear sky radiation [MJ m-2 day-1]
    ea            - actual vapour pressure [kPa]
    """
    # Raise exceptions
    # TODO: raise exceptions for radiation and avp
    if (tmin < -95.0 or tmin > 60.0):
        raise ValueError ('tmin=%g is not in range -95 to +60' % tmin)
    elif (tmax < -95.0 or tmax > 60.0):
        raise ValueError ('tmax=%g is not in range -95 to +60' % tmax)

    # Convert temps in deg C to Kelvin
    tmin_abs = tmin + 273.15
    tmax_abs = tmax + 273.15

    sb_const = 0.000000004903 # Stefan-Boltzmann constant [MJ K-4 m-2 day-1]
    tmp1 = sb_const * ((math.pow(tmax_abs, 4) + math.pow(tmin_abs, 4)) / 2)
    tmp2 = 0.34 - (0.14 * math.sqrt(ea))
    tmp3 = 0.0 # REMOVE THIS
    try:
        tmp3 = 1.35 * (sol_rad / clear_sky_rad) - 0.35
    except:
        print ('sol_rad', sol_rad, 'clear_sky_rad:', clear_sky_rad)
    net_out_lw_rad = tmp1 * tmp2 * tmp3
    return net_out_lw_rad

def net_rad(ni_sw_rad, no_lw_rad):
    """
    Calculates daily net radiation [MJ m-2 day-1] at the crop surface
    based on FAO equations 40 assuming a grass reference crop.
    Net radiation is the difference between the incoming net shortwave (or
    solar) radiation and the outgoing net longwave radiation. Output can be
    converted to equivalent evaporation [mm day-1] using the equiv_evap()
    function.

    Arguments:
    ni_sw_rad - net incoming shortwave radiation [MJ m-2 day-1]
    no_lw_rad - net outgoing longwave radiation [MJ m-2 day-1]
    """
    # Raise exceptions
    # TODO: raise exceptions for radiation arguments
    net_rad = ni_sw_rad - no_lw_rad
    return net_rad

def net_in_sol_rad(sol_rad):
    """
    Calculates net incoming solar (also known as shortwave)
    radiation [MJ m-2 day-1]
    based on FAO equation 38 for a grass reference crop. This is the net
    shortwave radiation resulting from the balance between incoming and
    reflected solar radiation. The output can be converted to
    equivalent evaporation [mm day-1] using the equiv_evap() function.

    Arguments:
    sol_rad     - (gross) incoming solar radiation [MJ m-2 day-1]
    """
    # Raise exceptions
    # TODO: Put in sensible boundaries for solar radiation
    #if (sol_rad < ?? or sol_rad > ??):
    #    raise ValueError, 'sol_rad=%g is not in range 0-366' %sol_rad

    grass_albedo = 0.23     # albedo coefficient for grass [dimensionless]
    net_in_sw_rad = (1 - grass_albedo) * sol_rad
    return net_in_sw_rad

def penman_monteith_ETo(Rn, t, ws, es, ea, delta_es, psy, shf=0.0):
    """
    Calculates the evapotransporation (ETo) [mm day-1] from a hypothetical
    grass reference surface using the FAO Penman-Monteith equation (equation 6).

    Arguments:
    Rn       - net radiation at crop surface [MJ m-2 day-1]
    t        - air temperature at 2 m height [deg C]
    ws       - wind speed at 2 m height [m s-1]. If not measured at 2m,
                convert using wind_speed_at_2m()
    es       - saturation vapour pressure [kPa]
    ea       - actual vapour pressure [kPa]
    delta_es - slope of vapour pressure curve [kPa  deg C]
    psy      - psychrometric constant [kPa deg C]
    shf      - soil heat flux (MJ m-2 day-1] (default = 0, fine for daily
               time step)
    """
    # TODO: raise exceptions for radiation and avp/svp etc.
    if (t < -95.0 or t > 60.0):
        raise ValueError ('t=%g is not in range -95 to +60' % t)
    elif (ws < 0.0 or ws > 150.0):
        raise ValueError ('ws=%g is not in range 0-150' % ws)

    # Convert t in deg C to deg Kelvin
    t += 273.15
    # Calculate evapotranspiration (ET0)
    a1 = 0.408 * (Rn - shf) * delta_es / (delta_es + (psy * (1 + 0.34 * ws)))
    a2 = 900 * ws / t * (es - ea) * psy / (delta_es + (psy * (1 + 0.34 * ws)))
    ETo = a1 + a2
    return ETo

def psy_const(atmos_pres):
    """
    Calculates the psychrometric constant (kPa degC-1) using equation (8)
    in the FAO paper (see references below) page 95. This method assumes that
    the air is saturated with water vapour at T_min. This assumption may not
    hold in arid areas.

    Arguments:
    atmos_pres - atmospheric pressure [kPa]
    """
    # TODO: raise exception if atmos_press outside sensible bounds
    return 0.000665 * atmos_pres

def psy_const_of_psychrometer(psychrometer, atmos_pres):
    """
    Calculates the psychrometric constant [kPa deg C-1] for different
    types of psychrometer at a given atmospheric pressure using FAO equation
    16.

    Arguments:
    psychrometer - integer between 1 and 3 which denotes type of psychrometer
                 - 1 = ventilated (Asmann or aspirated type) psychrometer with
                   an air movement of approx. 5 m s-1
                 - 2 = natural ventilated psychrometer with an air movement
                   of approx. 1 m s-1
                 - 3 = non ventilated psychrometer installed indoors
    atmos_pres - atmospheric pressure [kPa]
    """
    # TODO: raise exception if atmos_press outside sensible bounds
    if (psychrometer < 1 or psychrometer > 3):
        raise ValueError ('psychrometer=%d not in range 1-3' % psychrometer)

    # Assign values to coefficient depending on type of ventilation of the
    # wet bulb
    if (psychrometer == 1):
        psy_coeff = 0.000662
    elif (psychrometer == 2):
        psy_coeff = 0.000800
    elif (psychrometer == 3):
        psy_coeff = 0.001200

    pys_const = psy_coeff * atmos_pres
    return pys_const

def rad2equiv_evap(energy):
    """
    Converts radiation in MJ m-2 day-1 to the equivalent evaporation in
    mm day-1 assuming a grass reference crop using FAO equation 20.
    Energy is converted to equivalent evaporation using a conversion
    factor equal to the inverse of the latent heat of vapourisation
    (1 / lambda = 0.408).

    Arguments:
    energy - energy e.g. radiation, heat flux [MJ m-2 day-1]
    """
    # Determine the equivalent evaporation [mm day-1]
    equiv_evap = 0.408 * energy
    return equiv_evap

def rh_from_ea_es(ea, es):
    """
    Calculates relative humidity as the ratio of actual vapour pressure
    to saturation vapour pressure at the same temperature (see FAO paper
    p. 67).

    ea - actual vapour pressure [units don't matter as long as same as es]
    es - saturated vapour pressure [units don't matter as long as same as ea]
    """
    return 100.0 * ea / es

def sol_dec(doy):
    """
    Calculates solar declination [rad] from day of the year based on FAO
    equation 24.

    Arguments:
    doy - day of year (between 1 and 366)
    """
    # Raise exceptions
    if (doy < 1 or doy > 366):
        raise ValueError ('doy=%d is not in range 1-366' %doy)

    # Calculate solar declination [radians] using FAO eq. 24
    solar_dec = 0.409 * math.sin(((2.0 * math.pi / 365.0) * doy - 1.39))
    return solar_dec

def sol_rad_from_sun_hours(dl_hours, sun_hours, et_rad):
    """
    Calculates incoming solar (or shortwave) radiation [MJ m-2 day-1]
    (radiation hitting a horizontal plane after scattering by the atmosphere)
    from relative sunshine duration based on FAO equations 34 and 35.
    If measured radiation data are not available this
    method is preferable to calculating solar radiation from temperature .
    If a monthly mean is required then divide the monthly number
    of sunshine hours by number of days in month and ensure that et_rad and
    daylight hours was calculated using the day of the year that
    corresponds to the middle of the month.

    Arguments:
    dl_hours     - number of daylight hours [hours]
    sun_hours    - sunshine duration [hours]
    et_rad       - extraterrestrial radiation [MJ m-2 day-1]
    """
    # Raise exceptions
    # TODO: Raise exception for et_rad
    if (sun_hours < 0 or sun_hours > 24):
        raise ValueError ('sunshine hours=%g is not in range 0-24' % sun_hours)
    elif (dl_hours < 0 or dl_hours > 24):
        raise ValueError ('daylight hours=%g is not in range 0-24' % dl_hours)

    # Use default values of regression constants (Angstrom values)
    # recommended by FAO when calibrated values are unavailable.
    a = 0.25
    b = 0.50
    solar_rad = (b * sun_hours / dl_hours + a) * et_rad
    return solar_rad

def sol_rad_from_t(et_rad, cs_rad, tmin, tmax, coastal=-999):
    """
    Calculates incoming solar (or shortwave) radiation (Rs) [MJ m-2 day-1]
    (radiation hitting a horizontal plane after scattering by the atmosphere)
    from min and max temperatures together with
    an empirical adjustment coefficient for 'interior' and
    'coastal' regions. The formula is based on FAO equation 50 which
    is the Hargreaves' radiation formula (Hargreaves and Samani, 1982, 1985).
    This method should be used only when solar radiation or sunshine hours data
    are not available. It is only recommended for locations where it is not
    possible to use radiation data from a regional station (either because
    climate conditions are hetergeneous or data are lacking).
    NOTE: this method is not suitable for island locations
    due to the moderating effects of the surrounding water.

    Arguments:
    et_rad  - extraterrestrial radiation [MJ m-2 day-1]
    cs_rad  - clear sky radiation [MJ m-2 day-1]
    tmin    - daily minimum temperature [deg C]
    tmax    - daily maximum temperature [deg C]
    coastal - True if site is a coastal location, situated on or adjacent to
              coast of a large land mass and where air masses are influence
              by a nearby water body, False if interior location where land
              mass dominates and air masses are not strongly influenced by a
              large water body. -999 indicates no data.
    """
    # Raise exceptions
    # TODO: raise exceptions for cs_rad
    if (tmin < -95.0 or tmin > 60.0):
        raise ValueError ('tmin=%g is not in range -95 to +60' % tmin)
    elif (tmax < -95.0 or tmax > 60.0):
        raise ValueError ('tmax=%g is not in range -95 to +60' % tmax)

    # determine value of adjustment coefficient [deg C-0.5] for
    # coastal/interior locations
    if (coastal == True):
        adj = 0.19
    elif (coastal == False):
        adj = 0.16
    else:
        # hedge our bets and give a mean adjustment values and issue a warning
        adj = 0.175
        print ("""WARNING! Location not specified as coastal or interior for
        calculation of solar radiation. Using defalut adjustment factor.""")

    solar_rad = adj * math.sqrt(tmax - tmin) * et_rad

    # The solar radiation value is constrained (<=) by the clear sky radiation
    if (solar_rad > cs_rad):
        solar_rad = cs_rad
    return solar_rad

def sol_rad_island(et_rad):
    """
    Estimates incoming solar (or shortwave) radiation [MJ m-2 day-1]
    (radiation hitting a horizontal plane after scattering by the atmosphere)
    for an island location using FAO equation 51. An island is defined as a
    land mass with width perpendicular to the coastline <= 20 km. Use this
    method only if radiation data from elsewhere on the island is not
    available. NOTE: This method is only applicable for low altitudes (0-100 m)
    and monthly calculations.

    Arguments:
    et_rad  - extraterrestrial radiation [MJ m-2 day-1]
    """
    solar_rad = (0.7 * et_rad) - 4.0
    return solar_rad

def sunset_hour_angle(lat, sd):
    """
    Calculates sunset hour angle [rad] from latitude and solar
    declination using FAO equation 25.

    Arguments:
    lat    - latitude [decimal degrees] Note: value should be negative if it is
             degrees south, positive if degrees north
    sd     - solar declination [rad]
    """
    # Raise exceptions
    if lat < -90.0 or lat > 90.0:
        raise ValueError ('latitude=%g is not in range -90 - 906' %lat)

    # Convert latitude from decimal degrees to radians
    lat_rad = lat * (math.pi / 180.0)

    # Calculate sunset hour angle (sha) [radians] from latitude and solar
    # declination using FAO equation 25
    tmp = -math.tan(lat_rad) * math.tan(sd)
    # Domain of acos = -1 <= x <= 1; this is not pointed out by FAO
    tmp = max(tmp, -0.999999)
    tmp = min(tmp, 0.999999)
    sha = math.acos(tmp)
    return sha

def wind_speed_2m(meas_ws, z):
    """
    Converts wind speeds measured at different heights above the soil
    surface to wind speed at 2 m above the surface, assuming a short grass
    surface. Formula based on FAO equation 47.

    Arguments:
    meas_ws - measured wind speed [m s-1]
    z       - height of wind measurement above ground surface [m]
    """
    # Raise exceptions
    if (meas_ws < 0.0 or meas_ws > 150.0):
        raise ValueError ('meas_ws=%g is not in range 0-150 m s-1' % meas_ws)
    elif (z < 0.0 or z > 100.0):
        raise ValueError ('z=%g is not in range 0-100 m' % z)

    tmp1 = (67.8 * z) - 5.42
    ws2m = meas_ws * (4.87 / math.log(tmp1))
    return ws2m
