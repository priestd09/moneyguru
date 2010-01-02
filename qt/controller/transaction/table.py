# -*- coding: utf-8 -*-
# Created By: Virgil Dupras
# Created On: 2009-10-31
# Copyright 2010 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "HS" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/hs_license

from PyQt4.QtCore import Qt

from core.gui.transaction_table import TransactionTable as TransactionTableModel
from ..column import Column, DATE_EDIT, DESCRIPTION_EDIT, PAYEE_EDIT, ACCOUNT_EDIT
from ..table_with_transactions import TableWithTransactions

# XXX The totals label is tied to the table, even in the model. This is a design flaw. The totals
# label should be an independent gui element (or be a part of an eventual new transaction_view gui
# element).

class TransactionTable(TableWithTransactions):
    COLUMNS = [
        Column('status', '', 25),
        Column('date', 'Date', 86, editor=DATE_EDIT),
        Column('description', 'Description', 230, editor=DESCRIPTION_EDIT),
        Column('payee', 'Payee', 150, editor=PAYEE_EDIT),
        Column('checkno', 'Check #', 80),
        Column('from_', 'From', 120, editor=ACCOUNT_EDIT),
        Column('to', 'To', 120, editor=ACCOUNT_EDIT),
        Column('amount', 'Amount', 100, alignment=Qt.AlignRight),
    ]
    
    def __init__(self, doc, view, totalsLabel):
        model = TransactionTableModel(view=self, document=doc.model)
        TableWithTransactions.__init__(self, model, view)
        self.totalsLabel = totalsLabel
        self.view.horizontalHeader().sectionMoved.connect(self.headerSectionMoved)
        self.view.deletePressed.connect(self.model.delete)
    
    #--- ColumnBearer override
    def setHiddenColumns(self, hiddenColumns):
        # There doesn't seem to be a signal for column hide. Since we only hide column through this
        # call, we can call change_columns() here.
        TableWithTransactions.setHiddenColumns(self, hiddenColumns)
        self.model.change_columns(self.visibleRowAttrs())
    
    #--- Event Handling
    def headerSectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        self.model.change_columns(self.visibleRowAttrs())
    
    #--- model --> view
    def refresh(self):
        TableWithTransactions.refresh(self)
        self.totalsLabel.setText(self.model.totals)
    
