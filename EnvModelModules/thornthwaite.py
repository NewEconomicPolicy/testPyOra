#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      soi698
#
# Created:     07/10/2011
# Copyright:   (c) soi698 2011
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import calendar
import math

import fao_eto as fao

_monthdays = [31,28,31,30,31,30,31,31,30,31,30,31]
_leap_monthdays = [31,29,31,30,31,30,31,31,30,31,30,31]

def thornthwaite(monthly_t, lat, year=None):
    """
    Calculates Potentional Evapotranspiration [mm/month] for each month of the
    year using the Thornthwaite (1948) method.

    Arguments:
    monthly_t - Mean daily air temperature for each month of the year [deg C]
    lat       - Latitude [decimal degrees]
    year      - The year for which PET is required. The only effect of year
                is to change the number of days in Feb to 29 if it is a leap
                year. If left as the default, None, then a normal (non-leap)
                year is assumed.
    Return:
    pet       - List estimated PET for each month in the year [mm/month]
    """
    # Thornthwaite equation:
    # PET = 1.6 (L/12) (N/30) (10Ta / I)**a
    # Ta is the mean daily air temperature [deg C, if negative use 0] of the month being calculated
    # N is the number of days in the month being calculated
    # L is the mean day length [hours] of the month being calculated
    # a = (6.75 x 10-7)I**3 - (7.71 x 10-5)I**2 + (1.792 x 10-2)I + 0.49239
    # I is a heat index which depends on the 12 monthly mean temperatures
    #     calculated as the sum of (Tai / 5)**1.514 for each month
    #     where Tai is the air temperature for each month in the year

    if year == None or not calendar.isleap(year):
        month_days = _monthdays
    else:
        month_days = _leap_monthdays

    # Negative temperatures should be set to zero
##    monthly_t[:] = [0.0 if t < 0 else t for t in monthly_t] # Doesn't seem to work on Python 2.4 on RHEL
    monthly_t = [t * (t >= 0) for t in monthly_t]  # Does same as above but works on earlier versions of Python

    # Calculate the heat index
    I = 0.0
    for Tai in monthly_t:
        if Tai / 5.0 > 0.0:
           I += (Tai / 5.0)**1.514

    # Calculate the 'a' parameter
    a = (6.75e-07 * I**3) - (7.71e-05 * I**2) + (1.792e-02 * I) + 0.49239

    # Calculate mean daylength (daylight hours) of each month
    monthly_mean_dlh = _monthly_mean_daylight_hours(lat, year)

    # Calculate PET (* 10 to convert cm to mm)
    pet = []
    for Ta, L, N in zip(monthly_t, monthly_mean_dlh, month_days):
        # Multiply by 10: cm/month --> mm/month
        pet.append(1.6 * (L / 12.0) * (N / 30.0) * ((10.0 * Ta / I)**a) * 10.0)

    return pet

def _monthly_mean_daylight_hours(lat, year=None):
    """
    Calculates the mean daylength (daylight hours) for each month of the year
    at a given latitude. Note, leapyears are not handled.

    Arguments:
    lat       - Latitude [decimal degrees]
    year      - The year for which PET is required. The only effect of year
                is to change the number of days in Feb to 29 if it is a leap
                year. If left as the default, None, then a normal (non-leap)
                year is assumed.

    Returns:
    monthly_mean_dlh - List of mean daylight hours of each month of a year [hours]
    """
    if year == None or not calendar.isleap(year):
        month_days = _monthdays
    else:
        month_days = _leap_monthdays
    monthly_mean_dlh = []
    doy = 1    # Day of the year
    for mdays in month_days:
        dlh = 0   # Cumulative daylight hours
        for daynum in range (1, mdays+1):
            sd = fao.sol_dec(doy)    # Solar declination
            sha = fao.sunset_hour_angle(lat, sd)    # Sunset hour angle
            dlh += fao.daylight_hours(sha) # Daylight hours (daylength)
            doy +=1
        # Calc mean day length for the month
        monthly_mean_dlh.append(dlh / mdays)
    return monthly_mean_dlh
