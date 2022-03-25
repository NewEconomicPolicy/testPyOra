#-------------------------------------------------------------------------------
# Name:        livestockGui.py
# Purpose:     displays a table and chart of data
# Author:      Mike Martin
# Created:     14/04/2020
# Licence:     <your licence>
# Description:#
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'livestockGui.py'
__version__ = '0.0.0'

# Version history
# ---------------
#
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit, QLabel, QComboBox

STRATEGIES = ['On farm production', 'Buy/sell']
NFEED_TYPES = 5         # typically 5 feed types

STD_FLD_SIZE_60 = 60
STD_FLD_SIZE_40 = 40

def make_lvstck_wdgts(grid, anml_prodn, w_numbers, w_strtgs, w_feed_types, w_feed_qties, w_bought_in):
    '''
    construct grid of widgets defining livestock values
    '''
    irow = 0
    anml_typs = anml_prodn.gnrc_anml_types

    # headers
    # =======
    icol = 1
    for anml in anml_typs:
        hdr_lbl = QLabel(anml_typs[anml])
        hdr_lbl.setAlignment(Qt.AlignCenter)
        grid.addWidget(hdr_lbl, irow, icol)
        icol += 1

        w_feed_types[anml] = {}     # each animal type can have up to 5 feed types
        w_feed_qties[anml] = {}

    # setup row descriptions
    # ======================
    lvstck_row_dscrs = ['']

    # numbers of livestock
    # ====================
    lvstck_row_dscrs.append('Number')
    #                        ======
    irow += 1
    icol = 0
    for amnl in anml_typs:
        icol += 1
        w_numbers[amnl] = QLineEdit()
        w_numbers[amnl].setFixedWidth(STD_FLD_SIZE_40)
        w_numbers[amnl].setAlignment(Qt.AlignRight)
        grid.addWidget(w_numbers[amnl], irow, icol, alignment=Qt.AlignHCenter)
     # w_numbers[amnl].textChanged[str].connect(lambda: self.sbaDescRotaTextChanged(amnl))

    # =====
    irow += 1
    icol = 0
    lvstck_row_dscrs.append('Strategy')
    #                        ========
    helpText = 'Possible strategies for coping with changes in feed availability'

    for amnl in anml_typs:
        icol += 1
        w_strtgs[amnl] = QComboBox()
        for strategy in STRATEGIES:
            w_strtgs[amnl].addItem(strategy)
        w_strtgs[amnl].setToolTip(helpText)
        grid.addWidget(w_strtgs[amnl], irow, icol, alignment=Qt.AlignHCenter)

    # ======================
    for findx in range(NFEED_TYPES):
        irow += 1
        icol = 0
        fd_typ = str(findx + 1)
        lvstck_row_dscrs.append('Feed type ' + fd_typ)
        #                        =========
        for anml in anml_typs:
            icol += 1
            w_feed_type = QComboBox()
            for feed_typ in list(anml_prodn.crop_names ):
                w_feed_type.addItem(feed_typ)
            grid.addWidget(w_feed_type, irow, icol)
            w_feed_types[anml][fd_typ] = w_feed_type

        irow += 1
        icol = 0
        lvstck_row_dscrs.append('Feed value (%)')
        #                        ==============
        for anml in anml_typs:
            icol += 1
            w_feed_qty = QLineEdit()
            w_feed_qty.setFixedWidth(STD_FLD_SIZE_40)
            w_feed_qty.setAlignment(Qt.AlignRight)
            # w_feed_qty.textChanged[str].connect(lambda: feedValueChanged(anml, findx))
            grid.addWidget(w_feed_qty, irow, icol, alignment=Qt.AlignHCenter)
            w_feed_qties[anml][fd_typ] = w_feed_qty
 
    # =========
    irow += 1
    icol = 0
    lvstck_row_dscrs.append('Bought in (%)')
    #                        =============
    helpText = 'Feed value obtained from bought in feed (%)' \
               ''
    for amnl in anml_typs:
        icol += 1
        w_bought_in[amnl] = QLineEdit()
        w_bought_in[amnl].setFixedWidth(STD_FLD_SIZE_40)
        w_bought_in[amnl].setToolTip(helpText)
        grid.addWidget(w_bought_in[amnl], irow, icol, alignment=Qt.AlignHCenter)
    # w_numbers[amnl].textChanged[str].connect(lambda: self.sbaDescRotaTextChanged(amnl))

    # write row descriptions
    # ======================
    for irow, row_dscr in enumerate(lvstck_row_dscrs):
        grid.addWidget(QLabel(row_dscr), irow, 0, alignment=Qt.AlignRight)

    return irow, lvstck_row_dscrs

    def feedValueChanged(anml, findx):

        print(anml + str(findx))
