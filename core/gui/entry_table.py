# Created By: Eric Mc Sween
# Created On: 2008-07-06
# Copyright 2010 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "HS" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/hs_license

import datetime
from operator import attrgetter

from ..model.amount import parse_amount, convert_amount
from ..model.recurrence import Spawn
from .table import RowWithDebitAndCredit, RowWithDate, rowattr
from .transaction_table_base import TransactionTableBase

class EntryTable(TransactionTableBase):
    def __init__(self, view, document):
        TransactionTableBase.__init__(self, view, document)
        self.account = None
        self._total_increase = 0
        self._total_decrease = 0
    
    #--- Override
    def _do_add(self):
        entry = self.document.new_entry()
        for index, row in enumerate(self):
            if not isinstance(row, EntryTableRow):
                continue
            if row._date > entry.date:
                insert_index = index
                break
        else:
            insert_index = len(self)
        row = EntryTableRow(self, entry, entry.account)
        self.insert(insert_index, row)
        self.select([insert_index])
        self.document.select_transactions([entry.transaction])
        return row
    
    def _do_delete(self):
        entries = self.selected_entries
        if entries:
            self.document.delete_entries(entries)
    
    def _fill(self):
        account = self.document.shown_account
        if account is None:
            return
        date_range = self.document.date_range
        self.account = account
        if account.is_balance_sheet_account():
            prev_entry = self.document.previous_entry
            if prev_entry is not None:
                balance = prev_entry.balance
                rbalance = prev_entry.reconciled_balance
                self.append(PreviousBalanceRow(self, date_range.start, balance, rbalance, account))
        self._total_increase = 0
        self._total_decrease = 0
        for entry in self.document.visible_entries:
            row = EntryTableRow(self, entry, account)
            self.append(row)
            convert = lambda a: convert_amount(a, account.currency, entry.date)
            self._total_increase += convert(row._increase)
            self._total_decrease += convert(row._decrease)
        if self.document.explicitly_selected_transactions:
            self.select_transactions(self.document.explicitly_selected_transactions)
            if not self.selected_indexes:
                self.select_nearest_date(self.document.explicitly_selected_transactions[0].date)
    
    #--- Public
    def add(self):
        if self.account is None:
            return
        TransactionTableBase.add(self)
    
    def select_nearest_date(self, target_date):
        # This method assumes that self is sorted by date
        last_delta = datetime.timedelta.max
        for index, row in enumerate(self):
            delta = abs(row._date - target_date)
            if delta > last_delta:
                # The last iteration was the correct one
                self.selected_index = index - 1
                break
            last_delta = delta
        else:
            self.selected_index = len(self) - 1
    
    def should_show_balance_column(self):
        return bool(self.document.selected_account) and self.document.selected_account.is_balance_sheet_account()
    
    def show_transfer_account(self):
        if not self.selected_entries:
            return
        entry = self.selected_entries[0]
        splits = entry.transaction.splits
        index = splits.index(entry.split)
        if index < len(splits) - 1:
            account_to_show = splits[index+1].account
        else:
            account_to_show = splits[0].account
        self.document.show_account(account_to_show)
    
    def toggle_reconciled(self):
        """Toggle the reconcile flag of selected entries"""
        entries = [row.entry for row in self.selected_rows if row.can_reconcile()]
        self.document.toggle_entries_reconciled(entries)
    
    #--- Properties
    @property
    def selected_entries(self):
        return [row.entry for row in self.selected_rows if hasattr(row, 'entry')]
    
    @property
    def selected_transactions(self):
        return [entry.transaction for entry in self.selected_entries]
    
    @property
    def totals(self):
        shown = len(self.document.visible_entries)
        total = self.document.visible_unfiltered_entry_count
        increase = self.app.format_amount(self._total_increase)
        decrease = self.app.format_amount(self._total_decrease)
        msg = u"Showing {shown} out of {total}. Total increase: {increase} Total decrease: {decrease}"
        return msg.format(shown=shown, total=total, increase=increase, decrease=decrease)
    
    #--- Event Handlers
    def date_range_changed(self):
        date_range = self.document.date_range
        self.refresh()
        self.select_transactions(self.document.selected_transactions)
        if not self.selected_indexes:
            self.select_nearest_date(date_range.start + self._delta_before_change)
        self.view.refresh()
        self.view.show_selected_row()
        self.document.select_transactions(self.selected_transactions)
    
    def date_range_will_change(self):
        date_range = self.document.date_range
        transactions = self.selected_transactions
        date = transactions[0].date if transactions else date_range.end
        delta = date - date_range.start
        self._delta_before_change = delta
    
    def reconciliation_changed(self):
        self.refresh()
        self.view.refresh()
    account_must_be_shown = reconciliation_changed
    
    def transactions_imported(self):
        self.refresh()
        self.document.select_transactions(self.selected_transactions)
        self.view.refresh()

