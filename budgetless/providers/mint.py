from ..transactions import TransactionProvider

import mintapi
import datetime
import time

class MintAPIProvider(TransactionProvider):
    name = "mintapi"

    def __map_date(self, date):
        if len(date.split(" ")) != 3:
            date += " " + time.strftime('%Y')
        return datetime.datetime.strptime(date, '%b %d %Y').date()

    def __map_type(self, is_transfer, is_check ):
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

    def __remap(self, transactions):
        for transaction in transactions:
            yield self.__map_transaction(transaction)

    def transactions(self, fromdate=None):
        m = mintapi.Mint(self.__username, self.__password)
        time.sleep(20) # Give mint.com time to synchronise transactions with banks
        yield from self.__remap(m.get_transactions_json())


    def update_mapping(self, before, after):
        return {}

    # def __resolve(self, new, missing):
    #     assert all([m['pending'] == True for ms in missing.values() for m in ms])
    #
    #     update = {}
    #     insert = []
    #
    #     print(sorted(new.keys()))
    #     print(sorted(missing.keys()))
    #
    #     for key in missing:
    #         assert(key in new)
    #         assert(len(missing[key]) <= len(new[key]))
    #
    #         missing_amounts = [ txn['amount'] for txn in missing[key] ]
    #         new_amounts = [ txn['amount'] for txn in new[key] ]
    #
    #         matching = {}
    #         # Match identical values
    #         for i,amount in enumerate(missing_amounts):
    #             j = new_amounts.find(amount)
    #             while j!=-1:
    #                 if j not in matching.values():
    #                     matching[i] = j
    #                     break
    #                 j = new_amounts.find(amount, j+1)
    #
    #         new_amounts = np.array(new_amounts)
    #         # Match nearest values
    #         for i, amount in enumerate(missing_amounts):
    #             if i in matching:
    #                 continue
    #
    #             order = np.argsort(np.abs(new_amounts - amount))
    #             for j in order:
    #                 if j not in matching.values():
    #                     matching[i] = j
    #                     break
    #
    #         for i,j in matching.items():
    #             update[missing[i]['id']] = new[j]
    #
    #         for j in xrange(len(new_amounts)):
    #             if j not in matching.values():
    #                 insert.append(new[j])
    #
    #     return update, insert
