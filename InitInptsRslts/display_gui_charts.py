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
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, QTableWidget, QTableWidgetItem, \
                                                            QPushButton, QLineEdit, QLabel
from PyQt5.QtChart import QChart, QValueAxis, QChartView, QLineSeries
from random import random
from math import floor, ceil

from ora_lookup_df_fns import fetch_metric_detail

SUBAREAS = list(['Blackburn', 'Todmorden', 'Bury', 'Oldham', 'Rochdale'])   # for generation of random data
NTSTEPS = 240

SET_INDICES = {'carbon':0, 'nitrogen':1, 'soil_water':2}    # lookup table for data object
WARNING_STR = '*** Warning *** '
LRGE_NUM = 99999999

def display_metric(form, category, metric):

    subareas, data_for_display, ntsteps, description, units, out_format, pyora_display, yaxis_min, yaxis_max = \
                                                                _select_data_for_display(form, category, metric)
    if subareas is None:
        return

    form.second = Second('example sub-window', subareas, ntsteps, description)
    form.second.post_line_series(yaxis_min, yaxis_max, subareas, data_for_display, ntsteps, units,
                                                                            out_format, pyora_display)
    form.second.show()

class Second(QWidget):
    '''

    '''
    def __init__(self, title, subareas, ntsteps, description, parent = None):

        # calls the __init__() of the QWidget class, allowing you to use it in the Second class without repeating code
        super(Second, self).__init__(parent)

        CHART_MIN_WDTH = 1200
        TABLE_MIN_WDTH = 625

        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        # Table - one column for each subarea
        # ===================================
        w_table = QTableWidget()

        w_table.setMinimumWidth(TABLE_MIN_WDTH)
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
        rfrshButton = QPushButton("Refresh")
        rfrshButton.setFixedWidth(60)
        rfrshButton.clicked.connect(self.refreshClicked)

        resetButton = QPushButton("Reset")
        resetButton.setFixedWidth(60)
        resetButton.clicked.connect(self.resetClicked)

        dismiss = QPushButton("Dismiss")
        dismiss.setFixedWidth(60)
        dismiss.clicked.connect(self.dismissClicked)

        w_min_yval = QLineEdit()
        w_min_yval.setFixedWidth(60)
        self.w_min_yval = w_min_yval

        w_max_yval = QLineEdit()
        w_max_yval.setFixedWidth(60)
        self.w_max_yval = w_max_yval

        cntrl_layout = QHBoxLayout()
        cntrl_layout.addWidget(rfrshButton)
        cntrl_layout.addWidget(resetButton)
        cntrl_layout.addWidget(QLabel('   Y Min:'))
        cntrl_layout.addWidget(w_min_yval)
        cntrl_layout.addWidget(QLabel('   Y Max:'))
        cntrl_layout.addWidget(w_max_yval)
        cntrl_layout.addWidget(QLabel('\t\t'))
        cntrl_layout.addWidget(dismiss)
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
            ndecimals = int(out_format.rstrip('f'))

        line_series = {}
        for icol_indx, subarea in enumerate(subareas):
            lseries = QLineSeries()
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

        self.w_chart.axisY(lseries).setRange(yaxis_min, yaxis_max)
        self.w_chart.axisY(lseries).setTitleText(pyora_display + ' ' + units)

        self.ndecimals = ndecimals
        self.subareas = subareas
        self.data_for_display = data_for_display
        self.ntsteps = ntsteps
        self.units = units
        self.ndecimals = ndecimals
        self.pyora_display = pyora_display

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

        if ymin is not None and ymax is not None:
            if ymin > ymax:
                ytmp = ymin
                ymin = ymax
                ymax = ytmp

            if ymin == ymax:
                ymax += 10.0

        self.post_line_series(ymin, ymax)
        pass

    def resetClicked(self):

        pass

    def print_mess(self):

        print('Garbage')

def _select_data_for_display(form, category, metric):
    '''

    '''
    group_indx = SET_INDICES[category]

    if metric is None:
        form.w_report.append('Will generate random data')
        #                     =========================
        subareas = SUBAREAS
        description = 'Randomly generated data'
        ntsteps = 240; yaxis_min = 0.0; yaxis_max = 50.0; pyora_display = 'Random data'; units = 'km**2'
        out_format = '2f'

        NTSTEPS = 240

        data_for_display = {}
        for subarea in subareas:
            series = []
            for tstep in range(NTSTEPS):
                series.append(random() * 33)
            data_for_display[subarea] = series
    else:
        # actual data
        # ===========
        all_runs_output = form.all_runs_output
        subareas = list(all_runs_output.keys())
        description, units, out_format, pyora_display = fetch_metric_detail(form.settings['lookup_df'], metric)

        yaxis_min =  LRGE_NUM
        yaxis_max = -LRGE_NUM
        data_for_display = {}
        for subarea in subareas:
            this_data = all_runs_output[subarea][group_indx].data[metric]
            if len(this_data) == 0:
                form.w_report.append(WARNING_STR + 'could not display metric: ' + metric)
                return 9*[None]
            data_for_display[subarea] = this_data
            yaxis_min = min(yaxis_min, min(this_data))
            yaxis_max = max(yaxis_max, max(this_data))

        ntsteps = len(data_for_display[subareas[0]])
        ndecimals = int(out_format.rstrip('f'))
        '''
        # check min/max specified by user
        # ===============================

        try:
            ymin = float(form.second.w_min_yval.text())
        except ValueError as err:
            ymin = LRGE_NUM

        ymin = floor(min(ymin, yaxis_min))

        try:
            ymax = float(form.second.w_max_yval.text())
        except ValueError as err:
            ymax = -LRGE_NUM

        ymax = ceil(max(ymax, yaxis_max))
        '''
    return  subareas, data_for_display, ntsteps, description, units, out_format, pyora_display, yaxis_min, yaxis_max
