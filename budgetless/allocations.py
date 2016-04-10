from .db import DBPool, tbl_alloc
from sqlalchemy import select, insert, delete
import parampy

class AllocationPool(DBPool):

    def init(self):
        self.p = parampy.Parameters()
        self.p.scaling(time=(1, 'day'))

    def get_expenses(self, date=None):
        expenses = {}
        for allocation in self.list():
            if not allocation['income']:
                expenses[allocation['category']] = self.p._( (allocation['amount'], '$/'+allocation['interval']) )
        return expenses

    def get_categories(self, date=None):
        try:
            return self.__categories
        except:
            self.__categories = list(set([d['category'] for d in self.list()]))
            return self.__categories

    def get_income(self, date=None):
        income = {}
        for allocation in self.list():
            if allocation['income']:
                income[allocation['category']] = self.p._( (allocation['amount'], '$/'+allocation['interval']) )
        return income

    def get_surplus(self, date=None):
        v = self.p._( (0,'$/day') )
        print (self.get_income())
        for income in self.get_income().values():
            v += income
        for expense in self.get_expenses().values():
            v -= expense
        return v

    def get_daily_surplus(self, date=None):
        return self.get_surplus(date)('$/day').value


    # Database functions
    def clear_cache(self):
        try:
            del self.__categories
        except:
            pass

    def list(self):
        with self.engine.begin() as conn:
            s = select([tbl_alloc])
            return list(conn.execute(s))

    def add(self, **opts):
        self.clear_cache()
        with self.engine.begin() as conn:
            i = insert(tbl_alloc).values(**opts)
            conn.execute(i)

    def remove(self, id):
        self.clear_cache()
        with self.engine.begin() as conn:
            conn.execute(delete(tbl_alloc).where(tbl_alloc.c.id==id))
