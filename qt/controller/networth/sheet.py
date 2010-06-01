# -*- coding: utf-8 -*-
# Created By: Virgil Dupras
# Created On: 2009-11-01
# Copyright 2010 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "HS" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/hs_license

from PyQt4.QtCore import Qt

from qtlib.column import Column
from core.gui.balance_sheet import BalanceSheet as BalanceSheetModel
from ..account_sheet import AccountSheet, AccountSheetDelegate

class NetWorthSheet(AccountSheet):
    COLUMNS = [
        Column('name', 'Account', 133),
        Column('account_number', 'Account #', 80),
        Column('end', 'End', 100, alignment=Qt.AlignRight),
        Column('start', 'Start', 100, alignment=Qt.AlignRight),
        Column('delta', 'Change', 100, alignment=Qt.AlignRight),
        Column('delta_perc', 'Change %', 100),
        Column('budgeted', 'Budgeted', 100, alignment=Qt.AlignRight),
    ]
    AMOUNT_ATTRS = set(['end', 'start', 'delta', 'delta_perc', 'budgeted'])
    BOLD_ATTRS = set(['end'])
    
    def __init__(self, networth_view, view):
        model = BalanceSheetModel(view=self, networth_view=networth_view.model)
        AccountSheet.__init__(self, networth_view.doc, model, view)
    
