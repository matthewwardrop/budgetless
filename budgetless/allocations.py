from .db import DBPool, tbl_alloc
from sqlalchemy import select, insert, delete
import parampy
import datetime

# TODO: Consider optimising this module if required. In particular
# the lookup by date leaves a lot to be desired.

class AllocationPool(DBPool):

    def init(self):
        self.p = parampy.Parameters()
        self.p.scaling(time=(1, 'day'))
        self.zero = self.p._( (0, '$/day') )

    def __get_contribution(self, allocation, date, error=False):
        contrib = self.p._( (allocation['amount'], '$/'+allocation['interval']) )

        if allocation['start'] is None and allocation['end'] is None:
            return contrib

        if date is None:
            date = datetime.date.today()

        included = True

        if allocation['start'] is not None and allocation['start'] > date:
            include = False

        if allocation['end'] is not None and allocation['end'] < date:
            include = False

        if error and not include:
            raise ValueError("Allocation does not contribute.")

        return contrib if include else self.zero

    def get_income(self, date=None):
        income = {}
        for allocation in self.list():
            if allocation['income']:
                try:
                    income[allocation['category']] = self.__get_contribution(allocation, date, error=True)
                except ValueError:
                    pass
        return income

    def get_expenses(self, date=None):
        expenses = {}
        for allocation in self.list():
            if not allocation['income']:
                try:
                    expenses[allocation['category']] = self.__get_contribution(allocation, date, error=True)
                except ValueError:
                    pass
        return expenses

    def get_categories(self, date=None):
        categories = []
        for allocation in self.list():
            try:
                self.__get_contribution(allocation, date, error=True)
                categories.append(allocation['category'])
            except ValueError:
                pass
        return categories

    def get_surplus(self, date=None):
        v = self.p._( (0,'$/day') )
        for income in self.get_income(date).values():
            v += income
        for expense in self.get_expenses(date).values():
            v -= expense
        return v

    def get_daily_surplus(self, date=None):
        return self.get_surplus(date)('$/day').value

    # Database functions
    def clear_cache(self):
        try:
            del self.__list
            del self.__categories
        except:
            pass

    def list(self):
        try:
            return self.__list
        except:
            with self.engine.begin() as conn:
                s = select([tbl_alloc])
                self.__list = list(conn.execute(s))
                return self.__list

    def add(self, **opts):
        self.clear_cache()
        with self.engine.begin() as conn:
            i = insert(tbl_alloc).values(**opts)
            conn.execute(i)

    def remove(self, id):
        self.clear_cache()
        with self.engine.begin() as conn:
            conn.execute(delete(tbl_alloc).where(tbl_alloc.c.id==id))
