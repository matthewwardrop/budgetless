import datetime

from sqlalchemy import create_engine

import numpy as np
import pandas as pd

from .allocations import AllocationPool
from .config import ConfigPool
from .db import db_metadata
from .transactions import TransactionPool, TransactionSourcePool
from .analysis import Analysis
from . import util

class Budget(object):

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

    DEFAULT_WEEK_START = 5 # Saturday, 0=Monday

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
    def analysis(self):
        try:
            return self.__analysis
        except:
            self.__analysis = Analysis(self)
            return self.__analysis

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
