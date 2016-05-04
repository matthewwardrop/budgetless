from ..transactions import TransactionProvider
from .. import util

import mintapi
import datetime
import time
import pytz
import random


class MintAPIProvider(TransactionProvider):
    name = "mintapi"

    def __map_date(self, date):
        if len(date.split(" ")) != 3:
            date += " " + time.strftime('%Y')
        return datetime.datetime.strptime(date, '%b %d %Y').date()

    def __map_type(self, is_transfer, is_check):
        if is_transfer:
            return 'transfer'
        elif is_check:
            return 'check'
        else:
            return 'charge'

    def __map_amount(self, amount, is_debit):
        amount = amount.replace('$', '').split('.')
        out = int(amount[0].replace(',', ''))*100
        if len(amount) == 2:
            out += int(amount[1])
        if is_debit:
            out *= -1
        return out

    def __map_transaction(self, transaction):
        return {
            'account': transaction['account'],
            'institution': transaction['fi'],

            'notes': transaction['note'],
            'flags': ','.join([k['name'] for k in transaction['labels']]),

            'description': transaction['merchant'],
            'description_orig': transaction['omerchant'],
            'tracking_id': transaction['id'],

            'category_hint': transaction['category'],

            'pending': transaction['isPending'],

            'date': self.__map_date(transaction['date']),
            'date_orig': self.__map_date(transaction['date']),

            'type': self.__map_type(transaction['isTransfer'], transaction['isCheck']),

            'amount': self.__map_amount(transaction['amount'], transaction['isDebit']),
            'currency': 'USD'
        }

    def __init__(self, username, password):
        self.__username = username
        self.__password = password
        self.__sync_delay = 0

    def __remap(self, transactions):
        for transaction in transactions:
            yield self.__map_transaction(transaction)

    def transactions(self, fromdate=None):
        time.sleep(self.__sync_delay)
        self.__sync_delay = 0
        m = mintapi.Mint(self.__username, self.__password)
        time.sleep(20+10*random.random())  # Give mint.com time to synchronise transactions with banks
        yield from self.__remap(m.get_transactions_json())

    def should_sync(self):
        loc_date = util.current_datetime(self.timezone)

        if loc_date.hour == 23:
            self.__sync_delay = 45*60*random.random()  # random delay between 0 and 45 minutes
            return True
        return False

    @property
    def timezone(self):
        return pytz.timezone('America/Los_Angeles')

    def update_mapping(self, before, after):

        # We assume all deleted entries (i.e. all in before) are deleted because
        # they have been updated; i.e. moved from pending to non-pending.
        # Assert this assumption.
        assert all([b['pending'] is True for b in before])

        # Given the above assumption, every element in before should map to one
        # in after; unless it was a credit hold.

        mapping = {}

        # We begin by checking for exact matches; if duplicate transactions exist
        # this may fail to correctly associate entries; but since the transactions
        # have the same metadata, that does not matter.
        for i, b in enumerate(before):
            for j, a in enumerate(after):
                if j in mapping.values():
                    continue
                if (str(b['amount']) == str(a['amount']) and
                        b['description'].lower() == a['description'].lower() and
                        b['institution'].lower() == a['institution'].lower() and
                        b['account'].lower() == a['account'].lower()):
                    mapping[i] = j

        # TODO: More subtle cases

        return mapping