class BaseEntryTableRow(RowWithDebitAndCredit):
    def __init__(self, table):
        super(BaseEntryTableRow, self).__init__(table)
        self._date = datetime.date.today()
        self._position = 0
        self._description = ''
        self._payee = ''
        self._checkno = ''
        self._amount = 0
        self._transfer = ''
        self._balance = 0
        self._reconciled_balance = 0
        self._reconciled = False
        self._reconciliation_date = None
        self._reconciliation_pending = False
        self._recurrent = False
        self._is_budget = False
    
    def _the_balance(self):
        if self.table.document._in_reconciliation_mode:
            balance = self._reconciled_balance
        else:
            balance = self._balance
        if balance and self.table.document.selected_account.is_credit_account():
            balance = -balance
        return balance
    
    #--- Public
    def can_edit(self):
        return False
    
    def can_reconcile(self):
        return False
    
    def is_balance_negative(self):
        return self._the_balance() < 0
    
    def sort_key_for_column(self, column_name):
        if column_name == 'date':
            return (self._date, self._position)
        elif column_name == 'reconciliation_date' and self._reconciliation_date is None:
            return datetime.date.min
        elif column_name == 'status':
            # First reconciled, then plain ones, then schedules, then budgets
            if self.reconciled:
                return 0
            elif self.recurrent:
                return 2
            elif self.is_budget:
                return 3
            else:
                return 1
        else:
            return RowWithDebitAndCredit.sort_key_for_column(self, column_name)
    
    #--- Properties
    @property
    def date(self):
        return self.table.document.app.format_date(self._date)
    
    @property
    def description(self):
        return self._description
    
    @property
    def payee(self):
        return self._payee
    
    @property
    def checkno(self):
        return self._checkno
    
    @property
    def transfer(self):
        return self._transfer
    
    @property
    def increase(self):
        return self.table.document.app.format_amount(self._increase, blank_zero=True)
    
    @property
    def decrease(self):
        return self.table.document.app.format_amount(self._decrease, blank_zero=True)
    
    @property
    def balance(self):
        account_currency = self.table.account.currency
        return self.table.document.app.format_amount(self._the_balance(), zero_currency=account_currency)
    can_edit_balance = False
    
    @property
    def reconciled(self):
        return self._reconciled
    
    @property
    def reconciliation_date(self):
        if self._reconciliation_date is not None:
            return self.table.document.app.format_date(self._reconciliation_date)
        else:
            return ''
    
    @property
    def reconciliation_pending(self):
        return self._reconciliation_pending
    
    @property
    def recurrent(self):
        return self._recurrent
    
    @property
    def is_budget(self):
        return self._is_budget
    
    
AUTOFILL_ATTRS = frozenset(['description', 'payee', 'transfer', 'increase', 'decrease'])
AMOUNT_AUTOFILL_ATTRS = frozenset(['increase', 'decrease'])

