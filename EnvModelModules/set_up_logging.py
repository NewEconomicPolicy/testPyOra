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
from os.path import join, normpath, getmtime, isdir
from os import makedirs, remove
import logging
import time
from glob import glob
from PyQt5.QtGui import QTextCursor

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
    if not isdir(log_dir):
        makedirs(log_dir)

    log_fname = join(log_dir, log_file_name)

    # Setup up initial logger to handle logging prior to setting up the
    # full logger using config options
    form.lggr = logging.getLogger(appl_name)
    form.lggr.setLevel(logging.INFO)
    fh = logging.FileHandler(log_fname)    # send log recs (created by loggers) to appropriate destination
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)  # specify layout of records
    form.lggr.addHandler(fh)

    # if more than 15 or so files then delete oldest
    # ==============================================
    log_flist = glob(normpath(log_dir + '/' + appl_name + '*.log'))
    list_len = len(log_flist)
    max_log_files = 10
    num_to_delete = list_len - max_log_files
    if num_to_delete > 0:
        # date order list
        log_flist.sort(key=getmtime)
        for ifile in range(num_to_delete):
            try:
                remove(log_flist[ifile])
                form.lggr.info('removed log file: ' + log_flist[ifile])
            except (OSError, IOError) as e:
                print('Failed to delete log file: {0}'.format(e))

    return

class OutLog:
    def __init__(self, edit, out=None, color=None):
        """
        can write stdout, stderr to a QTextEdit widget
        edit = QTextEdit
        out = alternate stream (can be the original sys.stdout)
        color = alternate color (i.e. color stderr a different color)
        """
        self.edit = edit
        self.out = None
        self.color = color

    def flush(self):

        pass

    def write(self, mstr):
        if self.color:
            tc = self.edit.textColor()
            self.edit.setTextColor(self.color)

        self.edit.moveCursor(QTextCursor.End)
        self.edit.insertPlainText( mstr )

        if self.color:
            self.edit.setTextColor(tc)

        if self.out:
            self.out.write(mstr)