import pickle

import pandas
from sqlalchemy import insert, delete, select, update
from sqlalchemy.sql import and_, func
import pytz
import datetime
from . import util

from .db import DBPool, tbl_txn, tbl_src


class UpdateTransactionProviderRegistry(type):
    def __init__(cls, name, bases, dct):
        if not hasattr(cls, '_registry'):
            cls._registry = {}
        try:
            assert cls.name is not None
            cls._registry[cls.name] = cls
        except:
            pass
        super(UpdateTransactionProviderRegistry, cls).__init__(name, bases, dct)


class TransactionProvider(object, metaclass=UpdateTransactionProviderRegistry):
    name = None

    def __init__(self, *args, **kwargs):
        self.id = None
        self.init(*args, **kwargs)

    @classmethod
    def get(cls, name, *args, **kwargs):
        return cls._registry[name](*args, **kwargs)

    def init(self):
        raise NotImplementedError

    def transactions(self, fromdate=None):
        '''
        Returns an iterable (probably generator) object for transactions,
        ordered by date.
        '''
        raise NotImplementedError

    def set_id(self, id):
        self.id = id
        return self

    def update_mapping(self, before, after):
        mapping = {}
        return mapping

    @property
    def update_fields(self):
        return [
            'amount',
            'currency',
            'date',
            'date_orig',
            'description',
            'description_orig',
            'type',
            'category_hint',
            'account',
            'institution',
            'pending'
        ]

    @property
    def compare_fields(self):
        return [
            'account',
            'institution',
            'description_orig',
            'date_orig',
            'type',
            'amount',
            'currency'
        ]

    def compare(self, txn1, txn2):
        if self.provides_tracking:
            return txn1['tracking_id'] == txn2['tracking_id']

        # Returns True if transactions are the same, False otherwise
        for key in self.compare_fields:
            if not str(txn1[key]) == str(txn2[key]):
                return False
        return True

    @property
    def provides_tracking(self):
        return False

    def should_sync(self):
        return True

    def timezone(self):
        raise pytz.utc

class TransactionSourcePool(DBPool):

    def list(self):
        def mapping(source):
            source['options'] = pickle.loads(source['options'])
            return source
        with self.engine.begin() as conn:
            s = select([tbl_src])
            return [mapping(dict(source)) for source in conn.execute(s)]

    @property
    def providers(self):
        return [TransactionProvider.get(source['provider'], **source['options']).set_id(source['id'])
                for source in self.list()]

    def add(self, provider, **opts):
        with self.engine.begin() as conn:
            i = insert(tbl_src).values(provider=provider, options=pickle.dumps(opts))
            conn.execute(i)

    def remove(self, id):
        with self.engine.begin() as conn:
            conn.execute(delete(tbl_src).where(tbl_src.c.id==id))


class TransactionPool(object):

    def __init__(self, engine):
        self.engine = engine

    def sync(self, providers, force=False):  # TODO: Make this multithreaded
        for provider in providers:
            if provider.id is None:
                raise ValueError("Providers must have a valid id.")

            if not force and not provider.should_sync():
                continue

            def add_id(d):
                d['provider_id'] = provider.id
                return d

            txns = [add_id(txn) for txn in provider.transactions()]
            insert, update, remove = self.__get_sync_actions(provider, txns)

            if len(insert) > 0:
                self.add(insert, timezone=provider.timezone)
            if len(update) > 0:
                self.update(update, fields=provider.update_fields)
            if len(remove) > 0:
                self.remove(remove)

    def __get_sync_actions(self, provider, txns):
        if len(txns) == 0:
            return [], {}, []

        txns = sorted(txns, key=lambda x: x['date']) # TODO: Do we need this
        seen_txns = list(self.retrieve(start_date=txns[0]['date'], end_date=txns[-1]['date'], provider=provider.id))

        after = []
        before = []

        for txn in txns:
            if not any( [provider.compare(txn, t) for t in seen_txns] ):
                after.append(txn)

        for t in seen_txns:
            if not any( [provider.compare(txn, t) for txn in txns] ):
                before.append(t)

        mapping = provider.update_mapping(before, after)
        mapping_values = list(mapping.values())

        # Indices absent from mapping values implies insertion
        # list of dictionaries
        insert = [txn for i, txn in enumerate(after) if i not in mapping_values]

        # Mapped indicies imply updating of existing transactions
        # dictionary (by id) of dictionaries
        update = {before[i]['id']: after[j] for i, j in mapping.items()}

        # indices absent from mapping keys implies removal
        # list of ids
        remove = [txn['id'] for i, txn in enumerate(before) if i not in mapping]

        return insert, update, remove

    def add(self, txns, timezone=pytz.utc):
        if not isinstance(txns, list):
            txns = [txns]
        for txn in txns:
            txn['date_seen'] = util.current_date(timezone)
        with self.engine.begin() as conn:
            conn.execute(tbl_txn.insert(), txns)

    def update(self, updates, fields=None):
        with self.engine.begin() as conn:
            for id, txn in updates.items():
                if fields is not None:
                    txn = {field: txn.get(field, None) for field in fields}
                conn.execute(tbl_txn.update().where(tbl_txn.c.id == id).values(txn))

    def remove(self, ids):
        with self.engine.begin() as conn:
            conn.execute(tbl_txn.delete().where(tbl_txn.c.id.in_(ids)))

    def wipe_all(self):
        with self.engine.begin() as conn:
            conn.execute(tbl_txn.delete())
            tbl_txn.create(conn)

    def retrieve(self, start_date=None, end_date=None, date_seen=False, provider=None):
        assert type(start_date) == datetime.date
        assert type(end_date) == datetime.date
        with self.engine.begin() as conn:
            if date_seen:
                date_field = func.min(tbl_txn.c.date, tbl_txn.c.date_seen)
            else:
                date_field = tbl_txn.c.date
            s = select([tbl_txn]).where(
                and_(
                    date_field >= start_date if start_date is not None else True,
                    date_field <= end_date if end_date is not None else True,
                    tbl_txn.c.provider_id == provider if provider is not None else True
                )
            ).order_by(date_field)
            for txn in conn.execute(s):
                yield dict(txn)

    def retrieve_df(self, start_date=None, end_date=None, date_seen=False, provider=None):
        return pandas.DataFrame(list(self.retrieve(start_date, end_date, date_seen, provider)))

    def retrieve_categories(self):
        with self.engine.begin() as conn:
            s = select([tbl_txn.c.category]).distinct()
            s2 = select([tbl_txn.c.category_hint]).distinct()
            for category in conn.execute(s.union(s2)):
                yield category[0]

    def update_transaction(self, id, **props):
        stmt = update(tbl_txn).where(tbl_txn.c.id==id).values(**props)
        with self.engine.begin() as conn:
            conn.execute(stmt)
