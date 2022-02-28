#-------------------------------------------------------------------------------
# Name:        display_gui_charts.py
# Purpose:     displays a table and chart of data
# Author:      Mike Martin
# Created:     14/04/2020
# Licence:     <your licence>
# Description:#
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'display_gui_charts.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, \
                                                                                        QPushButton, QLineEdit, QLabel
from PyQt5.QtChart import QChart, QValueAxis, QChartView, QLineSeries, QScatterSeries
from random import random
from math import floor, ceil

from ora_lookup_df_fns import fetch_detail_from_varname

SUBAREAS = list(['Blackburn', 'Todmorden', 'Bury', 'Oldham', 'Rochdale'])   # for generation of random data
NTSTEPS = 240

SET_INDICES = {'carbon':0, 'nitrogen':1, 'soil_water':2, 'crop_model':None, 'livestock':None, 'economics' :None}    # lookup table for data object
WARNING_STR = '*** Warning *** '
LRGE_NUM = 99999999
THRESHOLD = 1e-10

def _check_yaxis_extent(ymin, ymax):
    '''
    adjust Y extent to sensible values
    '''
    if ymin > ymax:
        ytmp = ymin
        ymin = ymax
        ymax = ytmp

    # adjust by 5% each way when extent is almost zero
    # ================================================
    diff = ymax - ymin
    if diff < THRESHOLD:
        frac5 = 0.05*abs(max(0.1, diff))
        ymax += frac5
        ymin -= frac5

    return ymin, ymax

def display_metric(form, category, metric, sba, recalc_flag):

    rslts_set = _select_data_for_display(form, category, metric, sba, recalc_flag)
    if rslts_set is None:
        return

    subareas, data_for_display, ntsteps, description, units, out_format, pyora_display, yaxis_min, yaxis_max = rslts_set

    form.second = Second('example sub-window', subareas, ntsteps, description)
    form.second.post_line_series(yaxis_min, yaxis_max, subareas, data_for_display, ntsteps, units,
                                                                            out_format, pyora_display)
    form.second.show()