class EntryTableRow(RowWithDate, BaseEntryTableRow):
    def __init__(self, table, entry, account):
        super(EntryTableRow, self).__init__(table)
        self.entry = entry
        # makes possible to move more code down to TransactionTableBase
        self.transaction = entry.transaction
        self.account = account
        self.load()
    
    def _autofill_row(self, ref_row, dest_attrs):
        if len(ref_row.entry.transfer) > 1:
            dest_attrs.discard('_transfer')
        BaseEntryTableRow._autofill_row(self, ref_row, dest_attrs)
    
    def _get_autofill_attrs(self):
        return AUTOFILL_ATTRS
    
    def _get_autofill_dest_attrs(self, key_attr, all_attrs):
        dest_attrs = BaseEntryTableRow._get_autofill_dest_attrs(self, key_attr, AUTOFILL_ATTRS)
        if dest_attrs & AMOUNT_AUTOFILL_ATTRS:
            dest_attrs -= AMOUNT_AUTOFILL_ATTRS
            dest_attrs.add('amount')
        return dest_attrs
    
    def _get_autofill_rows(self):
        original = self.entry
        entries = sorted(self.account.entries, key=attrgetter('mtime'), reverse=True)
        for entry in entries:
            if entry is original:
                continue
            yield EntryTableRow(self.table, entry, self.account)
    
    def can_edit(self):
        return not self.is_budget
    
    def can_reconcile(self):
        inmode = self.table.document._in_reconciliation_mode
        canedit = self.can_edit()
        future = self._date > datetime.date.today()
        foreign = self._amount != 0 and self._amount.currency != self.account.currency
        balance_sheet = self.account.is_balance_sheet_account()
        return inmode and canedit and not future and not foreign and balance_sheet
    
    def load(self):
        entry = self.entry
        self._date = entry.date
        self._position = entry.transaction.position
        self._description = entry.description
        self._payee = entry.payee
        self._checkno = entry.checkno
        self._amount = entry.amount
        self._transfer = ', '.join(s.name for s in entry.transfer)
        self._balance = entry.balance_with_budget
        self._reconciled_balance = entry.reconciled_balance if entry.reconciled or entry.reconciliation_pending else None
        self._reconciled = entry.reconciled
        self._reconciliation_date = entry.reconciliation_date
        self._reconciliation_pending = entry.reconciliation_pending
        self._recurrent = isinstance(entry.transaction, Spawn)
        self._is_budget = getattr(entry.transaction, 'is_budget', False)
    
    def save(self):
        change = self.table.document.change_entry
        change(self.entry, date=self._date, reconciliation_date=self._reconciliation_date, 
            description=self._description, payee=self._payee, checkno=self._checkno,
            transfer=self._transfer, amount=self._amount)
        self.load()
    
    def toggle_reconciled(self):
        assert self.table.document._in_reconciliation_mode
        self.table.selected_row = self
        self.table._update_selection()
        self.table.toggle_reconciled()
    
    #--- Properties
    @BaseEntryTableRow.reconciliation_date.setter
    def reconciliation_date(self, value):
        parsed = self.table.document.app.parse_date(value)
        if parsed == self._reconciliation_date:
            return
        self._edit()
        self._reconciliation_date = parsed
    
    description = rowattr('_description', 'description')
    payee = rowattr('_payee', 'payee')
    checkno = rowattr('_checkno')
    transfer = rowattr('_transfer', 'transfer')
    @property
    def can_edit_transfer(self):
        return len(self.entry.splits) == 1
    
    @BaseEntryTableRow.increase.setter
    def increase(self, value):
        try:
            increase = parse_amount(value, self.table.document.selected_account.currency)
        except ValueError:
            return
        if increase == self._increase:
            return
        self._increase = increase
    
    @BaseEntryTableRow.decrease.setter
    def decrease(self, value):
        try:
            decrease = parse_amount(value, self.table.document.selected_account.currency)
        except ValueError:
            return
        if decrease == self._decrease:
            return
        self._decrease = decrease
    

class PreviousBalanceRow(BaseEntryTableRow):
    def __init__(self, table, date, balance, reconciled_balance, account):
        super(PreviousBalanceRow, self).__init__(table)
        self.account = account
        self._date = date
        self._balance = balance
        self._reconciled_balance = reconciled_balance
        self._description = 'Previous Balance'
        self._reconciled = False
        self._reconciliation_pending = False
    