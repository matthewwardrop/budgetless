import numpy as np
import pandas as pd

import datetime

from .util import get_date_range

class Analysis(object):

    def __init__(self, budget):
        self.budget = budget

    def transactions(self, start_date, end_date=None, date_seen=True):
        if end_date is None:
            end_date = start_date
        df = self.budget.transactions.retrieve_df(start_date, end_date, date_seen=date_seen)
        if len(df) > 0:
            df['category_ref'] = df['category'].fillna(df['category_hint'])
            df['date_ref'] = np.min([df['date_seen'], df['date']], axis=0)
            df['onbudget_ref'] = self.is_onbudget(df)
        return df

    def is_onbudget(self, df, date_seen=True): # TODO: FIX
        def is_onbudget_date(txns):
            if len(txns) == 0:
                return pd.DataFrame({'onbudget':pd.Series([])})
            date = txns['date_ref' if date_seen else 'date'].iloc[0]
            preallocated = self.budget.allocations.get_categories(date)
            return pd.DataFrame(
                        {'onbudget':
                            (txns['onbudget'] == 1) |
                            (
                                txns['onbudget'].isnull() &
                                ~(txns['category_ref'].str.lower().isin(preallocated) |
                                txns['description_orig'].str.lower().str.contains('transfer') |
                                txns['description_orig'].str.lower().str.contains('p2p'))
                            )
                        }
                    )
        return df.groupby('date_ref' if date_seen is True else 'date').apply(is_onbudget_date).reset_index(level=0, drop=True)['onbudget']

    def onbudget_transactions(self, start_date, end_date=None, date_seen=True):
        txns = self.transactions(start_date, end_date, date_seen=date_seen)
        return txns[txns['onbudget_ref']]

    def get_daily_stats(self, txns, date_seen=True, fill_start=None, fill_end=None):
        if len(txns) == 0:
            return txns
        def stats_date(txns):
            date = txns['date_ref' if date_seen else 'date'].iloc[0]
            surplus = self.budget.allocations.get_daily_surplus(date)
            onbudget = txns[txns['onbudget_ref']]
            return pd.DataFrame([{
                    'surplus': surplus + txns[txns['onbudget_ref']].amount.sum()/100,
                    'count': len(txns),
                    'net': txns['amount'].sum()/100,
                    'onbudget_net': onbudget.amount.sum()/100,
                    'onbudget_pending': onbudget[onbudget['pending']].amount.sum()/100,
                    'onbudget_reconciled': onbudget[~onbudget['pending']].amount.sum()/100,
                    'available': surplus
                }])
        stat_frames = [txns.groupby('date_ref').apply(stats_date).reset_index(level=1, drop=True)]
        if fill_start is not None and fill_end is not None:
            dates = get_date_range(fill_start, fill_end, inclusive=True)
            for date in dates:
                if date not in stat_frames[0].index:
                    stat_frames.append(
                        pd.DataFrame([{
                            'surplus': self.budget.allocations.get_daily_surplus(date),
                            'count': 0,
                            'net': 0,
                            'onbudget_net': 0,
                            'onbudget_pending': 0,
                            'onbudget_reconciled': 0,
                            'available': self.budget.allocations.get_daily_surplus(date)
                        }], index=[date])
                        )
        return pd.concat(stat_frames).sort_index()


    def get_stats(self, txns, date_seen=True, fill_start=None, fill_end=None):
        return self.get_daily_stats(txns, date_seen=date_seen, fill_start=fill_start, fill_end=fill_end).sum()

    def daily_stats(self, start_date, end_date=None, date_seen=True):
        return self.get_daily_stats(self.transactions(start_date, end_date, date_seen), date_seen=True, fill_start=start_date, fill_end=end_date)

    def stats(self, start_date, end_date=None, date_seen=True):
        return self.get_stats(self.transactions(start_date, end_date, date_seen), date_seen=True, fill_start=start_date, fill_end=end_date)

    # Week statii
    def yearly_week_dates(self, year, week_start=None):
        week_start = int(self.budget.config.get('week_start', self.budget.DEFAULT_WEEK_START))
        now = datetime.datetime.now().date()
        start_week = datetime.date(year,1,1)
        start_week += datetime.timedelta( (week_start - start_week.weekday()) % 7 )

        status = {}

        week = start_week
        while week.year == year:
            yield week
            week += datetime.timedelta(7)

    def yearly_week_stats(self, year, week_start=None, date_seen=True):
        for date in self.yearly_week_dates(year, week_start = week_start):
            yield (date, self.stats(date, date+datetime.timedelta(days=6), date_seen=date_seen))