class Second(QWidget):
    '''

    '''
    def __init__(self, title, subareas, ntsteps, description, parent = None):

        # calls the __init__() of the QWidget class, allowing you to use it in the DispSubareaMgmt class without repeating code
        super(Second, self).__init__(parent)

        CHART_MIN_WDTH = 1200
        TABLE_MIN_WDTH = 625
        TABLE_MAX_WDTH = 700

        self.setWindowTitle(title)
        # self.setWindowFlags(Qt.WindowStaysOnTopHint)

        # Table - one column for each subarea
        # ===================================
        w_table = QTableWidget()

        w_table.setMinimumWidth(TABLE_MIN_WDTH)
        w_table.setMaximumWidth(TABLE_MAX_WDTH)
        w_table.setRowCount(ntsteps)
        w_table.setColumnCount(len(subareas))
        w_table.setHorizontalHeaderLabels(subareas)
        self.w_table = w_table

        # LH vertical box consists of table only
        # ======================================
        lh_vbox = QVBoxLayout()
        lh_vbox.addWidget(w_table)

        # Chart - one line for each subarea
        # =================================
        w_chart = QChart()
        w_chart.legend().setVisible(True)
        w_chart.legend().setAlignment(Qt.AlignBottom)

        w_chart.setTitle(description)
        w_chart.setAnimationOptions(QChart.SeriesAnimations)
        w_chart.setMinimumWidth(CHART_MIN_WDTH)
        self.w_chart = w_chart

        chart_view = QChartView(w_chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        # this horizontal box consists of the chart only
        # ==============================================
        chart_layout = QHBoxLayout()
        chart_layout.addWidget(chart_view)

        # Control panel for buttons and text box
        # ======================================
        w_dump = QPushButton("Dump")
        w_dump.setFixedWidth(60)
        helpText = 'Write table and chart to Excel spreadsheet'
        w_dump.setToolTip(helpText)
        w_dump.clicked.connect(self.dumpClicked)

        w_rfrsh = QPushButton("Refresh")
        w_rfrsh.setFixedWidth(60)
        w_rfrsh.clicked.connect(self.refreshClicked)

        w_reset = QPushButton("Reset")
        w_reset.setFixedWidth(60)
        w_reset.clicked.connect(self.resetClicked)

        w_dismiss = QPushButton("Dismiss")
        w_dismiss.setFixedWidth(60)
        w_dismiss.clicked.connect(self.dismissClicked)

        w_min_yval = QLineEdit()
        w_min_yval.setFixedWidth(60)
        self.w_min_yval = w_min_yval

        w_max_yval = QLineEdit()
        w_max_yval.setFixedWidth(60)
        self.w_max_yval = w_max_yval

        cntrl_layout = QHBoxLayout()
        cntrl_layout.addWidget(w_dump)
        cntrl_layout.addWidget(w_rfrsh)
        cntrl_layout.addWidget(w_reset)
        cntrl_layout.addWidget(QLabel('   Y Min:'))
        cntrl_layout.addWidget(w_min_yval)
        cntrl_layout.addWidget(QLabel('   Y Max:'))
        cntrl_layout.addWidget(w_max_yval)
        cntrl_layout.addWidget(QLabel('\t\t'))
        cntrl_layout.addWidget(w_dismiss)
        cntrl_layout.addWidget(QLabel(), 1)

        # RH box consists of chart and grid boxes
        # ======================================
        rh_vbox = QVBoxLayout()
        rh_vbox.addLayout(chart_layout)
        rh_vbox.addLayout(cntrl_layout)

        # add LH and RH vertical boxes to horizontal box
        # ==============================================
        outer_layout = QHBoxLayout()
        outer_layout.addLayout(lh_vbox)
        outer_layout.addLayout(rh_vbox)  # vertical box goes into horizontal box
        self.setLayout(outer_layout)  # the horizontal box fits inside the window

        self.setGeometry(50, 250, 1000, 500)  # posx, posy, width, height

    def post_line_series(self, yaxis_min, yaxis_max, subareas = None, data_for_display = None, ntsteps = None,
                                                            units = None, out_format = None, pyora_display = None):
        '''
        create a dictionary of line series and populate table widget from data for each subarea
        '''
        if subareas is None:
            ndecimals = self.ndecimals
            subareas = self.subareas
            data_for_display = self.data_for_display
            ntsteps = self.ntsteps
            units = self.units
            ndecimals = self.ndecimals
            pyora_display = self.pyora_display
            self.w_chart.removeAllSeries()
            # self.w_chart.removeAxis()
        else:
            self.ymin_orig = yaxis_min
            self.ymax_orig = yaxis_max
            ndecimals = int(out_format.rstrip('f'))

        line_series = {}
        for icol_indx, subarea in enumerate(subareas):
            lseries = QLineSeries()
            # lseries = QScatterSeries()
            lseries.setName(subarea)
            for irow_indx, val in enumerate(data_for_display[subarea]):
                self.w_table.setItem(irow_indx, icol_indx, QTableWidgetItem(str(round(val, ndecimals))))
                lseries.append(irow_indx + 1, val)

            line_series[subarea] = lseries
            self.w_chart.addSeries(lseries)

        lseries = line_series[subareas[0]]
        axis = QValueAxis(lseries)
        axis.setRange(1, ntsteps)
        axis.setTitleText("Time step")
        axis.applyNiceNumbers()

        self.w_chart.createDefaultAxes()

        # required for each line series
        # =============================
        for subarea in subareas:
            self.w_chart.setAxisX(axis, line_series[subarea])

        yaxis_min, yaxis_max = _check_yaxis_extent(yaxis_min, yaxis_max)

        self.w_chart.axisY(lseries).setRange(yaxis_min, yaxis_max)
        self.w_chart.axisY(lseries).setTitleText(pyora_display + ' ' + units)

        self.w_min_yval.setText(str(round(yaxis_min,4)))
        self.w_max_yval.setText(str(round(yaxis_max,4)))

        self.ndecimals = ndecimals
        self.subareas = subareas
        self.data_for_display = data_for_display
        self.ntsteps = ntsteps
        self.units = units
        self.ndecimals = ndecimals
        self.pyora_display = pyora_display

    def dumpClicked(self):

        print('Not active')

    def dismissClicked(self):

        self.close()
        
    def refreshClicked(self):
        '''
        redisplay chart
        '''
        try:
            ymin = float(self.w_min_yval.text())
        except ValueError as err:
            ymin = None

        try:
            ymax = float(self.w_max_yval.text())
        except ValueError as err:
            ymax = None

        if ymin is None or ymax is None:
            self.post_line_series(self.ymin_orig, self.ymax_orig)
        else:
            self.post_line_series(ymin, ymax)

    def resetClicked(self):

        self.post_line_series(self.ymin_orig, self.ymax_orig)

    def print_mess(self):

        print('Garbage')

def _generate_random_data(w_report):

    w_report.append('Will generate random data')
    #                 =========================
    subareas = SUBAREAS

    descrip = 'Randomly generated data'
    ntsteps = 240;
    yaxis_min = 0.0;
    yaxis_max = 50.0;
    pyora_display = 'Random data';
    units = 'km**2'
    out_format = '2f'

    NTSTEPS = 240

    data_for_display = {}
    for subarea in subareas:
        series = []
        for tstep in range(NTSTEPS):
            series.append(random() * 33)
        data_for_display[subarea] = series

    rslts_set = (subareas, data_for_display, ntsteps, descrip, units, out_format, pyora_display, yaxis_min, yaxis_max)

    return rslts_set

def _select_data_for_display(form, category, metric, sba, recalc_flag):
    '''

    '''
    group_indx = SET_INDICES[category]

    if metric is None:
        rslts_set = _generate_random_data(form.w_report)
    else:
        # actual data
        # ===========
        if group_indx is None:
            if category == 'livestock':
                all_runs_output = form.all_farm_livestock_production
            elif category == 'crop_model':
                all_runs_output = form.all_runs_crop_model
            elif category == 'economics':
                all_runs_output = form.economics_calcs
        else:
            if recalc_flag:
                # instead of subareas use increments
                # ==================================
                all_runs_output = form.recalc_runs_fwd[sba]
            else:
                all_runs_output = form.all_runs_output

        subareas = list(all_runs_output.keys())
        description, units, out_format, pyora_display = fetch_detail_from_varname(form.settings['lookup_df'], metric)

        yaxis_min =  LRGE_NUM
        yaxis_max = -LRGE_NUM
        data_for_display = {}
        for subarea in subareas:
            if group_indx is None:
                this_data = all_runs_output[subarea].data[metric]
            else:
                this_data = all_runs_output[subarea][group_indx].data[metric]

            if len(this_data) == 0:
                mess = WARNING_STR + 'could not display metric: ' + metric
                if hasattr(form, 'w_report'):
                    form.w_report.append(mess)
                else:
                    print(mess)
                return None

            data_for_display[subarea] = this_data
            yaxis_min = min(yaxis_min, min(this_data))
            yaxis_max = max(yaxis_max, max(this_data))

        ntsteps = len(data_for_display[subareas[0]])
        ndecimals = int(out_format.rstrip('f'))
        rslts_set = (subareas, data_for_display, ntsteps, description, units, out_format, pyora_display,
                                                                                            yaxis_min, yaxis_max)
    return rslts_set
