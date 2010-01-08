# Created By: Virgil Dupras
# Created On: 2009-01-18
# Copyright 2010 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "HS" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/hs_license

from itertools import dropwhile

from hsutil.misc import first, nonone

from ..exception import FileLoadError
from ..loader.csv import CsvField
from .base import DocumentGUIObject

LAYOUT_PREFERENCE_NAME = 'CSVLayouts'
FIELD_NAMES = {
    None: 'None',
    CsvField.Date: 'Date',
    CsvField.Description: 'Description',
    CsvField.Payee: 'Payee',
    CsvField.Checkno: 'Check #',
    CsvField.Transfer: 'Transfer',
    CsvField.Amount: 'Amount',
    CsvField.Increase: 'Increase',
    CsvField.Decrease: 'Decrease',
    CsvField.Currency: 'Currency',
    CsvField.Reference: 'Transaction ID',
}

FIELD_ORDER = [None, CsvField.Date, CsvField.Description, CsvField.Payee, CsvField.Checkno, 
    CsvField.Transfer, CsvField.Amount, CsvField.Increase, CsvField.Decrease, CsvField.Currency,
    CsvField.Reference]

class Layout(object):
    def __init__(self, name):
        self.name = name
        self.columns = []
        self.excluded_lines = set()
        self.target_account_name = None
    
    def __repr__(self):
        return '<Layout {0} {1} {2}>'.format(self.name, self.columns, self.excluded_lines)
    
    def adjust_columns(self, colcount):
        diff = colcount - len(self.columns)
        if diff > 0:
            self.columns += [None] * diff
    
    def duplicate(self, newname):
        layout = Layout(newname)
        layout.columns = self.columns[:]
        layout.excluded_lines = self.excluded_lines.copy()
        return layout
    
    def set_column_field(self, index, field):
        assert field in FIELD_NAMES
        if field in self.columns:
            self.columns[self.columns.index(field)] = None
        self.columns[index] = field
    
    def set_line_excluded(self, index, value, linecount):
        if value:
            self.excluded_lines.add(index)
        else:
            self.excluded_lines.discard(index)
            self.excluded_lines.discard(index - linecount)
        # adjust line exclusion
        last_index = linecount - 1
        while last_index > 0:
            if last_index in self.excluded_lines:
                self.excluded_lines.remove(last_index)
                self.excluded_lines.add(last_index - linecount)
            # first line from the end to not be excluded, we stop
            if last_index - linecount not in self.excluded_lines:
                break
            last_index -= 1
    
    #--- Properties
    @property
    def field_indexes(self): # {fieldname: index}
        result = {}
        for index, field in enumerate(self.columns):
            if field is not None:
                result[field] = index
        return result
    

