#-------------------------------------------------------------------------------
# Name:        test_chart_subplot.py
# Purpose:     test_plot functions
# Author:      Mike Martin
# Created:     14/04/2020
# Licence:     <your licence>
# Description:#
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'test_chart_subplot.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem
from PyQt5.QtChart import QChart, QValueAxis, QChartView, QLineSeries
from random import random
from math import floor, ceil

from ora_lookup_df_fns import fetch_metric_detail

SET_INDICES = {'carbon':0, 'nitrogen':1, 'soil_water':2}    # lookup table for data object
WARNING_STR = '*** Warning *** '
LRGE_NUM = 99999999

def _generate_line_series(subareas, ntsteps, data_for_display, w_table, out_format):
    '''
    create line series from data
    '''
    tsteps = []
    for tstep in range(ntsteps):
        tsteps.append(str(tstep + 1))

    ndecimals = int(out_format.rstrip('f'))

    line_series = {}
    for icol_indx, subarea in enumerate(subareas):
        lseries = QLineSeries()
        lseries.setName(subarea)
        for irow_indx, val in enumerate(data_for_display[subarea]):
            w_table.setItem(irow_indx, icol_indx, QTableWidgetItem(str(round(val, ndecimals))))
            lseries.append(irow_indx + 1, val)

        line_series[subarea] = lseries

    return tsteps, line_series

def _select_data_for_display(form, category, metric):
    '''

    '''
    group_indx = SET_INDICES[category]
    all_runs_output = form.all_runs_output
    subareas = list(all_runs_output.keys())
    definition, units, out_format, pyora_display = fetch_metric_detail(form.settings['lookup_df'], metric)

    yaxis_min =  LRGE_NUM
    yaxis_max = -LRGE_NUM
    data_for_display = {}
    for subarea in subareas:
        this_data = all_runs_output[subarea][group_indx].data[metric]
        if len(this_data) == 0:
            print(WARNING_STR + 'could not display metric: ' + metric)
            return 9*[None]
        data_for_display[subarea] = this_data
        yaxis_min = min(yaxis_min, min(this_data))
        yaxis_max = max(yaxis_max, max(this_data))

    ntsteps = len(data_for_display[subareas[0]])

    ndecimals = int(out_format.rstrip('f'))

    # check min/max specified by user
    # ===============================
    try:
        ymin = float(form.w_min_wat.text())
    except ValueError as err:
        ymin = LRGE_NUM

    ymin = floor(min(ymin, yaxis_min))

    try:
        ymax = float(form.w_max_wat.text())
    except ValueError as err:
        ymax = -LRGE_NUM

    ymax = ceil(max(ymax, yaxis_max))

    return  subareas, data_for_display, ntsteps, definition, units, out_format, pyora_display, floor(ymin), ceil(ymax)

def display_metric(form, category, metric):

    subareas, data_for_display, ntsteps, description, units, out_format, pyora_display, yaxis_min, yaxis_max = \
                                                                _select_data_for_display(form, category, metric)
    if subareas is None:
        return

    form.second = Second()
    form.second.createWindow(500, 400)
    form.second.setWindowTitle('example sub-window')

    hbox = QHBoxLayout()

    # left hand vertical box consists of png image only
    # =================================================
    lh_vbox = QVBoxLayout()

    # Table
    # =====
    w_table = QTableWidget()

    w_table.setMinimumWidth(625)
    w_table.setRowCount(ntsteps)
    w_table.setColumnCount(len(subareas))
    w_table.setHorizontalHeaderLabels(subareas)
    tsteps, line_series = _generate_line_series(subareas, ntsteps, data_for_display, w_table, out_format)
    lh_vbox.addWidget(w_table)

    # add LH vertical box to horizontal box
    # =====================================
    hbox.addLayout(lh_vbox)

    # right hand box consists of combo boxes, labels and buttons
    # ==========================================================
    rh_vbox = QVBoxLayout()

    w_chart = QChart()
    # w_chart.setTheme(QChart.ChartThemeBrownSand)
    for subarea in subareas:
        w_chart.addSeries(line_series[subarea])

    lseries = line_series[subareas[0]]
    axis = QValueAxis(lseries)
    axis.setRange(1,ntsteps)
    axis.setTitleText("Time step")
    axis.applyNiceNumbers()

    w_chart.createDefaultAxes()
    for subarea in subareas:
        w_chart.setAxisX(axis, line_series[subarea])
    w_chart.axisY(lseries).setRange(yaxis_min, yaxis_max)
    w_chart.axisY(lseries).setTitleText(pyora_display + ' ' + units)

    w_chart.legend().setVisible(True)
    w_chart.legend().setAlignment(Qt.AlignBottom)

    w_chart.setTitle(description)
    w_chart.setAnimationOptions(QChart.SeriesAnimations)
    w_chart.setMinimumWidth(1200)

    chart_view = QChartView(w_chart)
    chart_view.setRenderHint(QPainter.Antialiasing)

    rh_vbox.addWidget(chart_view)     # add grid to RH vertical box
    hbox.addLayout(rh_vbox)     # vertical box goes into horizontal box
    form.second.setLayout(hbox)        # the horizontal box fits inside the window

    form.second.setGeometry(50, 250, 1000, 500)    # posx, posy, width, height
    form.second.setWindowTitle('example sub-window')

    form.second.show()

    '''
      grid.addWidget(chartView, 1, 0, 16, 6)

      okButton = QPushButton("OK")
      cancelButton = QPushButton("Cancel")
      hbox.addWidget(okButton)
      hbox.addWidget(cancelButton)

      dismiss = QPushButton("Dismiss")
      grid.addWidget(dismiss, 19, 5)
      dismiss.clicked.connect(form.second.dismissClicked)
      '''

class Second(QWidget):

    def createWindow(self, win_width, win_height):

        parent=None
        super(Second, self).__init__(parent)

        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(win_width, win_height)

    def dismissClicked(self):

        self.close()

def _generate_random_data(subareas, w_table):
    '''
    generate random data
    '''
    NTSTEPS = 240
    tsteps = []
    for tstep in range(NTSTEPS):
        tsteps.append(str(tstep + 1))

    series_dict = {}
    for subarea in subareas:
        series = []
        for tstep in range(NTSTEPS):
            series.append(random() * 33)
        series_dict[subarea] = series

    line_series = {}
    for icol_indx, subarea in enumerate(subareas):
        lseries = QLineSeries()
        for irow_indx, val in enumerate(series_dict[subarea]):
            w_table.setItem(irow_indx, icol_indx, QTableWidgetItem(str(round(val, 2))))
            lseries.append(irow_indx + 1, val)

        line_series[subarea] = lseries

    return tsteps, line_series