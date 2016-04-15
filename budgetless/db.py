from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, \
    Date, Boolean
import datetime

db_metadata = MetaData()
tbl_src = Table('providers', db_metadata,
                            Column('id', Integer, primary_key=True),
                            Column('provider', String, nullable=False),
                            Column('options', String)
                            )

tbl_txn = Table('transactions', db_metadata,
                Column('id', Integer, primary_key=True),
                Column('provider_id', Integer, ForeignKey("providers.id"), nullable=False),

                Column('tracking_id', String),
                Column('date_seen', Date, nullable=False,
                       default=datetime.datetime.utcnow),

                Column('amount', Integer, nullable=False),
                Column('currency', String, default='USD'),

                Column('date', Date),
                Column('date_orig', Date, nullable=False),

                Column('description', String),
                Column('description_orig', String),

                Column('type', String),

                Column('category', String),
                Column('category_hint', String),

                Column('account', String),
                Column('institution', String),

                Column('pending', Boolean),
                Column('flags', String),
                Column('notes', String),
                Column('onbudget', Integer)
                )

tbl_alloc = Table('allocations', db_metadata,
                    Column('id', Integer, primary_key=True),
                    Column('income', Boolean, default=False),

                    Column('category', String),
                    Column('amount', Integer, default=0),
                    Column('interval', String, default='month'),
                    Column('description', String),

                    Column('start', Date),
                    Column('end', Date)
                    )

tbl_conf = Table('config', db_metadata,
               Column('id', Integer, primary_key=True),

               Column('option', String, nullable=False),
               Column('value', String),
               Column('pickle', Boolean, default=False)
               )


class DBPool(object):

    def __init__(self, engine, *args, **kwargs):
        self.engine = engine
        self.init(*args, **kwargs)

    def init(self):
        pass
