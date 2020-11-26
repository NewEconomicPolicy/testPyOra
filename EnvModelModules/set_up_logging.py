"""
#-------------------------------------------------------------------------------
# Name:        set_up_logging.py
# Purpose:     script to read read and write the setup and configuration files
# Author:      Mike Martin
# Created:     31/07/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
"""

__prog__ = 'set_up_logging.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
import os
import logging
import time
import sys
from glob import glob

bbox_default = [116.90045, 28.2294, 117.0, 29.0] # bounding box default - somewhere in SE Europe
sleepTime = 5

def set_up_logging(form, appl_name):
    '''
    # this function is called to setup logging
    '''

    # for log file
    date_stamp = time.strftime('_%Y_%m_%d_%I_%M_%S')
    log_file_name = appl_name + date_stamp + '.log'

    # set up logging
    # ==============
    log_dir = form.settings['log_dir']
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)

    log_fname = os.path.join(log_dir, log_file_name)

    # Setup up initial logger to handle logging prior to setting up the
    # full logger using config options
    form.lgr = logging.getLogger(appl_name)
    form.lgr.setLevel(logging.INFO)
    fh = logging.FileHandler(log_fname)    # send log recs (created by loggers) to appropriate destination
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)  # specify layout of records
    form.lgr.addHandler(fh)

    # if more than 15 or so files then delete oldest
    # ==============================================
    log_flist = glob(os.path.normpath(log_dir + '/' + appl_name + '*.log'))
    list_len = len(log_flist)
    max_log_files = 10
    num_to_delete = list_len - max_log_files
    if num_to_delete > 0:
        # date order list
        log_flist.sort(key=os.path.getmtime)
        for ifile in range(num_to_delete):
            try:
                os.remove(log_flist[ifile])
                form.lgr.info('removed log file: ' + log_flist[ifile])
            except (OSError, IOError) as e:
                print('Failed to delete log file: {0}'.format(e))

    return
