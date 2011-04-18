# -*- coding: utf-8 -*-
# Created By: Virgil Dupras
# Created On: 2009-11-01
# Copyright 2011 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "BSD" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/bsd_license

from core.gui.profit_view import ProfitView as ProfitViewModel

from ..base_view import BaseView
from .sheet import ProfitSheet
from .graph import ProfitGraph
from .income_pie_chart import IncomePieChart
from .expense_pie_chart import ExpensePieChart
from ...ui.profit_view_ui import Ui_ProfitView

class ProfitView(BaseView, Ui_ProfitView):
    def __init__(self, mainwindow):
        BaseView.__init__(self)
        self.doc = mainwindow.doc
        self._setupUi()
        self.model = ProfitViewModel(view=self, mainwindow=mainwindow.model)
        self.psheet = ProfitSheet(self, view=self.treeView)
        self.pgraph = ProfitGraph(self, view=self.graphView)
        self.ipiechart = IncomePieChart(self, view=self.incomePieChart)
        self.epiechart = ExpensePieChart(self, view=self.expensePieChart)
        children = [self.psheet.model, self.pgraph.model, self.ipiechart.model, self.epiechart.model]
        self.model.set_children(children)
        self._setupColumns() # Can only be done after the model has been connected
    
    def _setupUi(self):
        self.setupUi(self)
    
    def _setupColumns(self):
        self.psheet.restore_columns()
    
    #--- QWidget override
    def setFocus(self):
        self.psheet.view.setFocus()
    
    #--- Public
    def fitViewsForPrint(self, viewPrinter):
        viewPrinter.fitTree(self.psheet)
        viewPrinter.fit(self.ipiechart.view, 150, 150, expandH=True)
        viewPrinter.fit(self.epiechart.view, 150, 150, expandH=True)
        viewPrinter.fit(self.pgraph.view, 300, 150, expandH=True, expandV=True)
    
    def updateOptionalWidgetsVisibility(self):
        prefs = self.doc.app.prefs
        self.graphView.setHidden(not prefs.profitGraphVisible)
        self.incomePieChart.setHidden(not prefs.profitPieChartsVisible)
        self.expensePieChart.setHidden(not prefs.profitPieChartsVisible)
    