class CSVOptions(DocumentGUIObject):
    def __init__(self, view, document):
        def preference2layout(pref):
            layout = Layout(pref['name'])
            columns = pref['columns']
            layout.columns = [col if col else None for col in columns]
            layout.excluded_lines = set(pref['excluded_lines'])
            layout.target_account_name = pref.get('target_account')
            return layout
        
        DocumentGUIObject.__init__(self, view, document)
        self.lines = []
        self._colcount = 0
        self._target_accounts = []
        self._default_layout = Layout('Default')
        preferences = self.app.get_default(LAYOUT_PREFERENCE_NAME)
        try:    
            self._layouts = [preference2layout(pref) for pref in preferences]
        except Exception: # probably because of corrupted prefs
            self._layouts = []
        self.layout = self._default_layout
    
    #--- Private
    def _refresh_columns(self):
        self._colcount = len(self.document.loader.lines[0])
        self.layout.adjust_columns(self._colcount)
        self.view.refresh_columns()
    
    def _refresh_lines(self):
        self.lines = self.document.loader.lines
        self.view.refresh_lines()
    
    def _refresh_targets(self):
        self._target_accounts = [a for a in self.document.accounts if a.is_balance_sheet_account()]
        self._target_accounts.sort(key=lambda a: a.name.lower())
        self.view.refresh_targets()
    
    #--- Public
    def continue_import(self):
        loader = self.document.loader
        loader.column_indexes = self.layout.field_indexes
        lines = [line for index, line in enumerate(self.lines) if not self.line_is_excluded(index)]
        loader.lines = lines
        target_name = self.layout.target_account_name
        loader.target_account = first(t for t in self._target_accounts if t.name == target_name)
        try:
            self.document.load_parsed_file_for_import()
        except FileLoadError as e:
            self.view.show_message(unicode(e))
        else:
            self.view.hide()
    
    def delete_selected_layout(self):
        if self.layout is self._default_layout:
            return
        self._layouts.remove(self.layout)
        self.layout = self._default_layout
        self.layout.adjust_columns(self._colcount)
        self.view.refresh_layout_menu()
        self.view.refresh_columns_name()
        self.view.refresh_lines()
    
    def get_column_name(self, index):
        return FIELD_NAMES[self.columns[index]]
    
    def line_is_excluded(self, index):
        if index in self.excluded_lines:
            return True
        elif index - len(self.lines) in self.excluded_lines:
            return True
        else:
            return False
    
    def new_layout(self, name):
        if not name:
            return
        new_layout = self.layout.duplicate(name)
        self._layouts.append(new_layout)
        self.layout = new_layout
        self.view.refresh_layout_menu()
    
    def rename_selected_layout(self, newname):
        if not newname:
            return
        self.layout.name = newname
        self.view.refresh_layout_menu()
    
    def select_layout(self, name):
        if not name:
            new_layout = self._default_layout
        else:
            new_layout = first(layout for layout in self._layouts if layout.name == name)
        if new_layout is self.layout:
            return
        self.layout = new_layout
        self.layout.adjust_columns(self._colcount)
        self.view.refresh_columns_name()
        self.view.refresh_lines()
        self.view.refresh_targets()
    
    def set_column_field(self, index, field):
        self.layout.set_column_field(index, field)
        self.view.refresh_columns_name()
    
    def set_line_excluded(self, index, value):
        self.layout.set_line_excluded(index, value, len(self.lines))
    
    #--- Properties
    @property
    def columns(self):
        columns = self.layout.columns
        if self._colcount < len(columns):
            columns = columns[:self._colcount]
        return columns
    
    @property
    def excluded_lines(self):
        return self.layout.excluded_lines
    
    @property
    def layout_names(self):
        return ['Default'] + [layout.name for layout in self._layouts]
    
    @property
    def selected_target_index(self):
        target_name = self.layout.target_account_name
        if not target_name:
            return 0
        index = first(i for i, t in enumerate(self._target_accounts) if t.name == target_name)
        return index + 1 if index is not None else 0
    
    @selected_target_index.setter
    def selected_target_index(self, value):
        self.layout.target_account_name = self._target_accounts[value - 1].name if value > 0 else None
    
    @property
    def target_account_names(self):
        return ['< New Account >'] + [a.name for a in self._target_accounts]
    
    #--- Events
    def csv_options_needed(self):
        self._default_layout = Layout('Default')
        self.layout = self._default_layout
        self._refresh_columns()
        self._refresh_lines()
        self._refresh_targets()
        self.view.refresh_layout_menu()
        self.view.show()
    
    def document_will_close(self):
        def layout2preference(layout):
            result = {}
            result['name'] = layout.name
            # trim trailing None values
            columns = list(dropwhile(lambda x: x is None, layout.columns[::-1]))[::-1]
            # None values cannot be put in preferences, change them to an empty string.
            columns = [nonone(col, '') for col in columns]
            result['columns'] = columns
            result['excluded_lines'] = sorted(list(layout.excluded_lines))
            if layout.target_account_name:
                result['target_account'] = layout.target_account_name
            return result
        
        layouts = map(layout2preference, self._layouts)
        self.app.set_default(LAYOUT_PREFERENCE_NAME, layouts)
    