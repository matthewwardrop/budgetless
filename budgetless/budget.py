import datetime

from sqlalchemy import create_engine

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .allocations import AllocationPool
from .config import ConfigPool
from .db import db_metadata
from .transactions import TransactionPool, TransactionSourcePool


MONTHS = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December'
    ]


class Budget(object):

    def __init__(self, database='budgetless.db', debug=False):
        self.debug = debug

        self.database = database
        if self.database.find(':') == -1:
            self.database = 'sqlite:///' + self.database

    @property
    def wsgi_app(self):
        try:
            return self.__wsgi_app
        except:
            from .ui import get_app_for_budget
            self.__wsgi_app = get_app_for_budget(self)
            return self.__wsgi_app

    def initialise(self, filename=None, config=None, sources=None, allocations=None):
        env = {'config': config, 'sources': sources, 'allocations': allocations}
        if filename is not None:
            with open(filename) as f:
                exec(f.read(), env)

        if env['config'] is not None:
            for key, value in env['config'].items():
                self.config.set(key, value)

        if env['sources'] is not None:
            for source in env['sources']:
                self.sources.add(source[0], **source[1])

        if env['allocations'] is not None:
            for alloc in env['allocations']:
                self.allocations.add(**alloc)

        self.sync()

    @property
    def engine(self):
        try:
            return self.__engine
        except:
            self.__engine = create_engine(self.database, echo=self.debug)
            db_metadata.create_all(self.engine)
            return self.__engine

    @property
    def sources(self):
        try:
            return self.__sources
        except:
            self.__sources = TransactionSourcePool(self.engine)
            return self.__sources

    @property
    def allocations(self):
        try:
            return self.__allocations
        except:
            self.__allocations = AllocationPool(self.engine)
            return self.__allocations

    @property
    def transactions(self):
        try:
            return self.__transactions
        except:
            self.__transactions = TransactionPool(self.engine)
            return self.__transactions

    @property
    def config(self):
        try:
            return self.__config
        except:
            self.__config = ConfigPool(self.engine)
            return self.__config

    def sync(self, force=False):
        self.transactions.sync(self.sources.providers, force=force)
        self.config.set('sync.last', datetime.datetime.utcnow(), pickle=True)

    def onbudget(self, df):
        preallocated = self.allocations.get_categories()
        return (df['onbudget'] == 1) | (df['onbudget'].isnull() & ~(df['category_hint'].str.lower().isin(preallocated) | df['description_orig'].str.lower().str.contains('transfer') | df['description_orig'].str.lower().str.contains('p2p')))

    def get_unallocated_transactions(self):
        df = self.transactions.retrieve_df()
        return df[self.onbudget(df)]

    def plot(self):
        df = self.get_unallocated_transactions()

        amounts = df.groupby('date').sum()['amount']

        min_date = min(amounts.index)
        max_date = max(amounts.index)

        daily_amount = self.allocations.get_daily_surplus()

        dates = pd.date_range(start=min_date, end=max_date)
        famounts = [amounts[date] if date in amounts.index else 0 for date in pd.date_range(start=min_date, end=max_date)]

        series = pd.Series(famounts, index=dates)
        series = series[series.index >= pd.to_datetime('2016-03-19')]

        plt.figure( figsize=(11,7) )
        series.plot(label='Daily Spending')
        plt.hlines([daily_amount,self.budget.daily_income().value], *plt.xlim(), label=['Available daily income', 'Total Daily Income'])

        (series.cumsum() / pd.Series(np.arange(1, len(series)+1), series.index)).plot(label='Average daily spending')

        plt.legend()

        plt.tight_layout()

        plt.savefig('test.pdf')

    def plot_new(self, start=None, end=None):
        # These are slow to import, so include them here, so that they are
        # only loaded if necessary.
        import plotly.graph_objs as go
        import plotly.offline as py

        df = self.get_unallocated_transactions()

        amounts = df.groupby('date').sum()['amount'].apply(lambda x: -float(x)/100)

        min_date = min(amounts.index)
        max_date = max(amounts.index)

        daily_amount = self.allocations.get_daily_surplus()

        dates = get_date_range(start_date=min_date, end_date=max_date, inclusive=True)
        famounts = [amounts[date] if date in amounts.index else 0 for date in dates]

        series = pd.Series(famounts, index=dates)
        if start is not None:
            series = series[series.index >= start.date()]
        if end is not None:
            series = series[series.index < end.date()]

        drange = get_date_range(start, end)
        pad = [0]* (len(drange) - len(series))

        trend = (series.cumsum() / pd.Series(np.arange(1, len(series)+1), series.index))
        trace1 = go.Bar(
            x=drange,
            y=list(series)+pad,
            name='Daily Spending'
        )
        trace2 = go.Scatter(
            x=trend.index,
            y=trend,
            name='Average Daily Spending'
        )
        trace3 = go.Scatter(
            x=trend.index,
            y=[daily_amount]*len(trend),
            name='Available daily Income')
        data = [trace1, trace2, trace3]
        layout = go.Layout(
                margin=go.Margin(
                    l=50,
                    r=50,
                    b=50,
                    t=0,
                    pad=0
                )
            )
        fig = go.Figure(data=data, layout=layout)
        plot_url = py.plot(fig, output_type='div', include_plotlyjs=False, show_link=False)
        return plot_url

        #plt.figure( figsize=(11,7) )
        #series.plot(label='Daily Spending')
        #plt.hlines([daily_amount,self.budget.daily_income().value], *plt.xlim(), label=['Available daily income', 'Total Daily Income'])

        #(series.cumsum() / pd.Series(np.arange(1, len(series)+1), series.index)).plot(label='Average daily spending')

        #plt.legend()

        #plt.tight_layout()

        #plt.savefig('test.pdf')

def get_date_range(start_date, end_date, step=datetime.timedelta(1), inclusive=False):
    out = []
    date = start_date
    while date < end_date:
        out.append(date)
        date += step
    if inclusive and date == end_date:
        out.append(date)
    return out

# 0 = Monday, 1 = Tuesday, 2 = Wednesday, 3 = Thursday..
def get_weeks_status(year, daystart=2):
    now = datetime.datetime.now().date()
    start_week = datetime.date(year,1,1)
    start_week += datetime.timedelta( (daystart - start_week.weekday()) % 7 )

    status = {}

    week = start_week
    while week.year == year:
        status[week.month] = status.get(week.month,[]) + [{'surplus': True, 'past': now > week, 'start': week}]
        week += datetime.timedelta(7)

    return status
